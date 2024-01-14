from __future__ import division
from osgeo import gdal, osr
import os
import json
import geojson
import fnmatch
from shapely.geometry import shape, LineString, Point, Polygon, mapping
from shapely.ops import cascaded_union, transform
import argparse
import exiftool
import datetime
from operator import itemgetter
import math
from math import *
import utm
from geojson_rewind import rewind
from progress.bar import Bar
import pyproj
import ntpath
import numpy as np
from testcon import calculate_drone_imagery_footprint_corners


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


def create_georaster(tags):
    # print(tags)
    """
    :param tags:
    :return:
    """
    out_out = ntpath.dirname(indir + "/output/")
    print("out dir", out_out)
    if not os.path.exists(out_out):
        os.makedirs(out_out)
    bar = Bar('Creating GeoTIFFs', max=len(tags))
    print("\n \n TAGS", tags, "\n \n")
    for tag in iter(tags):
        print("\n \n TAG", tag, "\n \n")
        coords = tag['geometry']['coordinates'][0]
        print("\n \n coords", coords, "\n \n")
        pt0 = coords[0][0], coords[0][1]
        pt1 = coords[1][0], coords[1][1]
        pt2 = coords[2][0], coords[2][1]
        pt3 = coords[3][0], coords[3][1]

        # print("OMGOMG", poly)
        props = tag['properties']
        # print("PROPS", props)
        # print(props)
        # print("LOOKIE" + indir)
        file_in = indir + "/" + props['File_Name']
        # print("file In", file_in)
        new_name = ntpath.basename(file_in[:-3]) + 'tif'
        # print(" here " + new_name)
        dst_filename = out_out + "/" + new_name
        # print("there " + dst_filename)
        # print(" OVER " + file_in)
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
            # print(x,y)
        yarr.reverse()
    return ext


def read_exif(files):
    """
    :param files:
    :return:
    """
    exif_array = []
    filename = file_name
    bar = Bar('Reading EXIF Data', max=len(files))
    with exiftool.ExifToolHelper() as et:
        metadata = iter(et.get_metadata(files))
    for d in metadata:
        exif_array.append(d)
        bar.next()
    bar.finish()
    print(color.BLUE + "Scanning images complete " + color.END)
    formatted = format_data(exif_array)
    writeOutputtoText(filename, formatted)
    print(color.GREEN + "Process Complete." + color.END)


