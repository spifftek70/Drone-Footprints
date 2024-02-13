#  __author__ = "Dean Hand"
#  __license__ = "AGPL"
#  __version__ = "1.0"

import numpy as np
from Bbox_calculations import CameraCalculator
from coordinate_conversions import *


def calculate_fov(altitude, focal_length, sensor_width, sensor_height, gimbal_roll_deg, gimbal_pitch_deg,
                  gimbal_yaw_deg, drone_lat, drone_lon):
    # Convert camera specifications to radians for FOV calculation
    if altitude < 0 or focal_length <= 0:
        raise ValueError("Altitude and focal length must be positive.")

        # Convert camera specifications to radians for FOV calculation
    FOVh = 2 * math.atan(sensor_width / (2 * focal_length))
    FOVv = 2 * math.atan(sensor_height / (2 * focal_length))

    # Instantiate CameraCalculator
    camera_calculator = CameraCalculator()

    # Correctly convert gimbal orientations to radians
    cal_roll_rad = np.radians(gimbal_roll_deg)
    cal_pitch_rad = np.radians(gimbal_pitch_deg % 90)  # Direct conversion to radians without modulo operation
    cal_yaw_rad = np.radians(gimbal_yaw_deg + 90)  # Direct conversion to radians without adding 90

    # Calculate bounding polygon using camera orientation
    bbox = camera_calculator.getBoundingPolygon(FOVh, FOVv, altitude, cal_roll_rad, cal_pitch_rad, cal_yaw_rad)

    # Translate bounding polygon to geographic coordinates
    translated_bbox = translate_to_geographic(bbox, drone_lon, drone_lat)
    return translated_bbox


def translate_to_geographic(bbox, drone_lon, drone_lat):
    # Determine the drone's UTM zone
    utm_zone = int((drone_lon + 180) / 6) + 1
    hemisphere = 'north' if drone_lat >= 0 else 'south'
    crs_geo = "epsg:4326"
    crs_utm = f"+proj=utm +zone={utm_zone} +{hemisphere} +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
    transformer_to_utm = Transformer.from_crs(crs_geo, crs_utm, always_xy=True)
    transformer_to_geo = Transformer.from_crs(crs_utm, crs_geo, always_xy=True)

    # Convert drone's geographic position to UTM
    drone_easting, drone_northing = transformer_to_utm.transform(drone_lon, drone_lat)

    # Translate and rotate bbox points based on gimbal orientation
    translated_bbox = []
    for point in bbox:
        # Adjust for the effect of gimbal pitch and yaw here before converting
        # This placeholder assumes direct conversion, add rotation and pitch adjustments as needed
        point_easting, point_northing = drone_easting + point.x, drone_northing + point.y

        # Convert adjusted points back to geographic coordinates
        point_lon, point_lat = transformer_to_geo.transform(point_easting, point_northing)
        translated_bbox.append((point_lon, point_lat))

    return translated_bbox
