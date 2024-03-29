from urllib.request import urlopen
from urllib.error import HTTPError
import json
import numpy as np
from osgeo import gdal, osr
from pyproj import Transformer
from loguru import logger
import Utils.config as config

yy = 0
dsm_prime = None

def dtm_function(coords, im_file_name, i):
    i = i[0]
    try:
        global yy
        global dsm_prime
        gdal.DontUseExceptions()
        if i == 0:
            dsm_file = gdal.Open(config.dtm_path)
            dsm_prime = dsm_file
        if i >= 1:
            dsm_file = dsm_prime
        dsm_epsg = get_epsg(dsm_file)
        if dsm_epsg is None:
            config.update_dtm("")
            logger.opt(exception=True).warning(f"Failed to get EPSG code from {config.dtm_path}. Using default elevation")
            return 0.0

        elevation_array = np.array(dsm_file.GetRasterBand(1).ReadAsArray())
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:" + str(dsm_epsg), always_xy=True)

        # Transform the coordinates
        lon, lat = coords
        x, y = transformer.transform(lon, lat)

        transform = dsm_file.GetGeoTransform()
        # Get the raster's extent
        min_x = transform[0]
        max_y = transform[3]
        max_x = min_x + transform[1] * dsm_file.RasterXSize
        min_y = max_y + transform[5] * dsm_file.RasterYSize
        # Check if the coordinates are within the extent
        if not (min_x <= x <= max_x and min_y <= y <= max_y):
            logger.opt(exception=True).warning(
                f"Coordinates ({x}, {y}) are outside of the DSM's extent provided for image {im_file_name}. Using default elevation")
            yy += 1
            if yy >= 10:
                logger.info("too many DSM failures.  Switching to default elevation model")
                config.update_dtm("")
            return 0.0
        else:
        # Use the transformed coordinates to calculate the row and col indices
            col = int((x - transform[0]) / transform[1])
            row = int((y - transform[3]) / transform[5])
        # Check if the row and col indices are within the array's extent
        if not (0 <= row < elevation_array.shape[0] and 0 <= col < elevation_array.shape[1]):
            logger.opt(exception=True).warning(
                f"Coordinates ({x}, {y}) are outside of the DSM's extent provided for image {im_file_name}. Using default elevation")
            return 0.0
        else:
            elevation = elevation_array[row][col]
    except IndexError as irr:
        raise IndexError(f"Index Error: Point out of range/ {irr} for {im_file_name}. Switching to Default Altitudes.")
    except ValueError as ve:
        raise ValueError(f"Value Error in {im_file_name}. Switching to Default Altitudes.")
    return elevation


def get_elevation(lat, long):
    try:
        url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{long}"
        response = urlopen(url)
        data = response.read().decode('utf-8')
        rtn = json.loads(data)['results'][0]['elevation']
        return rtn
    except HTTPError as err:
        config.update_elevation(False)
        logger.opt(exception=True).warning(f"Unable to Connect to OpenElevation. Switching to Default Altitudes. Error: {err}")
        return 0.0


def get_epsg(raster):
    try:
        if raster is None:
            return
        projection = osr.SpatialReference(wkt=raster.GetProjection())
        return projection.GetAttrValue('AUTHORITY', 1)
    except Exception as e:
        logger.opt(exception=True).warning(f"Error getting EPSG code")
