from __future__ import division
from osgeo import gdal, osr
import os
import json
import geojson
import fnmatch
from shapely import geometry
from shapely.geometry import shape, LineString, Point, Polygon
from shapely.ops import cascaded_union, transform
import argparse
from pyexiftool import exiftool
import datetime
from operator import itemgetter
import math
from math import *
import utm
from geojson_rewind import rewind
from progress.bar import Bar
import pyproj
from quaternion_process import to_quaternions, to_euler, quaternion_multiply
from functools import partial


parser = argparse.ArgumentParser(description="Input Mission JSON File")
parser.add_argument("-i", "--indir", help="Input directory", required=True)
parser.add_argument("-o", "--dest", help="Output directory", required=True)
parser.add_argument("-g", "--nonst", help="geoTIFF output", required=True)
args = parser.parse_args()
indir = args.indir
outdir = args.dest
geo_tiff = args.nonst
now = datetime.datetime.now()
file_name = "M_" + now.strftime("%Y-%m-%d_%H-%M") + ".json"


class color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def main():
    files = find_file(indir)
    read_exif(files)

#
# def create_georaster(tags):
#     # print(tags)
#     """
#     :param tags:
#     :return:
#     """
#     out_out = ntpath.dirname(indir + "/output/")
#     print("out dir", out_out)
#     if not os.path.exists(out_out):
#         os.makedirs(out_out)
#     bar = Bar('Creating GeoTIFFs', max=len(tags))
#
#     for tag in iter(tags):
#
#         coords = tag['geometry']['coordinates'][0]
#         # lonlat = coords[0]
#         pt0 = coords[0][0], coords[0][1]
#         pt1 = coords[1][0], coords[1][1]
#         pt2 = coords[2][0], coords[2][1]
#         pt3 = coords[3][0], coords[3][1]
#
#         # print("OMGOMG", poly)
#         props = tag['properties']
#         # print("PROPS", props)
#         # print(props)
#         file_in = indir + "/images/" + props['File_Name']
#         # print("file In", file_in)
#         new_name = ntpath.basename(file_in[:-3]) + 'tif'
#         dst_filename = out_out + "/" + new_name
#         ds = gdal.Open(file_in, 0)
#         gt = ds.GetGeoTransform()
#         cols = ds.RasterXSize
#         rows = ds.RasterYSize
#         ext = GetExtent(gt, cols, rows)
#         ext0 = ext[0][0], ext[0][1]
#         ext1 = ext[1][0], ext[1][1]
#         ext2 = ext[2][0], ext[2][1]
#         ext3 = ext[3][0], ext[3][1]
#
#         gcp_string = '-gcp {} {} {} {} ' \
#                      '-gcp {} {} {} {} ' \
#                      '-gcp {} {} {} {} ' \
#                      '-gcp {} {} {} {}'.format(ext0[0], ext0[1],
#                                                pt2[0], pt2[1],
#                                                ext1[0], ext1[1],
#                                                pt3[0], pt3[1],
#                                                ext2[0], ext2[1],
#                                                pt0[0], pt0[1],
#                                                ext3[0], ext3[1],
#                                                pt1[0], pt1[1])
#
#         gcp_items = filter(None, gcp_string.split("-gcp"))
#         gcp_list = []
#         for item in gcp_items:
#             pixel, line, x, y = map(float, item.split())
#             z = 0
#             gcp = gdal.GCP(x, y, z, pixel, line)
#             gcp_list.append(gcp)
#
#         srs = osr.SpatialReference()
#         srs.ImportFromEPSG(4326)
#         wkt = srs.ExportToWkt()
#         ds = gdal.Translate(dst_filename, ds, outputSRS=wkt, GCPs=gcp_list, noData=0)
#         ds = None
#         bar.next()
#     bar.finish()
#     return


