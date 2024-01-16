import math
import numpy as np
from shapely.geometry import Polygon
import json
import utm

class Quaternion:
    def __init__(self, roll, pitch, yaw, is_degrees):
        if is_degrees:
            roll = self.radians(roll)
            pitch = self.radians(pitch)
            yaw = self.radians(yaw)

        cy = math.cos(-yaw * 0.5)
        sy = math.sin(-yaw * 0.5)
        cr = math.cos(-roll * 0.5)
        sr = math.sin(-roll * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)

        self.w = cy * cr * cp + sy * sr * sp
        self.x = cy * sr * cp - sy * cr * sp
        self.y = cy * cr * sp + sy * sr * cp
        self.z = sy * cr * cp - cy * sr * sp

    def convert_to_euler(self, return_degrees=True):
        sinr = +2.0 * (self.w * self.x + self.y * self.z)
        cosr = +1.0 - 2.0 * (self.x * self.x + self.y * self.y)
        roll = math.atan2(sinr, cosr)

        sinp = +2.0 * (self.w * self.y - self.z * self.x)
        if abs(sinp) >= 1:
            pitch = self.copy_sign(math.pi / 2, sinp)
        else:
            pitch = math.asin(sinp)

        siny = +2.0 * (self.w * self.z + self.x * self.y)
        cosy = +1.0 - 2.0 * (self.y * self.y + self.z * self.z)
        yaw = math.atan2(siny, cosy)

        if return_degrees:
            roll = self.degrees(roll)
            pitch = self.degrees(pitch)
            yaw = self.degrees(yaw)

        return roll, pitch, yaw

    def multiply(self, q2):
        return Quaternion(
            self.x * q2.w + self.y * q2.z - self.z * q2.y + self.w * q2.x,
            -self.x * q2.z + self.y * q2.w + self.z * q2.x + self.w * q2.y,
            self.x * q2.y - self.y * q2.x + self.z * q2.w + self.w * q2.z,
            -self.x * q2.x - self.y * q2.y - self.z * q2.z + self.w * q2.w
        )

    @staticmethod
    def copy_sign(x, y):
        return abs(x) * math.copysign(1, y)

    @staticmethod
    def radians(deg):
        return deg * math.pi / 180.0

    @staticmethod
    def degrees(rad):
        return rad * 180.0 / math.pi


def generate_geojson_footprint(hfv, vfv, gimRoll, gimYaw, gimPitch, ac_height, angle_limit, utm_zone1, utm_zont2):
    TR = Quaternion(hfv / -2, vfv / 2, 0, True)
    TL = Quaternion(hfv / 2, vfv / 2, 0, True)
    BR = Quaternion(hfv / -2, vfv / -2, 0, True)
    BL = Quaternion(hfv / 2, vfv / -2, 0, True)

    gimRot = Quaternion(gimRoll, gimPitch, gimYaw, True)
    # acRot = Quaternion(acRoll, acPitch, acYaw, True)

    # TR1 = acRot.multiply(gimRot.multiply(TR))
    # TL1 = acRot.multiply(gimRot.multiply(TL))
    # BR1 = acRot.multiply(gimRot.multiply(BR))
    # BL1 = acRot.multiply(gimRot.multiply(BL))

    TR1 = gimRot.multiply(TR)
    TL1 = gimRot.multiply(TL)
    BR1 = gimRot.multiply(BR)
    BL1 = gimRot.multiply(BL)

    points = [
        get_point_on_ground(TR1, ac_height, angle_limit),
        get_point_on_ground(TL1, ac_height, angle_limit),
        get_point_on_ground(BL1, ac_height, angle_limit),
        get_point_on_ground(BR1, ac_height, angle_limit),
    ]

    # # Convert UTM coordinates to meters
    # utm_coords_meters = []
    # for point in points:
    #     utm_x, utm_y, _, _ = utm.to_latlon(point[0], point[1], utm_zone1, utm_zont2)
    #     utm_coords_meters.append((utm_x, utm_y))
    # #
    return points

def get_point_on_ground(q, anglelimit, acHeight):
    r, p, y = q.convert_to_euler(True)

    r = limit(r, -anglelimit, anglelimit)
    p = limit(p, -anglelimit, anglelimit)

    dx = acHeight * math.tan(math.radians(r))
    dy = acHeight * math.tan(math.radians(p))

    utmx =  dx * math.cos(math.radians(y)) - dy * math.sin(math.radians(y)) + 150
    utmy = -dx * math.sin(math.radians(y)) - dy * math.cos(math.radians(y)) + 150

    return utmx, utmy

def limit(value, min_val, max_val):
    if value < min_val:
        return min_val
    if value > max_val:
        return max_val
    return value

# Define the initial values for your variables here
# hfv = 60
# vfv = 30
# gimRoll = 0
# gimPitch = 0
# gimYaw = 0
# acRoll = 0
# acPitch = 0
# acYaw = 0
# ac_height = 50
# angle_limit = 10

# Call the gen_new_footprint function to generate the GeoJSON footprint
