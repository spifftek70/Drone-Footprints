#  Copyright (c) 2024.
#  __author__ = "Dean Hand"
#  __license__ = "AGPL"
#  __version__ = "1.0"

#### Created / written by Dean E. Hand (dean.e.hand@me.com).
import os
import exiftool
import argparse
import datetime
from coordinate_conversions import *
from geospatial_calculations import *
from Color_Class import Color
from operator import itemgetter
import geojson
from geojson_rewind import rewind
from shapely.geometry import Polygon
from os.path import splitext
from progress.bar import Bar


parser = argparse.ArgumentParser(description="Input Mission JSON File")
parser.add_argument("-i", "--indir", help="Input directory", required=True)
parser.add_argument("-o", "--dest", help="Output directory", required=True)
parser.add_argument("-w", "--sensorWidth", help="Sensor Width", required=False)
parser.add_argument("-d", "--sensorHeight", help="Sensor Height", required=False)
args = parser.parse_args()
indir = args.indir
outdir = args.dest
sensorWidth = args.sensorWidth
sensorHeight = args.sensorHeight
now = datetime.datetime.now()
geojson_file = "M_" + now.strftime("%Y-%m-%d_%H-%M") + ".json"


def get_metadata(files):
    exif_array = []
    with exiftool.ExifToolHelper() as et:
        metadata = iter(et.get_metadata(files))
    for d in metadata:
        exif_array.append(d)
    return exif_array


def format_data(indir_path, geotff, metadata):
    bar = Bar('Creating GeoTIFF', max=len(metadata))
    metadata.sort(key=itemgetter('EXIF:DateTimeOriginal'))
    feature_coll = dict(type="FeatureCollection", features=[])
    linecoords = []
    img_stuff = []
    sensor_model = ''
    sensor_make = ''
    datetime = ''
    i = 0
    for tags in iter(metadata):
        bar.next()
        i = i + 1
        if tags in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote', 'MPF'):
            metadata.pop(tags)
        if sensorWidth is not None:
            sensor_width = float(sensorWidth)
            sensor_height = float(sensorHeight)
        else:
            sensor_width = 13.2  # Example sensor width, adjust based on your sensor
            sensor_height = 8.8
        try:
            center_lat = float(tags['Composite:GPSLatitude'])
            center_lon = float(tags['Composite:GPSLongitude'])
        except KeyError:
            center_lat = float(tags['EXIF:GPSLatitude'])
            center_lon = float(tags['EXIF:GPSLongitude'])
        try:
            original_width = float(tags['EXIF:ImageWidth'])
            original_height = float(tags['EXIF:ImageHeight'])
        except KeyError:
            original_width = float(tags['EXIF:ExifImageWidth'])
            original_height = float(tags['EXIF:ExifImageHeight'])
        try:
            altitude = float(tags['XMP:RelativeAltitude'])
            yaw = float(tags['XMP:FlightYawDegree'])
        except KeyError:
            altitude = float(tags['EXIF:GPSAltitude'])
            yaw = float(tags["MakerNotes:Yaw"])
            # print(Color.RED + "Oops! Something went wrong. Not standard Metadata" + Color.END)
        focal_length = float(tags['EXIF:FocalLength'])
        file_Name = tags['File:FileName']
        image_path = os.path.join(indir_path, file_Name)
        if i == 1:
            datetime = tags['EXIF:DateTimeOriginal']
            sensor_model = tags['EXIF:Model']
            sensor_make = tags['EXIF:Make']
        gsd = (sensor_width * altitude) / (focal_length * original_width)
        pixel_width = pixel_height = gsd
        center_x, center_y, zone_number, hemisphere = decimal_degrees_to_utm(center_lat, center_lon)
        coord_array = calculate_gcp_list(center_x, center_y, pixel_width, pixel_height, yaw, original_width,
                                         original_height, zone_number, center_lat, center_lon, zone_number,
                                         hemisphere)

        g2 = Polygon(coord_array)
        poly = geojson.dumps(g2)
        polyed = geojson.loads(poly)
        poly_r = rewind(polyed)
        # hemisphere = hemisphere_flag(center_lat)
        output_file = splitext(file_Name)[0] + '.tif'
        geotiff_file = os.path.join(geotff, output_file)
        warp_image_with_gcp(image_path, geotiff_file, coord_array)
        coords = [float(center_lon), float(center_lat)]
        linecoords.append(coords)
        ptProps = dict(File_Name=tags['File:FileName'], Focal_Length=focal_length,
                       Image_Width=original_width, Image_Height=original_height, Sensor_Model=sensor_model,
                       Sensor_Make=sensor_make, RelativeAltitude=altitude, FlightYawDegree=yaw,
                       DateTimeOriginal=datetime)
        img_over = dict(coords=coords, props=ptProps)
        img_stuff.append(img_over)
        ptGeom = dict(type="Point", coordinates=coords)
        points = dict(type="Feature", geometry=ptGeom, properties=ptProps)
        gd_feat = dict(type="Feature", geometry=poly_r, properties=ptProps)
        feature_coll['features'].append(points)
        feature_coll['features'].append(gd_feat)
    lineGeom = dict(type="LineString", coordinates=linecoords)
    mission_props = dict(date=datetime, sensor_make=sensor_make, sensor_model=sensor_model)
    lines = dict(type="Feature", geometry=lineGeom, properties=mission_props)
    feature_coll['features'].insert(0, lines)
    bar.finish()
    return feature_coll


def writeOutputtoText(geojson_file, gjsonf, b_array):
    geojf = os.path.join(gjsonf, geojson_file)
    with open(geojf, 'w') as outfile:
        geojson.dump(b_array, outfile, indent=4, sort_keys=False)
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


def main():
    print(Color.BLUE + "Searching for Drone Images" + Color.END)
    files = find_file(indir)
    metadata = get_metadata(files)
    gjsonf = outdir + '/geojsons/'
    geotff = outdir + '/geotiffs/'
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    if not os.path.exists(gjsonf):
        os.makedirs(gjsonf)
    if not os.path.exists(geotff):
        os.makedirs(geotff)
    b_array = format_data(indir, geotff, metadata)
    print(Color.DARKCYAN + "All GeoTIFFs Created." + Color.END)
    writeOutputtoText(geojson_file, gjsonf, b_array)
    print(Color.GREEN + "Process Complete" + Color.END)


if __name__ == "__main__":
    main()