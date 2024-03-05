
import unittest
import math
import sys

from .. import Line, Segment, Ray, Point
from ..exceptions import *

class LineTestCase(unittest.TestCase):

    def testLineInitializationWithNoArguments(self):
        l = Line()
        # Line([0,0,0],[1,1,0])
        self.assertListEqual(l.A.xyz,[0]*3)
        self.assertListEqual(l.B.xyz,[0]*3)

    def testLineInitializaitonWithOneArgument(self):

        l = Line(Point([2]*3))
        self.assertListEqual(l.A.xyz,[2]*3)
        self.assertListEqual(l.B.xyz,[0]*3)

        l = Line(A=Point([2]*3))
        self.assertListEqual(l.A.xyz,[2]*3)
        self.assertListEqual(l.B.xyz,[0]*3)

        with self.assertRaises(UngrokkableObject):
            l = Line(A=self)

        l = Line(B=Point([2]*3))
        self.assertListEqual(l.A.xyz,[0]*3)
        self.assertListEqual(l.B.xyz,[2]*3)

        with self.assertRaises(UngrokkableObject):
            l = Line(B=self)

    def testLineInitializationWithTwoArguments(self):

        l = Line(A=Point(1,2,3),B=Point(4,5,6))
        self.assertListEqual(l.A.xyz,[1,2,3])
        self.assertListEqual(l.B.xyz,[4,5,6])

        with self.assertRaises(UngrokkableObject):
            l = Line(A=self,B=self)

    def testLineAGetter(self):
        l = Line(A=[1,2,3])
        self.assertListEqual(l.A.xyz,[1,2,3])

    def testLineASetter(self):
        l = Line()
        l.A = Point(1,1,1)
        self.assertListEqual(l.A.xyz,[1]*3)

    def testLineBGetter(self):
        l = Line(B=[1,2,3])
        self.assertListEqual(l.B.xyz,[1,2,3])

    def testLineBSetter(self):
        l = Line()
        l.B = Point(1,1,1)
        self.assertListEqual(l.B.xyz,[1]*3)
                             

    def testLineABGetter(self):

        l = Line([1,2,3],[4,5,6])
        A,B = l.AB
        self.assertListEqual(A.xyz,[1,2,3])
        self.assertListEqual(B.xyz,[4,5,6])

    def testLineABSetter(self):        
        
        l = Line()

        l.AB = [1,2,3],[4,5,6]
        self.assertListEqual(l.A.xyz,[1,2,3])
        self.assertListEqual(l.B.xyz,[4,5,6])

        l.AB = None
        self.assertListEqual(l.A.xyz,[0,0,0])
        self.assertListEqual(l.B.xyz,[0,0,0])

        l.AB = [1,1,1]
        self.assertListEqual(l.A.xyz,[1,1,1])
        self.assertListEqual(l.B.xyz,[0,0,0])

    def testLineFromLineWithMissingArgument(self):
        with self.assertRaises(TypeError):
            l = Line.fromLine()

    def testLineFromLineWithGoodLine(self):
        I,_,_ = Line.units()

        l = Line.fromLine(I)
        self.assertFalse(l is I)
        self.assertIsInstance(l,Line)
        self.assertIsInstance(I,Line)
        self.assertListEqual(l.A.xyz,I.A.xyz)
        self.assertListEqual(l.B.xyz,I.B.xyz)

    def testLineFromLineWithBadLine(self):
        with self.assertRaises(AttributeError):
            l = Line.fromLine(object())

    def testLineConversionFromSegmentWithMissingArgument(self):
        with self.assertRaises(TypeError):
            l = Line.fromSegment()

    def testLineConversionFromSegmentWithGoodSegment(self):
        s = Segment([1,2,3],[4,5,6])
        l = Line.fromSegment(s)
        self.assertFalse(s is l)
        self.assertIsInstance(s,Segment)
        self.assertIsInstance(l,Line)
        self.assertListEqual(l.A.xyz,s.A.xyz)
        self.assertListEqual(l.B.xyz,s.B.xyz)

    def testLineConversionFromSegmentWithBadSegment(self):
        with self.assertRaises(AttributeError):
            l = Line.fromSegment(object())

    def testLineConversionFromRayWithMissingArgument(self):
        with self.assertRaises(TypeError):
            l = Line.fromRay()

    def testLineConversionFromRayWithGoodRay(self):
        r = Ray([1,2,3],[4,5,6])
        l = Line.fromRay(r)
        self.assertFalse(r is l)
        self.assertIsInstance(r,Ray)
        self.assertIsInstance(l,Line)
        self.assertListEqual(l.A.xyz,r.A.xyz)
        self.assertListEqual(l.B.xyz,r.B.xyz)

    def testLineConversionFromRayWithBadRay(self):
        with self.assertRaises(AttributeError):
            l = Line.fromRay(object())

    def testLineClassmethodUnits(self):
        I,J,K = Line.units()

        self.assertIsInstance(I,Line)
        self.assertEqual(I.A.distance(I.B),1)
        
        self.assertIsInstance(J,Line)
        self.assertEqual(J.A.distance(J.B),1)
        
        self.assertIsInstance(K,Line)
        self.assertEqual(K.A.distance(K.B),1)
        
    def testLinePropertySlopeParameterM(self):
        l = Line(Point(),Point(1,1,1))
        self.assertListEqual(l.m.xyz,[1,1,1])

    def testLinePropertyMapping(self):
        l = Line()
        m = l.mapping
        self.assertIsInstance(m,dict)
        for key in Line.vertexNames:
            self.assertEqual(getattr(l,key),m[key])

    def testLinePropertyLength(self):
        l = Line()
        with self.assertRaises(InfiniteLength):
            l.length

    def testLinePropertyNormal(self):
        _,j,_ = Point.units()
        I,_,_ = Line.units()
        self.assertListEqual(I.normal.A.xyz,j.xyz)

    def testLineInstanceMethodPointAt(self):
        l = Line(B=[1,0,0])
        self.assertListEqual(l.pointAt(0).xyz,l.A.xyz)
        self.assertListEqual(l.pointAt(1).xyz,l.B.xyz)
        self.assertListEqual(l.pointAt(0.5).xyz,[0.5,0,0])

    def testLineStringMethods(self):

        l = Line(Point.gaussian(),Point.gaussian())

        s = str(l)
        self.assertEqual(s.count('A='),1)
        self.assertEqual(s.count('B='),1)
        self.assertEqual(s.count('x='),2)
        self.assertEqual(s.count('y='),2)
        self.assertEqual(s.count('z='),2)        
        
        r = repr(l)
        self.assertTrue(r.startswith(Line.__name__))
        self.assertEqual(s.count('A='),1)
        self.assertEqual(s.count('B='),1)
        self.assertEqual(s.count('x='),2)
        self.assertEqual(s.count('y='),2)
        self.assertEqual(s.count('z='),2)

    def testLineIteratorMethods(self):
        l = Line([1,2,3],[4,5,6])
        self.assertEqual(len(l),2)
        self.assertListEqual(l[0].xyz,[1,2,3])
        self.assertListEqual(l[1].xyz,[4,5,6])
        self.assertListEqual(l[-2].xyz,[1,2,3])
        self.assertListEqual(l[-1].xyz,[4,5,6])
        with self.assertRaises(IndexError):
            l[2]
        with self.assertRaises(IndexError):
            l[-3]

    def testLineInstaceMethodContains(self):
        l = Line(B=[1,0,0])
        p = Point(.5)
        q = Point(y=.5)
        self.assertTrue(p in l)
        self.assertFalse(q in l)

    def testLineInstanceMethodFlip(self):
        l = Line(B=[1,1,1])
        l.flip()
        self.assertListEqual(l.A.xyz,[1,1,1])
        self.assertListEqual(l.B.xyz,[0,0,0])

    def testLineInstanceMethodDoesIntersect(self):
        l,m,_ = Line.units()

        o = Line([0,1,0],[1,1,0])

        self.assertTrue(l.doesIntersect(l))
        self.assertTrue(l.doesIntersect(m))
        self.assertFalse(l.doesIntersect(o))
        
    def testLineInstanceMethodIntersection(self):
        l,m,_ = Line.units()
        
        self.assertListEqual(l.intersection(m).xyz,[0,0,0])

        with self.assertRaises(CollinearLines):
            p = l.intersection(l)

        with self.assertRaises(ParallelLines):
            p = l.intersection(Line((0,1),(1,1)))

    def testLineInstanceMethodDistanceFromPoint(self):
        i,j,_ = Point.units()
        l,_,_ = Line.units()

        self.assertEqual(l.distanceFromPoint(i),0)
        self.assertEqual(l.distanceFromPoint(j),1)

    def testLineInstanceMethodIsNormal(self):
        l,m,_ = Line.units()
        self.assertTrue(l.isNormal(m))


    def testLineInstanceMethodRadiansBetween(self):
        l,m,_ = Line.units()
        self.assertEqual(l.radiansBetween(m),math.pi/2)
        self.assertEqual(l.radiansBetween(l),0)
        

    def testLineInstanceMethodDegreesBetween(self):
        l,m,_ = Line.units()

        self.assertEqual(l.degreesBetween(m),90)
        self.assertEqual(l.degreesBetween(l),0)
    

        


