#  Copyright (c) 2024.
#  __author__ = "Dean Hand"
#  __license__ = "AGPL"
#  __version__ = "1.0"

import os
import argparse
import datetime
from pathlib import Path
import exiftool
import geojson
from geojson_rewind import rewind
from shapely.geometry import Polygon
from progress.bar import Bar
from fov_calculations import calculate_fov
from create_geotiffs import warp_image_to_gcp

# from create_raster import create_geotiffs
from utils import read_sensor_dimensions_from_csv, Color


# Constants
IMAGE_EXTENSIONS = {".jpg", ".jpeg"}
SENSOR_INFO_CSV = "drone_sensors.csv"
now = datetime.datetime.now()
geojson_file = "M_" + now.strftime("%Y-%m-%d_%H-%M") + ".json"


def parse_arguments():
    parser = argparse.ArgumentParser(description="Input Mission JSON File")
    parser.add_argument("-i", "--indir", help="Input directory", required=True)
    parser.add_argument("-o", "--dest", help="Output directory", required=True)
    parser.add_argument("-w", "--sensorWidth", help="Sensor Width", required=False)
    parser.add_argument("-d", "--sensorHeight", help="Sensor Height", required=False)
    return parser.parse_args()


def get_image_files(directory):
    image_files = [
        file
        for file in Path(directory).iterdir()
        if file.suffix.lower() in IMAGE_EXTENSIONS
    ]

    # Sort the list of image files by the digits in their filenames
    sorted_image_files = sorted(
        image_files, key=lambda x: int("".join(filter(str.isdigit, str(x.name))))
    )

    return sorted_image_files


def get_metadata(files):
    exif_array = []
    with exiftool.ExifToolHelper() as et:
        metadata = iter(et.get_metadata(files))
    for d in metadata:
        exif_array.append(d)
    return exif_array


