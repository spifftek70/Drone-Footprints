import utm
import math


def decimal_degrees_to_utm(latitude, longitude):
    utm_coord = utm.from_latlon(latitude, longitude)
    return utm_coord[0], utm_coord[1]


def calculate_drone_imagery_footprints(drone_params):
    fov_x = drone_params['FOV_x']
    fov_y = drone_params['FOV_y']
    pixel_resolution = drone_params['Average Pixel Resolution']
    focal_length = drone_params['Focal_Length']
    image_width = drone_params['Image_Width']
    image_height = drone_params['Image_Height']
    relative_altitude = drone_params['RelativeAltitude']
    drone_roll_degree = drone_params['DroneRollDegree']
    drone_yaw_degree = drone_params['DroneYawDegree']
    drone_pitch_degree = drone_params['DronePitchDegree']
    gimbal_roll_degree = drone_params['GimbalRollDegree']
    gimbal_yaw_degree = drone_params['GimbalYawDegree']
    gimbal_pitch_degree = drone_params['GimbalPitchDegree']
    drone_latitude = drone_params['drone_latitude']
    drone_longitude = drone_params['drone_longitude']
    sensor_width = drone_params['sensor_width']
    sensor_height = drone_params['sensor_height']

    # Convert degrees to radians
    drone_roll_rad = math.radians(drone_roll_degree)
    drone_yaw_rad = math.radians(drone_yaw_degree)
    drone_pitch_rad = math.radians(drone_pitch_degree)
    gimbal_roll_rad = math.radians(gimbal_roll_degree)
    gimbal_yaw_rad = math.radians(gimbal_yaw_degree)
    gimbal_pitch_rad = math.radians(gimbal_pitch_degree)

    # Calculate footprint size in meters
    footprint_x = (2 * relative_altitude * math.tan(math.radians(fov_x / 2))) / pixel_resolution
    footprint_y = (2 * relative_altitude * math.tan(math.radians(fov_y / 2))) / pixel_resolution

    # Calculate drone position offsets in meters
    x_offset = (footprint_x - image_width) / 2
    y_offset = (footprint_y - image_height) / 2

    # Calculate drone position in UTM coordinates
    drone_utm_x, drone_utm_y = decimal_degrees_to_utm(drone_latitude, drone_longitude)

    # Apply drone yaw, pitch, and roll adjustments
    adjusted_x = drone_utm_x + x_offset * math.cos(drone_yaw_rad) - y_offset * math.sin(drone_yaw_rad)
    adjusted_y = drone_utm_y + x_offset * math.sin(drone_yaw_rad) + y_offset * math.cos(drone_yaw_rad)

    # Adjust for drone pitch, gimbal roll, gimbal yaw, and gimbal pitch
    adjusted_x += focal_length * math.tan(drone_pitch_rad)
    adjusted_y += focal_length * math.tan(gimbal_roll_rad)
    adjusted_x += focal_length * math.tan(gimbal_yaw_rad)
    adjusted_y += focal_length * math.tan(gimbal_pitch_rad)

    # Adjust for drone roll
    adjusted_x += focal_length * math.tan(drone_roll_rad)

    # Calculate the four corners of the footprint polygon
    footprint = [
        (adjusted_x - footprint_x / 2, adjusted_y - footprint_y / 2),
        (adjusted_x + footprint_x / 2, adjusted_y - footprint_y / 2),
        (adjusted_x + footprint_x / 2, adjusted_y + footprint_y / 2),
        (adjusted_x - footprint_x / 2, adjusted_y + footprint_y / 2)
    ]

    return footprint


def utm_to_decimal_degrees(utm_x, utm_y, utm_zone_number, utm_zone_letter):
    lat, lon = utm.to_latlon(utm_x, utm_y, utm_zone_number, utm_zone_letter)
    return lat, lon


# Example usage:
drone_params = {
    'FOV_x': 3.1340926887457465,
    'FOV_y': 3.1303427722398847,
    'Average Pixel Resolution': 9.453977292158271,
    'Focal_Length': 10.26,
    'Image_Width': 5472,
    'Image_Height': 3648,
    'RelativeAltitude': 34.1,
    'DroneRollDegree': 6.30,
    'DroneYawDegree': 10.90,
    'DronePitchDegree': 14.20,
    'GimbalRollDegree': 0.00,
    'GimbalYawDegree': -3.4,
    'GimbalPitchDegree': -89.9,
    'drone_latitude': 33.3671694,
    'drone_longitude': -111.8852671,
    'sensor_width': 13.2,
    'sensor_height': 8.8,
}

footprint = calculate_drone_imagery_footprints(drone_params)
print("Footprint Coordinates:")
for coord in footprint:
    print(f"({coord[0]}, {coord[1]})")

# Provide the UTM zone number and letter for your specific location
utm_zone_number = 12  # Replace with your UTM zone number
utm_zone_letter = 'S'  # Replace with your UTM zone letter

# Convert UTM coordinates back to decimal degrees
for utm_coord in footprint:
    lat, lon = utm_to_decimal_degrees(utm_coord[0], utm_coord[1], utm_zone_number, utm_zone_letter)
    print(f"Decimal Degrees: ({lat}, {lon})")
