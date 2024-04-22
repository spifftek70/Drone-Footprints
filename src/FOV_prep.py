# Copyright (c) 2024
# Author: Dean Hand
# License: AGPL
# Version: 1.0

from new_fov import HighAccuracyFOVCalculator


def calculate_fov(re_altitude, ab_altitude, focal_length, sensor_width, sensor_height, image_width, image_height,
                  gimbal_roll_deg, gimbal_pitch_deg, gimbal_yaw_deg, flight_roll_deg, flight_pitch_deg,
                  flight_yaw_deg, drone_latitude, drone_longitude, datetime_original, lens_FOVwm, lens_FOVhm, i):

    camera_info = {
        'sensor_width': sensor_width,  # mm
        'sensor_height': sensor_height,  # mm (Optional if not used in calculations)
        'image_width': image_width,  # pixels
        'image_height': image_height,  # pixels
        'Focal_Length': focal_length,  # mm
        'lens_FOVw': lens_FOVwm,  # lens distortion in mm
        'lens_FOVh': lens_FOVhm  # lens distortion in mm
    }
    gimbal_orientation = {
        'roll': gimbal_roll_deg,  # Gimbal roll in degrees
        'pitch': gimbal_pitch_deg,  # Gimbal pitch in degrees (negative if pointing downwards)
        'yaw': gimbal_yaw_deg,  # Gimbal yaw in degrees
    }
    flight_orientation = {
        'roll': flight_roll_deg,  # Flight roll in degrees
        'pitch': flight_pitch_deg,  # Flight pitch in degrees
        'yaw': flight_yaw_deg,  # Flight yaw in degrees (direction of flight)
    }

    calculator = HighAccuracyFOVCalculator(
        drone_gps=(drone_latitude,
                   drone_longitude),
        drone_altitude=re_altitude,
        camera_info=camera_info,
        gimbal_orientation=gimbal_orientation,
        flight_orientation=flight_orientation,
        datetime_original=datetime_original,
        i=i
    )
    # print("Calculator", drone_latitude, drone_longitude, drone_altitude, camera_info, gimbal_orientation, flight_orientation, datetime_original)
    # exit()
    # Calculate the FOV bounding box
    cust_bbox, geojson_bbox = calculator.get_fov_bbox()

    return cust_bbox, geojson_bbox
