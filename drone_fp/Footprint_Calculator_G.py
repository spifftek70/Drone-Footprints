#### Created / written by Dean E. Hand (dean.e.hand@me.com).

import math
import pyproj

class DroneFootprintCalculator:
    def __init__(self, utm_zone, is_northern_hemisphere=True):
        self.utm_zone = utm_zone
        self.is_northern_hemisphere = is_northern_hemisphere
        self.utm_proj = pyproj.Proj(proj='utm', zone=self.utm_zone, ellps='WGS84', north=self.is_northern_hemisphere)
        self.max_gimbal_pitch = 70  # Maximum allowable Gimbal pitch in degrees

    def calculate_footprint(self, Focal_Length, Relative_Altitude, GimbalRollDegree,
                            GimbalYawDegree, GimbalPitchDegree, drone_longitude, drone_latitude, sensor_width, sensor_height):
        # Ensure Gimbal pitch is within the allowable range
        if GimbalPitchDegree < -self.max_gimbal_pitch:
            GimbalPitchDegree = -self.max_gimbal_pitch
        elif GimbalPitchDegree > self.max_gimbal_pitch:
            GimbalPitchDegree = self.max_gimbal_pitch

        # Convert drone's longitude and latitude to UTM
        drone_easting, drone_northing = self.utm_proj(drone_longitude, drone_latitude)

        # Calculate field of view angles
        fov_x_rad = 2.0 * math.atan(sensor_width / (2.0 * Focal_Length))
        fov_y_rad = 2.0 * math.atan(sensor_height / (2.0 * Focal_Length))

        # Calculate quaternion from gimbal angles with adjusted yaw angle
        roll_rad = math.radians(GimbalRollDegree)
        pitch_rad = math.radians(GimbalPitchDegree)
        yaw_rad = math.radians(GimbalYawDegree)

        cy = math.cos(yaw_rad)
        sy = math.sin(yaw_rad)
        cr = math.cos(roll_rad)
        sr = math.sin(roll_rad)
        cp = math.cos(pitch_rad)
        sp = math.sin(pitch_rad)

        qw = cy * cr * cp + sy * sr * sp
        qx = cy * sr * cp - sy * cr * sp
        qy = cy * cr * sp + sy * sr * cp
        qz = sy * cr * cp - cy * sr * sp

        # Calculate rotation matrix
        R_gimbal = [
            [1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qz * qw), 2 * (qx * qz + qy * qw)],
            [2 * (qx * qy + qz * qw), 1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz - qx * qw)],
            [2 * (qx * qz - qy * qw), 2 * (qy * qz + qx * qw), 1 - 2 * (qx * qx + qy * qy)]
        ]

        # Calculate footprint coordinates using rotation matrix
        altitude = Relative_Altitude
        half_width = altitude * math.tan(fov_x_rad / 2.0)
        half_height = altitude * math.tan(fov_y_rad / 2.0)

        # Calculate the corners in local coordinate system
        local_corners = [
            [-half_width, half_height],
            [half_width, half_height],
            [half_width, -half_height],
            [-half_width, -half_height]
        ]

        # Transform local coordinates to global coordinates
        global_corners = []
        for corner in local_corners:
            easting = drone_easting + corner[0] * R_gimbal[0][0] + corner[1] * R_gimbal[0][1]
            northing = drone_northing + corner[0] * R_gimbal[1][0] + corner[1] * R_gimbal[1][1]
            global_corners.append([easting, northing])

        # Convert UTM coordinates of the footprint corners to decimal degrees
        lonlat_corners = [self.utm_proj(corner[0], corner[1], inverse=True) for corner in global_corners]

        return lonlat_corners