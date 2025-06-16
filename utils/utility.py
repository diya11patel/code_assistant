# Determine the file type based on its path
from utils.logger import LOGGER

def get_file_type(file_path : str) -> str:
            if "app/Http/Controllers" in file_path:
                file_type = "controller"
                return file_type
            elif "app/Models" in file_path:
                file_type = "model"
                return file_type
            elif "routes" in file_path:
                file_type = "route"
                return file_type
            elif "database/seeders" in file_path:
                file_type = "seeder"
                return file_type
            elif "database/factories" in file_path:
                file_type = "factory"
                return file_type
            elif "database/migrations" in file_path:
                file_type = "migration"
                return file_type
            elif "resources/views" in file_path and file_path.endswith(".blade.php"):
                file_type = "blade_template"
                return file_type
            elif "app/Http/Middleware" in file_path:
                file_type = "middleware"
                return file_type
            elif "app/Http/Requests" in file_path:
                file_type = "form_request"
                return file_type
            elif "app/Services" in file_path:
                file_type = "service"
                return file_type
            elif "config" in file_path:
                file_type = "config"
                return file_type
            elif "app/Providers" in file_path:
                file_type = "provider"
                return file_type
            elif "app/Console/Commands" in file_path:
                file_type = "command"
                return file_type
            elif "app/Events" in file_path:
                file_type = "event"
                return file_type
            elif "app/Listeners" in file_path:
                file_type = "listener"
                return file_type
            elif "app/Jobs" in file_path:
                file_type = "job"
                return file_type
            elif "app/Notifications" in file_path:
                file_type = "notification"
                return file_type
            elif "app/Rules" in file_path:
                file_type = "validation_rule"
                return file_type
            elif "app/Exceptions/Handler.php" in file_path:
                file_type = "exception_handler"
                return file_type
            elif "app/Helpers" in file_path:
                file_type = "helper"
                return file_type
            elif "bootstrap/app.php" in file_path:
                file_type = "bootstrap_script"
                return file_type
            elif "public/index.php" in file_path:
                file_type = "public_entry_script"
                return file_type
            elif "tests" in file_path:
                file_type = "test"
                return file_type
            else:
                LOGGER.warning(f"Could not determine file type for {file_path}. Skipping Qdrant update.")
                return {"status": "warning", "message": f"Could not determine file type for {file_path}"}