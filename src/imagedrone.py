import os
from dataclasses import dataclass,field
from pathlib import Path
from datetime import datetime
import geojson
from geojson_rewind import rewind
from magnetic_field_calculator import MagneticFieldCalculator
import magnetismi.magnetismi as api
from shapely.geometry import Polygon
from Utils.utils import Color
from Utils import config
from create_geotiffs import set_raster_extents


@dataclass
class ImageDrone:
    metadata : dict
    sensor_dimensions : tuple
    config: config
    declination : float = None
    drone_hash : int = None
    feature_point : dict = field(default_factory=dict)
    feature_polygon : dict = field(default_factory=dict)
    properties : dict = field(default_factory=dict)
    coord_array : list = field(default_factory=list)
    footprint_coordinates : list = field(default_factory=list)
    image_path : str = ""
    output_file : str = ""
    geotiff_file : str = ""

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
                                         or self.metadata.get("MakerNotes:Pitch")or 999)
        self.flight_roll_degree = float(self.metadata.get("XMP:FlightRollDegree")
                                        or self.metadata.get("MakerNotes:Roll")or 999)
        self.flight_yaw_degree = float(self.metadata.get("XMP:FlightYawDegree")
                                       or self.metadata.get("MakerNotes:Yaw")or 999)
        if self.flight_pitch_degree is None : self.flight_pitch_degree = self.gimbal_pitch_degree
        if self.flight_roll_degree is None : self.flight_roll_degree = self.gimbal_roll_degree
        if self.flight_yaw_degree is None : self.flight_yaw_degree = self.gimbal_yaw_degree

        # Extracting image and sensor details
        self.image_width = int(self.metadata.get("EXIF:ImageWidth")
                               or self.metadata.get("EXIF:ExifImageWidth")) # pixels
        self.image_height = int(self.metadata.get("EXIF:ImageHeight")
                                or self.metadata.get("EXIF:ExifImageHeight")) # pixels
        self.focal_length = float(self.metadata.get("EXIF:FocalLength"))
        self.max_aperture_value = self.metadata.get("EXIF:MaxApertureValue")
        # date/time of original image capture
        self.datetime_original = self.metadata.get("EXIF:DateTimeOriginal")
        # Get sensor model and rig camera index from metadata
        self.sensor_model_data = self.metadata.get("EXIF:Model")
        self.sensor_index = str(self.metadata.get("XMP:RigCameraIndex")
                                or self.metadata.get('XMP:SensorIndex'))
        self.sensor_make = ""


        if self.sensor_model_data :
            # DJI Phantom4 and DJI Phantom4 RTK have the same sensor and lens
            if self.sensor_model_data == "FC6310R":
                self.sensor_model_data = "FC6310"

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
#               f"No sensor information found for {self.im_file_name} with sensor model {self.sensor_model_data} and rig camera index {self.sensor_index}. Using defaults.")
            print(f"No sensor information found for {self.im_file_name} with sensor model {self.sensor_model_data} and rig camera index {self.sensor_index}. Using defaults.")

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
        self.create_properties()
        self.create_hash()



#def find_declination(altitude, focal_length, drone_latitude, drone_longitude, datetime_original):
    def find_declination(self):
        str_date = datetime.strptime(self.datetime_original, '%Y:%m:%d %H:%M:%S')

        if str(str_date.year) > str(2019):
            mag_date = api.dti.date(str_date.year, str_date.month, str_date.day)
            # Find the magnetic declination reference
            model = api.Model(mag_date.year)
            field_point = model.at(lat_dd=self.latitude, lon_dd=self.longitude, alt_ft=self.relative_altitude, date=mag_date)
            declination = field_point.dec
        else:
            calculator = MagneticFieldCalculator()
            model = calculator.calculate(latitude=self.latitude, longitude=self.longitude)
            dec = model['field-value']['declination']
            declination = dec['value']

        if self.relative_altitude < 0 or self.focal_length <= 0:
            config.pbar.write(Color.RED + ValueError("Altitude and focal length must be positive.") + Color.END)
        self.declination=declination



    def generate_geotiff(self,indir_path:str, geotiff_dir:str,logger):
        """
         Generate GeoTIFF file image
        """
        self.image_path = os.path.join(indir_path, self.file_name)
        self.output_file = f"{Path(self.file_name).stem}.tif"
        self.geotiff_file = Path(geotiff_dir) / self.output_file
        #generate_geotiff(image_path, geotiff_file, self.coord_array)
        try:
            set_raster_extents(self)
        except ValueError as e:
            logger.opt(exception=True).warning(str(e))





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

    def create_properties(self):
        self.properties = dict(
            File_Name=self.file_name,
            Focal_Length=self.focal_length,
            Image_Width=self.image_width,
            Image_Height=self.image_height,
            Sensor_Model=self.sensor_model,
            Sensor_index=self.sensor_index,
            Sensor_Make=self.sensor_make,
            RelativeAltitude=self.relative_altitude,
            AbsoluteAltitude=self.absolute_altitude,
            FlightYawDegree=self.flight_yaw_degree,
            FlightPitchDegree=self.flight_pitch_degree,
            FlightRollDegree=self.flight_roll_degree,
            DateTimeOriginal=self.datetime_original,
            GimbalPitchDegree=self.gimbal_pitch_degree,
            GimbalYawDegree=self.gimbal_yaw_degree,
            GimbalRollDegree=self.gimbal_roll_degree,
            DroneCoordinates=[self.longitude, self.latitude],
            Sensor_Width=self.sensor_width,
            Sensor_Height=self.sensor_height,
            CameraMake=self.camera_make,
            Drone_Make=self.drone_make,
            Drone_Model=self.drone_model,
            MaxApertureValue=self.max_aperture_value,
            lens_FOV1h=self.lens_FOV_height,
            lens_FOVw1=self.lens_FOV_width,
            GSD=self.gsd,
            epsgCode=self.config.epsg_code)
        if self.gimbal_pitch_degree == 999:
            self.properties['FlightYawDegree']=self.gimbal_yaw_degree
            self.properties['FlightPitchDegree']=self.gimbal_pitch_degree
            self.properties['FlightRollDegree']=self.gimbal_roll_degree

    def create_hash(self) -> bool:
        self.drone_hash = hash((self.drone_make, self.drone_model ,self.camera_make, self.sensor_model, \
                self.sensor_width, self.sensor_height, self.lens_FOV_width, self.lens_FOV_height, self.focal_length, self.max_aperture_value))
