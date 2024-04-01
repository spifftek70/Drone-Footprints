# logger_config.py
from loguru import logger
from tqdm import tqdm
from pathlib import Path

script_path = Path(__file__).resolve()
script_dir = script_path.parent


def init_logger(log_path=None):
    global current_log_path

    if log_path is not None:
        # Make sure the directory exists
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)

        # Update the current log path
        current_log_path = log_path

    # Check if log_path is still None (not provided or incorrectly set)
    if current_log_path is None:
        raise ValueError("Log path must be provided and cannot be None.")


    logger.remove()  # Clear existing configuration

    # Setup console logging specifically for lower-severity messages
    # Using a condition function to explicitly filter out higher levels from console
    logger.add(lambda msg: tqdm.write(msg, end=""), 
               colorize=True, level="INFO",
               filter=lambda record: record["level"].name in ["INFO", "SUCCESS", "WARNING"])

    # Setup file logging for all messages, including detailed traceback for DEBUG and above
    logger.add(current_log_path, format="{time} | {level} | {message}",
               level="DEBUG", backtrace=True, diagnose=True)