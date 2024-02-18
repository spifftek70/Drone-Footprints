#  Copyright (c) 2024.
#  __author__ = "Dean Hand"
#  __license__ = "AGPL"
#  __version__ = "1.0"

from transformations import *
from Utils.raster_utils import *


def process_rasters(src_utf8_path, FOVh, FOVv,
                    width, height):
    dst_points = np.float32([
        [(width - width * FOVh) / 2, (height - height * FOVv) / 2],
        [width - (width - width * FOVh) / 2, (height - height * FOVv) / 2],
        [width - (width - width * FOVh) / 2, height - (height - height * FOVv) / 2],
        [(width - width * FOVh) / 2, height - (height - height * FOVv) / 2]
    ])

    # Transform source to rectified array using homography
    georef_image_array = rectify(orig_image_bounds,
                                georef_image_verts,
                                georef_rows,
                                georef_cols,
                                src_utf8_path)

    # Get a GeoTIFF driver dataset stored in memory with the rectified image
    topocentric_ds = array2ds(georef_image_array,
                              geotrans)

    return topocentric_ds
