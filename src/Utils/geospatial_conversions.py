#  Copyright (c) 2024.
#  __author__ = "Dean Hand"
#  __license__ = "AGPL"
#  __version__ = "1.0"

import math
import utm
from pyproj import Transformer, CRS, Geod


def decimal_degrees_to_utm(latitude, longitude):
    """
    Convert latitude and longitude in decimal degrees to UTM coordinates.

    Parameters:
    - latitude (float): Latitude in decimal degrees.
    - longitude (float): Longitude in decimal degrees.

    Returns:
    tuple: Easting, northing, zone number, and hemisphere of the UTM coordinates.
    """
    easting, northing, zone, hemisphere = utm.from_latlon(latitude, longitude)
    return easting, northing, zone, hemisphere


def convert_wgs_to_utm(utm_x, utm_y):
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


def utm_to_latlon(easting, northing, zone_number, hemisphere):
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
    lat, lon = utm.to_latlon(easting, northing, zone_number, hemisphere)
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
    utm_crs = CRS(proj="utm", zone=zone_number, ellps="WGS84", datum="WGS84", south=is_southern)
    wgs84_crs = CRS(proj="latlong", datum="WGS84")
    transformer = Transformer.from_crs(utm_crs, wgs84_crs, always_xy=True)
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
    geod = Geod(ellps="WGS84")
    new_longitude, new_latitude, _ = geod.fwd(longitude, latitude, bearing_degrees, distance_meters)
    return new_latitude, new_longitude
