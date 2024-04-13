#  Copyright (c) 2024.
#  __author__ = "Dean Hand"
#  __license__ = "AGPL"
#  __version__ = "1.0"

import math
import utm
from pyproj import Transformer, CRS, Geod
import Utils.config as config
from Utils.logger_config import *


def decimal_degrees_to_utm(latitude, longitude):
    """
    Convert latitude and longitude in decimal degrees to UTM coordinates.

    Parameters:
    - latitude (float): Latitude in decimal degrees.
    - longitude (float): Longitude in decimal degrees.

    Returns:
    tuple: Easting, northing, zone number, and hemisphere of the UTM coordinates.
    """
    utm_zone = int((longitude + 180) / 6) + 1
    hemisphere = "north" if latitude >= 0 else "south"
    easting, northing, zone_number, zone_letter = utm.from_latlon(latitude, longitude)
    return easting, northing, zone_number, hemisphere


def longitude_to_utm_zone(longitude):
    return int((longitude + 180) / 6) + 1


def gps_to_utm(latitude, longitude):
    zone_number = longitude_to_utm_zone(longitude)
    hemisphere = "north" if latitude >= 0 else "south"
    is_southern = latitude < 0
    utm_crs = CRS(proj="utm", zone=zone_number, ellps="WGS84", datum="WGS84", south=is_southern)
    wgs84_crs = CRS(proj="latlong", datum="WGS84")
    transformer = Transformer.from_crs(wgs84_crs, utm_crs, always_xy=True)
    x, y = transformer.transform(longitude, latitude)  # Corrected order
    return float(x), float(y), zone_number, hemisphere


def get_utm_transformer(latitude, longitude):
    zone_number = longitude_to_utm_zone(longitude)
    is_southern = latitude < 0
    utm_crs = CRS(proj="utm", zone=zone_number, ellps="WGS84", datum="WGS84", south=is_southern)
    wgs84_crs = CRS(proj="latlong", datum="WGS84")
    transformer = Transformer.from_crs(wgs84_crs, utm_crs, always_xy=True)
    return transformer


def find_epsg_code(utm_x, utm_y):
    """
    Determine the EPSG code for UTM coordinates based on longitude.

    Parameters:
    - utm_x (float): UTM easting.
    - utm_y (float): UTM northing.

    Returns:
    str: EPSG code for the UTM coordinates.
    """
    utm_band = str((math.floor((utm_y + 180) / 6) % 60) + 1)
    utm_band = utm_band.zfill(2)
    epsg_code = "326" + utm_band if utm_x >= 0 else "327" + utm_band
    return epsg_code


def utm_to_latlon(easting, northing, zone_number, hemi):
    """
    Convert UTM coordinates to latitude and longitude.

    Parameters:
    - easting (float): UTM easting.
    - northing (float): UTM northing.
    - zone_number (int): UTM zone number.
    - hemisphere (str): Hemisphere indicator ('N' for north, 'S' for south).

    Returns:
    tuple: Latitude and longitude in decimal degrees.
    """
    lat, lon = utm.to_latlon(float(easting), float(northing), zone_number, hemi)
    return lat, lon


def hemisphere_flag(latitude):
    """
    Determine the hemisphere ('N' or 'S') based on latitude.

    Parameters:
    - latitude (float): Latitude in decimal degrees.

    Returns:
    str: 'N' for northern hemisphere or 'S' for southern hemisphere.
    """
    return "N" if latitude >= 0 else "S"


def is_gimbal_pitch_in_range(gimbal_pitch_degree):
    """
    Check if the gimbal pitch degree is within a specific range.

    Parameters:
    - gimbal_pitch_degree (float): The pitch degree of the gimbal.

    Returns:
    bool: True if within range (-91 to -89 degrees), False otherwise.
    """
    return -91 <= gimbal_pitch_degree <= -89


def proj_stuff(center_latitude, zone_number):
    """
    Initialize a Transformer object for transforming coordinates from UTM to WGS84.

    Parameters:
    - center_latitude (float): Latitude used to determine the southern hemisphere.
    - zone_number (int): UTM zone number.

    Returns:
    Transformer: A transformer object for coordinate conversion.
    """
    is_southern = center_latitude < 0

    try:
        utm_crs = CRS(proj="utm", zone=zone_number, ellps="WGS84", datum="WGS84", south=is_southern)
        wgs84_crs = CRS(proj="latlong", datum="WGS84")
        transformer = Transformer.from_crs(utm_crs, wgs84_crs, always_xy=True)
    except Exception as e:
        logger.opt(exception=True).warning(f"Error initializing transformer: {e}")
    return transformer


