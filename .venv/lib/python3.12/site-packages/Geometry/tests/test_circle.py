
import unittest
import math
import sys
sys.path.append('..')
from Geometry import Point, Circle, Rectangle, Triangle, Segment, Line
from Geometry.exceptions import *

class CircleInitializationTestCase(unittest.TestCase):

    def testCircleCreationWithNoArgumentsOrKeywords(self):
        c = Circle()
        self.assertIsInstance(c,Circle)
        self.assertListEqual(c.center.xyz,[0]*3)
        self.assertEqual(c.radius,1)

    def testCircleCreationWithOnlyCenterArgument(self):
        p = Point.gaussian()
        c = Circle(p)
        self.assertIsInstance(c,Circle)
        self.assertListEqual(c.center.xyz,p.xyz)
        self.assertEqual(c.radius,1)

    def testCircleCreationWithEmptyContainersAsCenterArgument(self):
        for thing in [None,[],(),{}]:
            c = Circle(thing)
            self.assertIsInstance(c,Circle)
            self.assertListEqual(c.center.xyz,[0]*3)
            self.assertEqual(c.radius,1)
        
    def testCircleCreationWithOnlyCenterKeyword(self):
        p = Point.gaussian()
        c = Circle(center=p)
        self.assertIsInstance(c,Circle)
        self.assertListEqual(c.center.xyz,p.xyz)
        self.assertEqual(c.radius,1)

    def testCircleCreationWithOnlyRadiusKeyword(self):
        c = Circle(radius=2)
        self.assertIsInstance(c,Circle)
        self.assertListEqual(c.center.xyz,[0]*3)
        self.assertEqual(c.radius,2)

    def testCircleCreationWithAllKeywords(self):
        p = Point.gaussian()
        c = Circle(center=p,radius=2)
        self.assertIsInstance(c,Circle)
        self.assertListEqual(c.center.xyz,p.xyz)
        self.assertEqual(c.radius,2)

    def testCircleCreationWithKeywordsReversed(self):        
        p = Point.gaussian()
        c = Circle(radius=3,center=p)
        self.assertIsInstance(c,Circle)
        self.assertListEqual(c.center.xyz,p.xyz)
        self.assertEqual(c.radius,3)

    def testCircleCreationWithCenterAndRadiusArguments(self):
        p = Point.gaussian()
        c = Circle(p,2)
        self.assertIsInstance(c,Circle)
        self.assertListEqual(c.center.xyz,p.xyz)
        self.assertEqual(c.radius,2)

class CircleAttributeSettersTestCase(unittest.TestCase):

    def testCircleSettingCenterAttribute(self):
        p = Point.gaussian()
        c = Circle()
        c.center = p
        self.assertListEqual(c.center.xyz,p.xyz)

        c = Circle(p)
        c.center = None
        self.assertListEqual(c.center.xyz,[0]*3)
                                 
    def testCircleSettingRadiusAttributeWithNumbers(self):
        for number in [ 2, 3.4, '5.6']:
            c = Circle()
            c.radius = number
            self.assertEqual(c.radius,float(number))

        for number in [ 2, 3.4, '5.6']:
            c = Circle()
            c.r = number
            self.assertEqual(c.r,float(number))            

    def testCircleSettingRadiusAttributeWithNonNumbers(self):    
        for fail in [ [],{},() ]:
            c = Circle()
            with self.assertRaises(TypeError):
                c.radius = fail
        with self.assertRaises(ValueError):
            c.radius = 'fail'

        for fail in [ [],{},() ]:
            c = Circle()
            with self.assertRaises(TypeError):
                c.r = fail
        with self.assertRaises(ValueError):
            c.r = 'fail'            

class CircleAttributeGettersTestCase(unittest.TestCase):

    def testCircleCenterAttributeGetter(self):
        c = Circle()
        self.assertIsInstance(c.center,Point)
        self.assertListEqual(c.center.xyz,[0]*3)

    def testCircleRadiusAttributeGetter(self):
        c = Circle()
        self.assertIsInstance(c.radius,float)
        self.assertIsInstance(c.r,float)

        self.assertEqual(c.radius,1)
        self.assertEqual(c.r,1)

    def testCircleMappingAttributeGetter(self):
        c = Circle()
        self.assertIsInstance(c.mapping,dict)
        self.assertEqual(len(c.mapping),2)
        self.assertIsInstance(c.mapping['radius'],float)
        self.assertEqual(c.mapping['radius'],1)
        self.assertIsInstance(c.mapping['center'],Point)
        self.assertListEqual(c.mapping['center'].xyz,[0]*3)

    def testCircleDiameterAttributeGetter(self):
        c = Circle()
        self.assertEqual(c.diameter,2)

    def testCircleCircumfrenceAttributeGetter(self):
        c = Circle()
        self.assertEqual(c.circumfrence,math.pi * 2)

    def testCircleAreaAttributeGetter(self):
        c = Circle()
        self.assertEqual(c.area,math.pi)


class CircleClassmethodsTestCase(unittest.TestCase):

    def testCircleInscribedInRectangle(self):
        with self.assertRaises(NotImplementedError):
            r = Rectangle()
            c = Circle.inscribedInRectangle(r)

    def testCircleInscribedInTriangle(self):
        with self.assertRaises(NotImplementedError):
            t = Triangle()
            e = Circle.inscribedInTriangle(t)    


class CircleInstanceMethodsTestCase(unittest.TestCase):

    def testCircleContainsPointInstanceMethod(self):
        c = Circle(radius=2)
        self.assertTrue(c.center in c)
        for v in c.vertices.values():
            self.assertTrue(v in c,'{x} in {y}'.format(x=repr(v),y=repr(c)))
        for v in c.vertices.values():
            v *= 2
            self.assertFalse(v in c,'{x} in {y}'.format(x=repr(v),y=repr(c)))

    def testCircleContainsSegmentInstanceMethod(self):
        c = Circle(radius=2)
        s = Segment([-1,0],[1,0])
        self.assertTrue(s in c,'{x} in {y}'.format(x=repr(s),y=repr(c)))

        s = Segment(c.a,c.a_neg)
        self.assertTrue(s in c,'{x} in {y}'.format(x=repr(s),y=repr(c)))

    def testCircleContainsCircleInstanceMethod(self):
        c = Circle(radius=2)
        a = Circle(center=[1,0])
        b = Circle(center=[3,3],radius=3)
        self.assertTrue(c in c,'{x} in {y}'.format(x=repr(c),y=repr(c)))
        self.assertTrue(a in c,'{x} in {y}'.format(x=repr(a),y=repr(c)))
        self.assertFalse(b in c,'{x} in {y}'.format(x=repr(b),y=repr(c)))

    def testCircleDoesIntersectCircleInstanceMethod(self):
        c = Circle()
        a = Circle(center=[c.radius,0])
        b = Circle(center=[2,2])

        self.assertTrue(c.doesIntersect(c))
        self.assertTrue(c.doesIntersect(a))
        self.assertFalse(c.doesIntersect(b))

    def testCircleDoesIntersectGarbageInstanceMethod(self):
        c = Circle()
        for fail in [ None, [], {}, (), 'fail', 1]:
            with self.assertRaises(TypeError):
                c.doesIntersect(fail)

    def testCircleDoesIntersectLineInstanceMethod(self):
        c = Circle()

        l = Line(c.a,c.a_neg)

        with self.assertRaises(NotImplementedError):
            c.doesIntersect(l)
        


if __name__ == '__main__':
    unittest.main()

