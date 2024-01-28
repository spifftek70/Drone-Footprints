# Adjusting the script to change the polygon orientation by 180 degrees
# Re-executing the script after state reset
import math
import numpy as np
import pyproj

class DroneFootprintCalculator:
    def __init__(self, utm_zone, is_northern_hemisphere=True):
        self.utm_proj = pyproj.Proj(proj='utm', zone=utm_zone, ellps='WGS84', south=not is_northern_hemisphere)

    def calculate_footprint(self, Focal_Length, Relative_Altitude, GimbalRollDegree,
                            GimbalYawDegree, GimbalPitchDegree, FlightRollDegree, FlightYawDegree, FlightPitchDegree,
                            drone_longitude, drone_latitude, sensor_width, sensor_height):
        # Convert drone's longitude and latitude to UTM
        drone_easting, drone_northing = self.utm_proj(drone_longitude, drone_latitude)

        # Calculate field of view angles
        fov_x_rad = 2.0 * math.atan(sensor_width / (2.0 * Focal_Length))
        fov_y_rad = 2.0 * math.atan(sensor_height / (2.0 * Focal_Length))

        # Calculate footprint dimensions
        width = Relative_Altitude * math.tan(fov_x_rad / 2) * 2
        height = Relative_Altitude * math.tan(fov_y_rad / 2) * 2

        # Define footprint corners
        local_corners = [
            [-width / 2, height / 2, 0],
            [width / 2, height / 2, 0],
            [width / 2, -height / 2, 0],
            [-width / 2, -height / 2, 0]
        ]

        # Apply rotation based on Gimbal and Flight angles
        R_combined = self.calculate_combined_rotation_matrix(
            GimbalRollDegree, GimbalYawDegree, GimbalPitchDegree,
            FlightRollDegree, FlightYawDegree, FlightPitchDegree
        )

        # Transform local coordinates to global coordinates
        global_corners = []
        for corner in local_corners:
            rotated_corner = np.dot(R_combined, corner)
            easting = drone_easting + rotated_corner[0]
            northing = drone_northing + rotated_corner[1]
            global_corners.append([easting, northing])

        # Convert UTM coordinates of the footprint corners to decimal degrees
        lonlat_corners = [self.utm_proj(corner[0], corner[1], inverse=True) for corner in global_corners]

        return lonlat_corners

    def calculate_combined_rotation_matrix(self, GimbalRollDegree, GimbalYawDegree, GimbalPitchDegree,
                                           FlightRollDegree, FlightYawDegree, FlightPitchDegree):
        # Convert degrees to radians
        GimbalRoll_rad = math.radians(GimbalRollDegree)
        GimbalYaw_rad = math.radians(GimbalYawDegree)
        GimbalPitch_rad = math.radians(GimbalPitchDegree)
        FlightRoll_rad = math.radians(FlightRollDegree)
        FlightYaw_rad = math.radians(FlightYawDegree)
        FlightPitch_rad = math.radians(FlightPitchDegree)

        # Calculate rotation matrix for gimbal
        R_gimbal = self.rotation_matrix_from_euler(GimbalRoll_rad, GimbalPitch_rad, GimbalYaw_rad)

        # Calculate rotation matrix for flight
        R_flight = self.rotation_matrix_from_euler(FlightRoll_rad, FlightPitch_rad, FlightYaw_rad)

        # Combine gimbal and flight rotation matrices
        R_combined = np.dot(R_flight, R_gimbal)

        return R_combined

    def rotation_matrix_from_euler(self, roll, pitch, yaw):
        # Rotation calculations
        cy = math.cos(yaw)
        sy = math.sin(yaw)
        cp = math.cos(pitch)
        sp = math.sin(pitch)
        cr = math.cos(roll)
        sr = math.sin(roll)

        # Rotation matrix
        R = [
            [cp * cy, cp * sy, -sp],
            [sr * sp * cy - cr * sy, sr * sp * sy + cr * cy, sr * cp],
            [cr * sp * cy + sr * sy, cr * sp * sy - sr * cy, cr * cp]
        ]

        return R
#
# # Example usage
# calculator = DroneFootprintCalculator(utm_zone=12, is_northern_hemisphere=True)
# footprint = calculator.calculate_footprint(
#     10.26, 25.5, 0.0, 115.3, 89.9, 0.2, 116.5, 0.6, -111.885227722222, 33.3672385555556, 13.2, 8.8
# )
#
# footprint
#
#
# # Example usage
# calculator = DroneFootprintCalculator(utm_zone=12, is_northern_hemisphere=True)
# footprint = calculator.calculate_footprint(
#     10.26, 25.5, 0.0, 115.3, 89.9, 0.2, 116.5, 0.6, -111.885227722222, 33.3672385555556, 13.2, 8.8
# )
#
# footprint
#


# Adjusting the script to change the polygon orientation by 180 degrees

