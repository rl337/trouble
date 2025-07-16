import logging
import sys

LOG_FILE_PATH = "trouble.log"

def setup_logging():
    """
    Configures the root logger to output to both stdout and a file.
    This should be called once at the start of the application.
    """
    # Create a logger
    logger = logging.getLogger("trouble")
    logger.setLevel(logging.INFO)

    # Prevent propagation to the root logger if it has default handlers
    logger.propagate = False

    # If handlers are already configured, do nothing.
    if logger.hasHandlers():
        return

    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # File Handler
    # 'w' mode to overwrite the log file for each run.
    try:
        # Open in 'w' mode to clear it, then write a space to ensure it's not empty
        with open(LOG_FILE_PATH, 'w') as f:
            f.write(' ')

        file_handler = logging.FileHandler(LOG_FILE_PATH, mode='a') # Append from now on
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except IOError as e:
        print(f"Error: Could not set up log file at {LOG_FILE_PATH}: {e}", file=sys.stderr)


    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger instance with the specified name.
    It will be a child of the root 'trouble' logger.
    """
    return logging.getLogger(f"trouble.{name}")

# Set up logging when this module is first imported.
# Any module that needs logging can just do `from . import log_config`
# and then `logger = log_config.get_logger(__name__)`
setup_logging()