def process_metadata(metadata, indir_path, geotiff_dir, sensor_dimensions):
    feature_collection = {"type": "FeatureCollection", "features": []}
    line_coordinates = []
    bar = Bar(Color.BLUE + "Images Processed" + Color.END, max=len(metadata))
    datetime_original = ""
    sensor_make = ""
    sensor_model = ""
    i = 0
    for data in metadata:
        file_Name = "Unknown"  # Default file name to handle cases where metadata might be missing
        try:
            Drone_Lat = float(
                data.get("Composite:GPSLatitude") or data.get("EXIF:GPSLatitude")
            )
            Drone_Lon = float(
                data.get("Composite:GPSLongitude") or data.get("EXIF:GPSLongitude")
            )
            re_altitude = float(
                data.get("XMP:RelativeAltitude") or data.get("Composite:GPSAltitude")
            )
            GimbalRollDegree = float(
                data.get("XMP:GimbalRollDegree")
                or data.get("MakerNotes:CameraRoll")
                or data.get("XMP:Roll")
            )
            GimbalPitchDegree = float(
                data.get("XMP:GimbalPitchDegree")
                or data.get("MakerNotes:CameraPitch")
                or data.get("XMP:Pitch")
            )
            GimbalYawDegree = float(
                data.get("XMP:GimbalYawDegree")
                or data.get("MakerNotes:CameraYaw")
                or data.get("XMP:Yaw")
            )
            FlightPitchDegree = float(
                data.get("XMP:FlightPitchDegree") or data.get("MakerNotes:Pitch") or 000
            )
            FlightRollDegree = float(
                data.get("XMP:FlightRollDegree") or data.get("MakerNotes:Roll") or 000
            )
            FlightYawDegree = float(
                data.get("XMP:FlightYawDegree") or data.get("MakerNotes:Yaw") or 000
            )
            image_width = int(
                data.get("EXIF:ImageWidth") or data.get("EXIF:ExifImageWidth")
            )
            image_height = int(
                data.get("EXIF:ImageHeight") or data.get("EXIF:ExifImageHeight")
            )
            focal_length = float(data.get("EXIF:FocalLength"))
            file_Name = data.get("File:FileName")
            datetime_original = data.get("EXIF:DateTimeOriginal", "Unknown")
            sensor_model = data.get(
                "EXIF:Model", "default"
            )  # Fallback to 'default' if not found
            sensor_make = data.get("EXIF:Make", "default")
            sensor_width, sensor_height, drone_make, drone_model = (
                sensor_dimensions.get(sensor_model, sensor_dimensions.get("default"))
            )
            if drone_model and drone_make is None:
                drone_model = ""
                drone_make = "Unknown Drone"
            output_file = Path(file_Name).stem + ".tif"
            geotiff_file = Path(geotiff_dir) / output_file

            temp_file1 = Path(file_Name).stem + "_temp1.tif"
            geotiff_temp_file1 = Path(geotiff_dir) / temp_file1

            image_path = os.path.join(indir_path, file_Name)

            aux_name = Path(file_Name).stem + "_temp1.tif.aux.xml"
            aux_file = Path(geotiff_dir) / aux_name

            if FlightPitchDegree == 000:
                properties = dict(
                    File_Name=file_Name,
                    Focal_Length=focal_length,
                    Image_Width=image_width,
                    Image_Height=image_height,
                    Sensor_Model=sensor_model,
                    Sensor_Make=sensor_make,
                    relativeAltitude=re_altitude,
                    FlightYawDegree=GimbalYawDegree,
                    FlightPitchDegree=GimbalPitchDegree,
                    FlightRollDegree=GimbalRollDegree,
                    DateTimeOriginal=datetime_original,
                    GimbalPitchDegree=GimbalPitchDegree,
                    GimbalYawDegree=GimbalYawDegree,
                    GimbalRollDegree=GimbalRollDegree,
                )
            else:
                properties = dict(
                    File_Name=file_Name,
                    Focal_Length=focal_length,
                    Image_Width=image_width,
                    Image_Height=image_height,
                    Sensor_Model=sensor_model,
                    Sensor_Make=sensor_make,
                    relativeAltitude=re_altitude,
                    FlightYawDegree=FlightYawDegree,
                    FlightPitchDegree=FlightPitchDegree,
                    FlightRollDegree=FlightRollDegree,
                    DateTimeOriginal=datetime_original,
                    GimbalPitchDegree=GimbalPitchDegree,
                    GimbalYawDegree=FlightYawDegree,
                    GimbalRollDegree=GimbalRollDegree,
                )

            coord_array = calculate_fov(
                re_altitude,
                focal_length,
                sensor_width,
                sensor_height,
                GimbalRollDegree,
                GimbalPitchDegree,
                FlightYawDegree,
                Drone_Lat,
                Drone_Lon,
            )
            polygon = Polygon(coord_array)
            geojson_polygon = geojson.dumps(polygon)
            rewound_polygon = rewind(geojson.loads(geojson_polygon))
            array_rw = rewound_polygon["coordinates"][0]
            fix_array = [
                (coord_array[1]),
                (coord_array[2]),
                (coord_array[3]),
                (coord_array[0]),
            ]
            closed_array = [
                (array_rw[0]),
                (array_rw[3]),
                (array_rw[2]),
                (array_rw[1]),
                (array_rw[0]),
            ]
            if i == 0 and (drone_make and drone_model):
                print(
                    Color.PURPLE
                    + "Now processing images from -"
                    + drone_make
                    + " "
                    + drone_model
                    + " with -"
                    + sensor_make
                    + " "
                    + sensor_model
                    + " sensor"
                    + Color.END
                )
            i = i + 1
            # Create the GeoTiff from JPG files
            warp_image_to_gcp(image_path, geotiff_file, fix_array)
            # create_geotiffs(image_path, geotiff_temp_file1, geotiff_file, fix_array)
            type_point = dict(type="Point", coordinates=[Drone_Lon, Drone_Lat])
            type_polygon = dict(type="Polygon", coordinates=[closed_array])
            feature_point = dict(
                type="Feature", geometry=type_point, properties=properties
            )
            feature_polygon = dict(
                type="Feature", geometry=type_polygon, properties=properties
            )
            feature_collection["features"].append(feature_point)
            feature_collection["features"].append(feature_polygon)
            line_coordinates.append([Drone_Lon, Drone_Lat])
            # os.remove(geotiff_temp_file1)
            # os.remove(aux_file)
        except KeyError as e:
            print(Color.RED + f"Error processing {file_Name}: {e}" + Color.END)

        bar.next()
    if line_coordinates:
        line_feature = dict(type="LineString", coordinates=line_coordinates)
        mission_props = dict(
            date=datetime_original, sensor_make=sensor_make, sensor_model=sensor_model
        )
        lines = dict(type="Feature", geometry=line_feature, properties=mission_props)
        feature_collection["features"].insert(0, lines)
    bar.finish()
    return feature_collection


def write_geojson_file(geojson_file, geojson_dir, feature_collection):
    file_path = Path(geojson_dir) / geojson_file
    with open(file_path, "w") as file:
        geojson.dump(feature_collection, file, indent=4)


def main():
    args = parse_arguments()
    indir, outdir = args.indir, args.dest
    sensor_width, sensor_height = args.sensorWidth, args.sensorHeight

    files = get_image_files(indir)
    metadata = get_metadata(files)
    print(Color.YELLOW + "Metadata Gathered" + Color.END)
    geojson_dir = Path(outdir) / "geojsons"
    geotiff_dir = Path(outdir) / "geotiffs"
    geojson_dir.mkdir(parents=True, exist_ok=True)
    geotiff_dir.mkdir(parents=True, exist_ok=True)

    sensor_dimensions = read_sensor_dimensions_from_csv(
        SENSOR_INFO_CSV, sensor_width, sensor_height
    )
    feature_collection = process_metadata(
        metadata, indir, geotiff_dir, sensor_dimensions
    )

    now = datetime.datetime.now()
    geojson_file = f"M_{now.strftime('%Y-%m-%d_%H-%M')}.json"
    write_geojson_file(geojson_file, geojson_dir, feature_collection)
    print(Color.GREEN + "Process Complete" + Color.END)


if __name__ == "__main__":
    main()
