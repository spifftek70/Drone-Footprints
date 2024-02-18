#  Copyright (c) 2024.
#  __author__ = "Dean Hand"
#  __license__ = "AGPL"
#  __version__ = "1.0"

from Utils.raster_utils import *
import os
from shapely.geometry import Polygon
from PIL import Image
import numpy as np
from Utils.raster_utils import warp_image_to_polygon, warp_ds

def set_raster_extents(image_path, dst_utf8_path, coordinate_array):
    fixed_polygon = Polygon(coordinate_array)
    # Open the image and convert it to a NumPy array
    jpeg_img = Image.open(image_path)
    jpeg_img_array = np.array(jpeg_img)

    # Determine the number of bands based on the image array shape
    if jpeg_img_array.ndim == 3 and jpeg_img_array.shape[2] == 3:  # RGB
        num_bands = 3
    elif jpeg_img_array.ndim == 3 and jpeg_img_array.shape[2] == 4:  # RGBA
        num_bands = 4
    else:
        raise ValueError("Unsupported image format. Image must be RGB or RGBA.")
    rectify_and_warp_to_geotiff(jpeg_img_array, dst_utf8_path, fixed_polygon, coordinate_array)


def rectify_and_warp_to_geotiff(jpeg_img_array, dst_utf8_path, fixed_polygon, coordinate_array):
    polygon_wkt = str(fixed_polygon)
    georef_image_array = warp_image_to_polygon(jpeg_img_array, fixed_polygon, coordinate_array)
    # Turn off GDAL warnings
    os.environ['CPL_LOG'] = '/dev/null'
    gdal.SetConfigOption('CPL_DEBUG', 'OFF')
    dsArray = array2ds(georef_image_array, polygon_wkt)

    # gcp_list = create_gcps(coordinate_array, dsArray)
    warp_ds(dst_utf8_path, dsArray)

