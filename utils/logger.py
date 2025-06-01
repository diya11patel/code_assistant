import logging
import uuid
import sys # To get a default stream like sys.stdout

class CustomStreamLogFormatter(logging.Formatter):
    """
    Custom log formatter to output logs in the format:
    log_id: level: file_name method_name log_message
    """
    def format(self, record: logging.LogRecord) -> str:
        """
        Formats the log record.
        A unique log_id (UUID) is generated for each log entry.
        """
        log_id = uuid.uuid4()
        
        # record.filename gives the filename (e.g., 'example.py')
        # record.funcName gives the function name
        # record.levelname gives the log level string (e.g., 'INFO')
        # record.getMessage() correctly formats the log message with its arguments
        
        return f"{log_id}: {record.levelname}: {record.filename} {record.funcName}(): {record.getMessage()}"

def get_custom_stream_logger(logger_name: str = 'custom_app_logger', 
                             level: int = logging.INFO, 
                             stream = None) -> logging.Logger:
    """
    Configures and returns a logger with the CustomStreamLogFormatter.

    Args:
        logger_name (str): The name for the logger.
        level (int): The logging level (e.g., logging.INFO, logging.DEBUG).
        stream: The stream to which logs will be written. Defaults to sys.stdout.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(logger_name)
    
    # Set the logging level for the logger.
    # This means messages of this level and above will be processed.
    logger.setLevel(level)
    
    # Prevent adding multiple handlers if the function is called multiple times
    # for the same logger instance.
    if not logger.handlers:
        if stream is None:
            stream = sys.stdout # Default to standard output
            
        stream_handler = logging.StreamHandler(stream)
        
        # Create an instance of our custom formatter
        formatter = CustomStreamLogFormatter()
        
        # Set the custom formatter for the handler
        stream_handler.setFormatter(formatter)
        
        # Add the handler to the logger
        logger.addHandler(stream_handler)
        
    return logger

# --- Example Usage ---
if __name__ == "__main__":
    # Get a logger instance configured with our custom formatter
    # You can name your logger anything, e.g., based on the module or application
    app_logger = get_custom_stream_logger(__name__, level=logging.DEBUG)

    def my_function_to_log():
        app_logger.debug("This is a debug message from my_function_to_log.")
        app_logger.info("Informational message with a parameter: %s", "some_value")
        try:
            x = 1 / 0
        except ZeroDivisionError:
            app_logger.error("An error occurred: Division by zero!", exc_info=True) # exc_info=True adds traceback

    class MyClass:
        def __init__(self):
            # You can get a logger specific to the class or reuse a general one
            self.class_logger = get_custom_stream_logger(f"{__name__}.{self.__class__.__name__}")

        def do_something(self):
            self.class_logger.warning("A warning from MyClass.do_something.")
            my_variable = "test data"
            self.class_logger.info(f"Processing data: {my_variable}")


    print("--- Logging from function ---")
    my_function_to_log()
    
    print("\n--- Logging from class method ---")
    my_instance = MyClass()
    my_instance.do_something()

    # Example of logging from the root/main scope
    app_logger.critical("This is a critical message from the main execution block.")
