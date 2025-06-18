import logging
import uuid
import sys
import pytz
from datetime import datetime

class CustomStreamLogFormatter(logging.Formatter):
    """
    Custom log formatter to output logs in the format:
    timestamp - log_id: level: file_name method_name(): log_message
    """
    def format(self, record: logging.LogRecord) -> str:
        """
        Formats the log record.
        A unique log_id (UUID) is generated for each log entry, and a timestamp is included.
        """
        # Convert record.created (Unix timestamp in UTC) to IST
        ist = pytz.timezone('Asia/Kolkata')
        utc_time = datetime.fromtimestamp(record.created, tz=pytz.UTC)
        ist_time = utc_time.astimezone(ist)
        timestamp = ist_time.strftime("%Y-%m-%d %H:%M:%S %Z")

        log_id = uuid.uuid4()
        return f"{timestamp} - {log_id}: {record.levelname}: {record.filename} {record.funcName}(): {record.getMessage()}"

class Logger:
    """
    A simple logger class that initializes a logger instance and allows adding a stream handler.
    """
    def __init__(self, logger_name: str = "app_logger", level: int = logging.INFO):
        """
        Initializes the logger instance.

        Args:
            logger_name (str): The name for the logger.
            level (int): The logging level (e.g., logging.INFO, logging.DEBUG).
        """
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(level)

    def add_stream_handler(self, stream=None) -> logging.Logger:
        """
        Adds a stream handler to the logger with a custom formatter.

        Args:
            stream: The stream to which logs will be written. Defaults to sys.stdout.

        Returns:
            logging.Logger: The configured logger instance.
        """
        if not self.logger.handlers:  # Avoid adding multiple handlers
            if stream is None:
                stream = sys.stdout
            stream_handler = logging.StreamHandler(stream)
            formatter = CustomStreamLogFormatter()
            stream_handler.setFormatter(formatter)
            self.logger.addHandler(stream_handler)
        return self.logger

# Create a single logger instance for the application
logger_instance = Logger(logger_name="MyAppLogger", level=logging.INFO)
LOGGER = logger_instance.add_stream_handler()
