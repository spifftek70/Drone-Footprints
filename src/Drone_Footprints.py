# Copyright (c) 2024
# Author: Dean Hand
# License: AGPL
# Version: 1.0

import os
import sys
import argparse
import datetime
from pathlib import Path
import warnings
import exiftool
import geojson
from meta_data import process_metadata
from Utils.utils import read_sensor_dimensions_from_csv, Color
from Utils.logger_config import *
from Utils.raster_utils import create_mosaic
import Utils.config as config
from typing import List
from imagedrone import ImageDrone

warnings.filterwarnings("ignore", category=FutureWarning, module="osgeo")

# Constants for image file extensions and the sensor information CSV file path
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".tif", ".tiff"}
SENSOR_INFO_CSV = "drone_sensors.csv"
RTK_EXTENSION = {".obs", ".MRK", ".bin", "nav"}
now = datetime.datetime.now()


def is_valid_directory(arg):
    if os.path.isdir(arg):
        return arg
    # print(f'{arg} is not a valid input directory')
    sys.exit()


def is_valid_file(arg):
    if os.path.isfile(arg):
        return arg
    print(f'{arg}  is not a valid file.  Switching to Default elevation model')
    return

  
def get_image_files(directory:str)->list[Path]:
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


def get_metadata(files:List[Path])->List[dict]:
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
        exif_array.extend(iter(metadata))
    if exif_array is not None and exif_array:
        return exif_array
    logger.critical("Failed to extract metadata from image files.")
    sys.exit()


def find_MTK(some_dir):
    """
    Find MTK file from input dir.

    """
    return sorted(
        [file for file in Path(some_dir).iterdir() if file.suffix.lower() in RTK_EXTENSION],
        key=lambda x: int("".join(filter(str.isdigit, str(x.name))))
    )


def write_geojson_file(geojson_file, geojson_dir, feature_collection):
    """
    Write the GeoJSON feature collection to a file.

    Args:
        geojson_file (str): The filename for the GeoJSON output.
        geojson_dir (Path): The directory where the GeoJSON file should be saved.
        feature_collection (dict): The GeoJSON feature collection to be written.
    """
    file_path = Path(geojson_dir) / geojson_file
    try:
        with open(file_path, "w") as file:
            geojson.dump(feature_collection, file, indent=4)
    except Exception as e:
        logger.critical(f"Error writing GeoJSON file: {e}")


