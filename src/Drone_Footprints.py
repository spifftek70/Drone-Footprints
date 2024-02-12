#  Copyright (c) 2024.
#  __author__ = "Dean Hand"
#  __license__ = "AGPL"
#  __version__ = "1.0"

#### Created / written by Dean E. Hand (dean.e.hand@me.com).
import os
import exiftool
import argparse
import datetime
# from geospatial_calculations_nadir import *
from geospatial_calculations_nonnadir import calculate_fov
from create_geotiffs import warp_image_with_gcp
from Color_Class import Color
from operator import itemgetter
import geojson
from geojson_rewind import rewind
from shapely.geometry import Polygon
from os.path import splitext
from progress.bar import Bar
# from PPK_Process import find_MTK


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
    # ppk_meta = find_MTK(indir_path, metadata)
    for tags in iter(metadata):
        # print(tags)
        # exit()
        bar.next()
        i = i + 1
        if tags in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote', 'MPF'):
            metadata.pop(tags)
        if sensorWidth is not None:
            sensor_width = float(sensorWidth)
            sensor_height = float(sensorHeight)
        else:
            sensor_width = 13.2  # Example sensor width, adjust based on your sensor
            sensor_height = 8.8 # future non-nadir work
        try:
            center_lat = float(tags['Composite:GPSLatitude'])
            center_lon = float(tags['Composite:GPSLongitude'])
        except KeyError:
            center_lat = float(tags['EXIF:GPSLatitude'])
            center_lon = float(tags['EXIF:GPSLongitude'])
        try:
            original_width = int(tags['EXIF:ImageWidth'])
            original_height = int(tags['EXIF:ImageHeight'])
        except KeyError:
            original_width = int(tags['EXIF:ExifImageWidth'])
            original_height = int(tags['EXIF:ExifImageHeight'])
        try:
            re_altitude = float(tags['XMP:RelativeAltitude'])
            ab_altitude = float(tags['XMP:AbsoluteAltitude'])
            FlightPitchDegree = float(tags['XMP:FlightPitchDegree']) # future non-nadir work
            FlightRollDegree = float(tags['XMP:FlightRollDegree']) # future non-nadir work
            FlightYawDegree = float(tags['XMP:FlightYawDegree'])
            GimbalPitchDegree = float(tags['XMP:GimbalPitchDegree']) # future non-nadir work
            GimbalRollDegree = float(tags['XMP:GimbalRollDegree']) # future non-nadir work
            GimbalYawDegree = float(tags['XMP:GimbalYawDegree']) # future non-nadir work
        except KeyError:
            re_altitude = float(tags['Composite:GPSAltitude'])
            # FlightYawDegree = float(tags["MakerNotes:Yaw"])
            GimbalPitchDegree = float(tags["XMP:Pitch"])
            GimbalRollDegree = float(tags["XMP:Roll"])
            FlightYawDegree = float(tags["XMP:Yaw"])
        focal_length = float(tags['EXIF:FocalLength'])
        file_Name = tags['File:FileName']
        image_path = os.path.join(indir_path, file_Name)
        # if i == 1:
        datetime = tags['EXIF:DateTimeOriginal']
        sensor_model = tags['EXIF:Model']
        sensor_make = tags['EXIF:Make']
        # center_x, center_y, zone_number, hemisphere = decimal_degrees_to_utm(center_lat, center_lon)
        # gsd = (sensor_width * altitude) / (focal_length * original_width)
        # pixel_width = pixel_height = gsd
        # coord_array = calculate_footprints_nadir(center_x, center_y, pixel_width, pixel_height, FlightYawDegree,
        #                                          original_width, original_height, zone_number, center_lat)
        # print("\n\nfile name= ", file_Name, "\n\nfocal_length=", focal_length, "\naltitude=", re_altitude, "\nGimbalRollDegree=", GimbalRollDegree,
        #       "\nGimbalYawDegree=", GimbalYawDegree, "\nYaw_degree_fixed= ", GimbalYawDegree, "\nGimbalPitchDegree=", GimbalPitchDegree,
        #       "\nFlightRollDegree=", FlightRollDegree, "\nFlightYawDegree=", FlightYawDegree, "\nFlightPitchDegree=", FlightPitchDegree,
        #       "\nDrone Lon=", center_lon, "\nDrone lat=", center_lat, "\nsensor_width=", sensor_width,
        #       "\nsensor_height =", sensor_height, "\noriginal_width =", original_width, "\noriginal_height=", original_height, "\n\n")
        # continue
        coord_array = calculate_fov(re_altitude, focal_length, sensor_width, sensor_height,
                                    GimbalRollDegree, GimbalPitchDegree, FlightYawDegree,
                                    center_lat, center_lon)
        # print(coord_array)
        # continue
        g2 = Polygon(coord_array)
        poly = geojson.dumps(g2)
        polyed = geojson.loads(poly)
        poly_r = rewind(polyed)
        output_file = splitext(file_Name)[0] + '.tif'
        geotiff_file = os.path.join(geotff, output_file)
        warp_image_with_gcp(image_path, geotiff_file, coord_array, original_width, original_height)
        coords = [float(center_lon), float(center_lat)]
        linecoords.append(coords)
        ptProps = dict(File_Name=tags['File:FileName'], Focal_Length=focal_length,
                       Image_Width=original_width, Image_Height=original_height, Sensor_Model=sensor_model,
                       Sensor_Make=sensor_make, relativeAltitude=re_altitude, FlightYawDegree=FlightYawDegree,
                       FlightPitchDegree=FlightPitchDegree, FlightRollDegree=FlightRollDegree,
                       DateTimeOriginal=datetime, GimbalPitchDegree=GimbalPitchDegree, GimbalYawDegree=GimbalYawDegree,
                       GimbalRollDegree=GimbalRollDegree)
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
    if len(matches) == 0:
        print(Color.RED + "No image files found" + Color.END)
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
