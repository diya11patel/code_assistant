
# app/parsers/laravel_processor.py

import os
import re
from typing import List, Dict, Any
from tree_sitter import Node
from tree_sitter_languages import get_parser, get_language
from tree_sitter import Parser


class LaravelProcessor:
    def __init__(self, root_path: str):
        self.root_path = root_path
        self.supported_extensions = [".php"] # Primarily for PHP in Laravel
        try:
            self.parser = get_parser("php")
            print("Tree-sitter PHP parser loaded successfully.")
        except Exception as e: # pylint: disable=broad-except
            print(f"Failed to load tree-sitter PHP parser: {e}. Will attempt regex-based chunking for PHP files. Chunking quality may be significantly affected for complex files.")
            self.parser = None # Handle parser loading failure gracefully

    def chunk_codebase(self) -> List[Dict[str, Any]]:
        chunks: List[Dict[str, Any]] = []
        for dirpath, _, filenames in os.walk(self.root_path):
            for filename in filenames:
                if filename.endswith(tuple(self.supported_extensions)):
                    full_path = os.path.join(dirpath, filename)
                    if self.parser:
                        # Prioritize tree-sitter based chunking
                        file_chunks = self.chunk_using_treesitter(full_path)
                    else:
                        # Fallback to regex-based chunking if tree-sitter parser is not available
                        print(f"Using regex-based chunking for: {full_path}")
                        file_chunks = self.chunk_using_regex(full_path)
                    chunks.extend(file_chunks)
        print(f"Created {len(chunks)} chunks out of the code")
        return chunks
    
    def _extract_node_text(self, node: Node, content_bytes: bytes) -> str:
        """Extracts text from a tree-sitter node."""
        return content_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="ignore")

    def _traverse_node(self, node: Node, content_bytes: bytes, file_path: str, current_namespace: str = "", current_class_name: str = "") -> List[Dict[str, Any]]:
        """
        Recursively traverses the AST to find and create chunks for functions, methods, etc.
        """
        chunks = []
        node_type = node.type

        # Capture namespace to provide context
        if node_type == 'namespace_definition':
            name_node = node.child_by_field_name('name')
            if name_node:
                current_namespace = self._extract_node_text(name_node, content_bytes)

        # Capture class name to provide context
        elif node_type == 'class_declaration':
            name_node = node.child_by_field_name('name')
            if name_node:
                class_name_only = self._extract_node_text(name_node, content_bytes)
                # Update current_class_name with full namespace if available
                current_class_name = f"{current_namespace}\\{class_name_only}" if current_namespace else class_name_only
                # Optionally, you could create a chunk for the class definition itself here
                # For now, we focus on methods/functions within the class.

        # Capture functions and methods as primary chunks
        elif node_type == 'method_declaration' or node_type == 'function_definition':
            name_node = node.child_by_field_name('name')
            if name_node:
                function_name = self._extract_node_text(name_node, content_bytes)
                
                # Construct a fully qualified name for better context
                full_name_parts = []
                if current_namespace:
                    full_name_parts.append(current_namespace)
                if current_class_name and current_class_name.split("\\")[-1] != function_name: # Avoid class::class for constructors
                    # Use the fully qualified class name for methods
                    full_name_parts.append(current_class_name.split("\\")[-1] if node_type == 'method_declaration' else "") # Get simple class name for method
                
                qualified_prefix = "\\".join(filter(None, full_name_parts))
                if qualified_prefix and node_type == 'method_declaration':
                    full_function_name = f"{qualified_prefix}::{function_name}"
                elif qualified_prefix:
                     full_function_name = f"{qualified_prefix}\\{function_name}"
                else:
                    full_function_name = function_name

                chunk_content = self._extract_node_text(node, content_bytes)
                chunks.append({
                    "content": chunk_content,
                    "metadata": {
                        "file": file_path,
                        "type": "method" if node_type == 'method_declaration' else "function",
                        "namespace": current_namespace,
                        "class_name": current_class_name.split("\\")[-1] if current_class_name and node_type == 'method_declaration' else "",
                        "function_name": function_name,
                        "full_name": full_function_name,
                        "start_line": node.start_point[0] + 1, # tree-sitter is 0-indexed for lines
                        "end_line": node.end_point[0] + 1
                    }
                })
                # We've captured this function/method as a chunk, so we don't recurse further into its body
                # to avoid overly granular sub-chunks unless specifically desired.
                return chunks 

        # Recurse for other node types to find nested structures
        for child_node in node.children:
            chunks.extend(self._traverse_node(child_node, content_bytes, file_path, current_namespace, current_class_name))
        return chunks

    def chunk_using_treesitter(self, file_path: str) -> List[Dict[str, Any]]:
        if not self.parser:
            print(f"Tree-sitter parser not available for PHP. Cannot chunk file: {file_path}")
            return []
        chunks: List[Dict[str, Any]] = []
        try:
            with open(file_path, "rb") as f: # Read as bytes for tree-sitter
                content_bytes = f.read()
            
            if not content_bytes.strip(): # Skip empty or whitespace-only files
                return []

            tree = self.parser.parse(content_bytes)
            # Start traversal from the root node of the AST
            chunks.extend(self._traverse_node(tree.root_node, content_bytes, file_path))
            
            # Fallback: if no specific chunks (functions/methods) were found,
            # and the file has content, chunk the whole file.
            # This is useful for scripts, config files, or files without standard function/class structures.
            if not chunks and content_bytes.strip():
                 chunks.append({
                    "content": content_bytes.decode("utf-8", errors="ignore"),
                    "metadata": {
                        "file": file_path,
                        "type": "file_content", # Indicate it's the whole file
                        "namespace": "",
                        "class_name": "",
                        "function_name": "",
                        "full_name": os.path.basename(file_path), # Use filename as a general name
                        "start_line": 1,
                        "end_line": content_bytes.decode("utf-8", errors="ignore").count('\n') + 1
                    }
                })
        except FileNotFoundError:
            print(f"File not found during chunking: {file_path}")
        except Exception as e:
            print(f"Error parsing {file_path} with tree-sitter: {e}")
        return chunks
    
    def _extract_block_with_braces(self, text_content: str, match_start_offset: int) -> tuple[str | None, int]:
        """
        Tries to extract a code block enclosed in curly braces.
        Starts searching for the first '{' at or after match_start_offset.
        Returns the block content (including braces) and the end offset in the original text_content.
        NOTE: This is a simplified implementation and can be fooled by braces in comments or strings.
        """
        try:
            open_brace_index = text_content.index('{', match_start_offset)
        except ValueError:
            return None, -1 # No opening brace found

        brace_level = 1
        current_pos = open_brace_index + 1
        content_lines = text_content.splitlines()

        while current_pos < len(text_content):
            char = text_content[current_pos]
            if char == '{':
                brace_level += 1
            elif char == '}':
                brace_level -= 1
                if brace_level == 0:
                    block_text = text_content[open_brace_index : current_pos + 1]
                    return block_text, current_pos + 1
            current_pos += 1
        return None, -1 # Unmatched brace

    def chunk_using_regex(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Chunks PHP code using regular expressions. Less accurate than tree-sitter.
        """
        chunks: List[Dict[str, Any]] = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except FileNotFoundError:
            print(f"File not found during regex chunking: {file_path}")
            return []
        except Exception as e:
            print(f"Error reading file {file_path} for regex chunking: {e}")
            return []

        if not content.strip():
            return []

        # Regex patterns (simplified for clarity, can be made more comprehensive)
        # For capturing current namespace
        namespace_pattern = re.compile(r"^\s*namespace\s+([^;]+);", re.MULTILINE)
        # For classes
        class_pattern = re.compile(
            r"^\s*(?:abstract\s+|final\s+)*class\s+([a-zA-Z_\x7f-\xff][a-zA-Z0-9_\x7f-\xff]*)(?:\s+extends\s+[^{]+)?(?:\s+implements\s+[^{]+)?\s*{",
            re.MULTILINE
        )
        # For functions/methods
        function_pattern = re.compile(
            r"^\s*(?:(?:public|protected|private|static)\s+)*(?:function)\s+([a-zA-Z_\x7f-\xff][a-zA-Z0-9_\x7f-\xff]*)\s*\([^)]*\)\s*(?:[:]\s*\w+\s*)?{",
            re.MULTILINE
        )

        current_namespace = ""
        ns_match = namespace_pattern.search(content)
        if ns_match:
            current_namespace = ns_match.group(1).strip()

        # Find classes and functions
        # Note: This simple iteration won't handle nested classes/functions well for context.
        # It processes them as they appear in the file.
        definitions = []
        for pattern, def_type in [(class_pattern, "class"), (function_pattern, "function")]: # Order matters if functions can be outside classes
            for match in pattern.finditer(content):
                definitions.append({"match": match, "type": def_type})
        
        # Sort by start position to process in order
        definitions.sort(key=lambda x: x["match"].start())

        for definition in definitions:
            match = definition["match"]
            def_type = definition["type"]
            name = match.group(1)
            
            block_content, _ = self._extract_block_with_braces(content, match.start())
            
            if block_content:
                start_line = content.count('\n', 0, match.start()) + 1
                end_line = start_line + block_content.count('\n')
                
                # Basic metadata, less rich than tree-sitter
                metadata = {
                    "file": file_path,
                    "type": def_type, # Could be 'method' if inside a class context, harder with pure regex
                    "namespace": current_namespace, # Global namespace for the file
                    "class_name": name if def_type == "class" else "", # Simplified
                    "function_name": name if def_type == "function" else "",
                    "full_name": f"{current_namespace}\\{name}" if current_namespace else name,
                    "start_line": start_line,
                    "end_line": end_line,
                }
                chunks.append({"content": block_content, "metadata": metadata})

        if not chunks and content.strip(): # Fallback to whole file if no regex chunks found
            chunks.append({
                "content": content,
                "metadata": {
                    "file": file_path, "type": "file_content_regex",
                    "full_name": os.path.basename(file_path),
                    "start_line": 1, "end_line": content.count('\n') + 1
                }
            })
        return chunks
        
    def _get_files_to_process(self, project_path: str) -> list[str]:
            """
            Identifies relevant files in the project path for processing.
            Filters by extension and excludes common unnecessary directories/files.
            """
            filepaths = []
            # Tailored for Laravel, but can be expanded.
            # `chunk_codebase` uses `self.supported_extensions` which is currently just ".php".
            # This method provides a broader filter if used elsewhere or if `supported_extensions` is expanded.
            allowed_extensions = {
                ".php", ".blade.php", # Core Laravel files
                ".js", ".vue", ".ts",  # Frontend assets
                ".css", ".scss",       # Styles
                ".env", ".md", ".txt", ".json", ".yaml", ".yml", # Config, docs, data
            }
            excluded_dirs = {
                ".git", "__pycache__", "node_modules", "vendor", # Common and PHP vendor
                "storage/framework", "storage/logs", "storage/app/public", # Laravel specific storage
                "public/build", "public/hot", # Laravel Vite/Mix build output
                "bootstrap/cache", # Laravel cache
                "target", "build", "dist", ".venv", "venv", # General build/env dirs
            }
            excluded_files = {".DS_Store", "Thumbs.db", ".phpunit.result.cache"}

            print(f"Scanning for files in: {project_path}")
            for root, dirs, files in os.walk(project_path, topdown=True):
                # Modify dirs in-place to skip excluded directories
                dirs[:] = [d for d in dirs if d not in excluded_dirs and not d.startswith('.')]
                for file_name in files:
                    if file_name in excluded_files:
                        continue
                    _, ext = os.path.splitext(file_name)
                    if ext.lower() in allowed_extensions:
                        filepaths.append(os.path.join(root, file_name))
            print(f"Found {len(filepaths)} files to process.")
            return filepaths

# Example usage (for testing this file directly)
# if __name__ == "__main__":
#     # Create a dummy Laravel-like project structure for testing
#     # Ensure you have 'tree_sitter' and 'tree_sitter_languages' installed
#     # And that the PHP grammar can be loaded.
#     processor = LaravelProcessor(root_path="path/to/your/laravel_project")
#     all_chunks = processor.chunk_codebase()
#     for i, chunk_info in enumerate(all_chunks):
#         print(f"\n--- Chunk {i+1} ---")
#         print(f"  File: {chunk_info['metadata']['file']}")
#         print(f"  Type: {chunk_info['metadata']['type']}")
#         print(f"  Name: {chunk_info['metadata'].get('full_name', 'N/A')}")
#         print(f"  Lines: {chunk_info['metadata'].get('start_line')} - {chunk_info['metadata'].get('end_line')}")
#         # print(f"  Content:\n{chunk_info['content'][:200]}...") # Print start of content
#     print(f"\nTotal chunks created: {len(all_chunks)}")