# def GetExtent(gt, cols, rows):
#     ''' Return list of corner coordinates from a geotransform
#         @type gt:   C{tuple/list}
#         @param gt: geotransform
#         @type cols:   C{int}
#         @param cols: number of columns in the dataset
#         @type rows:   C{int}
#         @param rows: number of rows in the dataset
#         @rtype:    C{[float,...,float]}
#         @return:   coordinates of each corner
#     '''
#     ext = []
#     xarr = [0, cols]
#     yarr = [0, rows]
#
#     for px in xarr:
#         for py in yarr:
#             x = gt[0] + (px * gt[1]) + (py * gt[2])
#             y = gt[3] + (px * gt[4]) + (py * gt[5])
#             ext.append([x, y])
#             # print(x,y)
#         yarr.reverse()
#     return ext


def read_exif(files):
    """
    :param files:
    :return:
    """
    exif_array = []
    filename = file_name
    bar = Bar('Reading EXIF Data', max=len(files))
    with exiftool.ExifTool() as et:
        metadata = iter(et.get_metadata_batch(files))
    for d in metadata:
        exif_array.append(d)
        bar.next()
    bar.finish()
    print(color.BLUE + "Scanning images complete " + color.END)
    formatted = format_data(exif_array)
    writeOutputtoText(filename, formatted)
    print(color.GREEN + "Process Complete." + color.END)


def format_data(exif_array):
    """
    :param exif_array:
    :return:
    """
    exif_array.sort(key=itemgetter('EXIF:DateTimeOriginal'))
    feature_coll = dict(type="FeatureCollection", features=[])
    linecoords = []
    img_stuff = []
    datetime = ''
    sensor = ''
    sensor_make = ''
    i = 0
    bar = Bar('Creating GeoJSON', max=len(exif_array))
    for tags in iter(exif_array):
        i = i + 1
        for tag, val in tags.items():
            if tag in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
                exif_array.remove(tag)
        try:
            lat = float(tags['XMP:Latitude'])
            long = float(tags['XMP:Longitude'])
            imgwidth = tags['EXIF:ImageWidth']
            imghite = tags['EXIF:ImageHeight']
        except KeyError as e:
            lat = float(tags['Composite:GPSLatitude'])
            long = float(tags['Composite:GPSLongitude'])
            imgwidth = tags['EXIF:ExifImageWidth']
            imghite = tags['EXIF:ExifImageHeight']
        alt = float(tags['XMP:RelativeAltitude'])
        coords = [long, lat, alt]
        linecoords.append(coords)
        ptProps = {"File_Name": tags['File:FileName'], "Exposure Time": tags['EXIF:ExposureTime'],
                   "Focal_Length": tags['EXIF:FocalLength'], "Date_Time": tags['EXIF:DateTimeOriginal'],
                   "Image_Width": imgwidth, "Image_Height": imghite,
                   "Heading": tags['XMP:FlightYawDegree'], "AbsoluteAltitude": alt,
                   "Relative_Altitude": tags['XMP:RelativeAltitude'],
                   "FlightRollDegree": tags['XMP:FlightRollDegree'], "FlightYawDegree": tags['XMP:FlightYawDegree'],
                   "FlightPitchDegree": tags['XMP:FlightPitchDegree'], "GimbalRollDegree": tags['XMP:GimbalRollDegree'],
                   "GimbalYawDegree": tags['XMP:GimbalYawDegree'], "GimbalPitchDegree": tags['XMP:GimbalPitchDegree'],
                   "EXIF:DateTimeOriginal": tags['EXIF:DateTimeOriginal']}
        if i == 1:
            datetime = tags['EXIF:DateTimeOriginal']
            sensor = tags['EXIF:Model']
            sensor_make = tags['EXIF:Make']
        img_over = dict(coords=coords, props=ptProps)
        img_stuff.append(img_over)
        ptGeom = dict(type="Point", coordinates=coords)
        points = dict(type="Feature", geometry=ptGeom, properties=ptProps)
        feature_coll['features'].append(points)
        bar.next()
        # gcp_info = long, lat, alt
    img_box = image_poly(img_stuff)
    tiles = img_box[0]
    # write_gcpList(gcp_info)
    # if geo_tiff == 'y':
    #     create_georaster(tiles)
    # else:
    #     print("no georasters.")
    aoi = img_box[1]
    lineGeom = dict(type="LineString", coordinates=linecoords)
    lines = dict(type="Feature", geometry=lineGeom, properties={})
    feature_coll['features'].insert(0, lines)
    mission_props = dict(date=datetime, platform="DJI Mavic 2 Pro", sensor_make=sensor_make, sensor=sensor)
    polys = dict(type="Feature", geometry=aoi, properties=mission_props)
    feature_coll['features'].insert(0, polys)
    for imps in tiles:
        feature_coll['features'].append(imps)
    bar.finish()
    return feature_coll


