# Copyright (c) 2024.
# Author: Dean Hand
# License: AGPL
# Version: 1.0

from Utils.raster_utils import *
from Utils.utils import Color
from shapely.geometry import Polygon
from PIL import Image
import numpy as np
import os


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
        jpeg_img = Image.open(image_path)
        jpeg_img_array = np.array(jpeg_img)
    except FileNotFoundError:
        print(Color.RED + f"File not found: {image_path}" + Color.END)
        return
    except Exception as e:
        print(Color.RED + f"Error opening or processing image: {e}" + Color.END)
        return

    # Determine the number of bands based on the image array shape
    if jpeg_img_array.ndim == 3:
        if jpeg_img_array.shape[2] == 3:  # RGB
            num_bands = 3
        elif jpeg_img_array.shape[2] == 4:  # RGBA
            num_bands = 4
        else:
            raise ValueError("Unsupported image format. Image must be RGB or RGBA.")
    else:
        raise ValueError("Unsupported image format. Image must be RGB or RGBA.")

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
    gdal.SetConfigOption('CPL_DEBUG', 'OFF')

    try:
        georef_image_array = warp_image_to_polygon(jpeg_img_array, fixed_polygon, coordinate_array)
        dsArray = array2ds(georef_image_array, polygon_wkt)
    except Exception as e:
        print(Color.RED + f"Error during warping or dataset creation: {e}" + Color.END)
        return

    # Warp the GDAL dataset to the destination path
    try:
        warp_ds(dst_utf8_path, dsArray)
    except Exception as e:
        print(Color.RED + f"Error writing GeoTIFF: {e}" + Color.END)
        return

