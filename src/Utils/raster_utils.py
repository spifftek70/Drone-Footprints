#  Copyright (c) 2024
#  Author: Dean Hand
#  License: AGPL
#  Version: 1.0

from osgeo import gdal, ogr, osr
import numpy as np
import cv2 as cv
from shapely.wkt import loads


def gdal_dataset_to_numpy_array(dataset):
    """
    Converts a GDAL dataset to a NumPy array.

    Parameters:
    - dataset: GDAL dataset object to be converted.

    Returns:
    - NumPy array representing the dataset image, with all bands stacked.
    """
    bands = [dataset.GetRasterBand(i).ReadAsArray() for i in range(1, dataset.RasterCount + 1)]
    img = np.dstack(bands)  # Stack bands to create an image array
    return img


def warp_image_to_polygon(img_arry, polygon, coordinate_array):
    """
    Warps an image array to fit within a specified polygon using coordinates mapping.

    Parameters:
    - img_arry: The image array to be warped.
    - polygon: The polygon to which the image should be warped.
    - coordinate_array: Array of coordinates defining the mapping from image to polygon.

    Returns:
    - The image array warped to the polygon.
    """
    # Source points from the original image
    src_points = np.float32([
        [0, 0],
        [img_arry.shape[1], 0],
        [img_arry.shape[1], img_arry.shape[0]],
        [0, img_arry.shape[0]]
    ])

    # Calculate bounds and resolution
    minx, miny, maxx, maxy = polygon.bounds
    resolution_x = (maxx - minx) / img_arry.shape[1]
    resolution_y = (maxy - miny) / img_arry.shape[0]

    # Destination points within the polygon, based on provided coordinates
    dst_points = np.float32([gps_to_pixel(coord, minx, maxy, resolution_x, resolution_y) for coord in coordinate_array])

    # Calculate the homography matrix and apply warping
    h_matrix, _ = cv.findHomography(src_points, dst_points)
    georef_image_array = cv.warpPerspective(img_arry, h_matrix, (img_arry.shape[1], img_arry.shape[0]),
                                            borderMode=cv.BORDER_CONSTANT, borderValue=(0, 0, 0))
    return georef_image_array


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
    Px = (lon - x_min) / resolution_x
    Py = (y_max - lat) / resolution_y
    return int(Px), int(Py)


def array2ds(cv2_array, polygon_wkt, epsg_code=4326):
    """
    Converts an OpenCV image array to a GDAL dataset with geospatial data.

    Parameters:
    - cv2_array: The OpenCV image array to convert.
    - polygon_wkt: Well-Known Text (WKT) representation of the polygon for spatial reference.
    - epsg_code: EPSG code for the spatial reference system (default: 4326 for WGS84).

    Returns:
    - GDAL dataset object with the image and geospatial data.
    """
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

    # Create and configure the GDAL dataset
    gdal.DontUseExceptions()
    driver = gdal.GetDriverByName("MEM")
    ds = driver.Create("", width, height, bands, gdal.GDT_Byte)

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg_code)
    ds.SetProjection(srs.ExportToWkt())
    ds.SetGeoTransform((minx, pixel_size_x, 0, maxy, 0, -pixel_size_y))

    # Write image data to the dataset
    for i in range(1, bands + 1):
        band = ds.GetRasterBand(i)
        band.WriteArray(cv2_array[:, :, i - 1])
        # Set color interpretation for each band if applicable
        if bands == 3 or bands == 4:
            color_interpretations = [gdal.GCI_RedBand, gdal.GCI_GreenBand, gdal.GCI_BlueBand, gdal.GCI_AlphaBand]
            band.SetColorInterpretation(color_interpretations[i - 1])

    return ds


def warp_ds(dst_utf8_path, georef_image_array):
    """
    Warps a georeferenced image array into a GeoTIFF file.

    Parameters:
    - dst_utf8_path: Destination path for the output GeoTIFF file.
    - georef_image_array: The georeferenced image array to be saved.

    No return value.
    """
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    translate_options = gdal.TranslateOptions(noData=0)
    vrt_ds = gdal.Translate(dst_utf8_path, georef_image_array, format='GTiff', outputSRS=srs.ExportToWkt(),
                            options=translate_options)
    # Clean up to release resources
    del vrt_ds, georef_image_array
