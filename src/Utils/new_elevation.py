#  Copyright (c) 2024.
#  __author__ = "Dean Hand"
#  __license__ = "AGPL"
#  __version__ = "1.0"

from rasterio import rasterio
from rasterio.transform import rowcol
from pyproj import Transformer
from scipy.ndimage import map_coordinates
from urllib.request import urlopen
from urllib.error import HTTPError
import json
from loguru import logger
import Utils.config as config


class ElevationAdjuster:
    def __init__(self, elevation_data, crs, affine_transform):
        self.elevation_data = elevation_data
        self.crs = crs  # Store the CRS
        self.affine_transform = affine_transform

    def terrain_adjustment(self, col, row):
        try:
            row_f, col_f = float(row), float(col)
            interpolated_elevation = map_coordinates(self.elevation_data, [[row_f], [col_f]], order=1, mode='nearest')[
                0]
            return interpolated_elevation
        except Exception as e:
            logger.warning(
                f"Error calculating interpolated elevation: {e} for {config.im_file_name}. Switching to Default Altitudes.")
            return config.abso_altitude


def load_elevation_data_and_crs():
    if config.dtm_path is not None:
        with rasterio.open(config.dtm_path) as dsm:
            elevation_data = dsm.read(1)
            crs = dsm.crs  # Get the CRS directly
            affine_transform = dsm.transform  # Get the affine transform
            return elevation_data, crs, affine_transform


def translate_geo_to_utm(drone_longitude, drone_latitude):
    elevation_data, crs, affine_transform = load_elevation_data_and_crs()
    adjuster = ElevationAdjuster(elevation_data, crs, affine_transform)

    # Initialize transformer to convert from geographic coordinates to the CRS of the raster
    transformer = Transformer.from_crs("EPSG:4326", adjuster.crs, always_xy=True)

    # Transform drone coordinates
    utm_x, utm_y = transformer.transform(drone_longitude, drone_latitude)
    adjuster = ElevationAdjuster(elevation_data, crs, affine_transform)
    return utm_x, utm_y, adjuster


def get_altitude_at_point(x, y):
    elevation_data, _, affine_transform = load_elevation_data_and_crs()
    row, col = rowcol(affine_transform, x, y)
    if 0 <= row < elevation_data.shape[0] and 0 <= col < elevation_data.shape[1]:
        elevation = elevation_data[row, col]
        new_altitude = config.abso_altitude - elevation
        return new_altitude
    else:
        logger.warning(
            f"Point ({x}, {y}) is outside the elevation data bounds for file {config.im_file_name}. Switching to default elevation.")
        return None


def get_altitude_from_open(lat, long):
    yy = 0
    try:
        url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{long}"
        response = urlopen(url)
        data = response.read().decode('utf-8')
        elevation = json.loads(data)['results'][0]['elevation']
        new_altitude = config.abso_altitude - elevation
        # print(f"New Altitude: {new_altitude}", "Absolute Altitude: ", config.abso_altitude, "Elevation: ", elevation)
        # exit()
        return new_altitude
    except HTTPError as err:
        logger.warning(
            f"Unable to Connect to OpenElevation for file {config.im_file_name}. Switching to Default Altitudes. Error: {err}")
        yy += 1
        if yy > 20:
            logger.warning("Too many failures. Switching to default elevation.")
            config.update_elevation(False)
        return None
