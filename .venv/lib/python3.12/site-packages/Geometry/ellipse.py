'''a pythonic Ellipse.

Super awesome.
'''

import math
from .point import Point
from .rectangle import Rectangle
from .triangle import Triangle
from .line import Line, Segment
from .constants import epsilon


class Ellipse(object):
    '''
    Implements an ellipse in the XY plane with the supplied radii.

    Returns a unit ellipse centered on the origin by default.

    Usage:
    >>> from Geometry import Ellipse
    >>> e = Ellipse()
    >>> e.isCircle
    True
    >>> type(e)
    <class 'Geometry.ellipse.Ellipse'>
    >>> e.x_radius *= 2
    >>> e.isCircle,e.isEllipse
    (False,True)

    
    '''
    
    def __init__(self,center=None,x_radius=1,y_radius=1):
        '''
        :param: center    - optional Point subclass initializer
        :param: x_radius  - optional float
        :param: y_radius  - optional float
        Defaults to a unit ellipse centered on the origin.

        '''
        # XXX implement radius with a Point instead of scalar
        #     get a z radius
        #     simplifies circle subclass
        self.center   = center
        self.x_radius = x_radius
        self.y_radius = y_radius
        

    @property
    def x_radius(self):
        '''
        The absolute value of the X ordinate of a point on the ellipse
        when y == 0, float.

        '''
        try:
            return self._x_radius
        except AttributeError:
            pass
        self._x_radius = 1.0
        return self._x_radius

    @x_radius.setter
    def x_radius(self,newValue):
        self._x_radius = float(newValue)

    @property
    def y_radius(self):
        '''
        The absolute value of the Y ordinate of a point on the ellipse
        when y == 0, float.

        '''
        try:
            return self._y_radius
        except AttributeError:
            pass
        self._y_radius = 1.0
        return self._y_radius

    @y_radius.setter
    def y_radius(self,newValue):
        self._y_radius = float(newValue)

    @property
    def center(self):
        '''
        Center point of the ellipse, equidistance from foci, Point subclass.
        Defaults to the origin.

        '''
        try:
            return self._center
        except AttributeError:
            pass
        self._center = Point()
        return self._center

    @center.setter
    def center(self,newCenter):
        self.center.xyz = newCenter
        
    @property
    def mapping(self):
        '''
        A mapping of ellipse attribute names to attribute values, dict.
        '''
        return { 'x_radius':self.x_radius,
                 'y_radius':self.y_radius,
                 'center':self.center}

    def __str__(self):
        '''
        '''
        output = 'center=({center}), x_radius={x_radius}, y_radius={y_radius}'
        return output.format(**self.mapping) 

    def __repr__(self):
        '''
        '''
        return '{klass}({args})'.format(klass=self.__class__.__name__,
                                        args =str(self))
    
    def __hash__(self):
        '''
        '''
        # this will cause circles/ellipses to hash to points
        return hash(self.center)
    
    @property
    def majorRadius(self):
        '''
        The longest radius of the ellipse, float.

        '''
        return max(self.x_radius,self.y_radius)

    @property
    def minorRadius(self):
        '''
        The shortest radius of the ellipse, float.

        '''
        return min(self.x_radius,self.y_radius)

    @property
    def xAxisIsMajor(self):
        '''
        Returns True if the major axis is parallel to the X axis, boolean.
        '''
        return max(self.x_radius,self.y_radius) == self.x_radius

    @property
    def xAxisIsMinor(self):
        '''
        Returns True if the minor axis is parallel to the X axis, boolean.
        '''
        return min(self.x_radius,self.y_radius) == self.x_radius

    @property
    def yAxisIsMajor(self):
        '''
        Returns True if the major axis is parallel to the Y axis, boolean.
        '''
        return max(self.x_radius,self.y_radius) == self.y_radius

    @property
    def yAxisIsMinor(self):
        '''
        Returns True if the minor axis is parallel to the Y axis, boolean.
        '''
        return min(self.x_radius,self.y_radius) == self.y_radius

    @property
    def eccentricity(self):
        '''
        The ratio of the distance between the two foci to the length
        of the major axis, float.

        0 <= e <= 1

        An eccentricity of zero indicates the ellipse is a circle.

        As e tends towards 1, the ellipse elongates.  It tends to the
        shape of a line segment if the foci remain a finite distance
        apart and a parabola if one focus is kept fixed as the other
        is allowed to move arbitrarily far away.

        '''
        return math.sqrt(1-((self.minorRadius / self.majorRadius)**2))

    @property
    def e(self):
        '''
        Shorthand notation for eccentricity, float.

        '''
        return self.eccentricity

    @property
    def linearEccentricity(self):
        '''
        Distance between the center of the ellipse and a focus, float.

        '''
        return math.sqrt((self.majorRadius**2) - (self.minorRadius**2))

    @property
    def f(self):
        '''
        Shorthand notation for linearEccentricity, float.

        '''
        return self.linearEccentricity


    @property
    def a(self):
        '''
        Positive antipodal point on the major axis, Point subclass.

        '''
        a = Point(self.center)
        
        if self.xAxisIsMajor:
            a.x += self.majorRadius
        else:
            a.y += self.majorRadius
        return a


    @property
    def a_neg(self):
        '''
        Negative antipodal point on the major axis, Point subclass.
        
        '''
        na = Point(self.center)
        
        if self.xAxisIsMajor:
            na.x -= self.majorRadius
        else:
            na.y -= self.majorRadius
        return na

    @property
    def b(self):
        '''
        Positive antipodal point on the minor axis, Point subclass.

        '''
        b = Point(self.center)

        if self.xAxisIsMinor:
            b.x += self.minorRadius
        else:
            b.y += self.minorRadius
        return b
    

    @property
    def b_neg(self):
        '''
        Negative antipodal point on the minor axis, Point subclass.
        '''
        nb = Point(self.center)

        if self.xAxisIsMinor:
            nb.x -= self.minorRadius
        else:
            nb.y -= self.minorRadius
        return nb

    @property
    def vertices(self):
        '''
        A dictionary of four points where the axes intersect the ellipse, dict.
        '''
        return { 'a':self.a, 'a_neg':self.a_neg,
                 'b':self.b, 'b_neg':self.b_neg }

    @property
    def focus0(self):
        '''
        First focus of the ellipse, Point subclass.

        '''
        f = Point(self.center)
        
        if self.xAxisIsMajor:
            f.x -= self.linearEccentricity
        else:
            f.y -= self.linearEccentricity
        return f
               
    @property
    def f0(self):
        '''
        Shorthand notation for focus0, Point subclass
        '''
        return self.focus0

    @property
    def focus1(self):
        '''
        Second focus of the ellipse, Point subclass.
        '''
        f = Point(self.center)

        if self.xAxisIsMajor:
            f.x += self.linearEccentricity
        else:
            f.y += self.linearEccentricity
        return f

    @property
    def f1(self):
        '''
        Shorthand notation for focus1, Point subclass
        '''
        return self.focus1

    @property
    def foci(self):
        '''
        A list containing the ellipse's foci, list.

        '''
        return [self.focus0,self.focus1]

    @property
    def majorAxis(self):
        '''
        A line coincident with the ellipse's major axis, Segment subclass.
        The major axis is the largest distance across an ellipse.

        '''
        return Segment(self.a_neg,self.a)

    @property
    def minorAxis(self):
        '''
        A line coincident with the ellipse' minor axis, Segment subclass.
        The minor axis is the smallest distance across an ellipse.

        '''
        return Segment(self.b_neg,self.b)

    @property
    def isCircle(self):
        '''
        Is true if the major and minor axes are equal, boolean.

        '''
        return self.x_radius == self.y_radius

    @property
    def isEllipse(self):
        '''
        Is true if the major and minor axes are not equal, boolean.

        '''
        return self.x_radius != self.y_radius

    def __eq__(self,other):
        '''
        x == y iff:
            x.center == y.center
            x.x_radius == y.x_radius
            x.y_radius == y.y_radius
        '''
        if self.center != other.center:
            return False

        if self.x_radius != other.x_radius:
            return False

        if self.y_radius != other.y_radius:
            return False

        return True

    def __contains__(self,other):
        '''
        x in y 

        Is true iff x is a point on or inside the ellipse y.

        '''

        otherType = type(other)

        if issubclass(otherType,Point):
            d = sum([other.distance(f) for f in self.foci])
            # d < majorAxis.length interior point
            # d == majorAxis.length on perimeter of ellipse
            # d > majorAxis.length exterior point
            return d <= self.majorAxis.length

        if issubclass(otherType,Segment):
            return (other.A in self) and (other.B in self)        

        if issubclass(otherType,Ellipse):
            return (other.majorAxis in self) and (other.minorAxis in self)

        raise TypeError("unknown type '{t}'".format(t=otherType))
        
            
    