class SegmentTestCase(unittest.TestCase):

    def testSegmentInitializationWithNoArguments(self):
        s = Segment()
        # Segment([0,0,0],[1,1,0])
        self.assertListEqual(s.A.xyz,[0]*3)
        self.assertListEqual(s.B.xyz,[0]*3)

    def testSegmentInitializaitonWithOneArgument(self):

        s = Segment(Point([2]*3))
        self.assertListEqual(s.A.xyz,[2]*3)
        self.assertListEqual(s.B.xyz,[0]*3)

        s = Segment(A=Point([2]*3))
        self.assertListEqual(s.A.xyz,[2]*3)
        self.assertListEqual(s.B.xyz,[0]*3)

        with self.assertRaises(UngrokkableObject):
            s = Segment(A=self)

        s = Segment(B=Point([2]*3))
        self.assertListEqual(s.A.xyz,[0]*3)
        self.assertListEqual(s.B.xyz,[2]*3)

        with self.assertRaises(UngrokkableObject):
            s = Segment(B=self)

    def testSegmentInitializationWithTwoArguments(self):

        s = Segment(A=Point(1,2,3),B=Point(4,5,6))
        self.assertListEqual(s.A.xyz,[1,2,3])
        self.assertListEqual(s.B.xyz,[4,5,6])

        with self.assertRaises(UngrokkableObject):
            s = Segment(A=self,B=self)

    def testSegmentAGetter(self):
        s = Segment(A=[1,2,3])
        self.assertListEqual(s.A.xyz,[1,2,3])

    def testSegmentASetter(self):
        s = Segment()
        s.A = Point(1,1,1)
        self.assertListEqual(s.A.xyz,[1]*3)

    def testSegmentBGetter(self):
        s = Segment(B=[1,2,3])
        self.assertListEqual(s.B.xyz,[1,2,3])

    def testSegmentBSetter(self):
        s = Segment()
        s.B = Point(1,1,1)
        self.assertListEqual(s.B.xyz,[1]*3)
                             

    def testSegmentABGetter(self):
        s = Segment([1,2,3],[4,5,6])
        A,B = s.AB
        self.assertListEqual(A.xyz,[1,2,3])
        self.assertListEqual(B.xyz,[4,5,6])

    def testSegmentABSetter(self):        
        s = Segment()
        s.AB = [1,2,3],[4,5,6]
        self.assertListEqual(s.A.xyz,[1,2,3])
        self.assertListEqual(s.B.xyz,[4,5,6])
        s.AB = None
        self.assertListEqual(s.A.xyz,[0,0,0])
        self.assertListEqual(s.B.xyz,[0,0,0])
        s.AB = [1,1,1]
        self.assertListEqual(s.A.xyz,[1,1,1])
        self.assertListEqual(s.B.xyz,[0,0,0])

    def testSegmentConversionFromLineWithMissingArgument(self):
        with self.assertRaises(TypeError):
            s = Segment.fromSegment()

    def testSegmentConversionFromLineWithGoodLine(self):
        l = Line([1,2,3],[4,5,6])
        s = Segment.fromLine(l)
        
        self.assertFalse(s is l)
        self.assertIsInstance(l,Line)
        self.assertIsInstance(s,Segment)
        self.assertListEqual(s.A.xyz,l.A.xyz)
        self.assertListEqual(s.B.xyz,l.B.xyz)

    def testSegmentConversionFromRayWithMissingArgument(self):
        with self.assertRaises(TypeError):
            s = Segment.fromRay()

    def testSegmentConversionFromRayWithGoodRay(self):
        r = Ray([1,2,3],[4,5,6])
        s = Segment.fromRay(r)
        
        self.assertFalse(r is s)
        self.assertIsInstance(r,Ray)
        self.assertIsInstance(s,Segment)
        self.assertListEqual(s.A.xyz,r.A.xyz)
        self.assertListEqual(s.B.xyz,r.B.xyz)

    def testSegmentPropertySlopeParameterM(self):
        s = Segment(Point(),Point(1,1,1))
        
        self.assertListEqual(s.m.xyz,[1,1,1])

    def testSegmentPropertyMapping(self):
        s = Segment()
        
        m = s.mapping
        
        self.assertIsInstance(m,dict)
        for key in Segment.vertexNames:
            self.assertEqual(getattr(s,key),m[key])

    def testSegmentPropertyLength(self):
        i,j,k = Point.units()
        
        s = Segment(B=i)
        t = Segment(B=j)
        u = Segment(B=k)

        self.assertEqual(s.length,1)
        self.assertEqual(t.length,1)
        self.assertEqual(u.length,1)
        
    def testSegmentPropertyNormal(self):
        i,j,_ = Point.units()
        s = Segment(B=i)
        self.assertListEqual(s.normal.A.xyz,j.xyz)

    def testSegmentInstanceMethodPointAt(self):
        s = Segment(B=[1,0,0])
        self.assertListEqual(s.pointAt(0).xyz,s.A.xyz)
        self.assertListEqual(s.pointAt(1).xyz,s.B.xyz)
        self.assertListEqual(s.pointAt(0.5).xyz,[0.5,0,0])

    def testSegmentStringMethods(self):


        s = str(Segment(Point.gaussian(),Point.gaussian()))
        self.assertEqual(s.count('A='),1)
        self.assertEqual(s.count('B='),1)
        self.assertEqual(s.count('x='),2)
        self.assertEqual(s.count('y='),2)
        self.assertEqual(s.count('z='),2)        
        
        r = repr(Segment(Point.gaussian(),Point.gaussian()))
        self.assertTrue(r.startswith(Segment.__name__))
        self.assertEqual(s.count('A='),1)
        self.assertEqual(s.count('B='),1)
        self.assertEqual(s.count('x='),2)
        self.assertEqual(s.count('y='),2)
        self.assertEqual(s.count('z='),2)

    def testSegmentIteratorMethods(self):
        s = Segment([1,2,3],[4,5,6])
        
        self.assertEqual(len(s),2)
        self.assertListEqual(s[0].xyz,[1,2,3])
        self.assertListEqual(s[1].xyz,[4,5,6])
        self.assertListEqual(s[-2].xyz,[1,2,3])
        self.assertListEqual(s[-1].xyz,[4,5,6])
        with self.assertRaises(IndexError):
            s[2]
        with self.assertRaises(IndexError):
            s[-3]

    def testSegmentInstaceMethodContains(self):
        s = Segment(B=[1,0,0])
        p = Point(.5)
        q = Point(y=.5)
        self.assertTrue(p in s)
        self.assertFalse(q in s)

    def testSegmentInstanceMethodFlip(self):
        s = Segment(B=[1,1,1])
        s.flip()
        self.assertListEqual(s.A.xyz,[1,1,1])
        self.assertListEqual(s.B.xyz,[0,0,0])

    def testSegmentInstanceMethodDoesIntersect(self):
        i,j,_ = Point.units()
        s = Segment(B=i)
        t = Segment(B=j)
        o = Segment([0,1,0],[1,1,0])

        self.assertTrue(s.doesIntersect(s))
        self.assertTrue(s.doesIntersect(t))
        self.assertFalse(s.doesIntersect(o))
        
    def testSegmentInstanceMethodIntersection(self):
        i,j,_ = Point.units()
        s = Segment(B=i)
        t = Segment(B=j)
        self.assertListEqual(s.intersection(t).xyz,[0,0,0])

    def testSegmentInstanceMethodDistanceFromPoint(self):
        i,j,_ = Point.units()

        s = Segment(B=i)
        self.assertEqual(s.distanceFromPoint(j),1)
        self.assertEqual(s.distanceFromPoint(i),0)

    def testSegmentInstanceMethodIsNormal(self):
        i,j,_ = Point.units()

        s = Segment(B=i)
        t = Segment(B=j)

        self.assertTrue(s.isNormal(t))


    def testSegmentInstanceMethodRadiansBetween(self):
        i,j,_ = Point.units()

        s = Segment(B=i)
        t = Segment(B=j)

        self.assertEqual(s.radiansBetween(t),math.pi/2)
        self.assertEqual(s.radiansBetween(s),0)
        

    def testSegmentInstanceMethodDegreesBetween(self):
        i,j,_ = Point.units()

        s = Segment(B=i)
        t = Segment(B=j)

        self.assertEqual(s.degreesBetween(t),90)
        self.assertEqual(s.degreesBetween(s),0)
    
class RayTestCase(unittest.TestCase):
    pass
        
