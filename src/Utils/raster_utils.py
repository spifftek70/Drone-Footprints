#  Copyright (c) 2024
#  Author: Dean Hand
#  License: AGPL
#  Version: 1.0

from osgeo import gdal, osr
import numpy as np
import cv2 as cv
from shapely.wkt import loads
from Utils.logger_config import *
import Utils.config as config
from skimage.exposure import equalize_adapthist
from PIL import Image, ImageOps
from pathlib import Path
import math


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".tif", ".tiff"}


def warp_image_to_polygon(img_arry, polygon, coordinate_array):
    """
    Warps an image array to fit within a specified polygon using coordinates mapping
    after applying auto-leveling for color, brightness, and contrast adjustments.

    Parameters:
    - img_arry: The image array to be auto-leveled and then warped.
    - polygon: The polygon to which the image should be warped.
    - coordinate_array: Array of coordinates defining the mapping from image to polygon.

    Returns:
    - The auto-leveled and then warped image array.
    """

    if config.image_equalize is True:
        img_arry_equalized = equalize_adapthist(img_arry, clip_limit=0.03)
    else:
        img_arry_equalized = img_arry

    # Continue with warping as before
    src_points = np.float32([
        [0, 0],
        [img_arry_equalized.shape[1], 0],
        [img_arry_equalized.shape[1], img_arry_equalized.shape[0]],
        [0, img_arry_equalized.shape[0]]
    ])

    # Calculate bounds, resolution, and destination points as before

    minx, miny, maxx, maxy = polygon.bounds
    resolution_x = (maxx - minx) / img_arry_equalized.shape[1]
    resolution_y = (maxy - miny) / img_arry_equalized.shape[0]

    dst_points = np.float32([gps_to_pixel(coord, minx, maxy, resolution_x, resolution_y) for coord in coordinate_array])

    # Apply warping to the CLAHE-processed image
    try:
        h_matrix, _ = cv.findHomography(src_points, dst_points, cv.RANSAC, 5)
        georef_image_array = cv.warpPerspective(img_arry_equalized, h_matrix,
                                                (img_arry_equalized.shape[1], img_arry_equalized.shape[0]),
                                                borderMode=cv.BORDER_CONSTANT, borderValue=(0, 0, 0))
    except Exception as e:
        logger.opt(exception=True).warning(f"Error warping image to polygon: {e}")
        return None

    return georef_image_array


def equalize_images(image_array):
    """
    Equalizes the brightness and contrast of an image array.

    Parameters:
    - image_array: The image array to be equalized.

    Returns:
    - The equalized image array.
    """
    # Normalize the image if necessary
    if image_array.dtype == np.float32:  # Assuming the image is in float32 format
        image_array_normalized = image_array / 255
    else:  # Assuming the image is in uint8 format
        image_array_normalized = image_array.astype(np.float32) / 255

    # Apply CLAHE
    image_array_equalized = equalize_adapthist(image_array_normalized) * 255
    if image_array.dtype == np.uint8:
        image_array_equalized = image_array_equalized.astype(np.uint8)

    return image_array_equalized


def gps_to_pixel(gps_coord, x_min, y_max, resolution_x, resolution_y):
    """
    Converts GPS coordinates to pixel coordinates based on image resolution and bounds.

    Parameters:
    - gps_coord: Tuple of GPS coordinates (longitude, latitude).
    - x_min, y_max: Minimum X and maximum Y bounds of the target area.
    - resolution_x, resolution_y: X and Y resolutions of the target image.

    Returns:
    - Tuple of pixel coordinates (x, y).
    """
    lon, lat = gps_coord
    try:
        Px = (lon - x_min) / resolution_x
        Py = (y_max - lat) / resolution_y
    except Exception as e:
        logger.opt(exception=True).warning(f"Error converting GPS to pixel: {e}")
    return int(Px), int(Py)