@logger.catch
def main():
    """
    Main function to orchestrate the processing of drone imagery into GeoJSON and GeoTIFFs.
    """
    parser = argparse.ArgumentParser(description="Process drone imagery to generate GeoJSON and GeoTIFFs.")
    parser.add_argument("-o", "--output_directory", help="Path to the output directory for GeoJSON and GeoTIFFs.",
                        required=True)
    parser.add_argument("-i", "--input_directory", type=is_valid_directory,
                        help="Path to the input directory with images.",
                        required=True)
    parser.add_argument("-w", "--sensorWidth", type=float, help="Sensor width in millimeters (optional).",
                        required=False)
    parser.add_argument("-t", "--sensorHeight", type=float, help="Sensor height in millimeters (optional).",
                        required=False)
    parser.add_argument("-e", "--EPSG", type=int, default=4326, help="Desired EPSG code for output files (optional).",
                        required=False)
    parser.add_argument("-d", "--declination", action='store_true', required=False,
                        help="Correct images using local magnetic declination (optional).")
    parser.add_argument("-c", "--COG", action='store_true', required=False,
                        help="Cloud Optimized GeoTIFF (COG) for output tiff files (optional).")
    parser.add_argument("-z", "--image_equalize", action='store_true', required=False,
                        help="Improve local contrast option to can make details more visible (optional).")
    parser.add_argument("-l", "--lense_correction", action='store_true', required=False,
                        help="Applies lens distortion correction using lensfun api (optional).")
    parser.add_argument("-n", "--nodejs", action='store_true', required=False,
                        help="Experimental Nodejs graphical interface (optional).")

    # Add mutually exclusive arguments
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--DSMPATH", type=is_valid_file, help="Path to DSM file (optional).",
                       default="", required=False)
    group.add_argument("-m", "--elevation_service", action='store_true', required=False,
                       help="Use elevation services APIs (optional).")

    args = parser.parse_args()

    outer_path = args.output_directory
    log_file = f"L_M_{now.strftime('%Y-%m-%d_%H-%M')}.log"
    log_path = Path(outer_path) / "logfiles" / log_file
    config.update_nodejs_graphical_interface(args.nodejs)
    init_logger(log_path=log_path)

   
    # Access the arguments
    if args.DSMPATH:
        pass
    elif args.elevation_service:
        pass
    elif args.DSMPATH:
        logger.exception("")
    else:
        pass

    user_args = dict(vars(args))
    args_list = []
    for arg, value in user_args.items():
        if value != parser.get_default(arg):
            args_list.append(f"     {Color.PURPLE}{Color.BOLD}{arg}{Color.END}: {Color.BOLD}{value}{Color.END}")

    # Joining all the elements in the list into a single string with newline characters
    args_str = "\n".join(args_list)
    logger.info(f"{Color.ORANGE}{Color.BOLD}User arguments{Color.END} - \n{args_str}")
    # logger.exception(f"User arguments - {user_args}")
    indir, outdir = args.input_directory, args.output_directory
    sensor_width, sensor_height = args.sensorWidth, args.sensorHeight
    logger.info(f"{Color.PURPLE}Initializing {Color.END}{Color.BOLD}the Processing of Drone Footprints" + Color.END)

    config.update_epsg(args.EPSG)
    config.update_correct_magnetic_declinaison(args.declination)
    config.update_cog(args.COG)
    config.update_equalize(args.image_equalize)
    config.update_lense(args.lense_correction)
    config.update_elevation(args.elevation_service)
    rtk_rtn = find_MTK(indir)
    if rtk_rtn:
        config.update_rtk(True)
    config.update_dtm(args.DSMPATH)
    files = get_image_files(indir)
    logger.info(
        f"Found {Color.PURPLE}{len(files)} image files{Color.END}{Color.BOLD} in the specified directory." + Color.END)
    if files is None or len(files) == 0:
        logger.critical("No image files found in the specified directory.")
        sys.exit()
    metadata = get_metadata(files)
    logger.info(f"Metadata Gathered for {Color.PURPLE}{len(files)} image files{Color.END}.")
    try:
        geojson_dir = Path(outdir) / "geojsons"
        geotiff_dir = Path(outdir) / "geotiffs"
        geojson_dir.mkdir(parents=True, exist_ok=True)
        geotiff_dir.mkdir(parents=True, exist_ok=True)
    except Exception as exception:
        logger.opt(exception=True).warning(f"Error creating directories: {exception}")

    sensor_dimensions = read_sensor_dimensions_from_csv(
        SENSOR_INFO_CSV, sensor_width, sensor_height
    )
    if sensor_dimensions is None:
        logger.critical("Error reading sensor dimensions from CSV.")
        sys.exit()
    else:
        feature_collection, images_array= process_metadata(
            metadata, indir, geotiff_dir, sensor_dimensions
        )
    geojson_file = f"M_{now.strftime('%Y-%m-%d_%H-%M')}.json"
    write_geojson_file(geojson_file, geojson_dir, feature_collection)
    if args.nodejs:
        mosaic_path = Path(outdir) / "mosaic"
        mosaic_path.mkdir(parents=True, exist_ok=True)
        create_mosaic(indir, mosaic_path)

    if config.cog is True:
        geo_type = "Cloud Optimized"
    else:
        geo_type = "standard"

    logger.success(f"Process Complete. {len(images_array)} {geo_type} GeoTIFFs and a GeoJSON file were created.")
    logger.remove()  # Remove existing handlers


if __name__ == "__main__":
    main()
