#  Copyright (c) 2024.
#  __author__ = "Dean Hand"
#  __license__ = "AGPL"
#  __version__ = "1.0"

from osgeo import osr, gdal


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

    gcp_list = [
        gdal.GCP(pt0[0], pt0[1], 0, ext2[0], ext2[1]),
        gdal.GCP(pt1[0], pt1[1], 0, ext3[0], ext3[1]),
        gdal.GCP(pt2[0], pt2[1], 0, ext0[0], ext0[1]),
        gdal.GCP(pt3[0], pt3[1], 0, ext1[0], ext1[1])
    ]
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
    ds.SetGCPs(gcp_list, srs.ExportToWkt())
    nodata_value = 0
    # Define warp options
    warp_options = gdal.WarpOptions(dstSRS='EPSG:' + str(4326),
                                    resampleAlg=gdal.GRA_Bilinear,
                                    format='GTiff',
                                    srcNodata=nodata_value,
                                    dstNodata=nodata_value,
                                    creationOptions=['ALPHA=YES'])  # This option adds an alpha band for transparency

    # Perform the warp
    gdal.Warp(output_file, ds, options=warp_options)

    # Clean up
    ds = None