def writeOutputtoText(filename, file_list):
    # print("FILE FILE", file_list)
    """
    :param filename:
    :param file_list:
    :return:
    """
    dst_n = outdir + '/' + filename
    with open(dst_n, 'w') as outfile:
        geojson.dump(file_list, outfile, indent=4, sort_keys=False)
    print(color.GREEN + "GeoJSON Produced." + color.END)
    return


def image_poly(imgar):
    """
    :param imgar:
    :return:
    """
    polys = []
    over_poly = []
    bar = Bar('Plotting Image Bounds', max=len(imgar))
    # print("BAR", bar)
    for cent in iter(imgar):
        lat = float(cent['coords'][1])
        lng = float(cent['coords'][0])
        print("**Drones Lng, Lats**", lng, lat)
        prps = cent['props']
        fimy = float(prps['FlightRollDegree'])
        fimx = float(prps['FlightPitchDegree'])
        fimz = float(prps['FlightYawDegree'])
        gimr = float(prps['GimbalRollDegree'])
        gimp = float(prps['GimbalPitchDegree'])
        gimy = float(prps['GimbalYawDegree'])
        print("**Gimbal Pitch**", gimp, "\n **Gimbal Roll**", gimr, "\n **Gimbal Yaw**", gimy)
        img_n = prps['File_Name']
        # print("file name", img_n)
        focal_lgth = prps['Focal_Length']
        alt = float(prps["Relative_Altitude"])
        cds1 = utm.from_latlon(lat, lng)
        poly = new_gross(cds1, alt, focal_lgth, gimp, gimr, gimy, fimx, fimy, fimz)
        over_poly.append(poly)

        # Create GeoJSON
        wow3 = geojson.dumps(poly)
        wow4 = json.loads(wow3)
        wow4 = rewind(wow4)

        gd_feat = dict(type="Feature", geometry=wow4, properties=prps)
        gs1 = json.dumps(gd_feat)
        print("gs1", gs1)
        polys.append(gd_feat)
        bar.next()
    union_buffered_poly = cascaded_union([l.buffer(.001) for l in over_poly])
    print("UNION", union_buffered_poly)
    polyz = union_buffered_poly.simplify(0.005, preserve_topology=False)
    print("polyz", polyz)
    projected = partial(
        pyproj.transform,
        pyproj.Proj(init='epsg:3857'),  # source coordinate system
        pyproj.Proj(init='epsg:4326'))  # destination coordinate system
    g3 = transform(projected, polyz)
    print("G3", g3)
    pop3 = geojson.dumps(g3)
    print("POP3", pop3)
    pop4 = json.loads(pop3)
    pop4 = rewind(pop4)
    print("pops4", pop4, "\npolys", polys)
    ssx = json.dumps(polys)
    print("SSX", ssx)
    bar.finish()
    return polys, pop4


