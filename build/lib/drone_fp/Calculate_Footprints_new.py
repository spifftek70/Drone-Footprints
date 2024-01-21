import math

class Quaternion:
    def __init__(self, roll, pitch, yaw, is_degrees=True):
        if is_degrees:
            roll = self.radians(roll)
            pitch = self.radians(pitch)
            yaw = self.radians(yaw)
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)

        self.w = cy * cr * cp + sy * sr * sp
        self.x = cy * sr * cp - sy * cr * sp
        self.y = cy * cr * sp + sy * sr * cp
        self.z = sy * cr * cp - cy * sr * sp

    def convert_to_euler(self, return_degrees=True):
        roll, pitch, yaw = self.roll_pitch_yaw()
        if return_degrees:
            roll = self.degrees(roll)
            pitch = self.degrees(pitch)
            yaw = self.degrees(yaw)
        return roll, pitch, yaw

    def roll_pitch_yaw(self):
        sinr_cosp = 2 * (self.w * self.x + self.y * self.z)
        cosr_cosp = 1 - 2 * (self.x * self.x + self.y * self.y)
        roll = math.atan2(sinr_cosp, cosr_cosp)

        sinp = 2 * (self.w * self.y - self.z * self.x)
        if abs(sinp) >= 1:
            pitch = self.copy_sign(math.pi / 2, sinp)
        else:
            pitch = math.asin(sinp)

        siny_cosp = 2 * (self.w * self.z + self.x * self.y)
        cosy_cosp = 1 - 2 * (self.y * self.y + self.z * self.z)
        yaw = math.atan2(siny_cosp, cosy_cosp)

        return roll, pitch, yaw

    @staticmethod
    def radians(degrees):
        return math.radians(degrees)

    @staticmethod
    def degrees(radians):
        return math.degrees(radians)

    @staticmethod
    def copy_sign(val, sign):
        return abs(val) if sign >= 0 else -abs(val)