def format_data(exif_array):
    # print("ExIF ARRAY", exif_array)
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
        # print(exif_array)
        # exit()
        i = i + 1
        for tag, val in tags.items():
            if tag in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
                exif_array.remove(tag)
        try:
            lat = tags['XMP:GPSLatitude']
            long = tags['XMP:GPSLongitude']
            imgwidth = tags['EXIF:ImageWidth']
            imghite = tags['EXIF:ImageHeight']
            r_alt = float(tags['XMP:RelativeAltitude'])
            a_alt = float(tags['XMP:AbsoluteAltitude'])
            FlightRollDegree = float(tags['XMP:FlightRollDegree'])
            FlightYawDegree = float(tags['XMP:FlightYawDegree'])
            FlightPitchDegree = float(tags['XMP:FlightPitchDegree'])
            GimbalRollDegree = float(tags['XMP:GimbalRollDegree'])
            GimbalYawDegree = float(tags['XMP:GimbalYawDegree'])
            GimbalPitchDegree = float(tags['XMP:GimbalPitchDegree'])
        except KeyError as e:
            imgwidth = tags['EXIF:ExifImageWidth']
            imghite = tags['EXIF:ExifImageHeight']
            r_alt = float(tags['EXIF:GPSAltitudeRef'])
            a_alt = float(tags['EXIF:GPSAltitude'])
            # FlightRollDegree = float(tags['EXIF:FlightRollDegree'])
        coords = [float(long), float(lat), r_alt]
        linecoords.append(coords)
        ptProps = {"File_Name": tags['File:FileName'], "Exposure Time": tags['EXIF:ExposureTime'],
                   "Focal_Length": tags['EXIF:FocalLength'], "Date_Time": tags['EXIF:DateTimeOriginal'],
                   "Image_Width": imgwidth, "Image_Height": imghite,
                   "RelativeAltitude": r_alt, "AbsoluteAltitude": a_alt,
                   "FlightRollDegree": FlightRollDegree, "FlightYawDegree": FlightYawDegree,
                   "FlightPitchDegree": FlightPitchDegree,
                   "GimbalRollDegree": GimbalRollDegree, "GimbalYawDegree": GimbalYawDegree,
                   "GimbalPitchDegree": GimbalPitchDegree,
                   "EXIF:DateTimeOriginal": tags['EXIF:DateTimeOriginal']}
        # print(ptProps)
        # exit()
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
    # print("each one \n")
    # print("*&*&*&*", img_box)
    tiles = img_box[0]
    # write_gcpList(gcp_info)
    if geo_tiff == 'y':
        create_georaster(tiles)
    else:
        print("no georasters.")
    # aoi = img_box[1]
    lineGeom = dict(type="LineString", coordinates=linecoords)
    lines = dict(type="Feature", geometry=lineGeom, properties={})
    feature_coll['features'].insert(0, lines)
    mission_props = dict(date=datetime, platform="DJI Mavic 2 Pro", sensor_make=sensor_make, sensor=sensor)
    # polys = dict(type="Feature", geometry=aoi, properties=mission_props)
    # polyfix = rewind(polys)
    feature_coll['features'].insert(0, tiles[0])
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
        lat = cent['coords'][1]
        lng = cent['coords'][0]
        print("**Drones Lng, Lats**", lng, lat)
        prps = cent['props']
        fimr= float(prps['FlightRollDegree'])
        fimp = float(prps['FlightPitchDegree'])
        fimy = float(prps['FlightYawDegree'])
        gimr = float(prps['GimbalRollDegree'])
        gimp = int(prps['GimbalPitchDegree'])
        gimy = float(prps['GimbalYawDegree'])
        wid = float(prps['Image_Width'])
        hite = float(prps['Image_Height'])
        # print("**Gimbal Pitch**", gimp, "\n**Gimbal Roll**", gimr, "\n**Gimbal Yaw**", gimy)
        # print("**ACFT Pitch**", fimp, "\n**ACFT Roll**", fimr, "\n**ACFT Yaw**", fimy)
        img_n = prps['File_Name']
        # print("**file name**", img_n)
        focal_lgth = float(prps['Focal_Length'])
        r_alt = float(prps["RelativeAltitude"])
        a_alt = float(prps["AbsoluteAltitude"])
        # (print("REL", r_alt, "AB", a_alt))
        cds1 = utm.from_latlon(lat, lng)
        sensor_width = 13.2
        sensor_height = 8.8
        poly = calculate_drone_imagery_footprint_corners(focal_lgth, wid, hite, r_alt, fimr,
                                                         fimy, fimp, gimr, gimy,
                                                         gimp, cds1[2], cds1[3], cds1[0], cds1[1], sensor_width, sensor_height)
        # print(ltlgpy)
        ltlgpy = utm_polygon_to_latlon(poly, cds1[2], cds1[3])
        lastcod = [ltlgpy[0], ltlgpy[1], ltlgpy[2], ltlgpy[3], ltlgpy[0]]
        # update_poly = ltlgpy.extend(lastcod)
        # print("*&*&",  lastcod)
        # Create GeoJSON
        # over_poly.append(update_poly)
        # exit()
        # Create GeoJSON
        wow3 = geojson.dumps(lastcod)
        wow4 = json.loads(wow3)
        # print(wow4)
        wow5 = {
          "type": "Polygon",
          "coordinates": [wow4]
        }
        # exit()
        gd_feat = dict(type="Feature", geometry=wow5, properties=prps)
        wow6 = rewind(gd_feat)
        # gs1 = json.dumps(gd_feat)
        # print("gs1", gs1)
        polys.append(wow6)
        bar.next()
    # union_buffered_poly = cascaded_union([l.buffer(.001) for l in over_poly])
    # polyz = union_buffered_poly.simplify(0.005, preserve_topology=False)
    # projected = partial(
    #     pyproj.transform,
    #     pyproj.Proj(init='epsg:%s' % p2),  # source coordinate system
    #     pyproj.Proj(init='epsg:4326'))  # destination coordinate system
    # g3 = transform(projected, polyz)
    pop3 = geojson.dumps(over_poly)
    pop4 = json.loads(pop3)
    # pop4 = rewind(pop4)
    bar.finish()
    return polys, pop4


# def calculate_fov_resolution(wd, ht, cds1, r_alt, fl, gimr, gimp, gimy, fimr, fimp, fimy, lng, lat):
#     print(cds1)
#     # Extract UTM coordinates and zone information
#     utm_x, utm_y, utm_zone, utm_hemisphere = cds1
#     ang_lmt = 1
#     # Convert altitude to meters
#     alt_meters = r_alt
#
#     # Calculate IFOV in radians
#     ifov_x = math.radians(2 * math.atan((wd / (2 * fl))))
#     ifov_y = math.radians(2 * math.atan((ht / (2 * fl))))
#
#     # Calculate FOV in degrees
#     fov_x = math.degrees(ifov_x)
#     fov_y = math.degrees(ifov_y)
#
#     # Calculate pixel resolution based on IFOV
#     pixel_resolution_x = ifov_x * alt_meters
#     pixel_resolution_y = ifov_y * alt_meters
#     pix_resolution_out = ((pixel_resolution_x + pixel_resolution_y) / 2)
#
#     poly = generate_geojson_footprint(fov_x, fov_y, gimr, gimp, gimy, fimr, fimp, fimy, alt_meters, ang_lmt, utm_zone)
#
#     return poly

