'''a pythonic Line
'''

import math
from .point import Point
from .exceptions import *
from .constants import *

# 

class Line(object):
    vertexNames = 'AB'
    vertexNameA = vertexNames[0]
    vertexNameB = vertexNames[1]
    
    '''
    A line with infinite length defined by two points; A and B.

    Usage:
    >>> a = Line() 
    ...
    >>> b = Line((0,0),(1,1))
    >>> c = Line(Point(),{'y':1,'x':1])
    >>> b == c
    True
    >>> 
    '''
    
    @classmethod
    def fromSegment(cls,segment):
        '''
        :param: segment - Segment subclass
        :return: Line subclass

        Returns a coincident Line object.
        '''
        
        return cls(segment.A,segment.B)

    @classmethod
    def fromRay(cls,ray):
        '''
        :param: ray - Ray subclass
        :return: Line subclass

        Returns a coincident Line object.
        '''
        return cls(ray.A,ray.B)

    @classmethod
    def fromLine(cls,line):
        '''
        :param: line - Line subclass
        :return: Line subclass

        Returns a new coincident Line object.
        '''
        return cls(line.A,line.B)

    @classmethod
    def units(cls):
        '''
        Returns a list of three 'unit' lines whose first point is the origin
        and second points are (1,0,0), (0,1,0 and (0,0,1).
        '''
        return [cls(B=p) for p in Point.units()]


    def __init__(self,A=None,B=None):
        '''
        '''
        self.A = A
        self.B = B

    @property
    def A(self):
        '''
        A point on the line, Point subclass.
        '''
        try:
            return self._A
        except AttributeError:
            pass
        self._A = Point()
        return self._A
    
    @A.setter
    def A(self,newA):
        self.A.xyz = newA

    @property
    def B(self):
        '''
        A point on the line, Point subclass.
        '''
        try:
            return self._B
        except AttributeError:
            pass
        self._B = Point()
        return self._B
    
    @B.setter
    def B(self,newB):
        self.B.xyz = newB

    @property
    def AB(self):
        '''
        '''
        return [self.A,self.B]
    
    @AB.setter
    def AB(self,iterable):
        
        try:
            self.A,self.B = iterable
            return
        except TypeError:
            if iterable is None:
                self.A = None
                self.B = None
                return
        except ValueError:
            pass
            
        self.A = iterable

    @property
    def isVertical(self):
        '''
        XXX missing doc string
        '''
        return (self.A.x == self.B.x)

    @property
    def isHorizontal(self):
        '''
        XXX missing doc string
        '''
        return (self.A.y == self.B.y)
    
    @property
    def isCoplanar(self):
        # XXX what is the property of A.z == B.z called?
        '''
        XXX missing doc string
        '''
        return (self.A.z == self.B.z)
    
    @property
    def m(self):
        '''
        Slope parameter, Point(B - A).
        '''
        return self.B - self.A

    @property
    def mapping(self):
        return {self.vertexNameA:self.A.__class__(self.A),
                self.vertexNameB:self.B.__class__(self.B)}

    @property
    def length(self):
        '''
        Lines have an infinite length, raises InfiniteLength() exception.
        '''
        raise InfiniteLength()

    @property
    def normal(self):
        '''
        :return: Line
    
        Returns a line normal (perpendicular) to this line.
        '''
        
        d = self.B - self.A

        return Line([-d.y,d.x],[d.y,-d.x])    
    
    def pointAt(self,t):
        '''
        :param: t - float
        :return: Point subclass

        Varying 't' will produce a new point along this line.

        t = 0 -> point A
        t = 1 -> point B
        '''
        # p<xyz> = A<xyz> + t *( B<xyz> - A<xyz> )
        
        return self.A + (t * self.m)


    def t(self,point):
        '''
        :param: point - Point subclass
        :return: float

        If point is collinear, determine the 't' coefficient of
        the parametric equation:

        xyz = A<xyz> + t ( B<xyz> - A<xyz> )

        if t < 0, point is less than A and B on the line
        if t >= 0 and <= 1, point is between A and B
        if t > 1 point is greater than B

        XXX could use for an ordering on points?
        '''

        if point not in self:
            msg = "'{point}' is not collinear with '{line}'"
            raise CollinearPoints(msg.format(point=point,line=self))
        
        # p = A + t ( B - A)
        # p - A = t ( B - A)
        # p - A / (B -A) = t
        
        return (point-self.A) / self.m

    def __str__(self):
        '''

        '''
        return 'A=({A}), B=({B})'.format(**self.mapping)

    def __repr__(self):
        '''
        Returns a representation string of this instance.

        '''
        return '{klass}({args})'.format(klass=self.__class__.__name__,
                                        args=str(self))
    
    def __len__(self):
        '''
        Treat a line as a two item container with length '2'.
        '''
        return 2

    def __getitem__(self,key):
        '''
        index zero is equivalent to property A
        index one is equivalent to property B
        '''
        try:
            key = int(key)
            try:
                return self.AB[key]
            except IndexError:
                pass
            raise IndexError("index '{k}' out of range".format(k=key))
        except ValueError:
            pass
        raise ValueError("index '{k}' is not an integer".format(k=key))
        
    def __setitem__(self,key,value):
        '''
        index zero is equivalent to property A
        index one is equivalent to property B
        '''
        key = int(key)

        try:
            return [self.A,self.B][key]
        except IndexError:
            pass
        raise IndexError('index {i} out of range'.format(i=key))

    def __contains__(self,other):
        '''
        p in l

        Returns True iff p is a point and is collinear with l.A and l.B.

        Returns True iff p is a line and p.A is collinear with l.A and l.B.

        '''

        otherType = type(other)
        
        if issubclass(otherType,Point):
            return self.A.isCollinear(other,self.B)

        if issubclass(otherType,Line):
            if not self.A.isCollinear(other.A,self.B):
                return False
            return self.A.isCollinear(other.B,self.B)

        raise TypeError('unknown type {t}'.format(t=otherTYpe))

    def flip(self):
        '''
        :returns: None

        Swaps the positions of A and B.
        '''
        tmp = self.A.xyz
        self.A = self.B
        self.B = tmp

    def doesIntersect(self,other):
        '''
        :param: other - Line subclass
        :return: boolean

        Returns True iff:
           ccw(self.A,self.B,other.A) * ccw(self.A,self.B,other.B) <= 0
           and
           ccw(other.A,other.B,self.A) * ccw(other.A,other.B,self.B) <= 0

        '''
        if self.A.ccw(self.B,other.A) * self.A.ccw(self.B,other.B) > 0:
            return False

        if other.A.ccw(other.B,self.A) * other.A.ccw(other.B,self.B) > 0:
            return False

        return True

    def isParallel(self,other):
        '''
        :param: other - Line subclass
        :return: boolean

        Returns true if the two lines do not intersect and are not collinear.

        '''
        return not self.doesIntersect(other)

    def isCollinear(self,other):
        '''
        :param: other - Line subclass
        :return: boolean

        Returns true if the two lines are collinear.
        '''
        return other in self
        
    def intersection(self,other):
        '''
        :param: other - Line subclass
        :return: Point subclass

        Returns a Point object with the coordinates of the intersection
        between the current line and the other line. 

        Will raise Parallel() if the two lines are parallel.
        Will raise Collinear() if the two lines are collinear.
        '''

        if self.isCollinear(other):
            msg = '{s} and {o} are collinear'
            raise CollinearLines(msg.format(s=self,o=other))

        d0 = self.A - self.B
        d1 = other.A - other.B
        
        denominator = (d0.x * d1.y) - (d0.y * d1.x)
        
        if denominator == 0:
            msg = '{s} and {o} are parallel'
            raise ParallelLines(msg.format(s=self,o=other))
                                                                  
        cp0 = self.A.cross(self.B)
        cp1 = other.A.cross(other.B)
        
        x_num = (cp0 * d1.x) - (d0.x * cp1)
        y_num = (cp0 * d1.y) - (d0.y * cp1)

        p = Point( x_num / denominator, y_num / denominator)

        if p in self and p in other:
            return p

        # XXX thought this was accounted for in the denominator
        #     comparison to zero? I guess it can't hurt but I'm
        #     not sure how we would get here. Maybe a precision
        #     error?
        msg = "found point {p} but not in {a} and {b}"
        raise Parallel(msg.format(p=p,a=self,b=other))
    
    def distanceFromPoint(self,point):
        '''
        :param: point - Point subclass
        :return: float

        Distance from the line to the given point.
        '''
        # XXX planar distance, doesn't take into account z ?
        d = self.m
        n = (d.y*point.x) - (d.x*point.y) + self.A.cross(self.B)
        return abs(n / self.A.distance(self.B))


    def isNormal(self,other):
        '''
        :param: other - Line subclass
        :return: boolean

        Returns True if this line is perpendicular to the other line.
        '''

        return abs(self.degreesBetween(other)) == 90.0

    
    def radiansBetween(self,other):
        '''
        :param: other - Line subclass
        :return: float

        Returns the angle between two lines in radians [0, 2 * math.pi], float.

        '''
        # a.dot.b = |a||b| * cos(theta)
        # a.dot.b / |a||b| = cos(theta)
        # cos-1(a.dot.b / |a||b|) = theta

        # translate each line so that it passes through the origin and
        # produce a new point whose distance (magnitude) from the
        # origin is 1.
        #
        
        A = Point.unitize(self.A,self.B)
        B = Point.unitize(other.A,other.B)

        # in a perfect world, after unitize: |A| = |B| = 1
        # which is a noop when dividing the dot product of A,B
        # but sometimes they aren't but who cares?
        # let's just assume things are perfect.
        #
        #a = A.distance()
        #b = B.distance()
        #if abs(a - b) > epsilon:
        #    raise ExceededEpsilonError(a,b,epsilon)
        
        return math.acos(A.dot(B))

    def degreesBetween(self,other):
        '''
        :param: other - Line subclass
        :return: float

        Returns the angle between two lines in degrees [0,), float.
        '''
        return math.degrees(self.radiansBetween(other))

        
    
    
