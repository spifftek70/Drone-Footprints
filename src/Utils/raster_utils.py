#  Copyright (c) 2024.
#  __author__ = "Dean Hand"
#  __license__ = "AGPL"
#  __version__ = "1.0"


from osgeo import gdal, ogr, osr
import numpy as np
import cv2 as cv
from shapely.wkt import loads
import pandas as pd


def gdal_dataset_to_numpy_array(dataset):
    bands = [dataset.GetRasterBand(i).ReadAsArray() for i in range(1, dataset.RasterCount + 1)]
    img = np.dstack(bands)  # Stack bands to create an image array
    return img


def warp_image_to_polygon(img_arry, polygon, coordinate_array):
    src_points = np.float32([
        [0, 0],
        [img_arry.shape[1], 0],
        [img_arry.shape[1], img_arry.shape[0]],
        [0, img_arry.shape[0]]
    ])
    width, height = img_arry.shape[1], img_arry.shape[0]
    minx, miny, maxx, maxy = polygon.bounds

    # x_min, y_min, x_max, y_max = bbox
    resolution_x = (maxx - minx) / img_arry.shape[1]
    resolution_y = (maxy - miny) / img_arry.shape[0]

    # Ensure gps_polygon is ordered correctly as per src_points
    dst_points = np.float32([gps_to_pixel(coord, minx, maxy, resolution_x, resolution_y) for coord in coordinate_array])

    # Calculate the homography matrix
    h_matrix, _ = cv.findHomography(src_points, dst_points)

    # Apply the homography to rectify the image
    georef_image_array = cv.warpPerspective(img_arry, h_matrix, (img_arry.shape[1], img_arry.shape[0]), borderMode=cv.BORDER_CONSTANT, borderValue=(0, 0, 0))
    return georef_image_array


def gps_to_pixel(gps_coord, x_min, y_max, resolution_x, resolution_y):
    lon, lat = gps_coord
    Px = (lon - x_min) / resolution_x
    Py = (y_max - lat) / resolution_y
    return int(Px), int(Py)


def gps_to_pixel(coord, x_min, y_max, resolution_x, resolution_y):
    pixel_x = (coord[0] - x_min) / resolution_x
    pixel_y = (y_max - coord[1]) / resolution_y
    return [pixel_x, pixel_y]


def array2ds(cv2_array, polygon_wkt, epsg_code=4326):
    # Load the polygon from WKT and get its bounds
    polygon = loads(polygon_wkt)
    minx, miny, maxx, maxy = polygon.bounds

    # Image dimensions
    if len(cv2_array.shape) == 3:  # For color images
        height, width, bands = cv2_array.shape
    else:  # For grayscale images
        height, width = cv2_array.shape
        bands = 1

    # Calculate pixel size
    pixel_size_x = (maxx - minx) / width
    pixel_size_y = (maxy - miny) / height

    # Create a GDAL in-memory dataset
    gdal.DontUseExceptions()
    driver = gdal.GetDriverByName("MEM")
    ds = driver.Create("", width, height, bands, gdal.GDT_Byte)

    # Set the projection
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg_code)  # For example, WGS84
    ds.SetProjection(srs.ExportToWkt())

    # Set the geotransform
    geotransform = (minx, pixel_size_x, 0, maxy, 0, -pixel_size_y)
    ds.SetGeoTransform(geotransform)
    num_channels = cv2_array.shape[2]
    # Write the array data to the GDAL dataset bands
    for i in range(1, num_channels + 1):
        band = ds.GetRasterBand(i)
        band.WriteArray(cv2_array[:, :, i - 1])
        if num_channels == 3:
            if i == 1:
                band.SetColorInterpretation(gdal.GCI_RedBand)
            elif i == 2:
                band.SetColorInterpretation(gdal.GCI_GreenBand)
            elif i == 3:
                band.SetColorInterpretation(gdal.GCI_BlueBand)
        elif num_channels == 4:
            if i == 1:
                band.SetColorInterpretation(gdal.GCI_RedBand)
            elif i == 2:
                band.SetColorInterpretation(gdal.GCI_GreenBand)
            elif i == 3:
                band.SetColorInterpretation(gdal.GCI_BlueBand)
            elif i == 4:
                band.SetColorInterpretation(gdal.GCI_AlphaBand)

    return ds


def rasterize_polygon(polygon, width, height):
    polygon_wkt = str(polygon)
    # Create an in-memory vector layer
    mem_driver = ogr.GetDriverByName('Memory')
    mem_ds = mem_driver.CreateDataSource('out')
    layer = mem_ds.CreateLayer('poly', geom_type=ogr.wkbPolygon)

    # Create a polygon feature
    feature_def = layer.GetLayerDefn()
    feature = ogr.Feature(feature_def)
    polygon_geom = ogr.CreateGeometryFromWkt(polygon_wkt)
    feature.SetGeometry(polygon_geom)
    layer.CreateFeature(feature)

    # Create an in-memory raster layer
    raster_driver = gdal.GetDriverByName('MEM')
    raster_ds = raster_driver.Create('', width, height, 1, gdal.GDT_Byte)

    # Set a simple geotransform, based on the polygon's bounds
    minx, miny, maxx, maxy = polygon_geom.GetEnvelope()
    pixel_width = (maxx - minx) / width
    pixel_height = (maxy - miny) / height
    geo_transform = (minx, pixel_width, 0, maxy, 0, -pixel_height)

    raster_ds.SetGeoTransform(geo_transform)

    # The raster projection should match the polygon's (WGS84)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    raster_ds.SetProjection(srs.ExportToWkt())

    # Rasterize
    gdal.RasterizeLayer(raster_ds, [1], layer, burn_values=[1])

    # Convert to numpy array
    array = raster_ds.GetRasterBand(1).ReadAsArray()

    return array


def warp_ds(dst_utf8_path, georef_image_array):
    gdal.DontUseExceptions()
    # Assign GCPs to the dataset with correct geographic coordinates
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    translate_options = gdal.TranslateOptions(noData=0)
    vrt_ds = gdal.Translate(dst_utf8_path, georef_image_array, format='GTiff', outputSRS=srs.ExportToWkt(), options=translate_options)
    vrt_ds, georef_image_array = None, None
