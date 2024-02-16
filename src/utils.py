#  Copyright (c) 2024.
#  __author__ = "Dean Hand"
#  __license__ = "AGPL"
#  __version__ = "1.0"

import pandas as pd


class Color(object):
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
    DARKMAGENTA = ("\033[0,35m",)
    DARKGREEN = ("\033[0,32m",)

    def __init__(self):
        self.color = self.PURPLE
        self.color = self.BLUE
        self.color = self.GREEN
        self.color = self.YELLOW
        self.color = self.RED
        self.color = self.BOLD
        self.color = self.UNDERLINE
        self.color = self.END
        self.color = self.DARKMAGENTA


def read_sensor_dimensions_from_csv(
    csv_filepath, default_sensor_width=None, default_sensor_height=None
):
    """
    Reads sensor dimensions from a CSV file and returns a dictionary with sensor models as keys
    and tuples of (sensor width, sensor height) as values. If default_sensor_width and
    default_sensor_height are provided, sensors not found in the CSV will default to these values.

    :param csv_filepath: Path to the CSV file containing sensor dimensions.
    :param default_sensor_width: Default sensor width to use if a sensor model is not found in the CSV.
    :param default_sensor_height: Default sensor height to use if a sensor model is not found in the CSV.
    :return: A dictionary with sensor models as keys and (width, height) tuples as values.
    """
    # Initialize an empty dictionary to store sensor dimensions
    sensor_dimensions = {}

    try:
        # Read the CSV file into a DataFrame
        df = pd.read_csv(csv_filepath)
        # Iterate through each row in the DataFrame and populate the dictionary
        for index, row in df.iterrows():
            drone_make = row["DroneMake"]
            drone_model = row["DroneModel"]
            sensor_model = row[
                "SensorModel"
            ]  # Assuming the CSV has a column named 'SensorModel'
            width = row[
                "SensorWidth"
            ]  # Assuming the CSV has a column named 'SensorWidth'
            height = row[
                "SensorHeight"
            ]  # Assuming the CSV has a column named 'SensorHeight'
            sensor_dimensions[sensor_model] = (width, height, drone_make, drone_model)

    except FileNotFoundError:
        print(f"Error: The file {csv_filepath} was not found.")
    except pd.errors.EmptyDataError:
        print("Error: The CSV file is empty.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    # If default values are provided, use them as a fallback for any sensor model not in the CSV
    if default_sensor_width is not None and default_sensor_height is not None:
        sensor_dimensions["default"] = (default_sensor_width, default_sensor_height)
    return sensor_dimensions
