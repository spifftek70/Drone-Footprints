# Copyright (c) 2024
# __author__ = "Dean Hand"
# __license__ = "AGPL"
# __version__ = "1.0"
import pandas as pd
from loguru import logger


class Color:
    """Defines color codes for console output."""
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    DARKCYAN = "\033[36m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    ORANGE = "\033[0;33m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"
    DARKMAGENTA = "\033[0;35m"
    DARKGREEN = "\033[0;32m"

    def __init__(self):
        """Initializes the Color object with default color settings."""
        self.color = self.PURPLE
        self.color = self.BLUE
        self.color = self.GREEN
        self.color = self.YELLOW
        self.color = self.RED
        self.color = self.BOLD
        self.color = self.UNDERLINE
        self.color = self.END
        self.color = self.DARKMAGENTA


def read_sensor_dimensions_from_csv(csv_filepath, default_sensor_width=None, default_sensor_height=None,
                                    default_lens_FOVw=None, default_lens_FOVh=None):
    """
    Reads sensor dimensions from a CSV file, returning a dictionary with sensor models as keys
    and tuples of (sensor width, sensor height, drone make, drone model) as values. Provides
    default dimensions for sensors not found in the CSV.

    Parameters:
    - csv_filepath (str): Path to the CSV file containing sensor dimensions.
    - default_sensor_width (float, optional): Default sensor width if a model is not found in the CSV.
    - default_sensor_height (float, optional): Default sensor height if a model is not found in the CSV.

    Returns:
    - dict: A dictionary with sensor models as keys and tuples (width, height, make, model) as values.
    """
    sensor_dimensions = {}  # Initialize an empty dictionary to store sensor dimensions

    try:
        df = pd.read_csv(csv_filepath)  # Read the CSV file into a DataFrame
        for index, row in df.iterrows():  # Iterate through each row and populate the dictionary
            drone_make = row["DroneMake"]
            drone_model = row["DroneModel"]
            camera_make = row["CameraMake"]
            sensor_model = row["SensorModel"]
            width = row["SensorWidth"]
            height = row["SensorHeight"]
            lens_FOVw = row["LensFOVw"]
            lens_FOVh = row["LensFOVh"]
            sensor_dimensions[sensor_model] = (drone_make, drone_model, camera_make, sensor_model, width, height, lens_FOVw, lens_FOVh)
    except FileNotFoundError:
        logger.critical(f"Error: The file {csv_filepath} was not found.")
    except pd.errors.EmptyDataError:
        logger.critical("Error: The CSV file is empty.")
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}")

    # Use default values as a fallback for any sensor model not in the CSV
    if default_sensor_width is not None and default_sensor_height is not None and default_lens_FOVw is not None and default_lens_FOVh is not None:
        sensor_dimensions["default"] = (
        default_sensor_width, default_sensor_height, "Unknown", "Unknown", default_lens_FOVw, default_lens_FOVh)
        logger.info(f"No sensor information available. Using Defaults: {sensor_dimensions['default']}")
    return sensor_dimensions