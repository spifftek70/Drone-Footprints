import ntpath
import os
from osgeo import gdal, ogr, osr
from progress.bar import Bar
# from Drone_Footprints import Color
from Color_Class import Color


def create_georaster(tags, indir):
    print(Color.DARKCYAN + "Creating GeoTIFFs Files." + Color.END)
    out_out = ntpath.dirname(indir + "/output/")
    if not os.path.exists(out_out):
        os.makedirs(out_out)
    bar = Bar('Creating GeoTIFFs', max=len(tags))
    for tag in iter(tags):
        coords = tag['geometry']['coordinates'][0]
        pt0 = coords[3][0], coords[3][1]
        pt1 = coords[2][0], coords[2][1]
        pt2 = coords[1][0], coords[1][1]
        pt3 = coords[0][0], coords[0][1]
        props = tag['properties']
        file_in = indir + "/" + props['File_Name']
        new_name = ntpath.basename(file_in[:-3]) + 'tif'
        dst_filename = out_out + "/" + new_name
        gdal.UseExceptions()
        ds = gdal.Open(file_in, 0)
        gt = ds.GetGeoTransform()
        cols = ds.RasterXSize
        rows = ds.RasterYSize
        ext = GetExtent(gt, cols, rows)
        ext0 = ext[0][0], ext[0][1]
        ext1 = ext[1][0], ext[1][1]
        ext2 = ext[2][0], ext[2][1]
        ext3 = ext[3][0], ext[3][1]
        gcp_string = '-gcp {} {} {} {} ' \
                     '-gcp {} {} {} {} ' \
                     '-gcp {} {} {} {} ' \
                     '-gcp {} {} {} {}'.format(ext0[0], ext0[1],
                                               pt2[0], pt2[1],
                                               ext1[0], ext1[1],
                                               pt3[0], pt3[1],
                                               ext2[0], ext2[1],
                                               pt0[0], pt0[1],
                                               ext3[0], ext3[1],
                                               pt1[0], pt1[1])
        gcp_items = filter(None, gcp_string.split("-gcp"))
        gcp_list = []
        for item in gcp_items:
            pixel, line, x, y = map(float, item.split())
            z = 0
            gcp = gdal.GCP(x, y, z, pixel, line)
            gcp_list.append(gcp)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        wkt = srs.ExportToWkt()
        ds = gdal.Translate(dst_filename, ds, outputSRS=wkt, GCPs=gcp_list, noData=0)
        ds = None
        bar.next()
    bar.finish()
    print(Color.DARKCYAN + "All GeoTIFFs Created." + Color.END)
    return


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