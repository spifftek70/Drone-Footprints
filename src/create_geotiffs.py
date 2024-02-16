#  Copyright (c) 2024.
#  __author__ = "Dean Hand"
#  __license__ = "AGPL"
#  __version__ = "1.0"

from osgeo import gdal


def warp_image_to_gcp(jpg_image_path, new_image_path, coordinate_array):
    # Open the input image
    gdal.DontUseExceptions()
    src_ds = gdal.Open(jpg_image_path)
    if src_ds is None:
        raise FileNotFoundError(f"Unable to open {jpg_image_path}")

    # Define GCPs - The GCPs link pixel coordinates (px, py) to geographic coordinates (x, y).
    # Assuming the order in coordinate_array is [Top Left, Top Right, Bottom Right, Bottom Left]
    gcp_list = [
        gdal.GCP(coordinate_array[0][0], coordinate_array[0][1], 0, 0, 0),  # Top Left
        gdal.GCP(coordinate_array[1][0], coordinate_array[1][1], 0, src_ds.RasterXSize, 0),  # Top Right
        gdal.GCP(coordinate_array[2][0], coordinate_array[2][1], 0, src_ds.RasterXSize, src_ds.RasterYSize),
        # Bottom Right
        gdal.GCP(coordinate_array[3][0], coordinate_array[3][1], 0, 0, src_ds.RasterYSize)  # Bottom Left
    ]

    # Create a memory copy of the src_ds, to assign GCPs to it
    mem_driver = gdal.GetDriverByName('MEM')
    mem_ds = mem_driver.CreateCopy('', src_ds, 0)
    mem_ds.SetGCPs(gcp_list, src_ds.GetProjection())

    # Warp the image using the GCPs
    warp_options = gdal.WarpOptions(format='GTiff', dstSRS='EPSG:4326', dstNodata=255, outputType=gdal.GDT_Byte,
                                    resampleAlg=gdal.GRA_Bilinear,  options=["COPY_SRC_OVERVIEWS=YES", "TILED=YES", "COMPRESS=LZW"])
    warped_ds = gdal.Warp(new_image_path, mem_ds, options=warp_options)

    if warped_ds is None:
        raise Exception("Error warping image.")

    warped_ds = None  # Close the dataset
    mem_ds = None  # Close the in-memory dataset

