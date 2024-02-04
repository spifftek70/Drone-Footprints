#  Copyright (c) 2024.
#  __author__ = "Dean Hand"
#  __license__ = "AGPL"
#  __version__ = "1.0"

import numpy as np
from osgeo import osr, gdal
from pyproj import Proj, Transformer, CRS


def calculate_gcp_list(easting, northing, pixel_width, pixel_height, yaw, original_width,
                       original_height, zone_number, center_latitude, center_longitude, utm_zone, utm_nth):
    # Define the projection from UTM to WGS84 and vice versa
    # Assuming zone_number and center_latitude are already defined
    is_southern = center_latitude < 0
    utm_crs = CRS(proj='utm', zone=zone_number, ellps='WGS84', datum='WGS84', south=is_southern)
    wgs84_crs = CRS(proj='latlong', datum='WGS84')

    # Initialize the Transformer object for transforming from UTM to WGS84
    transformer = Transformer.from_crs(utm_crs, wgs84_crs, always_xy=True)

    # Calculate the corners of the image in UTM coordinates
    width_meter = original_width * pixel_width
    height_meter = original_height * pixel_height
    corners_utm = np.array([
        [easting - width_meter / 2, northing + height_meter / 2],  # Top-left
        [easting + width_meter / 2, northing + height_meter / 2],  # Top-right
        [easting + width_meter / 2, northing - height_meter / 2],  # Bottom-right
        [easting - width_meter / 2, northing - height_meter / 2]  # Bottom-left
    ])

    # Convert yaw from degrees to radians and calculate rotation matrix
    yaw_rad = np.radians(yaw)
    rotation_matrix = np.array([
        [np.cos(yaw_rad), -np.sin(yaw_rad)],
        [np.sin(yaw_rad), np.cos(yaw_rad)]
    ])

    # Rotate corners around the center point
    center_utm = np.array([easting, northing])
    rotated_corners_utm = np.dot(corners_utm - center_utm, rotation_matrix) + center_utm

    # Convert rotated corners back to decimal degrees
    rotated_corners_latlon = [transformer.transform(corner[0], corner[1]) for corner in rotated_corners_utm]

    return rotated_corners_latlon


def GetExtent(gt, cols, rows):
    ''' Return list of corner coordinates from a geotransform
        @type gt:   C{tuple/list}
        @param gt: geotransform
        @type cols:   C{int}
        @param cols: number of columns in the dataset
        @type rows:   C{int}
        @param rows: number of rows in the dataset
        @rtype:    C{[float,...,float]}
        @return:   coordinates of each corner
    '''
    ext = []
    xarr = [0, cols]
    yarr = [0, rows]

    for px in xarr:
        for py in yarr:
            x = gt[0] + (px * gt[1]) + (py * gt[2])
            y = gt[3] + (px * gt[4]) + (py * gt[5])
            ext.append([x, y])
        yarr.reverse()
    return ext


def create_gcp_list(coords, ext):
    pt1 = coords[0][0], coords[0][1]  # Now this is Top-right
    pt0 = coords[1][0], coords[1][1]  # Now this is Top-left
    pt3 = coords[2][0], coords[2][1]  # Now this is Bottom-left
    pt2 = coords[3][0], coords[3][1]  # Now this is Bottom-right

    ext1 = ext[0][0], ext[0][1]  # Assuming this is top-right
    ext2 = ext[1][0], ext[1][1]  # Assuming this is top-left
    ext3 = ext[2][0], ext[2][1]  # Assuming this is bottom-left
    ext0 = ext[3][0], ext[3][1]  # Assuming this is bottom-right

    # Modify the order of GCPs assignment here to correct the mirroring
    gcp_string = '-gcp {} {} {} {} ' \
                 '-gcp {} {} {} {} ' \
                 '-gcp {} {} {} {} ' \
                 '-gcp {} {} {} {}'.format(ext0[0], ext0[1], pt0[0], pt0[1],
                                           ext1[0], ext1[1], pt1[0], pt1[1],
                                           ext2[0], ext2[1], pt2[0], pt2[1],
                                           ext3[0], ext3[1], pt3[0], pt3[1])

    gcp_items = filter(None, gcp_string.split("-gcp"))
    gcp_list = []
    for item in gcp_items:
        pixel, line, x, y = map(float, item.split())
        z = 0
        gcp = gdal.GCP(x, y, z, pixel, line)
        gcp_list.append(gcp)
    return gcp_list


def warp_image_with_gcp(image_path, output_file, coord_array):
    """
    Warps an image using the provided list of GCPs to align it with geographic north.
    The output image will be saved to the specified path.
    """
    # Open the input dataset
    gdal.DontUseExceptions()
    ds = gdal.Open(image_path)
    gt = ds.GetGeoTransform()
    cols = ds.RasterXSize
    rows = ds.RasterYSize
    ext = GetExtent(gt, cols, rows)
    gcp_list = create_gcp_list(coord_array, ext)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    wkt = srs.ExportToWkt()
    ds = gdal.Translate(output_file, ds, outputSRS=wkt, GCPs=gcp_list, noData=0)
    ds = None