#### Created / written by Dean E. Hand (dean.e.hand@me.com).
from __future__ import division
import os
import geojson
from os.path import splitext
import argparse
import exiftool
import datetime
from operator import itemgetter
from progress.bar import Bar
from Create_GeoTiffs import create_georaster
from Color_Class import Color
# from RTK_Process import find_MTK
from Create_Polygons import image_poly


parser = argparse.ArgumentParser(description="Input Mission JSON File")
parser.add_argument("-i", "--indir", help="Input directory", required=True)
parser.add_argument("-o", "--dest", help="Output directory", required=True)
parser.add_argument("-g", "--geoTIFF", help="geoTIFF output", required=True)
parser.add_argument("-w", "--sensorWidth", help="Sensor Width", required=False)
parser.add_argument("-d", "--sensorHeight", help="Sensor Height", required=False)
args = parser.parse_args()
indir = args.indir
outdir = args.dest
geo_tiff = args.geoTIFF
sensorWidth = args.sensorWidth
sensorHeight = args.sensorHeight
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
    # rtkMod = find_MTK(indir, exif_array)
    # if rtkMod is None:
    #     tagz = rtkMod
    # else:
    #     tagz = exif_array
    for tags in iter(exif_array):
        # print(tags)
        # exit()
        i = i + 1
        for tag, val in tags.items():
            if tag in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote', 'MPF'):
                exif_array.pop(tag)
        try:
            lat = float(tags['Composite:GPSLatitude'])
            long = float(tags['Composite:GPSLongitude'])
        except KeyError:
            lat = float(tags['EXIF:GPSLatitude'])
            long = float(tags['EXIF:GPSLongitude'])
        try:
            imgwidth = float(tags['EXIF:ImageWidth'])
            imghite = float(tags['EXIF:ImageHeight'])
        except KeyError:
            imgwidth = float(tags['EXIF:ExifImageWidth'])
            imghite = float(tags['EXIF:ExifImageHeight'])
        try:
            FlightAltitude = float(tags['XMP:RelativeAltitude'])
            FlightRollDegree = float(tags['XMP:FlightRollDegree'])
            FlightYawDegree = float(tags['XMP:FlightYawDegree'])
            FlightPitchDegree = float(tags['XMP:FlightPitchDegree'])
            GimbalRollDegree = float(tags['XMP:GimbalRollDegree'])
            GimbalYawDegree = float(tags['XMP:GimbalYawDegree'])
            GimbalPitchDegree = float(tags['XMP:GimbalPitchDegree'])
        except:
            print(Color.RED + "Oops! Something went wrong. The metadata for Altitude, "
                              "Roll, Pitch and Yaw were not found." + Color.END)
        if i == 1:
            datetime = tags['EXIF:DateTimeOriginal']
            sensor = tags['EXIF:Model']
            sensor_make = tags['EXIF:Make']
        coords = [float(long), float(lat)]
        linecoords.append(coords)
        ptProps = dict(File_Name=tags['File:FileName'], Focal_Length=tags['EXIF:FocalLength'],
                   Image_Width = imgwidth, Image_Height = imghite,
                   RelativeAltitude = FlightAltitude,
                   FlightRollDegree = FlightRollDegree, FlightYawDegree = FlightYawDegree,
                   FlightPitchDegree = FlightPitchDegree,
                   GimbalRollDegree = GimbalRollDegree, GimbalYawDegree = GimbalYawDegree,
                   GimbalPitchDegree = GimbalPitchDegree,
                   DateTimeOriginal = datetime)
        img_over = dict(coords=coords, props=ptProps)
        img_stuff.append(img_over)
        ptGeom = dict(type="Point", coordinates=coords)
        points = dict(type="Feature", geometry=ptGeom, properties=ptProps)
        feature_coll['features'].append(points)
        bar.next()
    img_box = image_poly(img_stuff, sensorWidth, sensorHeight)
    tiles = img_box[0]
    polyArray = img_box[1]
    if geo_tiff == 'y':
        create_georaster(tiles, indir)
        # make_GeoTiFFs(polyArray, indir)
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
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    with open(dst_n, 'w') as outfile:
        geojson.dump(file_list, outfile, indent=4, sort_keys=False)
    print(Color.YELLOW + "GeoJSON File Created." + Color.END)
    return


def find_file(some_dir):
    matches = []
    for filename in os.listdir(some_dir):
        if splitext(filename)[1].lower() in {'.jpg'}:
            files = os.path.join(some_dir, filename)
            matches.append(files)
    matches.sort(key=lambda x: int(''.join(filter(str.isdigit, x))))
    return matches


if __name__ == "__main__":
    main()