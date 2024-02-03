#### Created / written by Dean E. Hand (dean.e.hand@me.com).
import math
import utm


def decimal_degrees_to_utm(latitude, longitude):
    # Convert decimal degrees to UTM coordinates
    easting, northing, zone, hemisphere = utm.from_latlon(latitude, longitude)
    return easting, northing, zone, hemisphere


def convert_wgs_to_utm(utm_x_str, utm_y_str):
    utm_band = str((math.floor((utm_y_str + 180) / 6) % 60) + 1)
    if len(utm_band) == 1:
        utm_band = '0'+utm_band
    if utm_x_str >= 0:
        epsg_code = '326' + utm_band
    else:
        epsg_code = '327' + utm_band
    return epsg_code


def utm_to_latlon(utm_x_str, utm_y_str, utm_zone, utm_nth):
    utm_x = utm_x_str
    utm_y = utm_y_str
    lat, lon = utm.to_latlon(utm_x, utm_y, utm_zone, utm_nth)
    return lon, lat


def hemisphere_flag(latitude):
    return 'N' if latitude >= 0 else 'S'