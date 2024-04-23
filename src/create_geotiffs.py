# Copyright (c) 2024.
# Author: Dean Hand
# License: AGPL
# Version: 1.0

from Utils.raster_utils import *
from shapely.geometry import Polygon
import cv2
import Utils.config as config
from loguru import logger
import lensfunpy


def set_raster_extents(image_path, dst_utf8_path, coordinate_array):
    try:
        jpeg_img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        if jpeg_img is None:
            logger.warning(f"File not found: {image_path}")
            return
        fixed_polygon = Polygon(coordinate_array)
        if config.lense_correction is True:
            try:
                focal_length = config.drone_properties['FocalLength']
                distance = config.center_distance
                cam_maker = config.drone_properties['CameraMake']
                cam_model = config.drone_properties['SensorModel']
                aperture = config.drone_properties['MaxApertureValue']

                # Load camera and lens from lensfun database
                db = lensfunpy.Database()
                cam = db.find_cameras(cam_maker, cam_model, True)[0]
                lens = db.find_lenses(cam, cam_maker, cam_model, True)[0]

                height, width = jpeg_img.shape[:2]
                mod = lensfunpy.Modifier(lens, cam.crop_factor, width, height)

                # Determine rasterio data type based on cv2_array data type
                if jpeg_img.dtype == np.uint8:
                    pixel_format = np.uint8
                elif jpeg_img.dtype == np.int16:
                    pixel_format = np.int16
                elif jpeg_img.dtype == np.uint16:
                    pixel_format = np.uint16
                elif jpeg_img.dtype == np.int32:
                    pixel_format = np.int32
                elif jpeg_img.dtype == np.float32:
                    pixel_format = np.float32
                elif jpeg_img.dtype == np.float64:
                    pixel_format = np.float64
                else:
                    logger.opt(exception=True).warning(f"Unsupported data type: {str(jpeg_img.dtype)}")

                mod.initialize(focal_length, aperture, distance, pixel_format=pixel_format)

                # Apply geometry distortion correction and obtain distortion maps
                maps = mod.apply_geometry_distortion()
                map_x = maps[:, :, 0]
                map_y = maps[:, :, 1]

                img_undistorted = cv2.remap(jpeg_img, map_x, map_y, interpolation=cv2.INTER_LANCZOS4)
            except IndexError as e:
                config.update_lense(False)
                img_undistorted = np.array(jpeg_img)
                logger.info("Cannot correct lens distortion. Camera properties not found in database.")
                logger.exception(f"Index error: {e} for {image_path}")
        else:
            img_undistorted = np.array(jpeg_img)

        if jpeg_img.ndim == 2:  # Single band image
            adjImg = img_undistorted
        elif jpeg_img.ndim == 3:  # Multiband image
            adjImg = cv2.cvtColor(img_undistorted, cv2.COLOR_BGR2RGB)
        else:
            adjImg = cv2.cvtColor(img_undistorted, cv2.COLOR_BGR2RGBA)

        rectify_and_warp_to_geotiff(adjImg, dst_utf8_path, fixed_polygon, coordinate_array)
    except FileNotFoundError as e:
        logger.exception(f"File not found: {image_path}. {e}")
    except Exception as e:
        logger.exception(f"Error opening or processing image: {e}")


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

    try:
        georef_image_array = warp_image_to_polygon(jpeg_img_array, fixed_polygon, coordinate_array)
        dsArray = array2ds(georef_image_array, polygon_wkt)
    except Exception as e:
        logger.opt(exception=True).warning(f"Error during warping or dataset creation: {e}")

    # Warp the rasterio dataset to the destination path
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
