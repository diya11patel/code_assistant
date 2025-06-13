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
        self._analyze_seeders(laravel_path / "database/seeders")
        self._analyze_factories(laravel_path / "database/factories")
        self._analyze_views(laravel_path / "resources/views")
        self._analyze_middleware(laravel_path / "app/Http/Middleware")
        self._analyze_requests(laravel_path / "app/Http/Requests")
        self._analyze_services(laravel_path / "app/Services")
        self._analyze_config(laravel_path / "config")
        self._analyze_providers(laravel_path / "app/Providers")
        self._analyze_commands(laravel_path / "app/Console/Commands")
        self._analyze_events(laravel_path / "app/Events")
        self._analyze_listeners(laravel_path / "app/Listeners")
        self._analyze_jobs(laravel_path / "app/Jobs")
        self._analyze_notifications(laravel_path / "app/Notifications")
        self._analyze_rules(laravel_path / "app/Rules")
        self._analyze_exceptions_handler(laravel_path / "app/Exceptions/Handler.php")
        self._analyze_custom_helpers(laravel_path / "app/Helpers") # Assuming a common custom location
        self._analyze_bootstrap_app(laravel_path / "bootstrap/app.php")
        self._analyze_public_index(laravel_path / "public/index.php")
        self._analyze_tests(laravel_path / "tests")
        
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

    def _analyze_seeders(self, seeders_path: Path):
        """Analyze database seeders"""
        if not seeders_path.exists():
            return
        for php_file in seeders_path.rglob("*.php"): # rglob for nested seeders
            self._parse_php_file(php_file, "seeder")

    def _analyze_factories(self, factories_path: Path):
        """Analyze model factories"""
        if not factories_path.exists():
            return
        for php_file in factories_path.rglob("*.php"): # rglob for nested factories
            self._parse_php_file(php_file, "factory")

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

    def _analyze_requests(self, requests_path: Path):
        """Analyze form request validation classes"""
        if not requests_path.exists():
            return

        for php_file in requests_path.rglob("*.php"):
            self._parse_php_file(php_file, "form_request")

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

    def _analyze_providers(self, providers_path: Path):
        """Analyze service providers"""
        if not providers_path.exists():
            return
        for php_file in providers_path.rglob("*.php"):
            self._parse_php_file(php_file, "provider")

    def _analyze_commands(self, commands_path: Path):
        """Analyze Artisan console commands"""
        if not commands_path.exists():
            return
        for php_file in commands_path.rglob("*.php"):
            self._parse_php_file(php_file, "command")

    def _analyze_events(self, events_path: Path):
        """Analyze event classes"""
        if not events_path.exists():
            return
        for php_file in events_path.rglob("*.php"):
            self._parse_php_file(php_file, "event")

    def _analyze_listeners(self, listeners_path: Path):
        """Analyze event listener classes"""
        if not listeners_path.exists():
            return
        for php_file in listeners_path.rglob("*.php"):
            self._parse_php_file(php_file, "listener")

    def _analyze_jobs(self, jobs_path: Path):
        """Analyze job classes"""
        if not jobs_path.exists():
            return
        for php_file in jobs_path.rglob("*.php"):
            self._parse_php_file(php_file, "job")

    def _analyze_notifications(self, notifications_path: Path):
        """Analyze notification classes"""
        if not notifications_path.exists():
            return
        for php_file in notifications_path.rglob("*.php"):
            self._parse_php_file(php_file, "notification")

    def _analyze_rules(self, rules_path: Path):
        """Analyze custom validation rules"""
        if not rules_path.exists():
            return
        for php_file in rules_path.rglob("*.php"):
            self._parse_php_file(php_file, "validation_rule")

    def _analyze_exceptions_handler(self, handler_file_path: Path):
        """Analyze the main exception handler file"""
        if handler_file_path.exists() and handler_file_path.is_file():
            self._parse_php_file(handler_file_path, "exception_handler")

    def _analyze_custom_helpers(self, helpers_path: Path):
        """Analyze custom helper files (if any)"""
        if not helpers_path.exists() or not helpers_path.is_dir():
            return
        for php_file in helpers_path.rglob("*.php"):
            self._parse_php_file(php_file, "helper")

    def _analyze_bootstrap_app(self, bootstrap_file_path: Path):
        if bootstrap_file_path.exists() and bootstrap_file_path.is_file():
            self._parse_php_file(bootstrap_file_path, "bootstrap_script")

    def _analyze_public_index(self, index_file_path: Path):
        if index_file_path.exists() and index_file_path.is_file():
            self._parse_php_file(index_file_path, "public_entry_script")

    def _analyze_tests(self, tests_path: Path):
        """Analyze PHPUnit test files"""
        if not tests_path.exists():
            return
        # Tests can be in subdirectories like Unit, Feature
        for php_file in tests_path.rglob("*.php"):
            self._parse_php_file(php_file, "test")

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
                import_dependencies=[],
                method_dependencies=[]
                #TODO: need to look into router dependencies
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
            import_dependencies=self._extract_blade_dependencies(content),
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
