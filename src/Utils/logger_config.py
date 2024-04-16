# logger_config.py
from loguru import logger
from tqdm import tqdm
from pathlib import Path
import json
import sys
import Utils.config as config

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

    if config.nodejgraphical_interface is True:
        logger.add(lambda msg: tqdm.write(msg, end=""),
                   colorize=True, level="INFO", format="{time} {level} {message}",
                   filter=lambda record: record["level"].name in ["INFO", "SUCCESS", "WARNING"])

        # logger.add(sys.stdout, format="{time} {level} {message}", level="INFO")

    else:

        logger.add(lambda msg: tqdm.write(msg, end=""),
                   colorize=True, level="INFO",
                   filter=lambda record: record["level"].name in ["INFO", "SUCCESS", "WARNING"])

        # Setup file logging for all messages, including detailed traceback for DEBUG and above
        logger.add(current_log_path, format="{time} | {level} | {message}",
                   level="DEBUG", backtrace=True, diagnose=True)

    logger.remove()  # Remove all other handlers to prevent interference
    # Add a handler specifically for tqdm compatibility
    logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True, diagnose=True)
    # If logging to a file, add that handler as well
    logger.add(log_path, format="{time} | {level} | {message}", backtrace=True, diagnose=True)