def proj_stuff2(zone_number, hemisphere):
    """
    Initialize a Transformer object for UTM to Web Mercator projection conversion.

    Parameters:
    - zone_number (int): UTM zone number.
    - hemisphere (str): Hemisphere indicator ('N' or 'S').

    Returns:
    Transformer: A transformer object for projection conversion.
    """
    south_flag = "+south" if hemisphere == "S" else ""
    proj_utm = f"+proj=utm +zone={zone_number} {south_flag} +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
    transformer = Transformer.from_proj(proj_utm, "epsg:3857", always_xy=True)
    return transformer


def calculate_geographic_offset(latitude, longitude, distance_meters, bearing_degrees):
    """
    Calculate the geographic offset from a point given distance and bearing.

    Parameters:
    - latitude (float): Starting latitude.
    - longitude (float): Starting longitude.
    - distance_meters (float): Distance to offset in meters.
    - bearing_degrees (float): Bearing in degrees from north.

    Returns:
    tuple: Latitude and longitude coordinates after the offset.
    """
    try:
        geod = Geod(ellps="WGS84")
        new_longitude, new_latitude, _ = geod.fwd(longitude, latitude, bearing_degrees, distance_meters)
    except Exception as e:
        logger.opt(exception=True).warning(f"Error calculating geographic offset: {e}")
    return new_latitude, new_longitude


def translate_to_wgs84(bbox, drone_lon, drone_lat):
    """
    Translates a bounding box to geographic coordinates based on the drone's location.

    Parameters:
    - bbox (list): List of bounding box coordinates in UTM.
    - drone_lon (float): Drone's longitude in decimal degrees.
    - drone_lat (float): Drone's latitude in decimal degrees.

    Returns:
    List of tuples containing translated bounding box points in geographic coordinates.
    """
    # Determine UTM zone and hemisphere from drone's coordinates
    crs_geo_outDD = "epsg:4326"
    crs_geo_out = f"epsg:{config.epsg_code}"
    # crs_utm = f"+proj=utm +zone={utm_zone} +{hemisphere} +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
    # utm_crs_code = find_epsg_code(bbox[0][0], bbox[0][1])
    utm_zone = int((drone_lon + 180) / 6) + 1
    hemisphere = "north" if drone_lat >= 0 else "south"
    crs_geo_outDD = "epsg:4326"
    # crs_geo_out = config.epsg_code
    crs_utm = f"+proj=utm +zone={utm_zone} +{hemisphere} +ellps=WGS84 +datum=WGS84 +units=m +no_defs"

    # Initialize transformers for coordinate conversion
    # transformer_to_utm = Transformer.from_crs(crs_geo_in, crs_utm, always_xy=True)
    transformer_to_geo = Transformer.from_crs(crs_utm, crs_geo_out, always_xy=True)
    transformer_to_decdree = Transformer.from_crs(crs_utm, crs_geo_outDD, always_xy=True)

    # Convert drone's location to UTM coordinates
    # drone_easting, drone_northing = transformer_to_utm.transform(drone_lon, drone_lat)
    translated_bbox = []
    polybox = []
    for point in bbox:
        # Unpack the point tuple into x and y
        x, y = point
        # Translate bounding box points
        # point_easting, point_northing = drone_easting + x, drone_northing + y

        # Convert points back to geographic coordinates
        point_lat, point_lon = transformer_to_geo.transform(x, y)
        dd_lat, dd_lon = transformer_to_decdree.transform(x, y)
        # print("\nEPSG code:", config.epsg_code)
        # print("UTM CRS:", crs_utm)
        # print("Input UTM coordinates:", point_lon, point_lat)
        # print("Output geographic coordinates:", point_lon, point_lat)
        # exit()
        translated_bbox.append((point_lat, point_lon))
        polybox.append((dd_lat, dd_lon))
    return translated_bbox, polybox


