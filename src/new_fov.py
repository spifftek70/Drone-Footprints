#  Copyright (c) 2024.
#  __author__ = "Dean Hand"
#  __license__ = "AGPL"
#  __version__ = "1.0"


import numpy as np
from mpmath import mp, radians, sqrt
import quaternion
from loguru import logger
from vector3d.vector import Vector
from Utils.geospatial_conversions import find_geodetic_intersections, gps_to_utm, translate_to_wgs84, utm_to_latlon
from Utils.new_elevation import get_altitude_at_point, get_altitude_from_open, get_altitudes_from_open
from Utils import config
from imagedrone import ImageDrone

latitude = 0
longitude = 0
lens_FOVh = 0.0
lens_FOVw = 0.0
mp.dps = 50  # set a higher precision


class HighAccuracyFOVCalculator:
    def __init__(self,image:ImageDrone):

        global latitude, longitude, lens_FOVh, lens_FOVw
        self.image = image
        self.drone_gps = (image.latitude, image.longitude)
        latitude = image.latitude
        longitude = image.longitude

        lens_FOVh = self.image.lens_FOV_height
        lens_FOVw = self.image.lens_FOV_width

    def calculate_fov_dimensions(self):
        FOVw = 2 * mp.atan(mp.mpf(self.image.sensor_width) / (2 * self.image.focal_length))
        FOVh = 2 * mp.atan(mp.mpf(self.image.sensor_height) / (2 * self.image.focal_length))

        # _sensor_lens_correction now inside this function
        corrected_fov_width = FOVw * lens_FOVw
        corrected_fov_height = FOVh * lens_FOVh

        return corrected_fov_width, corrected_fov_height


    @staticmethod
    def calculate_rads_from_angles(gimbal_yaw_deg, gimbal_pitch_deg, gimbal_roll_deg, declination):
        """
        Adjusts the gimbal's angles for magnetic declination and normalizes the roll orientation.
        - Yaw is adjusted for magnetic declination.
        - Roll is normalized if within a specific range to handle edge cases around 90 degrees.
        - Pitch is converted directly to radians.

        Parameters:
        - gimbal_yaw_deg (float): The gimbal's yaw angle in degrees.
        - gimbal_pitch_deg (float): The gimbal's pitch angle in degrees.
        - gimbal_roll_deg (float): The gimbal's roll angle in degrees.
        - declination (float): Magnetic declination in degrees.

        Returns:
        - tuple: Adjusted yaw, pitch, and roll angles in radians.
        """
        # Normalize yaw for magnetic declination
        if -120 <= gimbal_pitch_deg <= -60:
            pitch_rad = radians(90 - gimbal_pitch_deg)
        else:
            pitch_rad = radians(180 - gimbal_pitch_deg)

        if config.correct_magnetic_declinaison:
            yaw_rad = (mp.pi / 2) - radians(gimbal_yaw_deg + declination)
        else:
            yaw_rad = (mp.pi / 2) - radians(gimbal_yaw_deg)
        yaw_rad = yaw_rad % (2 * mp.pi)
        roll_rad = radians(gimbal_roll_deg)

        return yaw_rad, pitch_rad, roll_rad

    def get_bounding_polygon(self, FOVh, FOVv):
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
        rays = [
            Vector(-mp.tan(FOVv / 2), mp.tan(FOVh / 2), 1).normalize(),  # Flip horizontally
            Vector(-mp.tan(FOVv / 2), -mp.tan(FOVh / 2), 1).normalize(),  # Flip horizontally
            Vector(mp.tan(FOVv / 2), -mp.tan(FOVh / 2), 1).normalize(),  # Flip horizontally
            Vector(mp.tan(FOVv / 2), mp.tan(FOVh / 2), 1).normalize()  # Flip horizontally
        ]
        # Rotate rays according to camera orientation
        rotated_vectors = self.rotate_rays(rays)

        return rotated_vectors

    def rotate_rays(self, rays):
        # Calculate adjusted angles for gimbal and flight orientations
        self.image.find_declination()
        declination = self.image.declination

        adj_yaw, adj_pitch, adj_roll = self.calculate_rads_from_angles(self.image.gimbal_yaw_degree,
                                                                       self.image.gimbal_pitch_degree,
                                                                       self.image.gimbal_roll_degree,
                                                                       declination)

        q = quaternion.from_euler_angles(adj_yaw, adj_pitch, adj_roll)
        # Normalize the quaternion
        q = q.normalized()

        # Apply rotation to each ray
        return [Vector(*(q * np.quaternion(0, ray.x, ray.y, ray.z) * q.inverse()).vec) for ray in rays]

    def get_fov_bbox(self):
        try:
            FOVw, FOVh = self.calculate_fov_dimensions()
            rotated_vectors = self.get_bounding_polygon(FOVw, FOVh)
            utmx, utmy, zone_number, zone_letter = gps_to_utm(latitude, longitude)
            new_altitude = None
            # Determine new altitude based on different data sources
            if config.dtm_path:
                new_altitude = get_altitude_at_point(utmx, utmy)
            if config.global_elevation:
                new_altitude = get_altitude_from_open(latitude, longitude)
            if config.relative_altitude == 0.0:
                new_altitude = config.absolute_altitude
            if new_altitude and abs(new_altitude - config.relative_altitude) > 20:
                new_altitude = config.relative_altitude
            if config.absolute_altitude == config.relative_altitude:
                new_altitude = get_altitude_from_open(latitude, longitude)
            if new_altitude is None:  # and not config.dtm_path or not config.global_elevation is False or config.rtk:
                new_altitude = config.relative_altitude
                if config.global_elevation is True or config.dtm_path:
                    logger.warning(
                        f"Failed to get elevation for {config.im_file_name}, using drone altitude.")

            corrected_altitude = self._atmospheric_refraction_correction(new_altitude)

            elevation_bbox = HighAccuracyFOVCalculator.get_ray_ground_intersections(rotated_vectors, Vector(0, 0, float(
                corrected_altitude)))
            translated_bbox = find_geodetic_intersections(elevation_bbox, longitude, latitude)
            self.image.center_distance = drone_distance_to_polygon_center(translated_bbox, (utmx, utmy), corrected_altitude)
            new_translated_bbox = translated_bbox
            if config.dtm_path:
                altitudes = [get_altitude_at_point(*box[:2]) for box in new_translated_bbox]
                if None in altitudes:
                    logger.warning(
                        f"Failed to get elevation for image {config.im_file_name}. See log for details.")
                    return translate_to_wgs84(new_translated_bbox, longitude, latitude)

                # Calculate the ratios of distances to check the 5 times condition
                distances = [sqrt((new_translated_bbox[(i + 1) % len(new_translated_bbox)][0] - box[0]) ** 2 +
                                  (new_translated_bbox[(i + 1) % len(new_translated_bbox)][1] - box[1]) ** 2)
                             for i, box in enumerate(new_translated_bbox)]
                for dist in distances:
                    if any(other_dist * 6 < dist for other_dist in distances if other_dist != dist):
                        logger.warning(
                            f"One side of the polygon for {config.im_file_name} is at least 5 times longer than another.")
                        return translate_to_wgs84(new_translated_bbox, longitude, latitude)

            if config.global_elevation is True:
                trans_utmbox = [utm_to_latlon(box[0], box[1], zone_number, zone_letter) for box in new_translated_bbox]
                altitudes = get_altitudes_from_open(trans_utmbox)

                if None in altitudes:
                    logger.warning(f"Failed to get elevation at point for {config.im_file_name}.")
                    return translate_to_wgs84(new_translated_bbox, longitude, latitude)

                # Calculate the ratios of distances to check the 5 times condition
                distances = [sqrt((new_translated_bbox[(i + 1) % len(new_translated_bbox)][0] - box[0]) ** 2 +
                                  (new_translated_bbox[(i + 1) % len(new_translated_bbox)][1] - box[1]) ** 2)
                             for i, box in enumerate(new_translated_bbox)]
                for dist in distances:
                    if any(other_dist * 5 < dist for other_dist in distances if other_dist != dist):
                        logger.warning(
                            f"One side of the polygon for {config.im_file_name} is at least 5 times longer than another.")
                        return translate_to_wgs84(new_translated_bbox, longitude, latitude)

            # If no special conditions are met, process normally
            return translate_to_wgs84(new_translated_bbox, longitude, latitude)

        except Exception as e:
            logger.warning(f"Error in get_fov_bbox: {e}")
            return None, None

    @staticmethod
    def get_ray_ground_intersections(rays, origin):
        """
        Calculates the intersection points of the given rays with the ground plane.

        Parameters:
            rays (list): A list of Vector objects representing the rays.
            origin (Vector): The origin point of the rays.

        Returns:
            list: A list of Vector objects representing the intersection points on the ground.
        """

        intersections = [HighAccuracyFOVCalculator.find_ray_ground_intersection(ray, origin) for ray in rays if
                         HighAccuracyFOVCalculator.find_ray_ground_intersection(ray, origin) is not None]

        return intersections

    @staticmethod
    def find_ray_ground_intersection(ray, origin):
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

    def _atmospheric_refraction_correction(self, altitude):
        return altitude + (altitude * 0.0001)


