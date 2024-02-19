# Copyright (c) 2024
# Author: Dean Hand
# License: AGPL
# Version: 1.0

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
from create_geotiffs import set_raster_extents
from Utils.utils import read_sensor_dimensions_from_csv, Color

# Constants for image file extensions and the sensor information CSV file path
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".tif", ".tiff"}
SENSOR_INFO_CSV = "drone_sensors.csv"


def is_valid_directory(arg):
    if not os.path.isdir(arg):
        print(Color.RED, "\"" + arg + "\"""  is not a valid directory" + Color.END)
        exit()
    else:
        return arg

def parse_arguments():
    """
    Parse command-line arguments for processing drone imagery.

    Returns:
        argparse.Namespace: The parsed arguments with input directory, output directory, sensor width, and sensor height.
    """
    parser = argparse.ArgumentParser(description="Process drone imagery to generate GeoJSON and GeoTIFFs.")
    parser.add_argument("-i", "--indir", type=is_valid_directory, help="Path to the input directory with images.", required=True)
    parser.add_argument("-o", "--dest", help="Path to the output directory for GeoJSON and GeoTIFFs.", required=True)
    parser.add_argument("-w", "--sensorWidth", type=float, help="Sensor width in millimeters (optional).", required=False)
    parser.add_argument("-d", "--sensorHeight", type=float, help="Sensor height in millimeters (optional).", required=False)
    return parser.parse_args()

def get_image_files(directory):
    """
    Retrieve image files from the specified directory that match the defined extensions.

    Args:
        directory (str): The directory to scan for image files.

    Returns:
        List[Path]: A list of Path objects for each image file found.
    """
    return sorted(
        [file for file in Path(directory).iterdir() if file.suffix.lower() in IMAGE_EXTENSIONS],
        key=lambda x: int("".join(filter(str.isdigit, str(x.name))))
    )

def get_metadata(files):
    """
    Extract metadata from a list of image files using ExifTool.

    Args:
        files (List[Path]): Paths to the image files from which to extract metadata.

    Returns:
        List[dict]: A list of metadata dictionaries for each file.
    """
    exif_array = []
    with exiftool.ExifToolHelper() as et:
        metadata = iter(et.get_metadata(files))
    for d in metadata:
        exif_array.append(d)
    return exif_array