def translate_points_to_utm(bbox, drone_lon, drone_lat):
    """
    Translates a bounding box to geographic coordinates based on the drone's location.

    Parameters:
    - bbox (list): List of bounding box coordinates in UTM.
    - drone_lon (float): Drone's longitude in decimal degrees.
    - drone_lat (float): Drone's latitude in decimal degrees.

    Returns:
    List of tuples containing translated bounding box points in geographic coordinates.
    """
    # Determine UTM zone and hemisphere from drone's coordinates
    utm_zone = int((drone_lon + 180) / 6) + 1
    hemisphere = "north" if drone_lat >= 0 else "south"
    crs_geo = "epsg:4326"
    # crs_geo_out = config.epsg_code
    crs_utm = f"+proj=utm +zone={utm_zone} +{hemisphere} +ellps=WGS84 +datum=WGS84 +units=m +no_defs"

    # Initialize transformers for coordinate conversion
    transformer_to_utm = Transformer.from_crs(crs_geo, crs_utm, always_xy=True)

    # Convert drone's location to UTM coordinates
    drone_easting, drone_northing = transformer_to_utm.transform(drone_lon, drone_lat)

    translated_bbox = []
    for point in bbox:
        # Translate bounding box points based on drone's UTM coordinates
        point_easting, point_northing = drone_easting + point[0], drone_northing + point[1]
        translated_bbox.append((point_easting, point_northing))

    return translated_bbox


def geographic_to_utm(lon, lat):
    # print(lon, lat)
    utm_zone = int((lon + 180) / 6) + 1
    # print(utm_zone)
    hemisphere = "north" if lat >= 0 else "south"
    hemisphere_prefix = 326 if lat >= 0 else 327
    epsg_code = int(f"{hemisphere_prefix}{utm_zone}")
    # print(epsg_code)
    crs_utm = CRS.from_epsg(epsg_code)
    transformer = Transformer.from_crs(crs_utm, config.epsg_code, always_xy=True)
    easting, northing = transformer.transform(lon, lat)
    return easting, northing, epsg_code, hemisphere


def find_geodetic_intersections(bbox, drone_lon, drone_lat):
    """
    Translates a bounding box to geographic coordinates based on the drone's location.

    Parameters:
    - bbox (list): List of bounding box coordinates in UTM.
    - drone_lon (float): Drone's longitude in decimal degrees.
    - drone_lat (float): Drone's latitude in decimal degrees.

    Returns:
    List of tuples containing translated bounding box points in geographic coordinates.
    """
    # Determine UTM zone and hemisphere from drone's coordinates
    utm_zone = int((drone_lon + 180) / 6) + 1
    hemisphere = "north" if drone_lat >= 0 else "south"
    crs_geo_in = "epsg:4326"
    crs_utm = f"+proj=utm +zone={utm_zone} +{hemisphere} +ellps=WGS84 +datum=WGS84 +units=m +no_defs"

    # Initialize transformers for coordinate conversion
    transformer_to_utm = Transformer.from_crs(crs_geo_in, crs_utm, always_xy=True)
    transformer_to_geo = Transformer.from_crs(crs_utm, config.epsg_code, always_xy=True)

    # Convert drone's location to UTM coordinates
    drone_easting, drone_northing = transformer_to_utm.transform(drone_lon, drone_lat)

    translated_bbox = []
    for point in bbox:
        # Translate and rotate bounding box points
        point_easting, point_northing = drone_easting + point.x, drone_northing + point.y

        # Convert points back to geographic coordinates
        point_lon, point_lat = transformer_to_geo.transform(point_easting, point_northing)
        translated_bbox.append((point_easting, point_northing))

    return translated_bbox


def translate_to_geo_tgt(intersection, drone_lon, drone_lat):
    # Determine UTM zone and hemisphere from drone's coordinates
    utm_zone = int((drone_lon + 180) / 6) + 1
    hemisphere = "north" if drone_lat >= 0 else "south"
    crs_geo_in = "epsg:4326"
    crs_utm = f"+proj=utm +zone={utm_zone} +{hemisphere} +ellps=WGS84 +datum=WGS84 +units=m +no_defs"

    # Initialize transformers for coordinate conversion
    transformer_to_utm = Transformer.from_crs(crs_geo_in, crs_utm, always_xy=True)
    transformer_to_geo = Transformer.from_crs(crs_utm, crs_geo_in, always_xy=True)

    # Convert drone's location to UTM coordinates
    drone_easting, drone_northing = transformer_to_utm.transform(drone_lon, drone_lat)

    # Translate and rotate intersection point
    point_easting, point_northing = drone_easting + intersection.x, drone_northing + intersection.y

    # Convert points back to geographic coordinates
    lon, lat = transformer_to_geo.transform(point_easting, point_northing)
    return lat, lon
