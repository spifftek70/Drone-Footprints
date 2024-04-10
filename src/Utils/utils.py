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


def read_sensor_dimensions_from_csv(csv_filepath, default_sensor_width=0, default_sensor_height=0, default_lens_FOVw=0,
                                    default_lens_FOVh=0):
    """
    Reads sensor dimensions from a CSV file, returning a dictionary with sensor models and camera index as keys
    and tuples of sensor dimensions as values. If sensor dimensions are not found, default values are used.

    Parameters:
    - csv_filepath (str): Path to the CSV file containing sensor dimensions.
    - default_sensor_width (float, optional): Default sensor width if a model is not found in the CSV.
    - default_sensor_height (float, optional): Default sensor height if a model is not found in the CSV.
    - default_lens_FOVw (float, optional): Default lens FOVw if a model is not found in the CSV.
    - default_lens_FOVh (float, optional): Default lens FOVh if a model is not found in the CSV.

    Returns:
    - dict: A dictionary with (sensor model, rig camera index) as keys and sensor dimensions as values.
    """
    sensor_dimensions = {}
    try:
        df = pd.read_csv(csv_filepath)
        for _, row in df.iterrows():
            drone_make = row["DroneMake"]
            drone_model = row["DroneModel"]
            camera_make = row["CameraMake"]
            sensor_model = row["SensorModel"]
            # Handle missing RigCameraIndex as 'default'
            cam_index = row.get("RigCameraIndex", 'default')
            width = row.get("SensorWidth", default_sensor_width)
            height = row.get("SensorHeight", default_sensor_height)
            lens_FOVw = row.get("LensFOVw", default_lens_FOVw)
            lens_FOVh = row.get("LensFOVh", default_lens_FOVh)

            # Construct the key with care for default values
            key = (sensor_model, str(cam_index))
            sensor_dimensions[key] = (
            drone_make, drone_model, camera_make, sensor_model, str(cam_index), width, height, lens_FOVw, lens_FOVh)

        # Ensure a 'default' entry exists in the dictionary
        if ("default", 'default') not in sensor_dimensions:
            sensor_dimensions[("default", 'default')] = (
            "Unknown", "Unknown", "Unknown", "default", 'default', default_sensor_width, default_sensor_height,
            default_lens_FOVw, default_lens_FOVh)

    except FileNotFoundError:
        logger.critical(f"Error: The file {csv_filepath} was not found.")
    except pd.errors.EmptyDataError:
        logger.critical("Error: The CSV file is empty.")
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}")

    return sensor_dimensions
