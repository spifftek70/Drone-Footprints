# Copyright (c) 2024
# __author__ = "Dean Hand"
# __license__ = "AGPL"
# __version__ = "1.0"

import pandas as pd


class Color:
    """Defines color codes for console output."""
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    DARKCYAN = "\033[36m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
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


def read_sensor_dimensions_from_csv(csv_filepath, default_sensor_width=None, default_sensor_height=None):
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
            sensor_model = row["SensorModel"]
            width = row["SensorWidth"]
            height = row["SensorHeight"]
            drone_make = row["DroneMake"]
            drone_model = row["DroneModel"]
            sensor_dimensions[sensor_model] = (width, height, drone_make, drone_model)

    except FileNotFoundError:
        print(f"Error: The file {csv_filepath} was not found.")
    except pd.errors.EmptyDataError:
        print("Error: The CSV file is empty.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    # Use default values as a fallback for any sensor model not in the CSV
    if default_sensor_width is not None and default_sensor_height is not None:
        sensor_dimensions["default"] = (default_sensor_width, default_sensor_height)

    return sensor_dimensions