class Segment(Line):
    '''
    A Line subclass with finite length.
    '''

    @property
    def length(self):
        '''
        The scalar distance between A and B, float.
        '''
        return self.A.distance(self.B)

    @property
    def midpoint(self):
        '''
        The point between A and B, Point subclass.
        '''
        return self.A.midpoint(self.B)

    def __eq__(self,other):
        '''
        x == y iff:
         ((x.A == y.A) and (x.B == y.B)) 
           or 
         ((x.A == y.B) and (x.B == y.A))
        '''
        if (self.A == other.A) and (self.B == other.B):
            return True
        return (self.A == other.B) and (self.B == other.A)
        
    def __contains__(self,point):
        '''
        p in s
        Returns True iff:
               A,point,B are collinear and A.xyz <= point.xyz <= B.xyz
        '''
        if not super(self.__class__,self).__contains__(point):
            return False
        return point.isBetween(self.A,self.B)

    @property
    def normal(self):
        '''
        :return: Segment
    
        Returns a segment normal (perpendicular) to this segment.
        '''
        return Segment.fromLine(super(Segment,self).normal)
    
    
class Ray(Line):
    '''
    Rays have head and tail vertices with an infinite length in the
    direction of the head vertex.
    '''

    @property
    def head(self):
        '''
        The start (endpoint) of the ray, Point subclass.
        '''
        return self.A

    @head.setter
    def head(self,newValue):
        self.A = newValue    
    
    @property
    def tail(self):
        '''
        A point in the infinite direction of the ray, Point subclass.
        '''
        return self.B

    @tail.setter
    def tail(self,newValue):
        self.B = newValue

    def __eq__(self,other):
        '''
        x == y

        Returns true if x.head == y.head and y.tail.isCollinear(x.head,x.tail)
        '''
        return (self.head == other.head) and other.tail.isCollinear(self.head,self.tail)

    def __contains__(self,point):
        '''
        Returns true if point can be found in Ray.
        '''

        if not self.A.isCollinear(point,self.B):
            return False

        if self.A.isBetween(point,self.B):
            return False

        # point.isBetween(self.A,self.B) or self.B.isBetween(self.A,point):
        return True

    # intersection is tricky need to override
    
    def doesIntersect(self,other):
        raise NotImplementedError('doesIntersect')

    def isParallel(self,other):
        raise NotImplementedError('isParallel')

    def isCollinear(self,other):
        raise NotImplementedError('isCollinear')

    def intersection(self,other):
        raise NotImplementedError('intersection')


    @property
    def alpha(self):
        '''
        Angle in radians relative to the X axis.
        '''
        raise NotImplementedError('alpha')

    @property
    def beta(self):
        '''
        Angle in radians relative to the Y axis.
        '''
        raise NotImplementedError('beta')

    @property
    def gamma(self):
        '''
        Angle in radians relative to the Z axis.
        '''
        raise NotImplementedError('gamma')

    @property
    def normal(self):
        '''
        :return: Ray
    
        Returns a ray normal (perpendicular) to this segment.
        '''
        return Ray.fromLine(super(Ray,self).normal)

    # rays can be treated much like vectors so many of the point operations
    # can be reused here

    
