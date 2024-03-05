from .point import Point
from math import sqrt, acos, degrees
class Vector:
	x = float()
	y = float()
	z = float()
	
	def __init__(self, x=0, y=0, z=0):
		self.x = x
		self.y = y
		self.z = z
	
	def __eq__(self, other):
		if self.x == other.x and self.y == other.y and self.z == other.z: return True
		else: return False
	
	def __len__(self):
		return int(self.length())
	
	
	def __add__(self, o):
		return Vector((self.x + o.x), (self.y + o.y), (self.z + o.z))
	
	def __sub__(self, o):
		return Vector((self.x - o.x), (self.y - o.y), (self.z - o.z))
	
	def __mul__(self, o):
		if type(o) is Vector: return ((self.x * o.x) + (self.y * o.y) + (self.z * o.z))
		else: return Vector(self.x * o, self.y * o, self.z * o)
	
	def __iadd__(self, o):
		self.x += o.x
		self.y += o.y
		self.z += o.z
		return self
	
	def __isub__(self, o):
		self.x -= o.x
		self.y -= o.y
		self.z -= o.z
		return self
	
	def __neg__(self):
		return Vector(-self.x, -self.y, -self.z)
	
	def length(self):
		return sqrt(self.x*self.x + self.y*self.y + self.z*self.z)
	
	def normalize(self):
		return Vector((self.x / self.length()), (self.y / self.length()), (self.z / self.length()))

def from_points(a=Point(0,0,0), b=Point(0,0,0)):
	return Vector(b.x - a.x, b.y - a.y, b.z - a.z)

def angle(a, b):
	m = a.x*b.x + a.y*b.y + a.z*b.z
	return degrees(acos(__fix_cosinus__(m / (a.length() * b.length()))))

def horizontal_angle(a, b):
	return angle(Vector(a.x, a.y, 0), Vector(b.x, b.y, 0))

def vertical_angle(a, b):
	return angle(Vector(0, a.y, a.z), Vector(0, b.y, b.z))

def __fix_cosinus__(a):
	if a > 1: return 1
	if a < -1: return -1
	else: return a