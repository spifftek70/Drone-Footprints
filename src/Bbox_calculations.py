

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
        '''Get corners of the polygon captured by the camera on the ground.
        The calculations are performed in the axes origin (0, 0, altitude)
        and the points are not yet translated to camera's X-Y coordinates.
        Parameters:
            FOVh (float): Horizontal field of view in radians
            FOVv (float): Vertical field of view in radians
            altitude (float): Altitude of the camera in meters
            heading (float): Heading of the camera (z axis) in radians
            roll (float): Roll of the camera (x axis) in radians
            pitch (float): Pitch of the camera (y axis) in radians
        Returns:
            vector3d.vector.Vector: Array with 4 points defining a polygon
        '''
        # import ipdb; ipdb.set_trace()
        ray11 = CameraCalculator.ray1(FOVh, FOVv)
        ray22 = CameraCalculator.ray2(FOVh, FOVv)
        ray33 = CameraCalculator.ray3(FOVh, FOVv)
        ray44 = CameraCalculator.ray4(FOVh, FOVv)

        rotatedVectors = CameraCalculator.rotateRays(
                ray11, ray22, ray33, ray44, roll, pitch, heading * -1)

        origin = Vector(0, -0, altitude)
        intersections = CameraCalculator.getRayGroundIntersections(rotatedVectors, origin)

        return intersections


    # Ray-vectors defining the the camera's field of view. FOVh and FOVv are interchangeable
    # depending on the camera's orientation
    @staticmethod
    def ray1(FOVh, FOVv):
        '''
        tasto
        Parameters:
            FOVh (float): Horizontal field of view in radians
            FOVv (float): Vertical field of view in radians
        Returns:
            vector3d.vector.Vector: normalised vector
        '''
        pass
        ray = Vector(math.tan(FOVv/2), math.tan(FOVh/2), -1)
        return ray.normalize()

    @staticmethod
    def ray2(FOVh, FOVv):
        '''
        Parameters:
            FOVh (float): Horizontal field of view in radians
            FOVv (float): Vertical field of view in radians
        Returns:
            vector3d.vector.Vector: normalised vector
        '''
        ray = Vector(math.tan(FOVv/2), -math.tan(FOVh/2), -1)
        return ray.normalize()

    @staticmethod
    def ray3(FOVh, FOVv):
        '''
        Parameters:
            FOVh (float): Horizontal field of view in radians
            FOVv (float): Vertical field of view in radians
        Returns:
            vector3d.vector.Vector: normalised vector
        '''
        ray = Vector(-math.tan(FOVv/2), -math.tan(FOVh/2), -1)
        return ray.normalize()

    @staticmethod
    def ray4(FOVh, FOVv):
        '''
        Parameters:
            FOVh (float): Horizontal field of view in radians
            FOVv (float): Vertical field of view in radians
        Returns:
            vector3d.vector.Vector: normalised vector
        '''
        ray = Vector(-math.tan(FOVv/2), math.tan(FOVh/2), -1)
        return ray.normalize()

    @staticmethod
    def rotateRays(ray1, ray2, ray3, ray4, roll, pitch, yaw):
        """Rotates the four ray-vectors around all 3 axes
        Parameters:
            ray1 (vector3d.vector.Vector): First ray-vector
            ray2 (vector3d.vector.Vector): Second ray-vector
            ray3 (vector3d.vector.Vector): Third ray-vector
            ray4 (vector3d.vector.Vector): Fourth ray-vector
            roll float: Roll rotation
            pitch float: Pitch rotation
            yaw float: Yaw rotation
        Returns:
            Returns new rotated ray-vectors
        """
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

        rotationMatrix = np.array([[m00, m01, m02], [m10, m11, m12], [m20, m21, m22]])

        ray1Matrix = np.array([[ray1.x], [ray1.y], [ray1.z]])
        ray2Matrix = np.array([[ray2.x], [ray2.y], [ray2.z]])
        ray3Matrix = np.array([[ray3.x], [ray3.y], [ray3.z]])
        ray4Matrix = np.array([[ray4.x], [ray4.y], [ray4.z]])

        res1 = rotationMatrix.dot(ray1Matrix)
        res2 = rotationMatrix.dot(ray2Matrix)
        res3 = rotationMatrix.dot(ray3Matrix)
        res4 = rotationMatrix.dot(ray4Matrix)

        rotatedRay1 = Vector(res1[0, 0], res1[1, 0], res1[2, 0])
        rotatedRay2 = Vector(res2[0, 0], res2[1, 0], res2[2, 0])
        rotatedRay3 = Vector(res3[0, 0], res3[1, 0], res3[2, 0])
        rotatedRay4 = Vector(res4[0, 0], res4[1, 0], res4[2, 0])
        rayArray = [rotatedRay1, rotatedRay2, rotatedRay3, rotatedRay4]

        return rayArray

    @staticmethod
    def getRayGroundIntersections(rays, origin):
        """
        Finds the intersections of the camera's ray-vectors
        and the ground approximated by a horizontal plane
        Parameters:
            rays (vector3d.vector.Vector[]): Array of 4 ray-vectors
            origin (vector3d.vector.Vector): Position of the camera. The computation were developed
                                            assuming the camera was at the axes origin (0, 0, altitude) and the
                                            results translated by the camera's real position afterwards.
        Returns:
            vector3d.vector.Vector
        """
        intersections = []
        for i in range(len(rays)):
            intersections.append( CameraCalculator.findRayGroundIntersection(rays[i], origin) )
        return intersections

    @staticmethod
    def findRayGroundIntersection(ray, origin):
        """
        Finds a ray-vector's intersection with the ground approximated by a plane
        Parameters:
            ray (vector3d.vector.Vector): Ray-vector
            origin (vector3d.vector.Vector): Camera's position
        Returns:
            vector3d.vector.Vector: Intersection point with the ground plane
        """
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