class Circle(Ellipse):
    '''
    Implements a circle in the XY plane with the supplied
    center point and radius.

    Example usage:
    >>> from Geometry import Circle,Point
    >>> u = Circle()
    >>> u
    Circle((0.0,0.0,0.0),1.00)
    >>> import math
    >>> u.area == math.pi
    True
    >>> u.circumfrence == 2 * math.pi
    True
    >>> p = Point.gaussian()
    >>> p in u
    False
    >>> p.xyz = None
    >>> p in u
    True
    >>> p
    Point(0.0,0.0,0.0)
    
    '''

    @classmethod
    def inscribedInRectangle(cls,rectangle):
        raise NotImplementedError('inscribedInRectangle')

    @classmethod
    def inscribedInTriangle(cls,triangle):
        raise NotImplementedError('inscribedInTriangle')
        pass

    @classmethod
    def circumscribingRectangle(cls,rectangle):
        raise NotImplementedError('circumscribingRectangle')

    @classmethod
    def circumscribingTriangle(cls,triangle):
        raise NotImplementedError('circumscribingTriangle')

    @classmethod
    def circumcircleForTriangle(cls,triangle):
        '''
        :param: triangle - Triangle subclass
        :return: Circle subclass

        Returns the circle where every vertex in the input triangle is
        on the radius of that circle.

        '''
        
        if triangle.isRight:
            # circumcircle origin is the midpoint of the hypotenues
            o = t.hypotenuse.midpoint
            r = o.distance(t.A)
            return cls(o,r)

        # otherwise
        # 1. find the normals to two sides
        # 2. translate them to the midpoints of those two sides
        # 3. intersect those lines for center of circumcircle
        # 4. radius is distance from center to any vertex in the triangle

        abn  = t.AB.normal
        abn += t.AB.midpoint

        acn  = t.AC.normal
        acn += t.AC.midpoint

        o = abn.intersection(acn)
        r = o.distance(t.A)
        return cls(o,r)
    

    def __init__(self,center=None,radius=1.0):
        '''
        :param: center - optional Point subclass initializer
        :param: radius - optional float 
        Defaults to a unit circle centered on the origin.
        '''
        self.center = center
        self.radius = radius

    @Ellipse.x_radius.setter
    def x_radius(self,newValue):
        self._x_radius = self._y_radius = float(newValue)

    @Ellipse.y_radius.setter
    def y_radius(self,newValue):
        self._y_radius = self._x_radius = float(newValue)
        
    @property
    def radius(self):
        '''
        The circle's radius, float.
        '''
        return self.x_radius

    @radius.setter
    def radius(self,newValue):
        self.x_radius = newValue

    @property
    def r(self):
        '''
        Shorthand notation for radius, float.
        '''
        return self.x_radius

    @r.setter
    def r(self,newValue):
        self.radius = newValue

    @property
    def diameter(self):
        '''
        The circle's diameter, float.
        '''
        return self.radius * 2

    @property
    def circumfrence(self):
        '''
        The circle's circumfrence, float.
        '''
        return 2 * math.pi * self.radius

    @property
    def area(self):
        '''
        The circle's area, float.
        '''
        return  math.pi * (self.radius**2)

