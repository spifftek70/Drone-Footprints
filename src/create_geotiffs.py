#  Copyright (c) 2024.
#  __author__ = "Dean Hand"
#  __license__ = "AGPL"
#  __version__ = "1.0"

import numpy as np
from osgeo import gdal, osr
from PIL import Image


def set_raster_extents(image_path, dst_utf8_path, coordinate_array):
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

    height, width = jpeg_img_array.shape[:2]

    # Calculate bounding box from coordinate_array
    min_x = min(coordinate[0] for coordinate in coordinate_array)
    max_x = max(coordinate[0] for coordinate in coordinate_array)
    min_y = min(coordinate[1] for coordinate in coordinate_array)
    max_y = max(coordinate[1] for coordinate in coordinate_array)

    # Create a GDAL in-memory dataset
    gdal.DontUseExceptions()
    driver = gdal.GetDriverByName('MEM')
    dataset = driver.Create('', width, height, num_bands, gdal.GDT_Byte)  # Number of bands determined by image format

    # Set geotransform and projection
    pixel_width = (max_x - min_x) / width
    pixel_height = (max_y - min_y) / height
    geotransform = (min_x, pixel_width, 0, max_y, 0, -pixel_height)
    dataset.SetGeoTransform(geotransform)

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)  # WGS84
    dataset.SetProjection(srs.ExportToWkt())

    # Write image data to dataset bands
    for i in range(num_bands):
        band = dataset.GetRasterBand(i + 1)
        if num_bands == 3:  # RGB
            band.WriteArray(jpeg_img_array[:, :, i])
        elif num_bands == 4:  # RGBA
            band.WriteArray(jpeg_img_array[:, :, i])
    rectify_and_warp_to_geotiff(dataset, dst_utf8_path, coordinate_array)


def gdal_dataset_to_numpy_array(dataset):
    """Convert a GDAL dataset to a NumPy array, handling both RGB and RGBA images."""
    bands = [dataset.GetRasterBand(i).ReadAsArray() for i in range(1, dataset.RasterCount + 1)]
    img = np.dstack(bands)
    return img


def rectify_and_warp_to_geotiff(ds1a, dst_utf8_path, coordinate_array):
    # Convert GDAL dataset to NumPy array, handling both RGB and RGBA
    img = gdal_dataset_to_numpy_array(ds1a)


    # Log the format of the image
    num_channels = img.shape[2]
    height, width = img.shape[:2]

    # Create an in-memory dataset for the transformed image
    gdal.DontUseExceptions()
    driver = gdal.GetDriverByName('MEM')
    dst_ds = driver.Create('', width, height, num_channels, gdal.GDT_Byte)

    for i in range(num_channels):
        band = dst_ds.GetRasterBand(i + 1)  # Bands are 1-indexed in GDAL
        band.WriteArray(img[:, :, i])
        band.SetNoDataValue(255)  # Optionally set no-data value if applicable
    # Assign GCPs to the dataset with correct geographic coordinates
    gcp_list = [
        gdal.GCP(coordinate_array[0][0], coordinate_array[0][1], 0, 0, 0),
        gdal.GCP(coordinate_array[1][0], coordinate_array[1][1], 0, width, 0),
        gdal.GCP(coordinate_array[2][0], coordinate_array[2][1], 0, width, height),
        gdal.GCP(coordinate_array[3][0], coordinate_array[3][1], 0, 0, height),
    ]

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    dst_ds.SetGCPs(gcp_list, srs.ExportToWkt())

    vrt_ds = gdal.Translate(dst_utf8_path, dst_ds, format='GTiff', GCPs=gcp_list, outputSRS=srs.ExportToWkt())
    warp_options = gdal.WarpOptions(format="GTiff",
                                    dstSRS='EPSG:4326',
                                    dstNodata=0,
                                    outputType=gdal.GDT_Byte,
                                    resampleAlg=gdal.GRA_Bilinear)
    gdal.Warp(dst_utf8_path, vrt_ds, options=warp_options)
