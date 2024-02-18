#  Copyright (c) 2024.
#  __author__ = "Dean Hand"
#  __license__ = "AGPL"
#  __version__ = "1.0"


import numpy as np
from src.Utils.geospatial_conversions import *


def calculate_footprints_nadir(
    easting,
    northing,
    pixel_width,
    pixel_height,
    yaw,
    original_width,
    original_height,
    zone_number,
    center_latitude,
):
    transformer = proj_stuff(center_latitude, zone_number)
    # Define the projection from UTM to WGS84 and vice versa
    # Calculate the corners of the image in UTM coordinates
    width_meter = original_width * pixel_width
    height_meter = original_height * pixel_height
    corners_utm = np.array(
        [
            [easting - width_meter / 2, northing + height_meter / 2],  # Top-left
            [easting + width_meter / 2, northing + height_meter / 2],  # Top-right
            [easting + width_meter / 2, northing - height_meter / 2],  # Bottom-right
            [easting - width_meter / 2, northing - height_meter / 2],  # Bottom-left
        ]
    )

    # Convert yaw from degrees to radians and calculate rotation matrix
    yaw_rad = np.radians(yaw)
    rotation_matrix = np.array(
        [[np.cos(yaw_rad), -np.sin(yaw_rad)], [np.sin(yaw_rad), np.cos(yaw_rad)]]
    )

    # Rotate corners around the center point
    center_utm = np.array([easting, northing])
    rotated_corners_utm = np.dot(corners_utm - center_utm, rotation_matrix) + center_utm

    # Convert rotated corners back to decimal degrees
    rotated_corners_latlon = [
        transformer.transform(corner[0], corner[1]) for corner in rotated_corners_utm
    ]

    return rotated_corners_latlon
