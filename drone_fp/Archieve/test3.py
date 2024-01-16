import math
import geojson
from geojson_rewind import rewind

def drone_image_footprint(Focal_Length, Image_Width, Image_Height, Relative_Altitude,
                          GimbalRollDegree, GimbalYawDegree, GimbalPitchDegree,
                          drone_longitude, drone_latitude, sensor_width, sensor_height):

  # Calculate IFOV, FOV, resolution
  ifov_x = math.tan(math.radians(GimbalYawDegree)) * (Focal_Length / sensor_width)
  ifov_y = math.tan(math.radians(GimbalPitchDegree)) * (Focal_Length / sensor_height)
  fov_x = ifov_x * Image_Width
  fov_y = ifov_y * Image_Height
  resolution = Focal_Length / Image_Width

  # Convert longitude/latitude to decimal degrees
  drone_longitude = drone_longitude / 10000000
  drone_latitude = drone_latitude / 10000000

  # Calculate footprint polygon vertices
  half_width = fov_x / 2 * Relative_Altitude / 1000 / 111.12
  half_height = fov_y / 2 * Relative_Altitude / 1000 / 111.12

  footprint = {
    "type": "Feature",
    "properties": {},
    "geometry": {
      "type": "Polygon",
      "coordinates": [
        [
          [drone_longitude - half_width, drone_latitude - half_height],
          [drone_longitude - half_width, drone_latitude + half_height],
          [drone_longitude + half_width, drone_latitude + half_height],
          [drone_longitude + half_width, drone_latitude - half_height],
          [drone_longitude - half_width, drone_latitude - half_height]
        ]
      ]
    }
  }
  n1 = geojson.dumps(footprint)
  return n1

  print( n2 )

# Example usage:
Focal_Length = 10.26
Image_Width = 5472
Image_Height = 3648
Relative_Altitude = 402.1
GimbalRollDegree = 0.00
GimbalYawDegree = -3.4
GimbalPitchDegree = -89.9
drone_longitude = -111.8852671
drone_latitude = 33.3671694
sensor_width = 13.2
sensor_height = 8.8

footprint_geojson = drone_image_footprint(Focal_Length, Image_Width, Image_Height, Relative_Altitude, GimbalRollDegree, GimbalYawDegree, GimbalPitchDegree, drone_longitude, drone_latitude, sensor_width, sensor_height)
print(rewind(footprint_geojson))
