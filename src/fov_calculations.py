# Author: Dean Hand
# License: AGPL
# Version: 1.0

import numpy as np
from Bbox_calculations import CameraCalculator
from Utils.geospatial_conversions import *


def calculate_fov(altitude, focal_length, sensor_width, sensor_height, gimbal_roll_deg,
                  gimbal_pitch_deg, gimbal_yaw_deg, drone_lat, drone_lon):
    """
    Calculates the Field of View (FOV) for a given altitude and camera specifications,
    taking into account the gimbal orientation and the drone's geographic coordinates.

    Parameters:
    - altitude (float): Altitude of the drone in meters.
    - focal_length (float): Camera's focal length in meters.
    - sensor_width (float): Width of the camera sensor in meters.
    - sensor_height (float): Height of the camera sensor in meters.
    - gimbal_roll_deg (float): Gimbal roll in degrees.
    - gimbal_pitch_deg (float): Gimbal pitch in degrees.
    - gimbal_yaw_deg (float): Gimbal yaw in degrees.
    - drone_lat (float): Drone's latitude in decimal degrees.
    - drone_lon (float): Drone's longitude in decimal degrees.

    Returns:
    Tuple containing the translated bounding box in geographic coordinates, horizontal FOV, and vertical FOV.
    """
    if altitude < 0 or focal_length <= 0:
        raise ValueError("Altitude and focal length must be positive.")

    # Calculate horizontal and vertical FOV in radians
    FOVh = 2 * math.atan(sensor_width / (2 * focal_length))
    FOVv = 2 * math.atan(sensor_height / (2 * focal_length))

    # Initialize CameraCalculator
    camera_calculator = CameraCalculator()

    # Convert gimbal orientation angles from degrees to radians
    cal_roll_rad = np.radians(gimbal_roll_deg)
    cal_pitch_rad = np.radians(gimbal_pitch_deg % 90)
    cal_yaw_rad = np.radians((gimbal_yaw_deg + 90) * -1)

    # Determine bounding box based on camera and gimbal orientation
    bbox = camera_calculator.getBoundingPolygon(FOVh, FOVv, altitude, cal_roll_rad,
                                                cal_pitch_rad, cal_yaw_rad)

    # Convert bounding box to geographic coordinates
    translated_bbox = translate_to_geographic(bbox, drone_lon, drone_lat)
    return translated_bbox, FOVh, FOVv


def translate_to_geographic(bbox, drone_lon, drone_lat):
    """
    Translates a bounding box to geographic coordinates based on the drone's location.

    Parameters:
    - bbox (list): List of bounding box coordinates in UTM.
    - drone_lon (float): Drone's longitude in decimal degrees.
    - drone_lat (float): Drone's latitude in decimal degrees.

    Returns:
    List of tuples containing translated bounding box points in geographic coordinates.
    """
    # Determine UTM zone and hemisphere from drone's coordinates
    utm_zone = int((drone_lon + 180) / 6) + 1
    hemisphere = "north" if drone_lat >= 0 else "south"
    crs_geo = "epsg:4326"
    crs_utm = f"+proj=utm +zone={utm_zone} +{hemisphere} +ellps=WGS84 +datum=WGS84 +units=m +no_defs"

    # Initialize transformers for coordinate conversion
    transformer_to_utm = Transformer.from_crs(crs_geo, crs_utm, always_xy=True)
    transformer_to_geo = Transformer.from_crs(crs_utm, crs_geo, always_xy=True)

    # Convert drone's location to UTM coordinates
    drone_easting, drone_northing = transformer_to_utm.transform(drone_lon, drone_lat)

    translated_bbox = []
    for point in bbox:
        # Translate and rotate bounding box points
        point_easting, point_northing = drone_easting + point.x, drone_northing + point.y

        # Convert points back to geographic coordinates
        point_lon, point_lat = transformer_to_geo.transform(point_easting, point_northing)
        translated_bbox.append((point_lon, point_lat))

    return translated_bbox
