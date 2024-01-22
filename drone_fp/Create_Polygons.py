from progress.bar import Bar
import geojson
from geojson_rewind import rewind
from Footprint_Calculator import DroneFootprintCalculator
import utm
import json
import math
from Color_Class import Color
from shapely.geometry import Polygon


def image_poly(imgar, sensorWidth, sensorHeight):
    print(Color.CYAN + "\nPlotting Imagery Footprints" + Color.END)
    polys = []
    over_poly = []
    bar = Bar('Plotting Image Bounds', max=len(imgar))
    for cent in iter(imgar):
        drone_longitude = cent['coords'][0]
        drone_latitude = cent['coords'][1]
        prps = cent['props']
        zone, hemisphere, easting, northing = decimal_degrees_to_utm(drone_latitude, drone_longitude)
        utm_zone = int(zone)
        is_northern_hemisphere = True
        calculator = DroneFootprintCalculator(utm_zone, is_northern_hemisphere)
        file_name = prps['File_Name']
        GimbalRollDegree = prps['GimbalRollDegree']
        GimbalPitchDegree = prps['GimbalPitchDegree']
        GimbalYawDegree = prps['GimbalYawDegree']
        Focal_Length = prps['Focal_Length']
        Relative_Altitude = prps["RelativeAltitude"]
        if all(v is not None for v in [sensorWidth, sensorHeight]):
            sensor_width = float(sensorWidth)
            sensor_height = float(sensorHeight)
        else:
            sensor_width = 13.2
            sensor_height = 8.8
        poly = calculator.calculate_footprint(
            Focal_Length, Relative_Altitude, GimbalRollDegree, GimbalYawDegree, GimbalPitchDegree,
            drone_longitude, drone_latitude, sensor_width, sensor_height)
        g2 = Polygon(poly)
        wow3 = geojson.dumps(g2)
        wow4 = json.loads(wow3)
        wow5 = rewind(wow4)
        gd_feat = dict(type="Feature", geometry=wow5, properties=prps)
        polys.append(gd_feat)
        polyArray = dict(file_name=file_name, polygon=g2)
        over_poly.append(polyArray)
        bar.next()
    pop3 = geojson.dumps(polys)
    pop4 = json.loads(pop3)
    bar.finish()
    print(Color.CYAN + "All Imagery Footprints Plotted" + Color.END)
    return pop4, over_poly


def getFOV(sensor_width, sensor_height, Focal_Length):
    # Assuming sensor_width, sensor_height, and Focal_Length can be negative or positive (e.g., millimeters)
    sensor_width = abs(sensor_width)
    sensor_height = abs(sensor_height)
    Focal_Length = abs(Focal_Length)

    # Calculate FOV using absolute values

    FOV_horizontal_abs = 2 * math.degrees(
        math.atan(sensor_width / (2 * Focal_Length)))  # Absolute Field of View - Width
    FOV_vertical_abs = 2 * math.degrees(
        math.atan(sensor_height / (2 * Focal_Length)))  # Absolute Field of View - Height

    return FOV_vertical_abs, FOV_horizontal_abs


def decimal_degrees_to_utm(latitude, longitude):
    # Convert decimal degrees to UTM coordinates
    utm_coords = utm.from_latlon(latitude, longitude)
    zone = utm_coords[2]
    hemisphere = utm_coords[3]
    easting = utm_coords[0]
    northing = utm_coords[1]

    return zone, hemisphere, easting, northing


def convert_wgs_to_utm(poly):
    latlon_coords = []
    for utm_point_array in poly:
        utm_x_str, utm_y_str = utm_point_array
        utm_band = str((math.floor((utm_y_str + 180) / 6) % 60) + 1)
        if len(utm_band) == 1:
            utm_band = '0'+utm_band
        if utm_x_str >= 0:
            epsg_code = '326' + utm_band
        else:
            epsg_code = '327' + utm_band
        return epsg_code


def utm_polygon_to_latlon(utm_coords_strings, utm_zone, utm_nth):
    print(utm_coords_strings, utm_zone, utm_nth)
    latlon_coords = []
    for utm_point_array in utm_coords_strings:
        utm_x_str, utm_y_str = utm_point_array
        utm_x = utm_x_str
        utm_y = utm_y_str
        lat, lon = utm.to_latlon(utm_x, utm_y, utm_zone, utm_nth)
        latlon_coords.append((lon, lat))

    return latlon_coords


def convert_utm_to_decimal(z, a, b):
    lat, lng = utm.to_latlon(z[0], z[1], a, b)
    return lng, lat  # Swap longitude and latitude here
