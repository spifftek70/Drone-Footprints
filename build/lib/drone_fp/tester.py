import math
import geojson

def calculate_drone_footprint(drone_longitude, drone_latitude, relative_altitude, focal_length, image_size_width, image_size_height, sensor_width, sensor_height, gimbal_roll_degree, gimbal_yaw_degree, gimbal_pitch_degree):
    # Constants
    earth_radius = 6371000  # Radius of the Earth in meters
    degrees_to_radians = math.pi / 180.0
    radians_to_degrees = 180.0 / math.pi

    # Calculate the field of view (FOV) angles in radians
    fov_horizontal = 2 * math.atan((sensor_width / (2 * focal_length)) * image_size_width)
    fov_vertical = 2 * math.atan((sensor_height / (2 * focal_length)) * image_size_height)

    # Calculate the half-width and half-height of the footprint
    half_width = relative_altitude * math.tan(fov_horizontal / 2)
    half_height = relative_altitude * math.tan(fov_vertical / 2)

    # Convert drone latitude and longitude to radians
    lat_radians = drone_latitude * degrees_to_radians
    lon_radians = drone_longitude * degrees_to_radians

    # Apply gimbal rotations
    roll_radians = gimbal_roll_degree * degrees_to_radians
    yaw_radians = gimbal_yaw_degree * degrees_to_radians
    pitch_radians = gimbal_pitch_degree * degrees_to_radians

    # Calculate rotated coordinates of the four corners of the footprint
    half_width_rotated = half_width * math.cos(pitch_radians) + half_height * math.sin(pitch_radians)
    half_height_rotated = half_height * math.cos(pitch_radians) + half_width * math.sin(pitch_radians)

    bottom_left_lon = lon_radians - half_width_rotated
    bottom_left_lat = lat_radians - half_height_rotated
    bottom_right_lon = lon_radians + half_width_rotated
    bottom_right_lat = lat_radians - half_height_rotated
    top_right_lon = lon_radians + half_width_rotated
    top_right_lat = lat_radians + half_height_rotated
    top_left_lon = lon_radians - half_width_rotated
    top_left_lat = lat_radians + half_height_rotated

    # Create a GeoJSON polygon feature with the right-hand rule
    coordinates = [
        (bottom_left_lon * radians_to_degrees, bottom_left_lat * radians_to_degrees),
        (bottom_right_lon * radians_to_degrees, bottom_right_lat * radians_to_degrees),
        (top_right_lon * radians_to_degrees, top_right_lat * radians_to_degrees),
        (top_left_lon * radians_to_degrees, top_left_lat * radians_to_degrees),
        (bottom_left_lon * radians_to_degrees, bottom_left_lat * radians_to_degrees)
    ]

    footprint_polygon = geojson.Polygon([coordinates])

    # Create a GeoJSON feature
    feature = geojson.Feature(geometry=footprint_polygon)

    return geojson.dumps(feature)

# Example usage:
drone_longitude = -111.8852671
drone_latitude = 33.3671694
relative_altitude = 402.1
focal_length = 10.26
image_size_width = 5472
image_size_height = 3648
sensor_width = 13.2
sensor_height = 8.8
gimbal_roll_degree = 0.00
gimbal_yaw_degree = -3.4
gimbal_pitch_degree = -89.9

geojson_footprint = calculate_drone_footprint(drone_longitude, drone_latitude, relative_altitude, focal_length, image_size_width, image_size_height, sensor_width, sensor_height, gimbal_roll_degree, gimbal_yaw_degree, gimbal_pitch_degree)

print(geojson_footprint)
