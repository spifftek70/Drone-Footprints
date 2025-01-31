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


def read_sensor_dimensions_from_csv(csv_filepath, default_sensor_width=0, default_sensor_height=0, 
                                    default_lens_FOVw=0, default_lens_FOVh=0):
    """
    Reads sensor dimensions from a CSV file and returns a dictionary with sensor models and camera index as keys
    and tuples of sensor dimensions as values. Default values are used if sensor dimensions are not found.

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
        # Read the CSV file
        df = pd.read_csv(csv_filepath)
    except Exception as e:
        logger.critical(f"Error reading CSV file {csv_filepath}: {e}")
        return None

    for _, row in df.iterrows():
        # Extract values from each row, handling missing data by falling back to default values
        drone_make = row.get("DroneMake", "Unknown")
        drone_model = row.get("DroneModel", "Unknown")
        camera_make = row.get("CameraMake", "Unknown")
        sensor_model = row.get("SensorModel", "default")
        cam_index = str(row.get("RigCameraIndex", 'default'))
        width = row.get("SensorWidth", default_sensor_width)
        height = row.get("SensorHeight", default_sensor_height)
        lens_FOVw = row.get("LensFOVw", default_lens_FOVw)
        lens_FOVh = row.get("LensFOVh", default_lens_FOVh)

        # Create a key based on sensor model and camera index
        key = (sensor_model, cam_index)
        sensor_dimensions[key] = {
            'drone_make': drone_make,
            'drone_model': drone_model,
            'camera_make': camera_make,
            'sensor_model': sensor_model,
            'camera_index': cam_index,
            'sensor_width': width,
            'sensor_height': height,
            'lens_FOVw': lens_FOVw,
            'lens_FOVh': lens_FOVh
        }

        # if drone_make and drone_model is None:
        #     logger.error(f"We're terribly sorry, but the imagery uploaded is not currently supported at this time..")
        #     exit(0)
        # if sensor_model == "FC300S":
        #     logger.error(f"We're terribly sorry, but Drones using the {sensor_model} camera are not currently supported at this time.")
        #     exit(0)
        #     sensor_dimensions[key]['drone_make'] = "Unknown Drone"
    
    return sensor_dimensions
