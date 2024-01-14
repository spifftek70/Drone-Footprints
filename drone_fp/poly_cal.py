from shapely.geometry import Polygon
from geopy.distance import distance
import math


def calculate_polygon(center_latitude, center_longitude, rel_altitude, abs_altitude, pitch, yaw, roll, gimbal_pitch, gimbal_yaw, gimbal_roll, sensor_width, sensor_height):

    # Extract image metadata

    # Convert angles from degrees to radians
    pitch_rad = math.radians(pitch)
    yaw_rad = math.radians(yaw)
    roll_rad = math.radians(roll)
    gimbal_pitch_rad = math.radians(gimbal_pitch)
    gimbal_yaw_rad = math.radians(gimbal_yaw)
    gimbal_roll_rad = math.radians(gimbal_roll)

    # Calculate the coordinates of the four corners of the image
    half_sensor_width = sensor_width / 2
    half_sensor_height = sensor_height / 2

    # Image corners in image coordinate system
    image_corners = [
        (-half_sensor_width, -half_sensor_height),
        (half_sensor_width, -half_sensor_height),
        (half_sensor_width, half_sensor_height),
        (-half_sensor_width, half_sensor_height)
    ]

    # Convert image corners to ground coordinates
    ground_corners = []
    for corner in image_corners:
        x, y = corner
        # Apply transformations for drone attitude, yaw, and gimbal orientation
        rotated_x = x * math.cos(pitch_rad) + y * math.sin(pitch_rad)
        rotated_y = -x * math.sin(pitch_rad) + y * math.cos(pitch_rad)
        rotated_x = rotated_x * math.cos(yaw_rad) + rotated_y * math.sin(yaw_rad)
        rotated_y = -rotated_x * math.sin(yaw_rad) + rotated_y * math.cos(yaw_rad)
        rotated_x_gimbal = rotated_x * math.cos(gimbal_pitch_rad) + rotated_y * math.sin(gimbal_pitch_rad)
        rotated_y_gimbal = -rotated_x * math.sin(gimbal_pitch_rad) + rotated_y * math.cos(gimbal_pitch_rad)
        rotated_x_gimbal = rotated_x_gimbal * math.cos(gimbal_roll_rad) + rotated_y_gimbal * math.sin(gimbal_roll_rad)
        rotated_y_gimbal = -rotated_x_gimbal * math.sin(gimbal_roll_rad) + rotated_y_gimbal * math.cos(gimbal_roll_rad)

        # Convert distances to latitude and longitude using geopy
        lat_dist = rotated_x_gimbal / 111.32  # 1 degree of latitude is approximately 111.32 km
        lon_dist = rotated_y_gimbal / (111.32 * math.cos(math.radians(center_latitude)))

        # Calculate new latitude and longitude based on the azimuth (90 degrees for east)
        lat_increment = lat_dist * math.cos(math.radians(90))
        lon_increment = lon_dist * math.sin(math.radians(90))

        final_latitude = center_latitude + lat_increment
        final_longitude = center_longitude + lon_increment

        ground_corners.append((final_longitude, final_latitude))

    # Create a polygon using Shapely
    polygon = Polygon(ground_corners)

    return polygon


# Rest of the code remains the same...


def process_batch_images(image_metadata_list, center_latitude, center_longitude, rel_altitude, abs_altitude, pitch, yaw, roll, gimbal_altitude, gimbal_pitch, gimbal_yaw, gimbal_roll):
    polygons = []
    for image_metadata in image_metadata_list:
        # Pass the correct number of arguments
        polygon = calculate_polygon(center_latitude, center_longitude, rel_altitude, abs_altitude, pitch, yaw, roll, gimbal_altitude, gimbal_pitch, gimbal_yaw, gimbal_roll, image_metadata)
        polygons.append(polygon)
    return polygons
#
#
# # Example usage for batch processing:
# center_latitude = 37.7749
# center_longitude = -122.4194
# rel_altitude = 10.0
# abs_altitude = 50.0
# pitch = 5.0
# yaw = 10.0
# roll = 15.0
# gimbal_altitude = 5.0
# gimbal_pitch = 2.0
# gimbal_yaw = 5.0
# gimbal_roll = 1.0
#
# image_metadata_list = [
#     {'sensor_width': 22.3, 'sensor_height': 14.9, 'image_width': 4000, 'image_height': 3000},
#     {'sensor_width': 22.3, 'sensor_height': 14.9, 'image_width': 4000, 'image_height': 3000},
#     # Add more image metadata dictionaries as needed
# ]
#
# # Ensure the correct number of arguments is passed
# polygons = process_batch_images(image_metadata_list, center_latitude, center_longitude, rel_altitude, abs_altitude, pitch, yaw, roll, gimbal_altitude, gimbal_pitch, gimbal_yaw, gimbal_roll)
#
# for idx, polygon in enumerate(polygons):
#     print(f"Polygon {idx + 1} coordinates (latitude, longitude):", polygon.exterior.coords.xy)
