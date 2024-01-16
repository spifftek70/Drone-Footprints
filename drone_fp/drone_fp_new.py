from __future__ import division
from osgeo import gdal, osr
import os
import json
import geojson
import fnmatch
from shapely import affinity
import shapely.wkt
import shapely.geometry
from shapely.geometry import shape, LineString, Point, Polygon, mapping
import argparse
import exiftool
import datetime
from operator import itemgetter
import math
import utm
from progress.bar import Bar
import ntpath
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
    # print("out dir", out_out)
    if not os.path.exists(out_out):
        os.makedirs(out_out)
    bar = Bar('Creating GeoTIFFs', max=len(tags))
    # print("\n \n TAGS", tags, "\n \n")
    for tag in iter(tags):
        # print("\n \n TAG", tag, "\n \n")
        coords = tag['geometry']['coordinates'][0]
        # print("\n \n", coords, "\n \n")
        # exit()
        pt0 = coords[3][0], coords[3][1]
        pt1 = coords[2][0], coords[2][1]
        pt2 = coords[1][0], coords[1][1]
        pt3 = coords[0][0], coords[0][1]
        props = tag['properties']

        file_in = indir + "/" + props['File_Name']
        new_name = ntpath.basename(file_in[:-3]) + 'tif'
        dst_filename = out_out + "/" + new_name
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
        # print(tags)
        # exit()
        i = i + 1
        for tag, val in tags.items():
            if tag in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
                exif_array.remove(tag)
        try:
            lat = float(tags['XMP:GPSLatitude'])
            long = float(tags['XMP:GPSLongitude'])
        except KeyError as e:
            lat = float(tags['Composite:GPSLatitude'])
            long = float(tags['Composite:GPSLongitude'])
        except KeyError as b:
            lat = float(tags['EXIF:GPSLatitude'])
            long = float(tags['EXIF:GPSLongitude'])
        try:
            FlightRollDegree = float(tags['XMP:FlightRollDegree'])
            FlightYawDegree = float(tags['XMP:FlightYawDegree'])
            FlightPitchDegree = float(tags['XMP:FlightPitchDegree'])
            GimbalRollDegree = float(tags['XMP:GimbalRollDegree'])
            GimbalYawDegree = float(tags['XMP:GimbalYawDegree'])
            GimbalPitchDegree = float(tags['XMP:GimbalPitchDegree'])
        except KeyError as f:
            FlightRollDegree = float(tags['EXIF:FlightRollDegree'])
            FlightYawDegree = float(tags['EXIF:FlightYawDegree'])
            FlightPitchDegree = float(tags['EXIF:FlightPitchDegree'])
            GimbalRollDegree = float(tags['EXIF:GimbalRollDegree'])
            GimbalYawDegree = float(tags['EXIF:GimbalYawDegree'])
            GimbalPitchDegree = float(tags['EXIF:GimbalPitchDegree'])
        try:
            imgwidth = tags['EXIF:ImageWidth']
            imghite = tags['EXIF:ImageHeight']
        except KeyError as g:
            imgwidth = tags['EXIF:ExifImageWidth']
            imghite = tags['EXIF:ExifImageHeight']
        r_alt = float(tags['XMP:RelativeAltitude'])
        a_alt = float(tags['XMP:AbsoluteAltitude'])
        coords = [float(long), float(lat), r_alt]
        # print(long, lat)
        # exit()
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
    img_box = image_poly(img_stuff)
    tiles = img_box[0]
    if geo_tiff == 'y':
        create_georaster(tiles)
    else:
        print("no georasters.")
    lineGeom = dict(type="LineString", coordinates=linecoords)
    mission_props = dict(date=datetime, platform="DJI Mavic 2 Pro", sensor_make=sensor_make, sensor=sensor)
    lines = dict(type="Feature", geometry=lineGeom, properties=mission_props)
    feature_coll['features'].insert(0, lines)
    feature_coll['features'].insert(0, tiles[0])
    for imps in tiles:
        feature_coll['features'].append(imps)
    bar.finish()
    return feature_coll


def writeOutputtoText(filename, file_list):
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
    for cent in iter(imgar):
        lat = cent['coords'][1]
        lng = cent['coords'][0]
        # print("**Drones Lng, Lats**", lng, lat)
        prps = cent['props']
        fimr= float(prps['FlightRollDegree'])
        fimp = float(prps['FlightPitchDegree'])
        fimy = float(prps['FlightYawDegree'])
        gimr = float(prps['GimbalRollDegree'])
        gimp = int(prps['GimbalPitchDegree'])
        gimy = float(prps['GimbalYawDegree'])
        wid = float(prps['Image_Width'])
        hite = float(prps['Image_Height'])
        abso_yaw = ((gimy + fimy) / 2) + 180
        print("\n\n Dang yaws\n ", abso_yaw, fimy, gimy)
        img_n = prps['File_Name']
        focal_lgth = float(prps['Focal_Length'])
        r_alt = float(prps["RelativeAltitude"])
        a_alt = float(prps["AbsoluteAltitude"])
        zone, hemisphere, easting, northing = decimal_degrees_to_utm(lat, lng)
        sensor_width = 13.2
        sensor_height = 8.8
        poly = calculate_drone_imagery_footprint_corners(focal_lgth, wid, hite, r_alt, fimr,
                                                         fimy, fimp, gimr, gimy, gimp, zone, hemisphere,
                                                         lat, lng, easting, northing, sensor_width, sensor_height)
        ltlgpy = utm_polygon_to_latlon(poly, zone, hemisphere)
        g2 = Polygon(ltlgpy)
        # Change Heading / orientation
        head_ck = 0
        if abso_yaw > head_ck:
            header = 360 - abso_yaw
        else:
            header = 360 - abso_yaw
        ngf = affinity.rotate(g2, header, origin='centroid')
        g3 = ngf.reverse().wkt
        g4 = shapely.wkt.loads(g3)
        wow3 = geojson.dumps(g4)
        wow4 = json.loads(wow3)
        gd_feat = dict(type="Feature", geometry=wow4, properties=prps)
        print(lat, lng, "\n", gd_feat)
        polys.append(gd_feat)
        bar.next()
    pop3 = geojson.dumps(over_poly)
    pop4 = json.loads(pop3)
    bar.finish()
    return polys, pop4


def decimal_degrees_to_utm(latitude, longitude):
    # Convert decimal degrees to UTM coordinates
    utm_coords = utm.from_latlon(latitude, longitude)
    zone = utm_coords[2]
    hemisphere = utm_coords[3]
    easting = utm_coords[0]
    northing = utm_coords[1]

    return zone, hemisphere, easting, northing


def convert_wgs_to_utm(poly, zone, hemisphere):
    """
    :param lon:
    :param lat:
    :return:
    """
    latlon_coords = []
    for utm_point_array in poly:
        print(" 1", utm_point_array)
        utm_x_str, utm_y_str = utm_point_array
        # print(utm_x, utm_y, utm_zone, utm_nth)
        # exit()
        utm_band = str((math.floor((utm_y_str + 180) / 6) % 60) + 1)
        if len(utm_band) == 1:
            utm_band = '0'+utm_band
        if utm_x_str >= 0:
            epsg_code = '326' + utm_band
        else:
            epsg_code = '327' + utm_band
        return epsg_code


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
