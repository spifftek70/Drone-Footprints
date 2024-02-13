#  Copyright (c) 2024.
#  __author__ = "Dean Hand"
#  __license__ = "AGPL"
#  __version__ = "1.0"

# Based upon: https://github.com/frank-engel-usgs/camera-footprint-calculator/blob/master/camera_calculator.py
#    Orignal by           : Luigi Pirelli

import math
import numpy as np
from vector3d.vector import Vector


class CameraCalculator:
    def __init__(self):
        pass

    def __del__(delf):
        pass

    @staticmethod
    def getBoundingPolygon(FOVh, FOVv, altitude, roll, pitch, yaw):
        # Correctly handle vector initialization and heading adjustment
        rays = [Vector(math.tan(FOVv / 2), math.tan(FOVh / 2), -1).normalize(),
                Vector(math.tan(FOVv / 2), -math.tan(FOVh / 2), -1).normalize(),
                Vector(-math.tan(FOVv / 2), -math.tan(FOVh / 2), -1).normalize(),
                Vector(-math.tan(FOVv / 2), math.tan(FOVh / 2), -1).normalize()]

        # Adjust the heading correctly without negation unless specifically needed for the coordinate system
        rotated_vectors = CameraCalculator.rotateRays(rays, roll, pitch, yaw * -1)
        origin = Vector(0, 0, altitude)
        intersections = CameraCalculator.getRayGroundIntersections(rotated_vectors, origin)
        return intersections

    @staticmethod
    def rotateRays(rays, roll, pitch, yaw):
        # Calculate sine and cosine for each of the angles for efficiency
        sin_roll = math.sin(roll)
        cos_roll = math.cos(roll)
        sin_pitch = math.sin(pitch)
        cos_pitch = math.cos(pitch)
        sin_yaw = math.sin(yaw)
        cos_yaw = math.cos(yaw)

        # Rotation matrix components
        m00 = cos_yaw * cos_pitch
        m01 = cos_yaw * sin_pitch * sin_roll - sin_yaw * cos_roll
        m02 = cos_yaw * sin_pitch * cos_roll + sin_yaw * sin_roll
        m10 = sin_yaw * cos_pitch
        m11 = sin_yaw * sin_pitch * sin_roll + cos_yaw * cos_roll
        m12 = sin_yaw * sin_pitch * cos_roll - cos_yaw * sin_roll
        m20 = -sin_pitch
        m21 = cos_pitch * sin_roll
        m22 = cos_pitch * cos_roll

        # Create rotation matrix
        rotation_matrix = np.array([
            [m00, m01, m02],
            [m10, m11, m12],
            [m20, m21, m22]
        ])

        rotated_rays = []
        for ray in rays:
            # Convert Vector to numpy array for matrix multiplication
            ray_vector = np.array([ray.x, ray.y, ray.z])
            # Apply rotation
            rotated_vector = rotation_matrix.dot(ray_vector)
            # Convert back to Vector and add to the list
            rotated_rays.append(Vector(rotated_vector[0], rotated_vector[1], rotated_vector[2]))

        return rotated_rays

    @staticmethod
    def getRayGroundIntersections(rays, origin):
        intersections = []
        for ray in rays:
            intersection = CameraCalculator.findRayGroundIntersection(ray, origin)
            if intersection is not None:  # Handle potential None returns for parallel rays
                intersections.append(intersection)
        return intersections

    @staticmethod
    def findRayGroundIntersection(ray, origin):
        # Calculate t for the intersection with the ground plane (z = 0)
        if ray.z == 0:
            # Avoid division by zero; if ray.z is 0, the ray is parallel to the ground plane and won't intersect
            return None  # Or handle this case as per your application's logic
        t = -origin.z / ray.z

        # Calculate the intersection point using the parametric equation of the ray
        x = origin.x + ray.x * t
        y = origin.y + ray.y * t
        z = 0  # The intersection is with the ground plane, so z is 0

        return Vector(x, y, z)