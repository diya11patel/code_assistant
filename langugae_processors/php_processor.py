import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import asdict
import tree_sitter_php as tsphp
# import tree_sitter_javascript as tsjs
# import tree_sitter_html as tshtml
from tree_sitter import Language, Parser, Node
from dto.value_objects import CodeChunk
from utils.logger import LOGGER


class LaravelProcessor:
    def __init__(self, root_path: str = None):
        # Initialize parsers

        # self.js_parser = Parser()
        # self.html_parser = Parser()

        # Load languages
        PHP_LANGUAGE = Language(tsphp.language_php())
        self.php_parser = Parser(PHP_LANGUAGE)

        # JS_LANGUAGE = Language(tsjs.language())
        # HTML_LANGUAGE = Language(tshtml.language())

        # self.php_parser.set_language(PHP_LANGUAGE)
        # self.js_parser.set_language(JS_LANGUAGE)
        # self.html_parser.set_language(HTML_LANGUAGE)
        self.root_path = root_path
        self.chunks: List[CodeChunk] = []

    def analyze_codebase(self, laravel_root: str) -> List[CodeChunk]:
        """Analyze the codebase by traversing folders and routing files based on folder names."""
        self.root_path = laravel_root
        self.chunks = []

        # Dictionary to map folder names to parser methods
        folder_parsers = {
            "routes": self._parse_route_folder,
            "config": self._parse_config_folder,
            "env": self._parse_env_folder,  # For .env files
            "views": self._parse_blade_folder
        }

        # Traverse folders
        for root, dirs, files in os.walk(laravel_root, topdown=True):
            relative_path = os.path.relpath(root, laravel_root)
            folder_names = relative_path.split(os.sep)

            # Skip excluded directories
            if any(excluded in root for excluded in {
                ".git", "__pycache__", "node_modules", "vendor",
                "storage/framework", "storage/logs", "storage/app/public",
                "public/build", "public/hot", "bootstrap/cache", "target",
                "build", "dist", ".venv", "venv"
            }) or any(f.startswith('.') for f in folder_names):
                continue
            
            # Determine parser based on any folder name in the path
            parser = None
            for folder_name in folder_names:
                if folder_name.lower() in folder_parsers:
                    parser = folder_parsers[folder_name.lower()]
                    break

            # Route folder to specific parser if matched
            if parser:
                parser(root, files)
            else:
                # Fallback: process all .php files in the folder with _parse_php_file
                php_files = [f for f in files if f.endswith(('.php', '.blade.php'))]
                if php_files:
                    self._parse_php_folder(root, php_files)

        return self.chunks

    def _parse_route_folder(self, folder_path: str, files: list[str]):
        """Parse all route files in the folder."""
        for file_name in files:
            if file_name.endswith('.php'):
                file_path = os.path.join(folder_path, file_name)
                self._parse_route_file(Path(file_path))

    def _parse_config_folder(self, folder_path: str, files: list[str]):
        """Parse all config files in the folder."""
        for file_name in files:
            if file_name.endswith('.php'):
                file_path = os.path.join(folder_path, file_name)
                self._parse_config_file(Path(file_path))

    def _parse_env_folder(self, folder_path: str, files: list[str]):
        """Parse .env file in the folder."""
        env_file = next((f for f in files if f == '.env'), None)
        if env_file:
            file_path = os.path.join(folder_path, env_file)
            self._parse_env_file(Path(file_path))

    def _parse_blade_folder(self, folder_path: str, files: list[str]):
        """Parse all Blade files in the folder."""
        for file_name in files:
            if file_name.endswith('.blade.php'):
                file_path = os.path.join(folder_path, file_name)
                self._parse_blade_file(Path(file_path))

    def _parse_php_folder(self, folder_path: str, files: list[str]):
        """Parse all PHP files in the folder with generic PHP parser."""
        for file_name in files:
            file_path = os.path.join(folder_path, file_name)
            file_type = "php" if file_name.endswith('.php') else "blade_template"
            self._parse_php_file(Path(file_path), file_type)

    def _get_file_type(self, file_path: str) -> str:
        """Determine file type based on extension."""
        _, ext = os.path.splitext(file_path)
        if ext == ".php":
            return "php"
        elif ext == ".blade.php":
            return "blade_template"
        elif ext == ".env":
            return "env"
        return ext.lstrip('.')

    def _parse_php_file(self, file_path: Path, file_type: str):
        """Parse a PHP file and extract meaningful chunks"""
        try:
            LOGGER.info(f"Parsing file: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            return

        tree = self.php_parser.parse(bytes(content, 'utf8'))

        # Extract classes
        for class_node in self._query_nodes(tree.root_node, "class_declaration"):
            class_name = self._get_node_text(class_node.child_by_field_name("name"), content)

            chunk = CodeChunk(
                type=file_type,
                name=class_name,
                file_path=str(file_path),
                start_line=class_node.start_point[0] + 1,
                end_line=class_node.end_point[0] + 1,
                content=self._get_node_text(class_node, content),
                metadata=self._extract_class_metadata(class_node, content),
                import_dependencies=self._extract_dependencies(tree.root_node, content),
                method_dependencies=[]
            )
            self.chunks.append(chunk)

            # Extract methods within the class
            for method_node in self._query_nodes(class_node, "method_declaration"):
                method_name = self._get_node_text(method_node.child_by_field_name("name"), content)

                method_chunk = CodeChunk(
                    type=f"{file_type}_method",
                    name=f"{class_name}::{method_name}",
                    file_path=str(file_path),
                    start_line=method_node.start_point[0] + 1,
                    end_line=method_node.end_point[0] + 1,
                    content=self._get_node_text(method_node, content),
                    metadata=self._extract_method_metadata(method_node, content), # Keep existing metadata extraction
                    import_dependencies=self._extract_dependencies(tree.root_node, content),
                    method_dependencies=self._extract_internal_method_calls(method_node, content) # Add internal method call dependencies
                )
                self.chunks.append(method_chunk)

    def _parse_route_file(self, file_path: Path):
        """Parse Laravel route files with detailed route structure."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            return

        tree = self.php_parser.parse(bytes(content, 'utf8'))
        routes = self._find_route_definitions(tree.root_node, content)

        import re
        for i, route_call in enumerate(routes):
            # Extract route details
            route_text = route_call['content']
            metadata = route_call['metadata'].copy()
            start_line = route_call['start_line']
            end_line = route_call['end_line']

            # Attempt to parse route method (e.g., get, post) and URI
            method_match = re.search(r'Route::(\w+)\s*\(\s*[\'"]', route_text)
            uri_match = re.search(r'[\'"]((?:[^\'"]|\\.)*)[\'"]', route_text)
            controller_match = re.search(r'[\'"]((?:[^\'"]|\\.)*)@[\w]+[\'"]', route_text)

            metadata['method'] = method_match.group(1) if method_match else 'unknown'
            metadata['uri'] = uri_match.group(1) if uri_match else 'unknown'
            metadata['controller'] = controller_match.group(1) if controller_match else 'unknown'

            chunk = CodeChunk(
                type="route",
                name=f"Route_{metadata['method']}_{metadata['uri'].replace('/', '_')}_{i + 1}",
                file_path=str(file_path),
                start_line=start_line,
                end_line=end_line,
                content=route_text,
                metadata=metadata,
                import_dependencies=self._extract_route_dependencies(route_text),
                method_dependencies=[]
            )
            self.chunks.append(chunk)

    def _parse_config_file(self, file_path: Path):
        """Parse Laravel config files (e.g., PHP arrays or key-value pairs)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            return

        # Simple parsing for config files (assumes PHP return array syntax)
        tree = self.php_parser.parse(bytes(content, 'utf8'))
        root_node = tree.root_node

        # Look for return statements with arrays
        return_nodes = self._query_nodes(root_node, "return_statement")
        for return_node in return_nodes:
            array_node = next((child for child in return_node.children if child.type == "array_creation_expression"), None)
            if array_node:
                chunk = CodeChunk(
                    type="config",
                    name=os.path.basename(file_path),
                    file_path=str(file_path),
                    start_line=array_node.start_point[0] + 1,
                    end_line=array_node.end_point[0] + 1,
                    content=self._get_node_text(array_node, content),
                    metadata={"config_file": True},
                    import_dependencies=[],
                    method_dependencies=[]
                )
                self.chunks.append(chunk)
            else:
                # Fallback: treat entire file as a chunk if no array found
                chunk = CodeChunk(
                    type="config",
                    name=os.path.basename(file_path),
                    file_path=str(file_path),
                    start_line=1,
                    end_line=content.count('\n') + 1,
                    content=content,
                    metadata={"config_file": True},
                    import_dependencies=[],
                    method_dependencies=[]
                )
                self.chunks.append(chunk)

    def _parse_env_file(self, file_path: Path):
        """Parse .env files (key-value pairs)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            return

        # Parse key-value pairs (e.g., KEY=VALUE)
        lines = content.splitlines()
        current_line = 1
        current_content = []

        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):  # Ignore comments and empty lines
                current_content.append(line)
            if line or current_content:  # Create chunk when line ends or at EOF
                chunk = CodeChunk(
                    type="env",
                    name=f"Env_{os.path.basename(file_path)}_{current_line}",
                    file_path=str(file_path),
                    start_line=current_line,
                    end_line=current_line,
                    content=line if line else "\n".join(current_content),
                    metadata={"env_variable": True},
                    import_dependencies=[],
                    method_dependencies=[]
                )
                self.chunks.append(chunk)
                current_line += 1
                current_content = []


    def _parse_blade_file(self, file_path: Path):
        """Parse Blade template files with section-based chunking."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            return

        import re
        lines = content.splitlines()
        current_section = []
        current_start_line = 1
        section_pattern = re.compile(r'@section\s*\(\s*[\'"](\w+)[\'"]\s*\)|@component\s*\(\s*[\'"](\w+)[\'"]\s*\)')

        for i, line in enumerate(lines, 1):
            match = section_pattern.search(line)
            if match:
                # End previous section if exists
                if current_section:
                    self._create_blade_chunk(file_path, current_section, current_start_line, i - 1)
                    current_section = []
                current_start_line = i
            current_section.append(line)

        # Handle the last section or entire file if no sections
        if current_section:
            self._create_blade_chunk(file_path, current_section, current_start_line, len(lines))

    def _create_blade_chunk(self, file_path: Path, lines: List[str], start_line: int, end_line: int):
        import re
        content = "\n".join(lines)
        base_name = os.path.basename(file_path).replace('.blade.php', '')
        section_match = re.search(r'@section\s*\(\s*[\'"](\w+)[\'"]\s*\)', content)
        component_match = re.search(r'@component\s*\(\s*[\'"](\w+)[\'"]\s*\)', content)

        if section_match:
            name = f"{base_name}_blade_{section_match.group(1)}"
        elif component_match:
            name = f"{base_name}_blade_{component_match.group(1)}"
        else:
            name = f"{base_name}_blade_default_{start_line}"

        metadata = self._extract_blade_metadata(content)
        dependencies = self._extract_blade_dependencies(content)

        chunk = CodeChunk(
            type="blade_template",
            name=name,
            file_path=str(file_path),
            start_line=start_line,
            end_line=end_line,
            content=content,
            metadata=metadata,
            import_dependencies=dependencies,
            method_dependencies=[]
        )
        self.chunks.append(chunk)

    def _query_nodes(self, node: Node, node_type: str) -> List[Node]:
        """Find all nodes of a specific type"""
        results = []
        if node.type == node_type:
            results.append(node)

        for child in node.children:
            results.extend(self._query_nodes(child, node_type))

        return results

    def _get_node_text(self, node: Node, source_code: str) -> str:
        """Get the text content of a node"""
        if node is None:
            return ""
        return source_code[node.start_byte:node.end_byte]

    def _extract_class_metadata(self, class_node: Node, content: str) -> Dict[str, Any]:
        """Extract metadata from a class node"""
        metadata = {}

        # Check if it extends another class
        if class_node.child_by_field_name("superclass"):
            superclass = self._get_node_text(class_node.child_by_field_name("superclass"), content)
            metadata["extends"] = superclass

        # Check for implements
        if class_node.child_by_field_name("interfaces"):
            interfaces = self._get_node_text(class_node.child_by_field_name("interfaces"), content)
            metadata["implements"] = interfaces

        # Count methods
        methods = self._query_nodes(class_node, "method_declaration")
        metadata["method_count"] = len(methods)
        metadata["method_names"] = [
            self._get_node_text(m.child_by_field_name("name"), content)
            for m in methods
        ]

        return metadata

    def _extract_method_metadata(self, method_node: Node, content: str) -> Dict[str, Any]:
        """Extract metadata from a method node"""
        metadata = {}

        # Check visibility
        for child in method_node.children:
            if child.type == "visibility_modifier":
                metadata["visibility"] = self._get_node_text(child, content)
                break

        # Check if static
        for child in method_node.children:
            if child.type == "static_modifier":
                metadata["static"] = True
                break

        # Count parameters
        params = method_node.child_by_field_name("parameters")
        if params:
            param_count = len([c for c in params.children if c.type == "simple_parameter"])
            metadata["parameter_count"] = param_count
            
        return metadata
 
    def _extract_dependencies(self, root_node: Node, content: str) -> List[str]:
        """Extract use statements and dependencies - FIXED VERSION"""
        dependencies = []
        # Method 1: Look for namespace_use_declaration nodes
        use_declarations = self._query_nodes(root_node, "namespace_use_declaration")
        for use_decl in use_declarations:
            # Get the use clause
            use_clauses = self._query_nodes(use_decl, "namespace_use_clause")
            for clause in use_clauses:
                qualified_name = self._query_nodes(clause, "qualified_name")
                if qualified_name:
                    dep = self._get_node_text(qualified_name[0], content)
                    if dep:
                        dependencies.append(dep)
    
        # Method 2: Fallback - regex parsing for use statements
        if not dependencies:
            import re
            use_patterns = [
                r'use\s+([\\A-Za-z0-9_]+(?:\\[A-Za-z0-9_]+)*)\s*;',  # Standard use
                r'use\s+([\\A-Za-z0-9_]+(?:\\[A-Za-z0-9_]+)*)\s+as\s+[A-Za-z0-9_]+\s*;',  # Use with alias
                r'use\s+function\s+([\\A-Za-z0-9_]+(?:\\[A-Za-z0-9_]+)*)\s*;',  # Use function
                r'use\s+const\s+([\\A-Za-z0-9_]+(?:\\[A-Za-z0-9_]+)*)\s*;',  # Use const
            ]
            
            for pattern in use_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                dependencies.extend(matches)
            
        # Method 3: Additional Laravel-specific patterns
        laravel_patterns = [
            r'new\s+([A-Z][A-Za-z0-9_]*)',  # new ClassName()
            r'::class',  # SomeClass::class
            r'@extends\([\'"]([^\'"]+)[\'"]\)',  # Blade extends
            r'@include\([\'"]([^\'"]+)[\'"]\)',  # Blade includes
        ]   
        import re
        
        for pattern in laravel_patterns:
            matches = re.findall(pattern, content)
            dependencies.extend(matches)

        # Clean up dependencies
        cleaned_deps = []
        for dep in dependencies:
            dep = dep.strip().strip('\\')
            if dep and dep not in cleaned_deps:
                cleaned_deps.append(dep)

        return cleaned_deps


    def _extract_internal_method_calls(self, method_node: Node, source_code: str) -> List[str]:
        """Extracts internal method calls (e.g., $this->foo(), self::bar()) from a method body."""
        internal_calls = []
        # Method body is typically a 'compound_statement' node
        method_body = None
        for child in method_node.children:
            if child.type == 'compound_statement': # This is usually the { ... } block
                method_body = child
                break
        
        if not method_body:
            return internal_calls

        # Find $this->method() calls
        member_calls = self._query_nodes(method_body, "member_call_expression")
        for call_node in member_calls:
            object_node = call_node.child_by_field_name("object")
            name_node = call_node.child_by_field_name("name") # This should be an 'identifier' or 'variable_name'
            if object_node and name_node and object_node.type == 'variable_name' and self._get_node_text(object_node, source_code) == "$this":
                method_name_text = self._get_node_text(name_node, source_code)
                internal_calls.append(f"self::{method_name_text}") # Standardize to self:: for instance calls

        # Find self::method(), parent::method(), static::method() calls
        scoped_calls = self._query_nodes(method_body, "scoped_call_expression")
        for call_node in scoped_calls:
            scope_node = call_node.child_by_field_name("scope") # e.g., 'name' node for 'self', 'parent'
            name_node = call_node.child_by_field_name("name")   # e.g., 'identifier' for method name
            if scope_node and name_node:
                scope_text = self._get_node_text(scope_node, source_code)
                # Check for self, parent, static (internal) OR other class names (external static)
                # For external static calls, scope_node.type would typically be 'name'
                if scope_text in ["self", "parent", "static"] or scope_node.type == 'name':
                    method_name_text = self._get_node_text(name_node, source_code)
                    # If it's not self, parent, or static, it's an external static call
                    # We keep the full scope_text::method_name_text format
                    internal_calls.append(f"{scope_text}::{method_name_text}")
        
        return list(set(internal_calls)) # Remove duplicates

    def _find_route_definitions(self, root_node: Node, content: str) -> List[Dict]:
        """Find Route:: method calls"""
        routes = []

        # This is simplified - you'd want more sophisticated parsing
        # Look for method calls on "Route"
        method_calls = self._query_nodes(root_node, "member_call_expression")

        for call in method_calls:
            call_text = self._get_node_text(call, content)
            if "Route::" in call_text:
                routes.append({
                    'start_line': call.start_point[0] + 1,
                    'end_line': call.end_point[0] + 1,
                    'content': call_text,
                    'metadata': {'route_definition': True}
                })

        return routes

    def _extract_route_dependencies(self, route_text: str) -> List[str]:
        """Extract dependencies from route definitions (e.g., controllers, middleware)."""
        dependencies = []
        import re
        # Match controller classes (e.g., 'App\Http\Controllers\HomeController@index')
        controller_match = re.search(r'[\'"](\w+\\[\w\\]+)@[\w]+[\'"]', route_text)
        if controller_match:
            dependencies.append(controller_match.group(1))
        # Match middleware (e.g., 'middleware' => ['auth'])
        middleware_match = re.search(r'middleware\s*=>\s*[\'"](\w+(?:\\?\w+)*)[\'"]', route_text)
        if middleware_match:
            dependencies.append(middleware_match.group(1))
        return dependencies

    def _extract_blade_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata from Blade templates"""
        metadata = {}

        # Count Blade directives
        blade_directives = ['@extends', '@section', '@yield', '@include', '@component']
        for directive in blade_directives:
            count = content.count(directive)
            if count > 0:
                metadata[directive.replace('@', '')] = count

        return metadata

    def _extract_blade_dependencies(self, content: str) -> List[str]:
        """Extract Blade template dependencies"""
        dependencies = []

        # Look for @extends, @include, etc.
        import re

        extends_matches = re.findall(r"@extends\(['\"](.+?)['\"]\)", content)
        include_matches = re.findall(r"@include\(['\"](.+?)['\"]\)", content)

        dependencies.extend(extends_matches)
        dependencies.extend(include_matches)

        return dependencies

    def export_chunks(self, output_file: str):
        """Export chunks to JSON file"""
        chunks_data = [asdict(chunk) for chunk in self.chunks]

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chunks_data, f, indent=2, ensure_ascii=False)

    def get_chunks_by_type(self, chunk_type: str) -> List[CodeChunk]:
        """Get all chunks of a specific type"""
        return [chunk for chunk in self.chunks if chunk.type == chunk_type]

    def get_chunk_statistics(self) -> Dict[str, Any]:
        """Get statistics about the analyzed codebase"""
        stats = {}

        # Count by type
        type_counts = {}
        for chunk in self.chunks:
            type_counts[chunk.type] = type_counts.get(chunk.type, 0) + 1

        stats['chunk_types'] = type_counts
        stats['total_chunks'] = len(self.chunks)

        # Average chunk size
        chunk_sizes = [chunk.end_line - chunk.start_line + 1 for chunk in self.chunks]
        if chunk_sizes:
            stats['average_chunk_size'] = sum(chunk_sizes) / len(chunk_sizes)

        return stats