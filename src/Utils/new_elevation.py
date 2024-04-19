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
from Utils.logger_config import *
import Utils.config as config
from numpy import random
from time import sleep


ATTEMPS_NUMBERS:int= 10

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
            logger.info(
                f"Error calculating interpolated elevation: {e} for {config.im_file_name}. Switching to Default Altitudes.")
            return config.absolute_altitude


def load_elevation_data_and_crs():
    if config.dtm_path is not None:
        dsm = ''
        crs = ''
        src = ''
        affine_transform = ''
        with rasterio.open(config.dtm_path) as src:
            dsm = src.read(1)
            crs = src.crs  # Get the CRS directly
            affine_transform = src.transform  # Get the affine transform
        return dsm, crs, src, affine_transform


def translate_geo_to_utm(drone_longitude, drone_latitude):
    elevation_data, crs, _, affine_transform = load_elevation_data_and_crs()
    adjuster = ElevationAdjuster(elevation_data, crs, affine_transform)

    # Initialize transformer to convert from geographic coordinates to the CRS of the raster
    transformer = Transformer.from_crs("EPSG:4326", adjuster.crs, always_xy=True)

    # Transform drone coordinates
    utm_x, utm_y = transformer.transform(drone_longitude, drone_latitude)
    adjuster = ElevationAdjuster(elevation_data, crs, affine_transform)
    return utm_x, utm_y, adjuster


def get_altitude_at_point(x, y):
    elevation_data, _, _, affine_transform = load_elevation_data_and_crs()
    row, col = rowcol(affine_transform, x, y)
    if 0 <= row < elevation_data.shape[0] and 0 <= col < elevation_data.shape[1]:
        elevation = elevation_data[row, col]
        return config.absolute_altitude - elevation

    logger.exception(
        f"Point ({x}, {y}) is outside the elevation data bounds for file {config.im_file_name}. Switching to default elevation.")
    return None


def get_altitude_from_open(lat:float, long:float)->float:
    """
        Get GPS terrain altitude from open-elevation.com using input lat and long
        Returns corrected altitude.
    """

    nb_of_failed_connection = 0
    while nb_of_failed_connection < ATTEMPS_NUMBERS:
        try:
            url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{long}"
            with urlopen(url) as response:
                data = response.read().decode('utf-8')
            elevation = json.loads(data)['results'][0]['elevation']
            logger.info(f"Successfull connection to OpenElevation for file{config.im_file_name} with coordinates {lat},{long}")
            return config.absolute_altitude - elevation
        except HTTPError as err:
            logger.warning(f"Connexion error for OpenElevation file:{config.im_file_name} coordinates {lat},{long}. Error: {err}")
            nb_of_failed_connection += 1
            # Sleep random time before next try
            sleep(nb_of_failed_connection)
    logger.info(f"Too many failures for file {config.im_file_name}. Switching to default elevation.")
    config.update_elevation(False)
    return None

def get_altitudes_from_open(latlon_tupples:list[tuple])->list[float]:
    """
        Get GPS terrain altitude from open-elevation.com from a list of latlon tupples [(lat1,lon1),(lat2,lon2),...]
        Returns list of corrected altitude.
    """
    url_coordinates=""
    nb_of_coordinates=0
    #Prepare url values
    for coordinates in latlon_tupples:
        url_coordinates+=f'{coordinates[0]},{coordinates[1]}|'
        nb_of_coordinates+=1
    #remove last |
    url_coordinates=url_coordinates.rstrip('|')


    nb_of_failed_connection = 0
    while nb_of_failed_connection < ATTEMPS_NUMBERS:
        try:
            url = f"https://api.open-elevation.com/api/v1/lookup?locations={url_coordinates}"
            with urlopen(url) as response:
                data = response.read().decode('utf-8')

            logger.info(f"Successfull connection to OpenElevation for file {config.im_file_name} with coordinates {latlon_tupples}")
            # Extract altitude corrections
            alitude_list=[]
            for result in json.loads(data)['results']:
                alitude_list.append(config.absolute_altitude-result['elevation'])
            return alitude_list
        except HTTPError as err:
            logger.warning(f"Unable to Connect to OpenElevation for file {config.im_file_name} with coordinates {latlon_tupples}. Error: {err}")
            nb_of_failed_connection += 1
            # Sleep random time before next try
            sleep(nb_of_failed_connection)

    logger.info(f"Too many failures for file {config.im_file_name}. Switching to default elevation.")
    config.update_elevation(False)
    return None