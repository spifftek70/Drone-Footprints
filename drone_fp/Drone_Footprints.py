from __future__ import division
import os
import geojson
import fnmatch
import argparse
import exiftool
import datetime
from operator import itemgetter
from progress.bar import Bar
from Create_GeoTiffs import create_georaster
from Create_Polygons import image_poly
from Color_Class import Color


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


def main():
    files = find_file(indir)
    read_exif(files)


def read_exif(files):
    exif_array = []
    filename = file_name
    bar = Bar('Reading EXIF Data', max=len(files))
    with exiftool.ExifToolHelper() as et:
        metadata = iter(et.get_metadata(files))
    for d in metadata:
        exif_array.append(d)
        bar.next()
    bar.finish()
    print(Color.BLUE + "Scanning images complete " + Color.END)
    formatted = format_data(exif_array)
    writeOutputtoText(filename, formatted)
    print(Color.GREEN + "Process Complete." + Color.END)


def format_data(exif_array):
    print(Color.PURPLE + "Formatting Data For Calculations and GeoJSON." + Color.END)
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
        create_georaster(tiles, indir)
    else:
        print(Color.RED + "Georasters Not Requested" + Color.END)
    lineGeom = dict(type="LineString", coordinates=linecoords)
    mission_props = dict(date=datetime, platform="DJI Mavic 2 Pro", sensor_make=sensor_make, sensor=sensor)
    lines = dict(type="Feature", geometry=lineGeom, properties=mission_props)
    feature_coll['features'].insert(0, lines)
    feature_coll['features'].insert(0, tiles[0])
    for imps in tiles:
        feature_coll['features'].append(imps)
    bar.finish()
    print(Color.PURPLE + "Full GeoJSON Formatted." + Color.END)
    return feature_coll


def writeOutputtoText(filename, file_list):
    dst_n = outdir + '/' + filename
    with open(dst_n, 'w') as outfile:
        geojson.dump(file_list, outfile, indent=4, sort_keys=False)
    print(Color.YELLOW + "GeoJSON File Created." + Color.END)
    return


def find_file(some_dir):
    matches = []
    for root, dirnames, filenames in os.walk(some_dir):
        for filename in fnmatch.filter(filenames, '*.JPG'):
            matches.append(os.path.join(root, filename))
    return matches


if __name__ == "__main__":
    main()