def calculate_centroid(polygon_coords):
    """Calculate the centroid of a polygon given its vertices in UTM coordinates."""
    x_sum = 0
    y_sum = 0
    for (x, y) in polygon_coords:
        x_sum += x
        y_sum += y
    centroid = (x_sum / len(polygon_coords), y_sum / len(polygon_coords))
    return centroid


def distance_3d(point1, point2):
    """Calculate the 3D distance between two points in UTM coordinates."""
    return sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2 + (point1[2] - point2[2]) ** 2)


def drone_distance_to_polygon_center(polygon_coords, drone_coords, drone_altitude):
    """
    Calculate the distance from a drone to the center of a polygon in UTM coordinates.

    Parameters:
    - polygon_coords: list of tuples, each representing the (x, y) UTM coordinates of a polygon's vertex.
    - drone_coords: Tuple representing the (x, y) UTM coordinates of the drone's location.
    - drone_altitude: Float representing the drone's altitude in meters above the ground.

    Returns:
    - Float: The distance from the drone to the centroid of the polygon.
    """
    # Calculate the centroid of the polygon
    centroid = calculate_centroid(polygon_coords)
    centroid_3d = (centroid[0], centroid[1], 0)
    drone_position_3d = (drone_coords[0], drone_coords[1], drone_altitude)
    center_distance=distance_3d(centroid_3d, drone_position_3d)
    config.update_center_distance(center_distance)
    return center_distance
    # Calculate and return the 3D distance
