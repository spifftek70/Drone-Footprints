#  Copyright (c) 2024.
#  Author: Dean Hand
#  License: AGPL
#  Version: 1.0

import math
import numpy as np
from vector3d.vector import Vector


class CameraCalculator:
    def __init__(self):
        """Initializes the CameraCalculator object."""
        pass

    def __del__(self):
        """Cleans up any resources if necessary when the CameraCalculator object is destroyed."""
        pass

    @staticmethod
    def getBoundingPolygon(FOVh, FOVv, altitude, roll, pitch, yaw):
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
            Vector(math.tan(FOVv / 2), -math.tan(FOVh / 2), 1).normalize(),  # Bottom left
            Vector(-math.tan(FOVv / 2), -math.tan(FOVh / 2), 1).normalize(),  # Top left
            Vector(-math.tan(FOVv / 2), math.tan(FOVh / 2), 1).normalize(),  # Top right
            Vector(math.tan(FOVv / 2), math.tan(FOVh / 2), 1).normalize(),  # Bottom right
        ]

        # Rotate rays according to camera orientation
        rotated_vectors = CameraCalculator.rotateRays(rays, roll, pitch, yaw)

        # Calculate intersection points of rays with ground plane
        origin = Vector(0, 0, altitude)
        intersections = CameraCalculator.getRayGroundIntersections(rotated_vectors, origin)

        return intersections

    @staticmethod
    def rotateRays(rays, roll, pitch, yaw):
        """
        Rotates the given rays according to the specified roll, pitch, and yaw angles.

        Parameters:
            rays (list): A list of Vector objects representing the rays to rotate.
            roll (float): The roll angle in radians.
            pitch (float): The pitch angle in radians.
            yaw (float): The yaw angle in radians.

        Returns:
            list: A list of Vector objects representing the rotated rays.
        """

        # Pre-compute sine and cosine of angles for efficiency
        sin_roll, cos_roll = math.sin(roll), math.cos(roll)
        sin_pitch, cos_pitch = math.sin(pitch), math.cos(pitch)
        sin_yaw, cos_yaw = math.sin(yaw), math.cos(yaw)

        # Define rotation matrix components
        rotation_matrix = np.array([
            [cos_yaw * cos_pitch, cos_yaw * sin_pitch * sin_roll - sin_yaw * cos_roll,
             cos_yaw * sin_pitch * cos_roll + sin_yaw * sin_roll],
            [sin_yaw * cos_pitch, sin_yaw * sin_pitch * sin_roll + cos_yaw * cos_roll,
             sin_yaw * sin_pitch * cos_roll - cos_yaw * sin_roll],
            [-sin_pitch, cos_pitch * sin_roll, cos_pitch * cos_roll]
        ])

        # Rotate each ray and collect the results
        rotated_rays = [Vector(*(rotation_matrix.dot(np.array([ray.x, ray.y, ray.z])))) for ray in rays]

        return rotated_rays

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

        intersections = [CameraCalculator.findRayGroundIntersection(ray, origin) for ray in rays if
                         CameraCalculator.findRayGroundIntersection(ray, origin) is not None]

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

        # Calculate intersection point
        return Vector(origin.x + ray.x * t, origin.y + ray.y * t, 0)
