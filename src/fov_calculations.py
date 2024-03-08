# Copyright (c) 2024
# Author: Dean Hand
# License: AGPL
# Version: 1.0

from Bbox_calculations import CameraCalculator
import math
import numpy as np
from Utils.geospatial_conversions import translate_to_geographic
from magnetic_field_calculator import MagneticFieldCalculator
import magnetismi.magnetismi as api
from datetime import datetime
import Utils.config as config


def calculate_fov(altitude, focal_length, sensor_width, sensor_height, gimbal_roll_deg,
                  gimbal_pitch_deg, gimbal_yaw_deg, drone_latitude, drone_longitude, drone_roll_deg,
                  drone_pitch_deg, drone_yaw_deg, datetime_original):
    """
    Calculates the Field of View (FOV) for a given altitude and camera specifications,
    taking into account the adjusted orientations of the drone and gimbal.
    """
    str_date = datetime.strptime(datetime_original, '%Y:%m:%d %H:%M:%S')

    if str(str_date.year) > str(2019):
        mag_date = api.dti.date(str_date.year, str_date.month, str_date.day)
        # Find the magnetic declination reference
        model = api.Model(mag_date.year)
        field_point = model.at(lat_dd=drone_latitude, lon_dd=drone_longitude, alt_ft=altitude, date=mag_date)
        declination = field_point.dec
    else:
        calculator = MagneticFieldCalculator()
        model = calculator.calculate(latitude=drone_latitude, longitude=drone_longitude)
        dec = model['field-value']['declination']
        declination = dec['value']

    if altitude < 0 or focal_length <= 0:
        raise ValueError("Altitude and focal length must be positive.")

    # Calculate horizontal and vertical FOV in radians
    FOVh = 2 * math.atan(sensor_width / (2 * focal_length))
    FOVv = 2 * math.atan(sensor_height / (2 * focal_length))

    # Initialize CameraCalculator
    camera_calculator = CameraCalculator()

    # Convert gimbal orientation angles from degrees to radians
    adjusted_pitch_deg = 90 - gimbal_pitch_deg
    adjusted_yaw_deg = 90 - gimbal_yaw_deg
    # adjusted_declination = 90 - declination
    cal_roll_rad = np.radians(gimbal_roll_deg)
    cal_pitch_rad = np.radians(adjusted_pitch_deg)
    cal_yaw_rad = np.radians(adjusted_yaw_deg)
    declination_rad = np.radians(declination)
    # offset = 90
    adj_yaw_rad = (cal_yaw_rad - declination_rad) % (2 * math.pi)
    # Determine bounding box based on camera and gimbal orientation
    bbox = camera_calculator.getBoundingPolygon(FOVh, FOVv, altitude, cal_roll_rad,
                                                cal_pitch_rad, adj_yaw_rad)

    # Convert bounding box to geographic coordinates
    translated_bbox = translate_to_geographic(bbox, drone_longitude, drone_latitude, config.epsg_code)
    return translated_bbox