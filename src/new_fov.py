#  Copyright (c) 2024.
#  __author__ = "Dean Hand"
#  __license__ = "AGPL"
#  __version__ = "1.0"


import numpy as np
import quaternion
from Utils.geospatial_conversions import *
from mpmath import mp, radians
from vector3d.vector import Vector
from Utils.new_elevation import get_altitude_at_point, get_altitude_from_open
import Utils.config as config
from Utils.declination import find_declination

latitude = 0
longitude = 0
datetime_original = None
lens_FOVh = 0.0
lens_FOVw = 0.0
mp.dps = 50  # set a higher precision


class HighAccuracyFOVCalculator:
    def __init__(self, drone_gps, drone_altitude, camera_info, gimbal_orientation, flight_orientation,
                 datetime_original, i):
        global latitude, longitude, lens_FOVh, lens_FOVw
        self.drone_gps = drone_gps
        latitude = drone_gps[0]
        longitude = drone_gps[1]
        self.datetime_original = datetime_original
        self.drone_altitude = drone_altitude
        self.camera_info = camera_info
        lens_FOVh = camera_info['lens_FOVh']
        lens_FOVw = camera_info['lens_FOVw']
        self.gimbal_orientation = gimbal_orientation
        self.flight_orientation = flight_orientation
        self.i = i

    def calculate_fov_dimensions(self):
        FOVw = 2 * mp.atan(mp.mpf(self.camera_info['sensor_width']) / (2 * self.camera_info['focal_length']))
        FOVh = 2 * mp.atan(mp.mpf(self.camera_info['sensor_height']) / (2 * self.camera_info['focal_length']))

        adj_FOVw, adj_FOVh = HighAccuracyFOVCalculator._sensor_lens_correction(FOVw, FOVh)

        return adj_FOVw, adj_FOVh

    @staticmethod
    def calculate_rads_from_angles(gimbal_yaw_deg, gimbal_pitch_deg, declination):
        """
        Adjusts the gimbal's yaw angle for magnetic declination based on an internal condition.
        Assumes yaw is measured clockwise from magnetic north and declination is positive east of true north.
        """
        adjusted_pitch_deg = radians(gimbal_pitch_deg)
        cal_pitch_rad = (mp.pi / 2) - adjusted_pitch_deg
        yaw_rad = radians(gimbal_yaw_deg)
        if config.decl:
            declination_rad = radians(declination)
            adj_yaw_rad = (mp.pi / 2) - (yaw_rad + declination_rad)
        else:
            adj_yaw_rad = (mp.pi / 2) - yaw_rad
        return adj_yaw_rad, cal_pitch_rad

    def getBoundingPolygon(self, FOVh, FOVv):
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
            Vector(-mp.tan(FOVv / 2), mp.tan(FOVh / 2), 1).normalize(),
            Vector(-mp.tan(FOVv / 2), -mp.tan(FOVh / 2), 1).normalize(),  # Top right
            Vector(mp.tan(FOVv / 2), -mp.tan(FOVh / 2), 1).normalize(),  # Top left
            Vector(mp.tan(FOVv / 2), mp.tan(FOVh / 2), 1).normalize()  # Bottom left
        ]

        # Rotate rays according to camera orientation
        rotated_vectors = self.rotateRays(rays)

        return rotated_vectors

    def rotateRays(self, rays):
        # Calculate adjusted angles for gimbal and flight orientations
        declination = find_declination(self.drone_altitude, self.camera_info['focal_length'], *self.drone_gps,
                                       self.datetime_original)
        adj_yaw, adj_pitch = self.calculate_rads_from_angles(self.gimbal_orientation['yaw'],
                                                             self.gimbal_orientation['pitch'], declination)

        # Create quaternion for combined adjustments
        # Make sure to pass angles in the correct order based on your system's convention
        q = quaternion.from_euler_angles(adj_yaw, adj_pitch, self.gimbal_orientation['roll'])
        # q = quaternion.from_euler_angles(self.gimbal_orientation['roll'], adj_pitch, adj_yaw)
        # Normalize the quaternion
        q = q.normalized()

        # Apply rotation to each ray
        rotated_rays = [Vector(*(q * np.quaternion(0, ray.x, ray.y, ray.z) * q.inverse()).vec) for ray in rays]
        return rotated_rays

    def get_fov_bbox(self):
        try:
            FOVw, FOVh = self.calculate_fov_dimensions()
            rotated_vectors = self.getBoundingPolygon(FOVw, FOVh)
            utmx, utmy, zone_number, zone_letter = gps_to_utm(latitude, longitude)
            new_altitude = None
            # Determine new altitude based on different data sources
            if config.dtm_path:
                new_altitude = get_altitude_at_point(utmx, utmy)
            if config.global_elevation:
                new_altitude = get_altitude_from_open(latitude, longitude)
            if config.rel_altitude == 0.0:
                new_altitude = config.abso_altitude
            if new_altitude is None and not config.dtm_path and not config.global_elevation:
                logger.warning(f"Failed to get elevation for {config.im_file_name}, using drone altitude.")
                new_altitude = config.rel_altitude

            corrected_altitude = self._atmospheric_refraction_correction(new_altitude)
            elevation_bbox = HighAccuracyFOVCalculator.getRayGroundIntersections(rotated_vectors, Vector(0, 0, float(
                corrected_altitude)))
            translated_bbox = find_geodetic_intersections(elevation_bbox, longitude, latitude)
            # translated_bbox = translated_bbox[2:] + translated_bbox[:2]
            if not translated_bbox:
                logger.error("Failed to translate bbox to geographic coordinates.")
                return None, None

            # Check for altitude at each point if necessary and collect altitudes
            if config.dtm_path:
                altitudes = [get_altitude_at_point(*box[:2]) for box in translated_bbox]
                if None in altitudes:
                    logger.warning(f"Failed to get elevation at point for {config.im_file_name}.")
                    return translate_to_wgs84(translated_bbox, longitude, latitude)

                # Calculate the ratios of distances to check the 5 times condition
                distances = [sqrt((translated_bbox[(i + 1) % len(translated_bbox)][0] - box[0]) ** 2 +
                                  (translated_bbox[(i + 1) % len(translated_bbox)][1] - box[1]) ** 2)
                             for i, box in enumerate(translated_bbox)]
                for dist in distances:
                    if any(other_dist * 6 < dist for other_dist in distances if other_dist != dist):
                        logger.warning(
                            f"One side of the polygon for {config.im_file_name} is at least 5 times longer than another.")
                        return translate_to_wgs84(translated_bbox, longitude, latitude)

            if config.global_elevation is True:
                trans_utmbox = [utm_to_latlon(box[0], box[1], zone_number, zone_letter) for box in translated_bbox]
                altitudes = [get_altitude_from_open(*box[:2]) for box in trans_utmbox]
                if None in altitudes:
                    logger.warning(f"Failed to get elevation at point for {config.im_file_name}.")
                    return translate_to_wgs84(translated_bbox, longitude, latitude)

                # Calculate the ratios of distances to check the 5 times condition
                distances = [sqrt((translated_bbox[(i + 1) % len(translated_bbox)][0] - box[0]) ** 2 +
                                  (translated_bbox[(i + 1) % len(translated_bbox)][1] - box[1]) ** 2)
                             for i, box in enumerate(translated_bbox)]
                for dist in distances:
                    if any(other_dist * 5 < dist for other_dist in distances if other_dist != dist):
                        logger.warning(
                            f"One side of the polygon for {config.im_file_name} is at least 5 times longer than another.")
                        return translate_to_wgs84(translated_bbox, longitude, latitude)

            # If no special conditions are met, process normally
            return translate_to_wgs84(translated_bbox, longitude, latitude)

        except Exception as e:
            logger.opt(exception=True).warning(f"Error in get_fov_bbox: {e}")
            return None, None

    def _sensor_lens_correction(fov_width, fov_height):
        # Placeholder for sensor and lens correction
        corrected_fov_width = fov_width * lens_FOVw  # Example correction factor
        corrected_fov_height = fov_height * lens_FOVh
        return corrected_fov_width, corrected_fov_height

    @staticmethod
    def getRayGroundIntersections(rays, origin):
        """
        Calculates the intersection points of the given rays with the ground plane.

        Parameters:
            rays (list): A list of Vector objects representing the rays.
            origin (Vector): The origin point of the rays.

        Returns:
            list: A list of Vector objects representing the intersection points on the ground.
        """

        intersections = [HighAccuracyFOVCalculator.findRayGroundIntersection(ray, origin) for ray in rays if
                         HighAccuracyFOVCalculator.findRayGroundIntersection(ray, origin) is not None]

        return intersections

    @staticmethod
    def findRayGroundIntersection(ray, origin):
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
