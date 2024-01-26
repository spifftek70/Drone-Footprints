import math
import pyproj

class DroneFootprintCalculator:
    def __init__(self, utm_zone, is_northern_hemisphere=True):
        self.utm_zone = utm_zone
        self.is_northern_hemisphere = is_northern_hemisphere
        self.utm_proj = pyproj.Proj(proj='utm', zone=self.utm_zone, ellps='WGS84', north=self.is_northern_hemisphere)

    def calculate_footprint(self, metadata):
        # Extract relevant metadata
        Focal_Length = metadata["Composite:FocalLength35efl"]
        Relative_Altitude = metadata["XMP:RelativeAltitude"]
        GimbalRollDegree = metadata["XMP:GimbalRollDegree"]
        GimbalYawDegree = metadata["XMP:GimbalYawDegree"]
        GimbalPitchDegree = metadata["XMP:GimbalPitchDegree"]
        drone_longitude = metadata["Composite:GPSLongitude"]
        drone_latitude = metadata["Composite:GPSLatitude"]
        sensor_width = metadata["EXIF:ImageWidth"]
        sensor_height = metadata["EXIF:ImageHeight"]

        # Convert drone's longitude and latitude to UTM
        drone_easting, drone_northing = self.utm_proj(drone_longitude, drone_latitude)

        # Calculate field of view angles
        fov_x_rad = 2.0 * math.atan(float(sensor_width) / (2.0 * Focal_Length))
        fov_y_rad = 2.0 * math.atan(float(sensor_height) / (2.0 * Focal_Length))

        # Calculate quaternion from gimbal angles with adjusted yaw angle
        roll_rad = math.radians(GimbalRollDegree)
        pitch_rad = math.radians(GimbalPitchDegree)
        yaw_rad = -1 * (math.radians(GimbalYawDegree / 2.0))  # Note the division by 2

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
        altitude = float(Relative_Altitude)
        half_width = altitude * math.tan(fov_x_rad / 2.0)
        half_height = altitude * math.tan(fov_y_rad / 2.0)

        easting1 = drone_easting - (half_width * R_gimbal[0][0] + half_height * R_gimbal[1][0])
        northing1 = drone_northing - (half_width * R_gimbal[0][1] + half_height * R_gimbal[1][1])
        easting2 = drone_easting + (half_width * R_gimbal[0][0] + half_height * R_gimbal[1][0])
        northing2 = drone_northing + (half_width * R_gimbal[0][1] + half_height * R_gimbal[1][1])
        easting3 = drone_easting + (half_width * R_gimbal[0][0] - half_height * R_gimbal[1][0])
        northing3 = drone_northing + (half_width * R_gimbal[0][1] - half_height * R_gimbal[1][1])
        easting4 = drone_easting - (half_width * R_gimbal[0][0] - half_height * R_gimbal[1][0])
        northing4 = drone_northing - (half_width * R_gimbal[0][1] - half_height * R_gimbal[1][1])

        # Convert UTM coordinates of the footprint corners to decimal degrees
        lonlat1 = self.utm_proj(easting1, northing1, inverse=True)
        lonlat2 = self.utm_proj(easting2, northing2, inverse=True)
        lonlat3 = self.utm_proj(easting3, northing3, inverse=True)
        lonlat4 = self.utm_proj(easting4, northing4, inverse=True)

        return [lonlat1, lonlat2, lonlat3, lonlat4]

# Example usage
metadata = {
    # Include all the relevant metadata fields from your provided data
}
utm_zone = 12  # Replace with the correct UTM zone for your location
calculator = DroneFootprintCalculator(utm_zone)
footprint_coordinates = calculator.calculate_footprint(metadata)
print(footprint_coordinates)
