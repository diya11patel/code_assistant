
# app/parsers/laravel_processor.py

import os
import re
from typing import List, Dict, Any
from tree_sitter_languages import get_parser

class LaravelProcessor:
    def __init__(self, root_path: str):
        self.root_path = root_path
        self.supported_extensions = [".php"]
        self.parser = get_parser("php")

    def chunk_codebase(self) -> List[Dict[str, Any]]:
        chunks: List[Dict[str, Any]] = []
        for dirpath, _, filenames in os.walk(self.root_path):
            for filename in filenames:
                if filename.endswith(tuple(self.supported_extensions)):
                    full_path = os.path.join(dirpath, filename)
                    file_chunks = self.chunk_php_file(full_path)
                    chunks.extend(file_chunks)
        return chunks
    
    def chunk_using_treesitter(self) -> List[Dict[str, Any]]:
        chunks = []
        for php_file in self.root_path.rglob("*.php"):
            try:
                code = php_file.read_text()
                tree = self.parser.parse(bytes(code, "utf8"))
                root_node = tree.root_node

                for node in root_node.children:
                    if node.type in ("namespace_definition", "class_declaration", "function_definition"):
                        start_byte = node.start_byte
                        end_byte = node.end_byte
                        chunk_content = code[start_byte:end_byte]

                        chunks.append({
                            "content": chunk_content,
                            "metadata": {
                                "file": str(php_file),
                                "type": node.type,
                                "start_line": node.start_point[0] + 1,
                                "end_line": node.end_point[0] + 1,
                            }
                        })
            except Exception as e:
                print(f"Error parsing {php_file}: {e}")

        return chunks
    

    def chunk_php_file(self, file_path: str) -> List[Dict]:
        chunks = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            current_chunk = []
            metadata = {"file": file_path}
            in_function = False
            function_signature = ""

            for line in lines:
                # Detect class name
                class_match = re.match(r"\s*class\s+(\w+)", line)
                if class_match:
                    metadata["class"] = class_match.group(1)

                # Detect function
                function_match = re.match(r"\s*(public|protected|private)?\s*function\s+(\w+)", line)
                if function_match:
                    if current_chunk:
                        chunks.append({
                            "content": "".join(current_chunk),
                            "metadata": metadata.copy()
                        })
                        current_chunk = []

                    in_function = True
                    function_signature = function_match.group(2)
                    metadata["function"] = function_signature

                if in_function:
                    current_chunk.append(line)

            if current_chunk:
                chunks.append({
                    "content": "".join(current_chunk),
                    "metadata": metadata.copy()
                })

        except Exception as e:
            print(f"Error reading or parsing {file_path}: {e}")

        return chunks

     
    def _get_files_to_process(self, project_path: str) -> list[str]:
            """
            Identifies relevant files in the project path for processing.
            Filters by extension and excludes common unnecessary directories/files.
            """
            filepaths = []
            allowed_extensions = {".py", ".java", ".js", ".ts", ".go", ".rs", ".c", ".cpp", ".h", ".md", ".txt", ".json", ".yaml", ".yml"}
            excluded_dirs = {".git", "__pycache__", "node_modules", "target", "build", "dist", "venv", ".venv"}
            excluded_files = {".DS_Store"}

            print(f"Scanning for files in: {project_path}")
            for root, dirs, files in os.walk(project_path, topdown=True):
                # Modify dirs in-place to skip excluded directories
                dirs[:] = [d for d in dirs if d not in excluded_dirs]
                for file_name in files:
                    if file_name in excluded_files:
                        continue
                    _, ext = os.path.splitext(file_name)
                    if ext.lower() in allowed_extensions:
                        filepaths.append(os.path.join(root, file_name))
            print(f"Found {len(filepaths)} files to process.")
            return filepaths