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
    def getBoundingPolygon(FOVh, FOVv, altitude, roll, pitch, heading):
        # import ipdb; ipdb.set_trace()
        ray1 = Vector(math.tan(FOVv / 2), math.tan(FOVh / 2), -1)
        ray2 = Vector(math.tan(FOVv / 2), -math.tan(FOVh / 2), -1)
        ray3 = Vector(-math.tan(FOVv / 2), -math.tan(FOVh / 2), -1)
        ray4 = Vector(-math.tan(FOVv / 2), math.tan(FOVh / 2), -1)

        ray11 = ray1.normalize()
        ray22 = ray2.normalize()
        ray33 = ray3.normalize()
        ray44 = ray4.normalize()

        rotatedVectors = CameraCalculator.rotateRays(
                ray11, ray22, ray33, ray44, roll, pitch, heading * -1)

        origin = Vector(0, -0, altitude)
        intersections = CameraCalculator.getRayGroundIntersections(rotatedVectors, origin)

        return intersections

    @staticmethod
    def rotateRays(ray1, ray2, ray3, ray4, roll, pitch, yaw):
        sinAlpha = math.sin(yaw)
        sinBeta = math.sin(pitch)
        sinGamma = math.sin(roll)
        cosAlpha = math.cos(yaw)
        cosBeta = math.cos(pitch)
        cosGamma = math.cos(roll)
        m00 = cosAlpha * cosBeta
        m01 = cosAlpha * sinBeta * sinGamma - sinAlpha * cosGamma
        m02 = cosAlpha * sinBeta * cosGamma + sinAlpha * sinGamma
        m10 = sinAlpha * cosBeta
        m11 = sinAlpha * sinBeta * sinGamma + cosAlpha * cosGamma
        m12 = sinAlpha * sinBeta * cosGamma - cosAlpha * sinGamma
        m20 = -sinBeta
        m21 = cosBeta * sinGamma
        m22 = cosBeta * cosGamma

        RotationMatrix = np.array([[m00, m01, m02], [m10, m11, m12], [m20, m21, m22]])

        ray1Matrix = np.array([[ray1.x], [ray1.y], [ray1.z]])
        ray2Matrix = np.array([[ray2.x], [ray2.y], [ray2.z]])
        ray3Matrix = np.array([[ray3.x], [ray3.y], [ray3.z]])
        ray4Matrix = np.array([[ray4.x], [ray4.y], [ray4.z]])

        res1 = RotationMatrix.dot(ray1Matrix)
        res2 = RotationMatrix.dot(ray2Matrix)
        res3 = RotationMatrix.dot(ray3Matrix)
        res4 = RotationMatrix.dot(ray4Matrix)

        RotatedRay1 = Vector(res1[0, 0], res1[1, 0], res1[2, 0])
        RotatedRay2 = Vector(res2[0, 0], res2[1, 0], res2[2, 0])
        RotatedRay3 = Vector(res3[0, 0], res3[1, 0], res3[2, 0])
        RotatedRay4 = Vector(res4[0, 0], res4[1, 0], res4[2, 0])
        RayArray = [RotatedRay1, RotatedRay2, RotatedRay3, RotatedRay4]

        return RayArray

    @staticmethod
    def getRayGroundIntersections(rays, origin):
        intersections = []
        for i in range(len(rays)):
            intersections.append( CameraCalculator.findRayGroundIntersection(rays[i], origin) )
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