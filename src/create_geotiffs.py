# Copyright (c) 2024.
# Author: Dean Hand
# License: AGPL
# Version: 1.0

from Utils.raster_utils import *
from shapely.geometry import Polygon
import os
import cv2
from Utils.geospatial_conversions import *
from loguru import logger


def set_raster_extents(image_path, dst_utf8_path, coordinate_array):
    """
    Sets the raster extents of an image by warping it to a specified polygon defined by coordinates.

    Parameters:
    - image_path: Path to the source image.
    - dst_utf8_path: Destination path for the output GeoTIFF image.
    - coordinate_array: Array of coordinates defining the target polygon.
    """
    # Create a Polygon object from the coordinate array
    fixed_polygon = Polygon(coordinate_array)

    # Open the image and convert it to a NumPy array
    try:
        jpeg_img = cv2.imread(image_path)
        if jpeg_img.ndim == 2:  # Single band image
            jpeg_img_array = cv2.cvtColor(jpeg_img, cv2.COLOR_BGR2GRAY)
        elif jpeg_img.ndim == 3:  # Multiband image
            jpeg_img_array = cv2.cvtColor(jpeg_img, cv2.COLOR_BGR2RGB)
        else:
            jpeg_img_array = cv2.cvtColor(jpeg_img, cv2.COLOR_BGR2RGBA)
    except FileNotFoundError:
        logger.opt(exception=True).warning("File not found: {image_path}")
    except Exception as e:
        logger.opt(exception=True).warning(f"Error opening or processing image: {e}")

    # Determine the number of bands based on the image array shape
    if jpeg_img_array.ndim == 2:
        num_bands = 1  # Single band image
    elif jpeg_img_array.ndim == 3:
        num_bands = jpeg_img_array.shape[2]  # Multiband image
    else:
        logger.critical(f"Error: Unexpected image array shape: {jpeg_img_array.shape}")
    rectify_and_warp_to_geotiff(jpeg_img_array, dst_utf8_path, fixed_polygon, coordinate_array)


def rectify_and_warp_to_geotiff(jpeg_img_array, dst_utf8_path, fixed_polygon, coordinate_array):
    """
    Warps and rectifies a JPEG image array to a GeoTIFF format based on a fixed polygon and coordinate array.

    Parameters:
    - jpeg_img_array: The NumPy array of the JPEG image.
    - dst_utf8_path: Destination path for the output GeoTIFF image.
    - fixed_polygon: The shapely Polygon object defining the target area.
    - coordinate_array: Array of coordinates used for warping the image.
    """
    # Convert the Polygon to WKT format
    polygon_wkt = str(fixed_polygon)

    # Warp the image to the polygon using the coordinate array
    # Turn off GDAL warnings
    os.environ['CPL_LOG'] = '/dev/null'
    os.environ['GDAL_DATA'] = os.getenv('GDAL_DATA', '/usr/share/gdal')
    gdal.DontUseExceptions()
    gdal.SetConfigOption('CPL_DEBUG', 'OFF')

    try:
        georef_image_array = warp_image_to_polygon(jpeg_img_array, fixed_polygon, coordinate_array)
        dsArray = array2ds(georef_image_array, polygon_wkt)
    except Exception as e:
        logger.opt(exception=True).warning(f"Error during warping or dataset creation: {e}")

    # Warp the GDAL dataset to the destination path
    try:
        warp_ds(dst_utf8_path, dsArray)
    except Exception as e:
        logger.opt(exception=True).warning(f"Error writing GeoTIFF: {e}")


def generate_geotiff(image_path, geotiff_file, coord_array):
    """
    Generate a GeoTIFF file for a single image.

    Args:
        image_path (str): The path to the original image file.
        geotiff_file (Path): The path where the GeoTIFF should be saved.
        coord_array (list): A list of coordinate pairs defining the image's footprint.
    """
    try:
        set_raster_extents(image_path, geotiff_file, coord_array)
    except ValueError as e:
        logger.opt(exception=True).warning(str(e))