# # Example usage
# calculator = DroneFootprintCalculator(utm_zone=12, is_northern_hemisphere=True)
# footprint = calculator.calculate_footprint(
#     10.26, 25.5, 0.0, 115.3, 89.9, 0.2, 116.5, 0.6, -111.885227722222, 33.3672385555556, 13.2, 8.8
# )
# print(footprint)


# # Example usage
# calculator = DroneFootprintCalculator(utm_zone=12, is_northern_hemisphere=True)
# footprint = calculator.calculate_footprint(
#     10.26, 25.5, 0.0, 115.3, 89.9, 0.2, 116.5, 0.6, -111.885227722222, 33.3672385555556, 13.2, 8.8
# )
#
# foot

#
# # Example usage
# calculator = DroneFootprintCalculator(utm_zone=12, is_northern_hemisphere=True)
# footprint = calculator.calculate_footprint(
#     10.26, 25.5, 0.0, 115.3, 89.9, 0.2, 116.5, 0.6, -111.885227722222, 33.3672385555556, 13.2, 8.8
# )
# print(footprint)


# # Revising the code to change the polygon orientation by -90 degrees
# import math
# import numpy as np
# import pyproj
#
# class DroneFootprintCalculator:
#     def __init__(self, utm_zone, is_northern_hemisphere=True):
#         self.utm_proj = pyproj.Proj(proj='utm', zone=utm_zone, ellps='WGS84', south=not is_northern_hemisphere)
#
#     def calculate_footprint(self, Focal_Length, Relative_Altitude, GimbalRollDegree,
#                             GimbalYawDegree, GimbalPitchDegree, FlightRollDegree, FlightYawDegree, FlightPitchDegree,
#                             drone_longitude, drone_latitude, sensor_width, sensor_height):
#         # Convert drone's longitude and latitude to UTM
#         drone_easting, drone_northing = self.utm_proj(drone_longitude, drone_latitude)
#
#         # Calculate field of view angles
#         fov_x_rad = 2.0 * math.atan(sensor_width / (2.0 * Focal_Length))
#         fov_y_rad = 2.0 * math.atan(sensor_height / (2.0 * Focal_Length))
#
#         # Calculate footprint dimensions
#         width = Relative_Altitude * math.tan(fov_x_rad / 2) * 2
#         height = Relative_Altitude * math.tan(fov_y_rad / 2) * 2
#
#         # Adjust the order of corners to change the orientation by -90 degrees
#         local_corners = [
#             [height / 2, width / 2, 0],
#             [-height / 2, width / 2, 0],
#             [-height / 2, -width / 2, 0],
#             [height / 2, -width / 2, 0]
#         ]
#
#         # Apply rotation based only on FlightYawDegree
#         R_combined = self.calculate_combined_rotation_matrix(
#             FlightRollDegree, FlightYawDegree, FlightPitchDegree
#         )
#
#         # Transform local coordinates to global coordinates
#         global_corners = []
#         for corner in local_corners:
#             rotated_corner = np.dot(R_combined, corner)
#             easting = drone_easting + rotated_corner[0]
#             northing = drone_northing + rotated_corner[1]
#             global_corners.append([easting, northing])
#
#         # Convert UTM coordinates of the footprint corners to decimal degrees
#         lonlat_corners = [self.utm_proj(corner[0], corner[1], inverse=True) for corner in global_corners]
#
#         return lonlat_corners
#
#     def calculate_combined_rotation_matrix(self, FlightRollDegree, FlightYawDegree, FlightPitchDegree):
#         # Convert degrees to radians
#         FlightRollDegree_rad = math.radians(FlightRollDegree)
#         FlightYawDegree_rad = math.radians(FlightYawDegree)
#         FlightPitchDegree_rad = math.radians(FlightPitchDegree)
#
#         # Calculate rotation matrix from Euler angles (roll, pitch, yaw)
#         R = self.rotation_matrix_from_euler(FlightRollDegree_rad, FlightPitchDegree_rad, FlightYawDegree_rad)
#
#         return R
#
#     def rotation_matrix_from_euler(self, roll, pitch, yaw):
#         # Rotation calculations
#         cy = math.cos(yaw)
#         sy = math.sin(yaw)
#         cr = math.cos(roll)
#         sr = math.sin(roll)
#         cp = math.cos(pitch)
#         sp = math.sin(pitch)
#
#         # Rotation matrix
#         R = [
#             [cp * cy, cp * sy, -sp],
#             [sr * sp * cy - cr * sy, sr * sp * sy + cr * cy, sr * cp],
#             [cr * sp * cy + sr * sy, cr * sp * sy - sr * cy, cr * cp]
#         ]
#
#         return R
#
# # # Example usage
# # calculator = DroneFootprintCalculator(utm_zone=12, is_northern_hemisphere=True)
# # footprint = calculator.calculate_footprint(
# #     10.26, 25.5, 0.0, 115.3, 89.9, 0.2, 116.5, 0.6, -111.885227722222, 33.3672385555556, 13.2, 8.8
# # )
# #
# # footprint
# #
