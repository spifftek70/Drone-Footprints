#  Copyright (c) 2024
#  Author: Dean Hand
#  License: AGPL
#  Version: 1.0
import os
import sys
from contextlib import contextmanager
import rasterio
from rasterio.transform import from_bounds
from rasterio.enums import ColorInterp
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
import numpy as np
import cv2 as cv
from shapely.wkt import loads
from loguru import logger
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
    Converts an OpenCV image array to a rasterio dataset with geospatial data.

    Parameters:
    - cv2_array: The OpenCV image array to convert.
    - polygon_wkt: Well-Known Text (WKT) representation of the polygon for spatial reference.
    - epsg_code: EPSG code for the spatial reference system (default: 4326 for WGS84).

    Returns:
    - rasterio dataset object with the image and geospatial data.
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

    # Determine rasterio data type based on cv2_array data type
    if cv2_array.dtype == np.uint8:
        dtype = rasterio.uint8
    elif cv2_array.dtype == np.uint16:
        dtype = rasterio.uint16
    elif cv2_array.dtype == np.int32:
        dtype = rasterio.int32
    elif cv2_array.dtype == np.float32:
        dtype = rasterio.float32
    elif cv2_array.dtype == np.float64:
        dtype = rasterio.float64
    else:
        logger.opt(exception=True).warning(f"Unsupported data type: {str(cv2_array.dtype)}")

    # Create and configure the rasterio dataset
    transform = from_bounds(minx, miny, maxx, maxy, width, height)
    crs = rasterio.crs.CRS.from_epsg(config.epsg_code)

    with rasterio.MemoryFile() as memfile:
        with memfile.open(driver='GTiff', height=height, width=width, count=bands, dtype=dtype, crs=crs,
                          transform=transform) as dst:
            if len(cv2_array.shape) == 3:  # For color images
                for i in range(1, bands + 1):
                    dst.write(cv2_array[:, :, i - 1], i)
                    # Set color interpretation for each band if applicable
                    if bands == 3:
                        color_interpretations = [ColorInterp.red, ColorInterp.green, ColorInterp.blue]
                        dst.colorinterp = color_interpretations[:bands]
                    elif bands == 4:
                        color_interpretations = [ColorInterp.red, ColorInterp.green, ColorInterp.blue,
                                                 ColorInterp.alpha]
                        dst.colorinterp = color_interpretations[:bands]
            else:  # For grayscale images
                dst.write(cv2_array, 1)
                color_interpretations = [ColorInterp.gray]
                dst.colorinterp = color_interpretations[:bands]
        return memfile.open()


@contextmanager
def suppress_stdout_stderr():
    """A context manager that redirects stdout and stderr to devnull"""
    with open(os.devnull, 'w') as null:
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = null, null
        try:
            yield
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr

def warp_ds(dst_utf8_path, ds):
    """
    Warps a georeferenced image array into a GeoTIFF file.

    Parameters:
    - dst_utf8_path: Destination path for the output GeoTIFF file.
    - ds: rasterio dataset object to be warped.

    No return value.
    """
    dst_crs = rasterio.crs.CRS.from_epsg(config.epsg_code)

    transform, width, height = calculate_default_transform(
        ds.crs, dst_crs, ds.width, ds.height, *ds.bounds)

    kwargs = ds.meta.copy()
    kwargs.update({
        'crs': dst_crs,
        'transform': transform,
        'width': width,
        'height': height,
        'nodata': 0  # Set nodata value to 0 (transparent)
    })

    with rasterio.open(dst_utf8_path, 'w', **kwargs) as dst:
        for i in range(1, ds.count + 1):
            reproject(
                source=rasterio.band(ds, i),
                destination=rasterio.band(dst, i),
                src_transform=ds.transform,
                src_crs=ds.crs,
                dst_transform=transform,
                dst_crs=dst_crs,
                resampling=Resampling.nearest)

    if config.cog:
        # Convert the GeoTIFF to a Cloud Optimized GeoTIFF (COG)
        cogeo_profile = 'deflate'
        with suppress_stdout_stderr():
            cog_translate(dst_utf8_path, dst_utf8_path, cog_profiles.get(cogeo_profile), in_memory=True)


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

        # Check if the image is a single band image
        if len(img.getbands()) == 1:
            # Convert the image to 'L' mode if it is not already
            if img.mode != 'L':
                img = img.convert('L')
            # Convert the PIL Image to a numpy array
            img_array = np.array(img)
            # Convert the single band image to a 3 band image using OpenCV
            img_array = cv.cvtColor(img_array, cv.COLOR_GRAY2RGB)
            # Convert the numpy array back to a PIL Image
            img = Image.fromarray(img_array)
        else:
            img = img.convert('RGB')  # Convert image to 'RGB' mode

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