def process_metadata(metadata, indir_path, geotiff_dir, sensor_dimensions):
    """
    Process and convert image metadata into GeoJSON features and create GeoTIFFs.

    Args:
        metadata (List[dict]): Metadata from each image file.
        indir_path (Path): Input directory path containing the original images.
        geotiff_dir (Path): Output directory path for saving generated GeoTIFFs.
        sensor_dimensions (dict): A dictionary with sensor model keys and dimension values.

    Returns:
        dict: A GeoJSON FeatureCollection comprising features derived from the image metadata.
    """
    feature_collection = {"type": "FeatureCollection", "features": []}
    line_coordinates = []
    bar = Bar(Color.BLUE + "Images Processed" + Color.END, max=len(metadata))
    datetime_original = ""
    sensor_make = ""
    sensor_model = ""
    i = 0
    # print(metadata)
    # exit()
    for data in metadata:
        try:
            Drone_Lat = float(data.get("Composite:GPSLatitude") or data.get("EXIF:GPSLatitude"))
            Drone_Lon = float(data.get("Composite:GPSLongitude") or data.get("EXIF:GPSLongitude"))
            re_altitude = float(data.get("XMP:RelativeAltitude") or data.get("Composite:GPSAltitude"))
            GimbalRollDegree = float(
                data.get("XMP:GimbalRollDegree") or data.get("MakerNotes:CameraRoll") - 90 or data.get("XMP:Roll"))
            GimbalPitchDegree = float(
                data.get("XMP:GimbalPitchDegree") or data.get("MakerNotes:CameraPitch") or data.get("XMP:Pitch"))
            GimbalYawDegree = float(
                data.get("XMP:GimbalYawDegree") or data.get("MakerNotes:CameraYaw") or data.get("XMP:Yaw"))
            FlightPitchDegree = float(data.get("XMP:FlightPitchDegree") or data.get("MakerNotes:Pitch") or 999)
            FlightRollDegree = float(data.get("XMP:FlightRollDegree") or data.get("MakerNotes:Roll") or 999)
            FlightYawDegree = float(data.get("XMP:FlightYawDegree") or data.get("MakerNotes:Yaw") or 999)
            image_width = int(data.get("EXIF:ImageWidth") or data.get("EXIF:ExifImageWidth"))
            image_height = int(data.get("EXIF:ImageHeight") or data.get("EXIF:ExifImageHeight"))
            focal_length = float(data.get("EXIF:FocalLength"))
            file_Name = data.get("File:FileName")
            datetime_original = data.get("EXIF:DateTimeOriginal", "Unknown")
            sensor_model = data.get("EXIF:Model", "default")  # Fallback to 'default' if not found
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
            gsd = (sensor_width * re_altitude) / (focal_length * image_width)
            if FlightPitchDegree == 999:
                properties = dict(
                    File_Name=file_Name,
                    Focal_Length=focal_length,
                    Image_Width=image_width,
                    Image_Height=image_height,
                    Sensor_Model=sensor_model,
                    Sensor_Make=sensor_make,
                    relativeAltitude=re_altitude,
                    FlightYawDegree=round(GimbalYawDegree, 2),
                    FlightPitchDegree=round(GimbalPitchDegree, 2),
                    FlightRollDegree=round(GimbalRollDegree, 2),
                    DateTimeOriginal=datetime_original,
                    GimbalPitchDegree=round(GimbalPitchDegree, 2),
                    GimbalYawDegree=round(GimbalYawDegree, 2),
                    GimbalRollDegree=round(GimbalRollDegree, 2),
                    DroneCoordinates=[Drone_Lon, Drone_Lat],
                    GSD=gsd
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
                    FlightYawDegree=round(FlightYawDegree, 2),
                    FlightPitchDegree=round(FlightPitchDegree, 2),
                    FlightRollDegree=round(FlightRollDegree, 2),
                    DateTimeOriginal=datetime_original,
                    GimbalPitchDegree=round(GimbalPitchDegree, 2),
                    GimbalYawDegree=round(GimbalYawDegree, 2),
                    GimbalRollDegree=round(GimbalRollDegree, 2),
                    DroneCoordinates=[Drone_Lon, Drone_Lat],
                    Sensor_Width=sensor_width,
                    Sensor_Height=sensor_height,
                    GSD=gsd
                )
            # print(properties)
            # continue
            coord_array, FOVh, FOVv = calculate_fov(
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
            # print(fix_array)
            # continue
            closed_array = [
                (array_rw[0]),
                (array_rw[3]),
                (array_rw[2]),
                (array_rw[1]),
                (array_rw[0]),
            ]
            if i == 0 and (drone_make and drone_model):
                print(Color.PURPLE+ "Now processing images from -" + drone_make + " "
                      + drone_model + " with -" + sensor_make + " " + sensor_model
                      + " sensor" + Color.END)
            i = i + 1
            # Create the GeoTiff from JPG files
            set_raster_extents(image_path, geotiff_file, fix_array)
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
        mission_props = dict(date=datetime_original, sensor_make=sensor_make, sensor_model=sensor_model)
        lines = dict(type="Feature", geometry=line_feature, properties=mission_props)
        feature_collection["features"].insert(0, lines)
    bar.finish()
    return feature_collection


def write_geojson_file(geojson_file, geojson_dir, feature_collection):
    """
    Write the GeoJSON feature collection to a file.

    Args:
        geojson_file (str): The filename for the GeoJSON output.
        geojson_dir (Path): The directory where the GeoJSON file should be saved.
        feature_collection (dict): The GeoJSON feature collection to be written.
    """
    file_path = Path(geojson_dir) / geojson_file
    with open(file_path, "w") as file:
        geojson.dump(feature_collection, file, indent=4)


def main():
    """
    Main function to orchestrate the processing of drone imagery into GeoJSON and GeoTIFFs.
    """
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
