#  Copyright (c) 2024.
#  __author__ = "Dean Hand"
#  __license__ = "AGPL"
#  __version__ = "1.0"

from Utils.raster_utils import *
from Utils.process_raster import process_rasters

def set_raster_extents(image_path, dst_utf8_path, coordinate_array, properties):
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
    bbox1 = get_bbox(coordinate_array)
    gsd = properties['GSD']
    bbox2 = refine_bbox(bbox1, gsd)
    xmin, ymin, xmax, ymax = bbox2

    # Create a GDAL in-memory dataset
    gdal.DontUseExceptions()
    driver = gdal.GetDriverByName('MEM')
    dataset = driver.Create('', width, height, num_bands, gdal.GDT_Byte)  # Number of bands determined by image format

    # Set geotransform and projection
    pixel_width = (xmax - xmin) / width
    pixel_height = (ymax - ymin) / height
    geotransform = (xmin, pixel_width, 0, ymax, 0, -pixel_height)
    dataset.SetGeoTransform(geotransform)

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)  # WGS84
    dataset.SetProjection(srs.ExportToWkt())
    rasterize_raster(jpeg_img_array, dataset, num_bands)

    rectify_and_warp_to_geotiff(dataset, dst_utf8_path, coordinate_array, bbox2, properties, height, width)


def gdal_dataset_to_numpy_array(dataset):
    """Convert a GDAL dataset to a NumPy array, handling both RGB and RGBA images."""
    bands = [dataset.GetRasterBand(i).ReadAsArray() for i in range(1, dataset.RasterCount + 1)]
    img = np.dstack(bands)  # Stack bands to create an image array
    return img


def rectify_and_warp_to_geotiff(ds1a, dst_utf8_path, coordinate_array, bbox2, properties, org_height, org_width):
    # Convert GDAL dataset to NumPy array, handling both RGB and RGBA
    dsArray = gdal_dataset_to_numpy_array(ds1a)

    # Log the format of the image
    num_channels = dsArray.shape[2]
    height, width = dsArray.shape[:2]

    topocentric_ds = process_rasters(dst_utf8_path, properties)
    # orig_image_bounds = get_bounds(org_height, org_width)
    # new_bounds = get_bounds(width, height)
    #
    # # Transform source to rectified array using homography
    # georef_image_array = rectify(orig_image_bounds, new_bounds, width, height, dsArray)
    #
    # xmin, ymin, xmax, ymax = bbox2
    # geotrans = [xmin, gsd, 0, ymax, 0, -gsd]
    # topocentric_ds = array2ds(georef_image_array, geotrans)
    # # Create an in-memory dataset for the transformed image

    rasterize_raster(dsArray, topocentric_ds, num_channels)

    warp_ds(dst_utf8_path, topocentric_ds, width, height, coordinate_array)