def new_gross(cds1, alt, fl, gimp, gimr, gimy, fimx, fimy, fimz):
    # print(" coords", cds1, "\n Alt", alt, "\n focal length", fl, "\n gimbal pitch",
    #       gimp, "\n gimbal roll", gimr, "\n gimbal yaw", gimy)
    sw = 8  # Sensor Width
    sh = 5.3  # Sensor Height
    print("**Relative Altitude**", alt, "**Focal, length**", fl)
    print("**Sensor Width**", sw, "\n **Sensor Height**", sh)
    print("**Drone Coordinates**", cds1)
    fov_x = 2 * degrees(atan(sw / (2 * fl)))  # Field of View - Width
    fov_y = 2 * degrees(atan(sh / (2 * fl)))  # Field of View - Height
    print("**HFoV**", fov_x, "\n **VFoV**", fov_y)
    #  Calculate FOVs corners and transform into Quaternions
    TR = to_quaternions((fov_x / -2), (fov_y / 2), 0)
    TL = to_quaternions((fov_x / 2), (fov_y / 2), 0)
    BR = to_quaternions((fov_x / -2), (fov_y / -2), 0)
    BL = to_quaternions((fov_x / 2), (fov_y / -2), 0)
    print("**TR**", TR, "\n **TL**", TL, "\n **BR**", BR, "\n **BL**", BL)
    #  Transform gimbal pitch, roll, & yaw into Quaternions
    gimRot = to_quaternions(gimp, gimr, gimy)
    print("**gimRoT**", gimRot)
    ##  Transform aircraft pitch, roll, & yaw into Quaternions
    # acRot = np.quaternion(fimx, fimy, fimz)
    # Multiply gimbal Quaternions by corner(FOV) Quaternions
    TR1 = quaternion_multiply(gimRot, TR)
    TL1 = quaternion_multiply(gimRot, TL)
    BR1 = quaternion_multiply(gimRot, BR)
    BL1 = quaternion_multiply(gimRot, BL)
    print("**TR1**", TR1, "\n **TL1**", TL1, "\n **BR1**", BR1, "\n **BL1**", BL1)
    # corner Quaternions products into array and process
    crn = [TR1, TL1, BL1, BR1]
    coords = []
    for c in crn:
        bod = post_quat(cds1, c, alt)
        coords.append(bod)
    poly = geometry.Polygon([coords[0], coords[1], coords[2], coords[3], coords[0]])

    return poly


def gross_crds(lat, lng):
    cds1 = utm.from_latlon(lat, lng)
    return cds1[0], cds1[1]


def post_quat(cent, crn, alt):
    # print("CRN", crn[0], crn[1], crn[2])
    crn2 = to_euler(crn[0], crn[1], crn[2], crn[3])
    print("**to_euler return**", crn2)
    p = crn2[0]  # GimbalPitchDegree
    r = crn2[1]  # GimbalRollDegree
    y = crn2[2]  # GimbalYawDegree
    # print(" pitch", p, "\n roll", r, "\n yaw", y)

    dx = alt * math.tan(math.radians(r))
    dy = alt * math.tan(math.radians(p))
    print("**dx**", dx, "dy**", dy)
    utmx = dx * math.cos(math.radians(y)) - dy * math.sin(math.radians(y))
    utmy = -dx * math.sin(math.radians(y)) - dy * math.cos(math.radians(y))
    print("**utmx**", utmx, "\n **utmy**", utmy)
    utmx1 = cent[0] + utmx
    utmy1 = cent[1] + utmy
    print("**utmx1**", utmx1, "\n **utmy1**", utmy1)
    # print("UTMS**", utmx1, utmy1)
    coords = utm.to_latlon(utmx1, utmy1, cent[2], cent[3])
    print("**converted to latlong**", coords)
    return [coords[1], coords[0]]


def convert_wgs_to_utm(lon, lat):
    """
    :param lon:
    :param lat:
    :return:
    """
    utm_band = str((math.floor((lon + 180) / 6) % 60) + 1)
    if len(utm_band) == 1:
        utm_band = '0' + utm_band
    if lat >= 0:
        epsg_code = '326' + utm_band
    else:
        epsg_code = '327' + utm_band
    return epsg_code


def find_file(some_dir):
    """
    :param some_dir:
    :return:
    """
    matches = []
    for root, dirnames, filenames in os.walk(some_dir):
        for filename in fnmatch.filter(filenames, '*.JPG'):
            matches.append(os.path.join(root, filename))
    return matches


if __name__ == "__main__":
    main()