# class Sphere(Circle):
#    @property
#    def volume(self):
#        '''
#        The spherical volume bounded by this circle, float.
#        '''
#        return (4./3.) * math.pi * (self.radius**3)
        
    def __contains__(self,other):
        '''
        :param: Point | Segment | Ellipse subclass
        :return: boolean

        Returns True if the distance from the center to the point
        is less than or equal to the radius.
        '''
        otherType = type(other)

        if issubclass(otherType,Point):
            return other.distance(self.center) <= self.radius

        if issubclass(otherType,Segment):
            return (other.A in self) and (other.B in self)

        if issubclass(otherType,Ellipse):
            return (other.majorAxis in self) and (other.minorAxis in self)

        raise TypeError("unknown type '{t}'".format(t=otherType))

    @property
    def mapping(self):
        return { 'center':self.center,'radius':self.radius }

    def __str__(self):
        '''
        '''
        return 'center=({center}), radius={radius}'.format(**self.mapping)

    def __add__(self,other):
        '''
        x + y => Circle(x.radius+y.radius,x.center.midpoint(y.center))
        
        Returns a new Circle object.

        '''
        try:
            return Circle(self.radius+other.radius,
                          self.center.midpoint(other.center))
        except AttributeError:
            return self.__radd__(other)

    def __radd__(self,other):
        '''
        x + y => Circle(x.radius+y,x.origin)

        Returns a new Circle object.
        '''
        # other isn't a circle
        return Circle(self.radius+other,self.center)

    def __iadd__(self,other):
        '''
        x += y => 
          x.center += y.center
          x.center /= 2
          x.radius += y.radius

        Updates the current object.
        '''
        try:
            self.center += other.center
            self.center /= 2.
            self.radius += other.radius
        except AttributeError:
            self.radius += other
        return self


    def __sub__(self,other):
        '''
        x - y => 

        Returns a new Circle object.
        '''
        raise NotImplementedError('__sub__')

    def __rsub__(self,other):
        '''
        x - y => 

        Returns a new Circle object.
        '''
        raise NotImplementedError('__rsub__')

    def __isub__(self,other):
        '''
        x -= y

        Updates the current object.
        '''
        raise NotImplementedError('__isub__')

    def __mul__(self,other):
        '''
        x * y => 

        Returns a new Circle object.
        '''
        raise NotImplementedError('__mul__')

    def __rmul__(self,other):
        '''
        x * y => 

        Returns a new Circle object.
        '''
        raise NotImplementedError('__rmul__')

    def __imul__(self,other):
        '''
        x *= y

        Returns a new Circle object
        Updates the current object..
        '''
        raise NotImplementedError('__imul__')

    def __floordiv__(self,other):
        '''
        x // y =>

        Returns a new Circle object.
        '''
        raise NotImplementedError('__floordiv__')
    
    def __rfloordiv__(self,other):
        '''
        x // y =>

        Returns a new Circle object.
        '''  
        raise NotImplementedError('__rfloordiv__')
    
    def __ifloordiv__(self,other):
        '''
        x //= y

        Updates the current object.
        '''
        raise NotImplementedError('__rfloordiv__')

    def __truediv__(self,other):
        '''
        x / y =>

        Returns a new Circle object.
        '''
        raise NotImplementedError('__truediv__')
    
    def __rtruediv__(self,other):
        '''
        x / y =>

        Returns a new Circle object.
        '''  
        raise NotImplementedError('__rtruediv__')
    
    def __itruediv__(self,other):
        '''
        x /= y

        Updates the current object.
        '''
        raise NotImplementedError('__rtruediv__')

    def __mod__(self,other):
        '''
        x % y 

        Returns a new Circle object
        '''
        raise NotImplementedError('__mod__')
    
    def __rmod__(self,other):
        '''
        x % y 

        Returns a new Circle object
        '''
        raise NotImplementedError('__rmod__')

    def __imod__(self,other):
        '''
        x %= y 

        Updates the current object.
        '''
        raise NotImplementedError('__imod__')

    def __pow__(self,other):
        '''
        x ** y 

        Returns a new Circle object
        '''
        raise NotImplementedError('__pow__')
    
    def __rpow__(self,other):
        '''
        x ** y 

        Returns a new Circle object
        '''
        raise NotImplementedError('__rpow__')

    def __ipow__(self,other):
        '''
        x **= y 

        Updates the current object.
        '''
        raise NotImplementedError('__ipow__')

    def __neg__(self):
        '''
        -x

        '''
        raise NotImplementedError('__neg__')

    def __pos__(self):
        '''
        +x

        '''
        raise NotImplementedError('__pos__')    

    def doesIntersect(self,other):
        '''
        :param: other - Circle subclass

        Returns True iff:
          self.center.distance(other.center) <= self.radius+other.radius
        '''

        otherType = type(other)

        if issubclass(otherType,Ellipse):
            distance = self.center.distance(other.center)
            radiisum = self.radius + other.radius
            return distance <= radiisum

        if issubclass(otherType,Line):
            raise NotImplementedError('doesIntersect,other is Line subclass')

        raise TypeError("unknown type '{t}'".format(t=otherType))
        