def new_gross(wd, ht, cds1, alt, fl, gimr, gimp, gimy, fimr, fimp, fimy, lng, lat):
    sw = 13.2  # Sensor Width
    sh = 8.8  # Sensor Height
    xview = 2 * degrees(atan(sw / (2 * fl)))  # Field of View - Width
    yview = 2 * degrees(atan(sh / (2 * fl)))  # Field of View - Height
    res, fov_x, fov_y = calc_res(wd, ht, xview, yview, alt)
    # ang_lmt = 1
    poly = generate_geojson_footprint(fov_x, fov_y, gimr, gimp, gimy, fimr, fimp, fimy, alt, ang_lmt, cds1[2], lng, lat)
    # print("\n\n\n ugggg ", poly)
    return res, fov_x, fov_y



def calc_res(pixel_x, pixel_y, x_angle, y_angle, alt):

    """
    :param pixel_x:
    :param pixel_y:
    :param x_angle:
    :param y_angle:
    :param alt:
    :return:
    """
    # Calc IFOV, based on right angle trig of one-half the lens angles
    fov_x = 2 * (math.tan(math.radians(0.5 * x_angle)) * alt)
    fov_y = 2 * (math.tan(math.radians(0.5 * y_angle)) * alt)

    # Calc pixel resolutions based on the IFOV and sensor size
    pixel_resx = (fov_x / pixel_x) * 100
    pixel_resy = (fov_y / pixel_y) * 100

    # Average the X and Y resolutions
    pix_resolution_out = ((pixel_resx + pixel_resy) / 2)

    return pix_resolution_out, fov_x, fov_y

# def post_quat(cent, crn, alt):
#     r, p, y = to_euler(crn[0], crn[1], crn[2], crn[3])
#     dx = alt * math.tan(math.radians(r))
#     dy = alt * math.tan(math.radians(p))
#     utmx = dx * math.cos(math.radians(y)) - dy * math.sin(math.radians(y))
#     utmy = -dx * math.sin(math.radians(y)) - dy * math.cos(math.radians(y))
#     utmx1 = cent[0] + utmx
#     utmy1 = cent[1] + utmy
#     coords = utm.to_latlon(utmx1, utmy1, cent[2], cent[3])
#     return [coords[1], coords[0]]
#
# def convert_utm_to_decimal(coords):
#     lat, lng = utm.to_latlon(coords[0], coords[1], coords[3], coords[4])
#     return lng, lat  # Swap longitude and latitude here
#
# def create_polygon(coords):
#     polygon = Polygon(coords)
#     return polygon


def utm_polygon_to_latlon(utm_coords_strings, utm_zone, utm_nth):
    """
    Convert a list of UTM coordinates in string format to decimal degree latitude and longitude coordinates.

    Args:
    utm_coords_strings (list): A list of UTM coordinates as strings.
    utm_zone (int): The UTM zone of the UTM coordinates.
    utm_nth (str): UTM hemisphere (N or S).

    Returns:
    Polygon: A Shapely Polygon in decimal degree latitude and longitude coordinates.
    """
    latlon_coords = []
    for utm_point_array in utm_coords_strings:
        print(" 1", utm_point_array)
        utm_x_str, utm_y_str = utm_point_array
        utm_x = utm_x_str
        utm_y = utm_y_str
        # print(utm_x, utm_y, utm_zone, utm_nth)
        # exit()
        lat, lon = utm.to_latlon(utm_x, utm_y, utm_zone, utm_nth)
        latlon_coords.append((lon, lat))

    return latlon_coords


def convert_utm_to_decimal(z, y, a, b):
    print("easting: ", type(z))
    print("northing: ", type(y))
    print("a: ", type(a))
    print("b: ", type(b))
    lat, lng = utm.to_latlon(z, y, a, b)
    return lng, lat  # Swap longitude and latitude here


def convert_decimal_to_utm(lat, lng):
    utm_coords = utm.from_latlon(lat, lng)
    return utm_coords


def create_polygon(coords):
    polygon = Polygon(coords)
    return polygon


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
