from progress.bar import Bar
import geojson
from geojson_rewind import rewind
import pyproj
from drone_footprint_calculator import DroneFootprintCalculator
import utm
import json
import math
from Color_Class import Color
from shapely.geometry import shape, LineString, Point, Polygon
from shapely.ops import transform
import geopandas as gpd
from shapely import affinity


def image_poly(imgar):
    print(Color.CYAN + "\nPlotting Imagery Footprints" + Color.END)
    polys = []
    over_poly = []
    bar = Bar('Plotting Image Bounds', max=len(imgar))
    # print(imgar)
    # exit()
    for cent in iter(imgar):
        lng = cent['coords'][1]
        lat = cent['coords'][0]
        prps = cent['props']
        zone, hemisphere, easting, northing = decimal_degrees_to_utm(lat, lng)
        utm_zone = int(zone)
        is_northern_hemisphere = True
        calculator = DroneFootprintCalculator(utm_zone, is_northern_hemisphere)
        file_name = prps['File_Name']
        GimbalRollDegree = prps['GimbalRollDegree']
        GimbalPitchDegree = prps['GimbalPitchDegree']
        GimbalYawDegree = prps['GimbalYawDegree']
        # utm_zone_number = zone
        utm_zone_letter = hemisphere
        Image_Width = prps['Image_Width']
        Image_Height = prps['Image_Height']
        # abso_yaw = gimy
        # img_n = prps['File_Name']
        Focal_Length = prps['Focal_Length']
        Relative_Altitude = prps["RelativeAltitude"]
        sensor_width = 13.2
        sensor_height = 8.8
        drone_longitude = cent['coords'][1]
        drone_latitude = cent['coords'][0]
        # print(Focal_Length, " - ", type(Focal_Length), "\n", Image_Width, " - ", type(Image_Width), "\n",Image_Height, " - ", type(Image_Height), "\n",
        #         Relative_Altitude, " - ", type(Relative_Altitude), "\n",GimbalRollDegree, " - ", type(GimbalRollDegree), "\n",
        #         GimbalYawDegree, " - ", type(GimbalYawDegree), "\n",GimbalPitchDegree, " - ", type(GimbalPitchDegree), "\n",
        #         drone_longitude, " - ", type(drone_longitude), "\n",drone_latitude, type(drone_latitude), "\n",
        #         sensor_width, " - ", type(sensor_width), "\n",sensor_height,  type(sensor_height), "\n")
        # exit()
        poly = calculator.calculate_footprint(
            Focal_Length, Image_Width, Image_Height, Relative_Altitude,
            GimbalRollDegree, GimbalYawDegree, GimbalPitchDegree,
            drone_longitude, drone_latitude, sensor_width, sensor_height
        )
        g2 = Polygon(poly)
        # print(geom)
        # exit()
        # print(rectangle_polygon_geometry)
        # exit()
        # g2 = Polygon(lonlat_coords)
        # g3 = affinity.rotate(g2, 180, origin='centroid')
        # ngf = affinity.scale(g2, xfact=-1.0, yfact=-1.0, zfact=-1.0, origin='center')
        # ngfs =affinity.rotate(ngf, GimbalYawDegree - 8, origin='center', use_radians=False)
        # ngfs = affinity.rotate(ngf, 180, origin='centroid', dians=True)  #
        wow3 = geojson.dumps(g2)
        wow4 = json.loads(wow3)
        wow5 = rewind(wow4)
        gd_feat = dict(type="Feature", geometry=wow5, properties=prps)
        # print(gd_feat)
        # exit()
        polys.append(gd_feat)
        polyArray = dict(file_name=file_name, polygon=g2)
        over_poly.append(polyArray)
        bar.next()
    # pop3 = geojson.dumps(over_poly)
    # pop4 = json.loads(pop3)
    bar.finish()
    print(Color.CYAN + "All Imagery Footprints Plotted" + Color.END)
    return polys, over_poly


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
