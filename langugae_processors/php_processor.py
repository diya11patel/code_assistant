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




class LaravelProcessor:
    def __init__(self):
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

        self.chunks: List[CodeChunk] = []

    def analyze_codebase(self, laravel_root: str) -> List[CodeChunk]:
        """Analyze entire Laravel codebase and return chunks"""
        laravel_path = Path(laravel_root)
        # Analyze different Laravel directories
        self._analyze_controllers(laravel_path / "app/Http/Controllers")
        self._analyze_models(laravel_path / "app/Models")
        self._analyze_routes(laravel_path / "routes")
        self._analyze_migrations(laravel_path / "database/migrations")
        self._analyze_views(laravel_path / "resources/views")
        self._analyze_middleware(laravel_path / "app/Http/Middleware")
        self._analyze_services(laravel_path / "app/Services")
        self._analyze_config(laravel_path / "config")

        return self.chunks

    def _analyze_controllers(self, controllers_path: Path):
        """Analyze Laravel controllers"""
        if not controllers_path.exists():
            return

        for php_file in controllers_path.rglob("*.php"):
            self._parse_php_file(php_file, "controller")

    def _analyze_models(self, models_path: Path):
        """Analyze Eloquent models"""
        if not models_path.exists():
            return

        for php_file in models_path.rglob("*.php"):
            self._parse_php_file(php_file, "model")

    def _analyze_routes(self, routes_path: Path):
        """Analyze route files"""
        if not routes_path.exists():
            return

        for php_file in routes_path.glob("*.php"):
            self._parse_route_file(php_file)

    def _analyze_migrations(self, migrations_path: Path):
        """Analyze database migrations"""
        if not migrations_path.exists():
            return

        for php_file in migrations_path.glob("*.php"):
            self._parse_php_file(php_file, "migration")

    def _analyze_views(self, views_path: Path):
        """Analyze Blade templates"""
        if not views_path.exists():
            return

        for blade_file in views_path.rglob("*.blade.php"):
            self._parse_blade_file(blade_file)

    def _analyze_middleware(self, middleware_path: Path):
        """Analyze middleware classes"""
        if not middleware_path.exists():
            return

        for php_file in middleware_path.rglob("*.php"):
            self._parse_php_file(php_file, "middleware")

    def _analyze_services(self, services_path: Path):
        """Analyze service classes"""
        if not services_path.exists():
            return

        for php_file in services_path.rglob("*.php"):
            self._parse_php_file(php_file, "service")

    def _analyze_config(self, config_path: Path):
        """Analyze configuration files"""
        if not config_path.exists():
            return

        for php_file in config_path.glob("*.php"):
            self._parse_php_file(php_file, "config")

    def _parse_php_file(self, file_path: Path, file_type: str):
        """Parse a PHP file and extract meaningful chunks"""
        try:
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
                dependencies=self._extract_dependencies(tree.root_node, content)
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
                    metadata=self._extract_method_metadata(method_node, content),
                    dependencies=[]
                )
                self.chunks.append(method_chunk)

    def _parse_route_file(self, file_path: Path):
        """Parse Laravel route files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            return

        tree = self.php_parser.parse(bytes(content, 'utf8'))

        # Look for Route:: method calls
        route_calls = self._find_route_definitions(tree.root_node, content)

        for i, route_call in enumerate(route_calls):
            chunk = CodeChunk(
                type="route",
                name=f"Route_{i + 1}",
                file_path=str(file_path),
                start_line=route_call['start_line'],
                end_line=route_call['end_line'],
                content=route_call['content'],
                metadata=route_call['metadata'],
                dependencies=[]
            )
            self.chunks.append(chunk)

    def _parse_blade_file(self, file_path: Path):
        """Parse Blade template files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            return

        # For Blade files, we'll chunk by sections or components
        # This is a simplified approach - you might want more sophisticated parsing

        chunk = CodeChunk(
            type="blade_template",
            name=file_path.stem,
            file_path=str(file_path),
            start_line=1,
            end_line=len(content.splitlines()),
            content=content,
            metadata=self._extract_blade_metadata(content),
            dependencies=self._extract_blade_dependencies(content)
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
        """Extract use statements and dependencies"""
        dependencies = []

        use_statements = self._query_nodes(root_node, "use_declaration")
        for use_stmt in use_statements:
            dep = self._get_node_text(use_stmt, content).replace("use ", "").replace(";", "").strip()
            dependencies.append(dep)

        return dependencies

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


