# Copyright (c) 2024
# Author: Dean Hand
# License: AGPL
# Version: 1.0

import sys
import argparse
import datetime
from pathlib import Path
import warnings
import exiftool
import geojson
from Utils.config import Config
from meta_data import process_metadata
from Utils.utils import read_sensor_dimensions_from_csv, Color
from Utils.logger_config import logger, init_logger
from Utils.raster_utils import create_mosaic

warnings.filterwarnings("ignore", category=FutureWarning, module="osgeo")

# Constants for image file extensions and the sensor information CSV file path
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".tif", ".tiff"}
SENSOR_INFO_CSV = "drone_sensors.csv"
RTK_EXTENSION = {".obs", ".MRK", ".bin", ".nav"}
now = datetime.datetime.now()


def is_valid_directory(arg):
    if Path(arg).is_dir():
        return arg
    print(f'{arg} is not a valid input directory')
    sys.exit()


def is_valid_file(arg):
    if Path(arg).is_file():
        return arg
    logger.warning(f'{arg} is not a valid file. Using default elevation model')
    return None


def get_image_files(directory: Path) -> list[Path]:
    """
    Retrieve image files from the specified directory that match the defined extensions.

    Args:
        directory (str): The directory to scan for image files.

    Returns:
        list[Path]: A list of Path objects for each image file found.
    """
    return sorted(
        [file for file in directory.iterdir()
         if file.suffix.lower() in IMAGE_EXTENSIONS],
        key=lambda x: int("".join(filter(str.isdigit, str(x.name)))))


def get_metadata(files: list[Path]) -> list[dict]:
    """
    Extract metadata from a list of image files using ExifTool.

    Args:
        files (list[Path]): Paths to the image files from which to extract metadata.

    Returns:
        list[dict]: A list of metadata dictionaries for each file.
    """
    exif_array = []
    with exiftool.ExifToolHelper() as et:
        metadata = iter(et.get_metadata(files))
        exif_array.extend(iter(metadata))
    if exif_array is not None and exif_array:
        return exif_array
    logger.critical("Failed to extract metadata from image files.")
    sys.exit()


def find_mtk(some_dir):
    """
    Find MTK file from input dir.

    """
    return sorted(
        [file for file in Path(some_dir).iterdir() if file.suffix.lower() in RTK_EXTENSION],
        key=lambda x: int("".join(filter(str.isdigit, str(x.name))))
    )


def write_geojson_file(geojson_file: str, geojson_dir: Path, feature_collection: dict) -> None:
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


def setup_logging(output_path: Path, nodejs: bool) -> None:
    """Configure le système de logging"""
    log_file = f"L_M_{now.strftime('%Y-%m-%d_%H-%M')}.log"
    log_path = Path(output_path) / "logfiles" / log_file


    init_logger(nodejs_graphical_interface=nodejs, log_path=log_path)


def validate_inputs(args: argparse.Namespace) -> None:
    """Valide tous les arguments d'entrée"""
    input_image_directory = Path(args.input_directory)
    output_directory_path = Path(args.output_directory)

    if not input_image_directory.is_dir():
        logger.critical(f"Input directory {input_image_directory} is not valid.")
        sys.exit()

    if not output_directory_path.is_dir():
        logger.critical(f"Output directory {output_directory_path} is not valid.")
        sys.exit()
    return input_image_directory, output_directory_path


def initialize_config(args: argparse.Namespace) -> Config:
    """Crée et initialise l'objet Config"""
    config = Config()
    config.epsg_code = args.EPSG
    config.correct_magnetic_declinaison = args.declination
    config.cog = args.COG
    config.image_equalize = args.image_equalize
    config.lense_correction = args.lense_correction
    config.global_elevation = args.elevation_service

    return config


def process_images(config: Config, input_dir: Path, sensor_dimensions: tuple, output_directory_path: Path) -> tuple:
    """Traite toutes les images"""
    files = get_image_files(input_dir)
    logger.info(f"Found {Color.PURPLE}{len(files)} image files{Color.END}{Color.BOLD} in the specified directory.{Color.END}")

    if not files:
        logger.critical("No image files found in the specified directory.")
        sys.exit()

    metadata = get_metadata(files)

    logger.info(f"Metadata Gathered for {Color.PURPLE}{len(files)} image files{Color.END}.")
    try:
        geojson_dir = Path(output_directory_path) / "geojsons"
        geotiff_dir = Path(output_directory_path) / "geotiffs"
        geojson_dir.mkdir(parents=True, exist_ok=True)
        geotiff_dir.mkdir(parents=True, exist_ok=True)
    except Exception as exception:
        logger.opt(exception=True).warning(f"Error creating directories: {exception}")


    feature_collection, nb_processed_images= process_metadata(metadata, config,input_dir, geotiff_dir, sensor_dimensions)

    return feature_collection, nb_processed_images


@logger.catch
def main() -> None:
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

    input_dir, output_dir = validate_inputs(args)

    geojson_dir = output_dir / "geojsons"

    setup_logging(output_dir, args.nodejs)

    config = initialize_config(args)
    config.rtk_file_available = bool(find_mtk(input_dir))
    config.dtm_path = Path(args.DSMPATH) if args.DSMPATH else None
    try:
        config.init_dtm_cache()
    except Exception as e:
        logger.warning(f"Failed to initialize DTM cache: {e}")
        sys.exit()

    sensor_dimensions = read_sensor_dimensions_from_csv(
        SENSOR_INFO_CSV, args.sensorWidth, args.sensorHeight
    )
    if sensor_dimensions is None:
        logger.critical("Error reading sensor dimensions from CSV.")
        sys.exit()


    feature_collection, nb_processed_images = process_images(config, input_dir, sensor_dimensions, output_dir)

    geojson_file = f"M_{now.strftime('%Y-%m-%d_%H-%M')}.json"
    write_geojson_file(geojson_file, geojson_dir, feature_collection)
    if args.nodejs:
        mosaic_path = output_dir / "mosaic"
        mosaic_path.mkdir(parents=True, exist_ok=True)
        create_mosaic(input_dir, mosaic_path)


    logger.success(f"Process Complete. {nb_processed_images} {config.geo_type} GeoTIFFs and a GeoJSON file were created.")
    logger.remove()  # Remove existing handlers


if __name__ == "__main__":
    main()
