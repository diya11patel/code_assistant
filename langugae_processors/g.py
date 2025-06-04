# build_grammars.py
import os
from tree_sitter import Language

# --- Configuration ---
# Adjust this path to where you cloned the tree-sitter-php repository
PHP_GRAMMAR_PATH = "D:\\codes\\langGraph_venv\\code_dependecies\\tree-sitter-php"  # IMPORTANT: UPDATE THIS PATH

# Output directory for the compiled library (e.g., 'build' in your project root)
BUILD_DIR = "build"
# Output library name
LIB_NAME = "my-languages.so"
if os.name == 'nt': # For Windows
    LIB_NAME = "my-languages.dll"

OUTPUT_LIB_PATH = os.path.join(BUILD_DIR, LIB_NAME)
# --- End Configuration ---

def main():
    if not os.path.exists(PHP_GRAMMAR_PATH) or not os.path.isdir(PHP_GRAMMAR_PATH):
        print(f"Error: PHP grammar path not found or not a directory: {PHP_GRAMMAR_PATH}")
        print("Please clone the 'tree-sitter-php' repository and update PHP_GRAMMAR_PATH in this script.")
        return

    if not os.path.exists(BUILD_DIR):
        os.makedirs(BUILD_DIR)
        print(f"Created build directory: {BUILD_DIR}")

    print(f"Attempting to build language library at: {OUTPUT_LIB_PATH}")
    print(f"Using PHP grammar from: {PHP_GRAMMAR_PATH}")

    try:
        Language.build_library(
            OUTPUT_LIB_PATH,
            [
                PHP_GRAMMAR_PATH,
                # You can add paths to other grammar repositories here if needed
                # e.g., 'path/to/tree-sitter-javascript'
            ]
        )
        print(f"Successfully built language library: {OUTPUT_LIB_PATH}")
        print("You can now use this library in your Tree-sitter parser.")
    except Exception as e:
        print(f"Error building language library: {e}")
        print("Please ensure you have a C/C++ compiler installed and configured.")
        print("For Windows: You might need 'Build Tools for Visual Studio'.")
        print("For Linux: You might need 'build-essential' or similar.")
        print("For macOS: You might need Xcode Command Line Tools.")

if __name__ == "__main__":
    main()
