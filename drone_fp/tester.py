import math


def calculate_image_footprints(fov_x, fov_y, pixel_resolution_x, pixel_resolution_y, focal_length, heading,
                               relative_altitude, drone_roll_degree, drone_yaw_degree, drone_pitch_degree,
                               drone_longitude, drone_latitude):
    # Constants
    earth_radius = 6378137  # Earth's radius in meters (WGS-84)
    pi = math.pi

    # Calculate drone's position in UTM coordinates
    drone_x = drone_longitude * (earth_radius * pi / 180)
    drone_y = drone_latitude * (earth_radius * pi / 180)

    # Calculate the rotation matrix for the drone's orientation
    roll_rad = math.radians(drone_roll_degree)
    pitch_rad = math.radians(drone_pitch_degree)
    yaw_rad = math.radians(drone_yaw_degree)

    rotation_matrix = [
        [math.cos(yaw_rad) * math.cos(pitch_rad),
         math.cos(yaw_rad) * math.sin(pitch_rad) * math.sin(roll_rad) - math.sin(yaw_rad) * math.cos(roll_rad),
         math.cos(yaw_rad) * math.sin(pitch_rad) * math.cos(roll_rad) + math.sin(yaw_rad) * math.sin(roll_rad)],

        [math.sin(yaw_rad) * math.cos(pitch_rad),
         math.sin(yaw_rad) * math.sin(pitch_rad) * math.sin(roll_rad) + math.cos(yaw_rad) * math.cos(roll_rad),
         math.sin(yaw_rad) * math.sin(pitch_rad) * math.cos(roll_rad) - math.cos(yaw_rad) * math.sin(roll_rad)],

        [-math.sin(pitch_rad),
         math.cos(pitch_rad) * math.sin(roll_rad),
         math.cos(pitch_rad) * math.cos(roll_rad)]
    ]

    # Calculate the pixel size in meters
    pixel_size_x = pixel_resolution_x / focal_length
    pixel_size_y = pixel_resolution_y / focal_length

    # Calculate the FOV in meters
    fov_x_meters = pixel_size_x * fov_x
    fov_y_meters = pixel_size_y * fov_y

    # Calculate the image footprint vertices
    vertices = []
    for i in range(-1, 2, 2):
        for j in range(-1, 2, 2):
            x = (i * fov_x_meters / 2)
            y = (j * fov_y_meters / 2)
            vertices.append([x, y, 0])

    # Apply the rotation matrix to the vertices
    rotated_vertices = []
    for vertex in vertices:
        rotated_vertex = [0, 0, 0]
        for i in range(3):
            for j in range(3):
                rotated_vertex[i] += vertex[j] * rotation_matrix[i][j]
        rotated_vertices.append(rotated_vertex)

    # Adjust the altitude
    for i in range(len(rotated_vertices)):
        rotated_vertices[i][2] = -relative_altitude

    # Calculate the image footprint in UTM coordinates
    utm_coordinates = []
    for vertex in rotated_vertices:
        easting = drone_x + vertex[0]
        northing = drone_y + vertex[1]
        utm_coordinates.append([easting, northing])

    return utm_coordinates


# Example usage
fov_x = 517.3216374269006
fov_y = 344.88109161793375
pixel_resolution_x = 9.453977292158271
pixel_resolution_y = 9.453977292158271
focal_length = 10.26
heading = 10.90
relative_altitude = 34.00
drone_roll_degree = 6.30
drone_yaw_degree = 10.90
drone_pitch_degree = 14.20
drone_longitude = -111.8852671
drone_latitude = 33.3671694

utm_coordinates = calculate_image_footprints(fov_x, fov_y, pixel_resolution_x, pixel_resolution_y, focal_length,
                                             heading, relative_altitude, drone_roll_degree, drone_yaw_degree,
                                             drone_pitch_degree, drone_longitude, drone_latitude)

for i, point in enumerate(utm_coordinates):
    print(f"Point {i + 1}: Easting={point[0]:.2f}m, Northing={point[1]:.2f}m")
