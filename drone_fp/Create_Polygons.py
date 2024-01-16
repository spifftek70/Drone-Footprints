from progress.bar import Bar
import geojson
from shapely import affinity
import shapely.wkt
import shapely.geometry
from shapely.geometry import shape, LineString, Point, Polygon, mapping
from Calculate_Footprints import calculate_drone_imagery_footprint_corners
import utm
import json
import math


def image_poly(imgar):
    """
    :param imgar:
    :return:
    """
    polys = []
    over_poly = []
    bar = Bar('Plotting Image Bounds', max=len(imgar))
    for cent in iter(imgar):
        lat = cent['coords'][1]
        lng = cent['coords'][0]
        # print("**Drones Lng, Lats**", lng, lat)
        prps = cent['props']
        fimr= float(prps['FlightRollDegree'])
        fimp = float(prps['FlightPitchDegree'])
        fimy = float(prps['FlightYawDegree'])
        gimr = float(prps['GimbalRollDegree'])
        gimp = int(prps['GimbalPitchDegree'])
        gimy = float(prps['GimbalYawDegree'])
        wid = float(prps['Image_Width'])
        hite = float(prps['Image_Height'])
        abso_yaw = ((gimy + fimy) / 2) + 180
        print("\n\n Dang yaws\n ", abso_yaw, fimy, gimy)
        img_n = prps['File_Name']
        focal_lgth = float(prps['Focal_Length'])
        r_alt = float(prps["RelativeAltitude"])
        a_alt = float(prps["AbsoluteAltitude"])
        zone, hemisphere, easting, northing = decimal_degrees_to_utm(lat, lng)
        sensor_width = 13.2
        sensor_height = 8.8
        poly = calculate_drone_imagery_footprint_corners(focal_lgth, wid, hite, r_alt, fimr,
                                                         fimy, fimp, gimr, gimy, gimp, zone, hemisphere,
                                                         lat, lng, easting, northing, sensor_width, sensor_height)
        ltlgpy = utm_polygon_to_latlon(poly, zone, hemisphere)
        g2 = Polygon(ltlgpy)
        # Change Heading / orientation
        head_ck = 0
        if abso_yaw > head_ck:
            header = 360 - abso_yaw
        else:
            header = 360 - abso_yaw
        ngf = affinity.rotate(g2, header, origin='centroid')
        g3 = ngf.reverse().wkt
        g4 = shapely.wkt.loads(g3)
        wow3 = geojson.dumps(g4)
        wow4 = json.loads(wow3)
        gd_feat = dict(type="Feature", geometry=wow4, properties=prps)
        print(lat, lng, "\n", gd_feat)
        polys.append(gd_feat)
        bar.next()
    pop3 = geojson.dumps(over_poly)
    pop4 = json.loads(pop3)
    bar.finish()
    return polys, pop4


def decimal_degrees_to_utm(latitude, longitude):
    # Convert decimal degrees to UTM coordinates
    utm_coords = utm.from_latlon(latitude, longitude)
    zone = utm_coords[2]
    hemisphere = utm_coords[3]
    easting = utm_coords[0]
    northing = utm_coords[1]

    return zone, hemisphere, easting, northing


def convert_wgs_to_utm(poly, zone, hemisphere):
    """
    :param lon:
    :param lat:
    :return:
    """
    latlon_coords = []
    for utm_point_array in poly:
        print(" 1", utm_point_array)
        utm_x_str, utm_y_str = utm_point_array
        # print(utm_x, utm_y, utm_zone, utm_nth)
        # exit()
        utm_band = str((math.floor((utm_y_str + 180) / 6) % 60) + 1)
        if len(utm_band) == 1:
            utm_band = '0'+utm_band
        if utm_x_str >= 0:
            epsg_code = '326' + utm_band
        else:
            epsg_code = '327' + utm_band
        return epsg_code


def utm_polygon_to_latlon(utm_coords_strings, utm_zone, utm_nth):
    """
    Convert a list of UTM coordinates in string format to decimal degree latitude and longitude coordinates.

    Args:
    utm_coords_strings (list): A list of UTM coordinates as strings.
    utm_zone (int): The UTM zone of the UTM coordinates.
    utm_nth (str): UTM hemisphere (N or S).

    Returns:
    Polygon: A Shapely Polygon in decimal degree latitude and longitude coordinates.
    """
    latlon_coords = []
    for utm_point_array in utm_coords_strings:
        print(" 1", utm_point_array)
        utm_x_str, utm_y_str = utm_point_array
        utm_x = utm_x_str
        utm_y = utm_y_str
        lat, lon = utm.to_latlon(utm_x, utm_y, utm_zone, utm_nth)
        latlon_coords.append((lon, lat))

    return latlon_coords


def convert_utm_to_decimal(z, y, a, b):
    print("easting: ", type(z))
    print("northing: ", type(y))
    print("a: ", type(a))
    print("b: ", type(b))
    lat, lng = utm.to_latlon(z, y, a, b)
    return lng, lat  # Swap longitude and latitude here
