import math
import pyproj


class DroneFootprintCalculator:
    def __init__(self, utm_zone, is_northern_hemisphere=True):
        self.utm_zone = utm_zone
        self.is_northern_hemisphere = is_northern_hemisphere
        self.utm_proj = pyproj.Proj(proj='utm', zone=self.utm_zone, ellps='WGS84', north=self.is_northern_hemisphere)

    def calculate_footprint(self, Focal_Length, Image_Width, Image_Height, Relative_Altitude, GimbalRollDegree, GimbalYawDegree, GimbalPitchDegree, drone_longitude, drone_latitude, sensor_width, sensor_height):
        # Convert drone's longitude and latitude to UTM
        drone_easting, drone_northing = self.utm_proj(drone_longitude, drone_latitude)

        # Calculate field of view angles
        fov_x_rad = 2.0 * math.atan(sensor_width / (2.0 * Focal_Length))
        fov_y_rad = 2.0 * math.atan(sensor_height / (2.0 * Focal_Length))

        # Calculate quaternion from gimbal angles
        roll_rad = math.radians(GimbalRollDegree)
        pitch_rad = math.radians(GimbalPitchDegree)
        yaw_rad = math.radians(GimbalYawDegree / 2.0)  # Note the division by 2

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

        # Calculate footprint coordinates in UTM
        altitude = Relative_Altitude
        half_width = altitude * math.tan(fov_x_rad / 2.0)
        half_height = altitude * math.tan(fov_y_rad / 2.0)

        # Calculate rotation matrix
        R = [
            [1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qz * qw), 2 * (qx * qz + qy * qw)],
            [2 * (qx * qy + qz * qw), 1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz - qx * qw)],
            [2 * (qx * qz - qy * qw), 2 * (qy * qz + qx * qw), 1 - 2 * (qx * qx + qy * qy)]
        ]

        # Calculate footprint coordinates using rotation matrix
        easting1 = drone_easting - (half_width * R[0][0] + half_height * R[1][0])
        northing1 = drone_northing - (half_width * R[0][1] + half_height * R[1][1])
        easting2 = drone_easting + (half_width * R[0][0] + half_height * R[1][0])
        northing2 = drone_northing + (half_width * R[0][1] + half_height * R[1][1])
        easting3 = drone_easting + (half_width * R[0][0] - half_height * R[1][0])
        northing3 = drone_northing + (half_width * R[0][1] - half_height * R[1][1])
        easting4 = drone_easting - (half_width * R[0][0] - half_height * R[1][0])
        northing4 = drone_northing - (half_width * R[0][1] - half_height * R[1][1])

        # Convert UTM coordinates of the footprint corners to decimal degrees
        lonlat1 = self.utm_proj(easting1, northing1, inverse=True)
        lonlat2 = self.utm_proj(easting2, northing2, inverse=True)
        lonlat3 = self.utm_proj(easting3, northing3, inverse=True)
        lonlat4 = self.utm_proj(easting4, northing4, inverse=True)

        return [lonlat1, lonlat2, lonlat3, lonlat4]
        # return [lonlat3, lonlat2, lonlat4, lonlat1]
        # return [lonlat2, lonlat4, lonlat1, lonlat3]
        # return [lonlat1, lonlat4, lonlat2, lonlat3]

