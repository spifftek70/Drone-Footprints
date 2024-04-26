import os
from dataclasses import dataclass,field
from pathlib import Path
import geojson
from geojson_rewind import rewind
from shapely.geometry import Polygon
import Utils.config as config
from create_geotiffs import generate_geotiff
from typing import List


@dataclass
class ImageDrone:
    metadata : dict
    sensor_dimensions : tuple
    config: config
    feature_point : dict = field(default_factory=dict)
    feature_polygon : dict = field(default_factory=dict)
    coord_array : list = field(default_factory=list)
    footprint_coordinates : list = field(default_factory=list)

    def __post_init__(self):
        self.file_name = str(self.metadata.get("File:FileName"))

        # Extract detailed sensor and drone info for the current image
        # Extracting latitude, longitude, and altitude details
        self.latitude = float(self.metadata.get("Composite:GPSLatitude")
                                or self.metadata.get("EXIF:GPSLatitude"))
        self.longitude = float(self.metadata.get("Composite:GPSLongitude")
                                or self.metadata.get("EXIF:GPSLongitude"))
        self.focal_length = float(self.metadata.get("EXIF:FocalLength"))
        self.focal_length35mm = float(self.metadata.get("EXIF:FocalLengthIn35mmFormat"))

        self.relative_altitude = float(self.metadata.get("XMP:RelativeAltitude")
                                        or self.metadata.get("Composite:GPSAltitude"))
        self.absolute_altitude = float(self.metadata.get("XMP:AbsoluteAltitude")
                                        or self.metadata.get("Composite:GPSAltitude"))

        # Extracting gimbal and flight orientation details
        self.gimbal_roll_degree = float(
            self.metadata.get("XMP:GimbalRollDegree") or
            self.metadata.get("MakerNotes:CameraRoll") or self.metadata.get("XMP:Roll"))
        self.gimbal_pitch_degree = float(
            self.metadata.get("XMP:GimbalPitchDegree") or
            self.metadata.get("MakerNotes:CameraPitch") or self.metadata.get("XMP:Pitch"))
        self.gimbal_yaw_degree = float(
            self.metadata.get("XMP:GimbalYawDegree") or
            self.metadata.get("MakerNotes:CameraYaw") or self.metadata.get("XMP:Yaw"))
        self.flight_pitch_degree = float(self.metadata.get("XMP:FlightPitchDegree")
                                         or self.metadata.get("MakerNotes:Pitch"))
        self.flight_roll_degree = float(self.metadata.get("XMP:FlightRollDegree")
                                        or self.metadata.get("MakerNotes:Roll"))
        self.flight_yaw_degree = float(self.metadata.get("XMP:FlightYawDegree")
                                       or self.metadata.get("MakerNotes:Yaw"))

        if self.flight_pitch_degree is None : self.flight_pitch_degree = self.gimbal_pitch_degree
        if self.flight_roll_degree is None : self.flight_roll_degree = self.gimbal_roll_degree
        if self.flight_yaw_degree is None : self.flight_yaw_degree = self.gimbal_yaw_degree



        # Extracting image and sensor details
        self.image_width = int(self.metadata.get("EXIF:ImageWidth")
                               or self.metadata.get("EXIF:ExifImageWidth",1.0)) # pixels
        self.image_height = int(self.metadata.get("EXIF:ImageHeight",1.0)
                                or self.metadata.get("EXIF:ExifImageHeight")) # pixels
        self.focal_length = float(self.metadata.get("EXIF:FocalLength"))
        self.max_aerture_value = self.metadata.get("EXIF:MaxApertureValue")
        # date/time of original image capture
        self.datetime_original = self.metadata.get("EXIF:DateTimeOriginal")
        # Get sensor model and rig camera index from metadata
        self.sensor_model_data = self.metadata.get("EXIF:Model")
        self.sensor_index = str(self.metadata.get("XMP:RigCameraIndex")
                                or self.metadata.get('XMP:SensorIndex','nan'))

        if self.sensor_model_data :
            # Prioritize direct match with sensor model and rig camera index
            key = (self.sensor_model_data, self.sensor_index)
            self.sensor_info = self.sensor_dimensions.get((key))
            #from IPython import embed; embed()
            # If no direct match, try just with sensor model (for cases without multiple entries)
            if self.sensor_info is None :
                self.sensor_info = next(
                    (value for (model, idx), value in self.sensor_dimensions.items() if model == self.sensor_model_data), None)
        else:
            # Use default when sensor_model_data is 'default'
            self.sensor_info = self.sensor_dimensions.get(("default", 'nan'))

        # Ensure we have valid sensor_info; otherwise, log error or take necessary action
        if not self.sensor_info:
#            logger.error(
            print(f"No sensor information found for {self.file_name} with sensor model {self.sensor_model_data} and rig camera index {self.sensor_index}. Using defaults.")
            self.sensor_info = self.sensor_dimensions.get(("default", 'nan'))

        self.drone_make = self.sensor_info[0]
        self.drone_model = self.sensor_info[1]
        self.camera_make = self.sensor_info[2]
        self.sensor_model = self.sensor_info[3]
        self.cam_index = self.sensor_info[4]
        self.sensor_width = self.sensor_info[5]
        self.sensor_height = self.sensor_info[6]
        self.lens_FOV_width = self.sensor_info[7]
        self.lens_FOV_height = self.sensor_info [8]


        # Special case
        if self.sensor_model in ["FC2103", "FC220", "FC300X", "FC200"]:
            self.sensor_model = f"{self.drone_model} {self.sensor_model}"

        if self.sensor_model and self.drone_make is None:
            self.drone_model = ""
            self.drone_make = "Unknown Drone"

        self.gsd = (self.sensor_width * self.relative_altitude) / (self.focal_length * self.image_width)


    def generate_geotiff(self,indir_path:str, geotiff_dir:str):
        """
         Generate GeoTIFF file image
        """
        image_path = os.path.join(indir_path, self.file_name)
        output_file = f"{Path(self.file_name).stem}.tif"
        geotiff_file = Path(geotiff_dir) / output_file
        generate_geotiff(image_path, geotiff_file, self.coord_array)


    def create_geojson_feature(self, properties):
        """
        Create GeoJSON features from image metadata.

        """
        # Properties setup and other related processing goes here.
        # This is simplified to focus on structure. Implement as needed based on the original function.

        geojson_polygon = geojson.dumps(Polygon(self.footprint_coordinates))
        rewound_polygon = rewind(geojson.loads(geojson_polygon))
        array_rw = rewound_polygon["coordinates"][0]
        closed_array = [
            (array_rw[0]),
            (array_rw[3]),
            (array_rw[2]),
            (array_rw[1]),
            (array_rw[0]),
        ]
        type_point = dict(type="Point", coordinates=[self.longitude, self.latitude])
        type_polygon = dict(type="Polygon", coordinates=[closed_array])
        self.feature_point = dict(type="Feature", geometry=type_point, properties=properties)
        self.feature_polygon = dict(type="Feature", geometry=type_polygon, properties=properties)