def array2ds(cv2_array, polygon_wkt):
    """
    Converts an OpenCV image array to a GDAL dataset with geospatial data.

    Parameters:
    - cv2_array: The OpenCV image array to convert.
    - polygon_wkt: Well-Known Text (WKT) representation of the polygon for spatial reference.
    - epsg_code: EPSG code for the spatial reference system (default: 4326 for WGS84).

    Returns:
    - GDAL dataset object with the image and geospatial data.
    """
    # Check input parameters
    if not isinstance(cv2_array, np.ndarray):
        logger.opt(exception=True).warning(f"cv2_array must be a numpy array.")
    if not isinstance(polygon_wkt, str):
        logger.opt(exception=True).warning(f"polygon_wkt must be a string.")
    if not isinstance(config.epsg_code, int):
        logger.opt(exception=True).warning(f"epsg_code must be an integer.")

    polygon = loads(polygon_wkt)
    minx, miny, maxx, maxy = polygon.bounds

    # Image dimensions and bands
    if len(cv2_array.shape) == 3:  # For color images
        height, width, bands = cv2_array.shape
    else:  # For grayscale images
        height, width = cv2_array.shape
        bands = 1

    pixel_size_x = (maxx - minx) / width
    pixel_size_y = (maxy - miny) / height

    # Determine GDAL data type based on cv2_array data type
    gdal.DontUseExceptions()
    if cv2_array.dtype == np.uint8:
        gdal_dtype = gdal.GDT_Byte
    elif cv2_array.dtype == np.int16:
        gdal_dtype = gdal.GDT_Int16
    elif cv2_array.dtype == np.int32:
        gdal_dtype = gdal.GDT_Int32
    elif cv2_array.dtype == np.float32:
        gdal_dtype = gdal.GDT_Float32
    elif cv2_array.dtype == np.float64:
        gdal_dtype = gdal.GDT_Float64
    else:
        logger.opt(exception=True).warning(f"Unsupported data type: {str(cv2_array.dtype)}")
        # print(ValueError("Unsupported data type: " + str(cv2_array.dtype))

    # Create and configure the GDAL dataset
    driver = gdal.GetDriverByName("MEM")
    if config.cog is True:
        gdal.SetConfigOption("COMPRESS_OVERVIEW", "DEFLATE")
    ds = driver.Create("", width, height, bands, gdal_dtype)
    if config.cog is True:
        ds.BuildOverviews("AVERAGE", [2, 4, 8, 16, 32, 64, 128, 256])
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(config.epsg_code)
    ds.SetProjection(srs.ExportToWkt())
    ds.SetGeoTransform((minx, pixel_size_x, 0, maxy, 0, -pixel_size_y))

    # Write image data to the dataset
    if len(cv2_array.shape) == 3:  # For color images
        for i in range(1, bands + 1):
            band = ds.GetRasterBand(i)
            band.WriteArray(cv2_array[:, :, i - 1])
            # Set color interpretation for each band if applicable
            if bands == 3 or bands == 4:
                color_interpretations = [gdal.GCI_RedBand, gdal.GCI_GreenBand, gdal.GCI_BlueBand, gdal.GCI_AlphaBand]
                band.SetColorInterpretation(color_interpretations[i - 1])
    else:  # For grayscale images
        band = ds.GetRasterBand(1)
        band.WriteArray(cv2_array)

    return ds


def warp_ds(dst_utf8_path, ds):
    """
    Warps a georeferenced image array into a GeoTIFF file.

    Parameters:
    - dst_utf8_path: Destination path for the output GeoTIFF file.
    - georef_image_array: The georeferenced image array to be saved.

    No return value.
    """
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(config.epsg_code)

    if config.cog is False:
        translate_options = gdal.TranslateOptions(noData=0)
        vrt_ds = gdal.Translate(dst_utf8_path, ds, format='GTiff', COMPRESS='LZW', outputSRS=srs.ExportToWkt(),
                                options=translate_options)
        # Clean up to release resources
        del vrt_ds, ds
    else:
        warp_options = gdal.WarpOptions(creationOptions=["COPY_SRC_OVERVIEWS=YES", "TILED=YES", "COMPRESS=LZW"])
        vrt_ds = gdal.Translate('', ds, format='VRT', noData=0, outputSRS=srs.ExportToWkt())
        vs = gdal.Warp(dst_utf8_path, vrt_ds, format='GTiff', options=warp_options, dstSRS=srs.ExportToWkt())
        # Clean up to release resources
        del vrt_ds, ds, vs


def calculate_grid(num_images):
    """
    Calculates grid dimensions (rows, columns) for a given number of images.
    Tries to keep the grid as square as possible.
    """
    cols = math.ceil(math.sqrt(num_images))
    rows = math.ceil(num_images / cols)
    return rows, cols


def create_mosaic(directory, output_base_path, mosaic_size=(400, 350), border_size=1, border_color='black'):
    images_paths = [p for p in Path(directory).iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS]
    num_images = len(images_paths)
    if num_images == 0:
        return

    images_per_row = math.ceil(math.sqrt(num_images))
    images_per_column = math.ceil(num_images / images_per_row)

    tile_width = mosaic_size[0] // images_per_row
    tile_height = mosaic_size[1] // images_per_column

    mosaic_image = Image.new('RGB', mosaic_size)
    x_offset, y_offset = 0, 0

    for img_path in images_paths:
        img = Image.open(img_path)
        img = img.convert('RGB')  # Convert image to 'L' mode

        # Always scale based on the tile height to image height ratio
        scale_factor = tile_height / img.height

        new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
        img_resized = img.resize(new_size, Image.Resampling.LANCZOS)

        # Add a border to the image
        img_resized = ImageOps.expand(img_resized, border=border_size, fill=border_color)

        x_pad = (tile_width - img_resized.width) // 2

        mosaic_image.paste(img_resized, (x_offset + x_pad, y_offset))

        x_offset += tile_width
        if x_offset >= mosaic_size[0]:
            x_offset = 0
            y_offset += tile_height

    # Adjusting output path to ensure it points to the correct subdirectory and file
    output_path = Path(output_base_path) / "mosaic.jpg"
    output_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure the mosaic directory exists

    mosaic_image.save(output_path, format='JPEG')