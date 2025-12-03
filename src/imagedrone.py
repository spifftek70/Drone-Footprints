import os
from dataclasses import dataclass,field
from pathlib import Path
from datetime import datetime
import geojson
from geojson_rewind import rewind
from magnetic_field_calculator import MagneticFieldCalculator
import magnetismi.magnetismi as api
import numpy as np
import quaternion
from shapely.geometry import Polygon
from Utils.geospatial_conversions import *
from Utils.new_elevation import *
from Utils.utils import Color
from Utils import config
from create_geotiffs import set_raster_extents
from mpmath import mp, radians, sqrt
from vector3d.vector import Vector
from loguru import logger


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

        self.lense_correction = config.lense_correction

        # Extract detailed sensor and drone info for the current image
        # Extracting latitude, longitude, and altitude details
        self.latitude = float(self.metadata.get("Composite:GPSLatitude")
                                or self.metadata.get("EXIF:GPSLatitude"))
        self.longitude = float(self.metadata.get("Composite:GPSLongitude")
                                or self.metadata.get("EXIF:GPSLongitude"))
        self.focal_length = float(self.metadata.get("EXIF:FocalLength"))
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

            print(f"No sensor information found for {self.file_name} with sensor model"
                  f" {self.sensor_model_data} and rig camera index "
                  f"{self.sensor_index}. Using defaults.")
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

    def get_HighAccuracyFOV(self):
        try:
            self.calculate_fov_dimensions()
            self.get_bounding_polygon()
            self.utmx, self.utmy, self.zone_number, self.zone_letter = gps_to_utm(self.latitude, self.longitude)

            # Determine new altitude based on different data sources
            if config.dtm_path:
                self.new_altitude = get_altitude_at_point(self.utmx, self.utmy)
            elif config.global_elevation:
                self.new_altitude = get_altitude_from_open(self.latitude, self.longitude)
            else:
                self.new_altitude = config.absolute_altitude
            #print(f"config.relative_altitude {config.relative_altitude} config.absolute_altitude {config.absolute_altitude} new_altitude: {self.new_altitude}")
            self.corrected_altitude = self.new_altitude
            self.elevation_bbox = self.get_ray_ground_intersections()

            self.translated_bbox= find_geodetic_intersections(self.elevation_bbox, self.longitude, self.latitude)
            self.center_distance = drone_distance_to_polygon_center(self.translated_bbox, (self.utmx, self.utmy), self.corrected_altitude)
            self.new_translated_bbox = self.translated_bbox

            if config.dtm_path:
                altitudes = [get_altitude_at_point(*box[:2]) for box in self.new_translated_bbox]
                if None in altitudes:
                    logger.warning(
                        f"Failed to get elevation for image {self.file_name}. See log for details.")
                    self.coord_array, self.footprint_coordinates = translate_to_wgs84(self.new_translated_bbox, self.longitude, self.latitude)
                    return
                # Calculate the ratios of distances to check the 5 times condition
                distances = [sqrt((self.new_translated_bbox[(i + 1) % len(self.new_translated_bbox)][0] - box[0]) ** 2 +
                                    (self.new_translated_bbox[(i + 1) % len(self.new_translated_bbox)][1] - box[1]) ** 2)
                                for i, box in enumerate(self.new_translated_bbox)]
                for dist in distances:
                    if any(other_dist * 6 < dist for other_dist in distances if other_dist != dist):
                        logger.warning(
                            f"One side of the polygon for {self.file_name} is at least 5 times longer than another.")
                        self.coord_array, self.footprint_coordinates = translate_to_wgs84(self.new_translated_bbox, self.longitude, self.latitude)
                        return

            elif config.global_elevation:
                    trans_utmbox = [utm_to_latlon(box[0], box[1], self.zone_number, self.zone_letter) for box in self.new_translated_bbox]
                    altitudes = get_altitudes_from_open(trans_utmbox)

                    if None in altitudes:
                        logger.warning(f"Failed to get elevation at point for {self.file_name}.")
                        self.coord_array, self.footprint_coordinates = translate_to_wgs84(self.new_translated_bbox, self.longitude, self.latitude)

                    # Calculate the ratios of distances to check the 5 times condition
                    distances = [sqrt((self.new_translated_bbox[(i + 1) % len(self.new_translated_bbox)][0] - box[0]) ** 2 +
                                    (self.new_translated_bbox[(i + 1) % len(self.new_translated_bbox)][1] - box[1]) ** 2)
                                for i, box in enumerate(self.new_translated_bbox)]
                    for dist in distances:
                        if any(other_dist * 5 < dist for other_dist in distances if other_dist != dist):
                            logger.warning(
                                f"One side of the polygon for {self.file_name} is at least 5 times longer than another.")
                            self.coord_array, self.footprint_coordinates = translate_to_wgs84(self.new_translated_bbox, self.longitude, self.latitude)
                            return
                # If no special conditions are met, process normally
            self.coord_array, self.footprint_coordinates = translate_to_wgs84(self.new_translated_bbox, self.longitude, self.latitude)
            return
        except Exception as e:
            logger.warning(f"Error in get_fov_bbox: {e}")
            self.coord_array, self.footprint_coordinates = None, None

    def get_ray_ground_intersections(self):
        """
        Calculates the intersection points of the given self.rotated_vectorsrays with the ground plane.

        Returns:
            list: A list of Vector objects representing the intersection points on the ground.
        """
        origin = Vector(0, 0, float(self.corrected_altitude))

        return [
            self.find_ray_ground_intersection(ray, origin)
            for ray in self.rotated_vectors
            if self.find_ray_ground_intersection(ray, origin) is not None
        ]


    def find_ray_ground_intersection(self,ray, origin):
        """
        Finds the intersection point of a single ray with the ground plane.

        Parameters:
            ray (Vector): The ray vector.
            origin (Vector): The origin point of the ray.

        Returns:
            Vector: The intersection point with the ground, or None if the ray is parallel to the ground.
        """

        if ray.z == 0:  # Ray is parallel to ground
            return None

        # Calculate intersection parameter t
        t = -origin.z / ray.z
        return Vector(origin.x + ray.x * t, origin.y + ray.y * t, 0)



    def calculate_fov_dimensions(self):
        FOVw = 2 * mp.atan(mp.mpf(self.sensor_width) / (2 * self.focal_length))
        FOVh = 2 * mp.atan(mp.mpf(self.sensor_height) / (2 * self.focal_length))

        # _sensor_lens_correction now inside this function
        self.corrected_fov_width = FOVw * self.lens_FOV_width
        self.corrected_fov_height = FOVh * self.lens_FOV_height

    def get_bounding_polygon(self):
        """
        Calculates the bounding polygon of a camera's footprint given its field of view, position, and orientation.

        Parameters:
            FOVh (float): The horizontal field of view in radians.
            FOVv (float): The vertical field of view in radians.
            altitude (float): The altitude above ground in meters.
            roll (float): The roll angle in radians.
            pitch (float): The pitch angle in radians.
            yaw (float): The yaw angle in radians.

        Returns:
            list: A list of Vector objects representing the corners of the bounding polygon on the ground.
        """

        # Define camera rays based on field of view
        self.rays = [
            Vector(-mp.tan(self.corrected_fov_height / 2), mp.tan(self.corrected_fov_width / 2), 1).normalize(),  # Flip horizontally
            Vector(-mp.tan(self.corrected_fov_height / 2), -mp.tan(self.corrected_fov_width / 2), 1).normalize(),  # Flip horizontally
            Vector(mp.tan(self.corrected_fov_height / 2), -mp.tan(self.corrected_fov_width / 2), 1).normalize(),  # Flip horizontally
            Vector(mp.tan(self.corrected_fov_height / 2), mp.tan(self.corrected_fov_width / 2), 1).normalize()  # Flip horizontally
        ]
        # Rotate rays according to camera orientation

        # Calculate adjusted angles for gimbal and flight orientations
        self.find_declination()
        adj_yaw, adj_pitch, adj_roll = calculate_rads_from_angles(self.gimbal_yaw_degree,
                                                                       self.gimbal_pitch_degree,
                                                                       self.gimbal_roll_degree,
                                                                       self.declination)

        q = quaternion.from_euler_angles(adj_yaw, adj_pitch, adj_roll)
        # Normalize the quaternion
        q = q.normalized()

        # Apply rotation to each ray
        self.rotated_vectors = [Vector(*(q * np.quaternion(0, ray.x, ray.y, ray.z) * q.inverse()).vec) for ray in self.rays]


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





    def create_geojson_feature(self):
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
        self.feature_point = dict(type="Feature", geometry=type_point, properties=self.properties)
        self.feature_polygon = dict(type="Feature", geometry=type_polygon, properties=self.properties)

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
