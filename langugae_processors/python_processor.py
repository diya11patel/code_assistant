
import ast, os
from utils.logger import LOGGER


logger = LOGGER
logger.propagate = False

class PythonProcessor():
    def parse(self):
        self.files = []
        for root, _, files in os.walk(self.project_path):
            for f in files:
                if f.endswith('.py'):
                    self.files.append(os.path.join(root, f))

    def chunk(self):
        chunks = []
        for file in self.files:
            with open(file, 'r') as f:
                code = f.read()
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) or isinstance(node, ast.ClassDef):
                        start = node.lineno - 1
                        end = getattr(node, 'end_lineno', start + 10)  # fallback
                        lines = code.splitlines()[start:end]
                        chunk = '\n'.join(lines)
                        chunks.append({
                            'text': chunk,
                            'metadata': {
                                'file': file,
                                'type': 'function' if isinstance(node, ast.FunctionDef) else 'class',
                                'name': node.name
                            }
                        })
            except Exception as e:
                logger.info(f"Error parsing {file}: {e}")
        return chunks