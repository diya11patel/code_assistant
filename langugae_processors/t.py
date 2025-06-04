
from tree_sitter_languages import get_parser

parser = get_parser("php")

code = b"""
<?php
namespace MyApp;

class Hello {
    public function sayHello() {
        echo 'Hello, world!';
    }
}
"""

tree = parser.parse(code)
print(tree.root_node.sexp())
