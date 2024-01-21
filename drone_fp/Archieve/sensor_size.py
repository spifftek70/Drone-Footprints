import math

# Given data
Focal_Length = 10.26  # mm
Image_Width = 5472  # pixels
Image_Height = 3648  # pixels
Drone_Altitude = 34  # meters
GimbalRollDegree = 0.00  # degrees
GimbalYawDegree = -3.4  # degrees
GimbalPitchDegree = -89.9  # degrees
drone_longitude = -111.8852671
drone_latitude = 33.3671694
sensor_width = 13.2  # mm
sensor_height = 8.8  # mm

# Calculate the diagonal of the sensor (image sensor diagonal)
sensor_diagonal = math.sqrt(sensor_width**2 + sensor_height**2)

# Calculate the FOV using the formula
FOV = 2 * math.degrees(math.atan(sensor_diagonal / (2 * Focal_Length)))

# Calculate the width and height of the image footprint on the ground
Ground_Width = 2 * Drone_Altitude * math.tan(math.radians(FOV / 2))
Ground_Height = Ground_Width * (Image_Height / Image_Width)

# Calculate the area covered on the ground
Footprint_Area = Ground_Width * Ground_Height

# Print the corrected results
print(f"The Field of View (FOV) from the drone is approximately {FOV:.2f} degrees.")
print(f"The image footprint width on the ground is approximately {Ground_Width:.2f} meters.")
print(f"The image footprint height on the ground is approximately {Ground_Height:.2f} meters.")
print(f"The area covered on the ground is approximately {Footprint_Area:.2f} square meters.")
