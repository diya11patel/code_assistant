# Determine the file type based on its path
from pathlib import Path
import re
from utils.logger import LOGGER

def get_file_type(file_path_str : str) -> str:
            # Normalize the path to use forward slashes for consistent checking across OS
            # Path() also handles normalization of redundant slashes like '//'
            normalized_path = Path(file_path_str).as_posix()

            if "app/Http/Controllers" in normalized_path:
                file_type = "controller"
                return file_type
            elif "app/Models" in normalized_path:
                file_type = "model"
                return file_type
            elif "routes" in normalized_path:
                file_type = "route"
                return file_type
            elif "database/seeders" in normalized_path:
                file_type = "seeder"
                return file_type
            elif "database/factories" in normalized_path:
                file_type = "factory"
                return file_type
            elif "database/migrations" in normalized_path:
                file_type = "migration"
                return file_type
            elif "resources/views" in normalized_path and normalized_path.endswith(".blade.php"):
                file_type = "blade_template"
                return file_type
            elif "app/Http/Middleware" in normalized_path:
                file_type = "middleware"
                return file_type
            elif "app/Http/Requests" in normalized_path:
                file_type = "form_request"
                return file_type
            elif "app/Services" in normalized_path:
                file_type = "service"
                return file_type
            elif "config" in normalized_path:
                file_type = "config"
                return file_type
            elif "app/Providers" in normalized_path:
                file_type = "provider"
                return file_type
            elif "app/Console/Commands" in normalized_path:
                file_type = "command"
                return file_type
            elif "app/Events" in normalized_path:
                file_type = "event"
                return file_type
            elif "app/Listeners" in normalized_path:
                file_type = "listener"
                return file_type
            elif "app/Jobs" in normalized_path:
                file_type = "job"
                return file_type
            elif "app/Notifications" in normalized_path:
                file_type = "notification"
                return file_type
            elif "app/Rules" in normalized_path:
                file_type = "validation_rule"
                return file_type
            elif "app/Exceptions/Handler.php" in normalized_path:
                file_type = "exception_handler"
                return file_type
            elif "app/Helpers" in normalized_path:
                file_type = "helper"
                return file_type
            elif "bootstrap/app.php" in normalized_path:
                file_type = "bootstrap_script"
                return file_type
            elif "public/index.php" in normalized_path:
                file_type = "public_entry_script"
                return file_type
            elif "tests" in normalized_path:
                file_type = "test"
                return file_type
            else:
                LOGGER.warning(f"Could not determine file type for {file_path_str}. Defaulting to 'unknown'.")
                return "unknown" # Ensure a string is returned for consistency
            


def normalize_line(line: str):
        line = line.replace('\t', '    ')             # Convert tabs to spaces
        line = re.sub(r'\s*\{', ' {', line)           # Collapse spaces before {
        return line.strip()

