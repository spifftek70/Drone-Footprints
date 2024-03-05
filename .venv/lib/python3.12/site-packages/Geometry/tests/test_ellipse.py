
import unittest

from .. import Point, Ellipse, Rectangle, Triangle, Segment
from ..exceptions import *

class EllipseTestCase(unittest.TestCase):
    
    def testEllipseCreationWithNoArgumentsOrKeywords(self):
        e = Ellipse()
        self.assertIsInstance(e,Ellipse)
        self.assertListEqual(e.center.xyz,[0]*3)
        self.assertEqual(e.x_radius,1)
        self.assertEqual(e.y_radius,1)

    def testEllipseCreationWithOnlyCenterArgument(self):
        p = Point.gaussian()
        e = Ellipse(p)
        self.assertIsInstance(e,Ellipse)
        self.assertListEqual(e.center.xyz,p.xyz)
        self.assertEqual(e.x_radius,1)
        self.assertEqual(e.y_radius,1)

    def testEllipseCreationWithOnlyCenterKeyword(self):
        p = Point.gaussian()
        e = Ellipse(center=p)
        self.assertIsInstance(e,Ellipse)
        self.assertListEqual(e.center.xyz,p.xyz)
        self.assertEqual(e.x_radius,1)
        self.assertEqual(e.y_radius,1)

    def testEllipseCreationWithOnlyXRadiusKeyword(self):
        e = Ellipse(x_radius=2)
        self.assertIsInstance(e,Ellipse)
        self.assertListEqual(e.center.xyz,[0]*3)
        self.assertEqual(e.x_radius,2)
        self.assertEqual(e.y_radius,1)

    def testEllipseCreationWithOnlyYRadiusKeyword(self):
        e = Ellipse(y_radius=2)
        self.assertIsInstance(e,Ellipse)
        self.assertListEqual(e.center.xyz,[0]*3)
        self.assertEqual(e.x_radius,1)
        self.assertEqual(e.y_radius,2)

    def testEllipseCreationWithOnlyRadiusKeywords(self):
        e = Ellipse(x_radius=2,y_radius=3)
        self.assertIsInstance(e,Ellipse)
        self.assertListEqual(e.center.xyz,[0]*3)
        self.assertEqual(e.x_radius,2)
        self.assertEqual(e.y_radius,3)

    def testEllipseCreationWithAllKeywords(self):
        p = Point.gaussian()
        e = Ellipse(center=p,x_radius=2,y_radius=3)
        self.assertIsInstance(e,Ellipse)
        self.assertListEqual(e.center.xyz,p.xyz)        
        self.assertEqual(e.x_radius,2)
        self.assertEqual(e.y_radius,3)

    def testEllipseCreationWithCenterAndXRadius(self):
        p = Point.gaussian()
        e = Ellipse(p,2)
        self.assertIsInstance(e,Ellipse)
        self.assertListEqual(e.center.xyz,p.xyz)
        self.assertEqual(e.x_radius,2)
        self.assertEqual(e.y_radius,1)

    def testEllipseCreationWithCenterAndRadii(self):
        p = Point.gaussian()
        e = Ellipse(p,2,3)
        self.assertIsInstance(e,Ellipse)
        self.assertListEqual(e.center.xyz,p.xyz)
        self.assertEqual(e.x_radius,2)
        self.assertEqual(e.y_radius,3)

    def testEllipseSettingCenterAttribute(self):
        
        for p in [Point(2,2,2), Point.gaussian()]:
            e = Ellipse()
            e.center = p
            self.assertListEqual(e.center.xyz,p.xyz)

        e = Ellipse(Point.gaussian())
        e.center = None
        self.assertListEqual(e.center.xyz,[0]*3)

        e = Ellipse()
        e.center = [1]*3
        self.assertListEqual(e.center.xyz,[1]*3)

    def testEllipseSettingXRadiusWithNumbers(self):
        
        for n in [ 2, 3.4, '5', '6.7' ]:
            e = Ellipse()
            e.x_radius = n
            self.assertListEqual(e.center.xyz,[0]*3)
            self.assertEqual(e.x_radius,float(n))
            self.assertEqual(e.y_radius,1)

    def testEllipseSettingYRadiusWithNumbers(self):
        
        for n in [ 2, 3.4, '5', '6.7' ]:
            e = Ellipse()
            e.y_radius = n
            self.assertListEqual(e.center.xyz,[0]*3)
            self.assertEqual(e.x_radius,1)
            self.assertEqual(e.y_radius,float(n))

    def testEllipseSettingXRadiusWithNonNumbers(self):

        with self.assertRaises(ValueError):
            e = Ellipse()
            e.x_radius = 'fail'

        for fail in [ None, [], {}, () ]:
            with self.assertRaises(TypeError):
                e = Ellipse()
                e.x_radius = fail

    def testEllipseSettingYRadiusWithNonNumbers(self):

        with self.assertRaises(ValueError):
            e = Ellipse()
            e.y_radius = 'fail'

        for fail in [ None, [], {}, () ]:
            with self.assertRaises(TypeError):
                e = Ellipse()
                e.y_radius = fail                

    def testEllipseCenterGetter(self):
        e = Ellipse()
        c = e.center
        self.assertIsInstance(c,Point)
        self.assertListEqual(c.xyz,[0]*3)

    def testEllipseXRadiusGetter(self):
        e = Ellipse(x_radius=2)
        xr = e.x_radius
        self.assertIsInstance(xr,float)
        self.assertEqual(xr,2)

    def testEllipseYRadiusGetter(self):
        e = Ellipse(y_radius=2)
        yr = e.y_radius
        self.assertIsInstance(yr,float)
        self.assertEqual(yr,2)

    def testEllipseMappingGetter(self):
        e = Ellipse()
        m = e.mapping
        self.assertIsInstance(m,dict)
        self.assertEqual(len(m),3)
        self.assertIsInstance(m['center'],Point)
        self.assertListEqual(m['center'].xyz,[0]*3)
        self.assertIsInstance(m['x_radius'],float)
        self.assertEqual(m['x_radius'],1)
        self.assertIsInstance(m['y_radius'],float)
        self.assertEqual(m['y_radius'],1)

    def testEllipseMajorRadiusGetter(self):
        e = Ellipse()
        maj = e.majorRadius
        self.assertIsInstance(maj,float)
        self.assertEqual(maj,1)

        e = Ellipse(x_radius=2)
        maj = e.majorRadius
        self.assertIsInstance(maj,float)
        self.assertEqual(maj,2)

        e = Ellipse(y_radius=3)
        maj = e.majorRadius
        self.assertIsInstance(maj,float)
        self.assertEqual(maj,3)

    def testEllipseMinorRadiusGetter(self):
        e = Ellipse()
        minor = e.minorRadius
        self.assertIsInstance(minor,float)
        self.assertEqual(minor,1)

        e = Ellipse(x_radius=2)
        minor = e.minorRadius
        self.assertIsInstance(minor,float)
        self.assertEqual(minor,1)

        e = Ellipse(y_radius=3)
        minor = e.minorRadius
        self.assertIsInstance(minor,float)
        self.assertEqual(minor,1)        

    def testEllipseXAxisIsMajorGetter(self):
        e = Ellipse(y_radius=2)
        self.assertFalse(e.xAxisIsMajor)
        e = Ellipse(x_radius=2)
        self.assertTrue(e.xAxisIsMajor)

    def testEllipseXAxisIsMinorGetter(self):
        e = Ellipse(y_radius=2)
        self.assertTrue(e.xAxisIsMinor)
        e = Ellipse(x_radius=2)
        self.assertFalse(e.xAxisIsMinor)

    def testEllipseYAxisIsMajorGetter(self):
        e = Ellipse(x_radius=2)
        self.assertFalse(e.yAxisIsMajor)
        e = Ellipse(y_radius=2)
        self.assertTrue(e.yAxisIsMajor)

    def testEllipseYAxisIsMinorGetter(self):
        e = Ellipse(y_radius=2)
        self.assertFalse(e.yAxisIsMinor)
        e = Ellipse(x_radius=2)
        self.assertTrue(e.yAxisIsMinor)                

    def testEllipseEccentricityGetter(self):
        e = Ellipse()

        self.assertEqual(e.eccentricity,0)
        self.assertEqual(e.e,0)
        
        for y in range(1,5,10000000):
            e.y_radius = y
            self.assertLessEqual(e.eccentricity,1)
            self.assertLessEqual(e.e,1)

        for x in range(1,5,10000000):
            e.x_radius = x
            self.assertLessEqual(e.eccentricity,1)
            self.assertLessEqual(e.e,1)

    def testEllipseLinearEccentricityGetter(self):
        e = Ellipse()
        self.assertEqual(e.linearEccentricity,0)
        self.assertEqual(e.f,0)
        # XXX need more tests

    def testEllipsePositiveAntipodalPointOnMajorAxis(self):
        e = Ellipse(x_radius=2)
        p = e.a
        self.assertIsInstance(p,Point)
        self.assertListEqual(p.xyz,[2,0,0])
        
    def testEllipseNegativeAntipodalPointOnMajorAxis(self):
        e = Ellipse(x_radius=2)
        p = e.a_neg
        self.assertIsInstance(p,Point)
        self.assertListEqual(p.xyz,[-2,0,0])

    def testEllipsePositiveAntipodalPointOnMinorAxis(self):
        e = Ellipse(x_radius=2)
        p = e.b
        self.assertIsInstance(p,Point)
        self.assertListEqual(p.xyz,[0,1,0])        
        
    def testEllipseNegativeAntipodalPointOnMinorAxis(self):
        e = Ellipse(x_radius=2)
        p = e.b_neg
        self.assertIsInstance(p,Point)
        self.assertListEqual(p.xyz,[0,-1,0])

    def testEllipseVerticesGetter(self):
        e = Ellipse(x_radius=2)
        verts = e.vertices
        self.assertIsInstance(verts,dict)
        self.assertEqual(len(verts),4)
        for k,p in verts.items():
            v = getattr(e,k)
            self.assertIsInstance(p,Point)
            self.assertListEqual(p.xyz,v.xyz)

    def testEllipseFocus0Getter(self):
        e = Ellipse()
        for f in [e.focus0, e.f0]:
            self.assertIsInstance(f,Point)
            self.assertListEqual(f.xyz,[0]*3)

    def testEllipseFocus1Getter(self):
        e = Ellipse()
        for f in [e.focus1, e.f1]:
            self.assertIsInstance(f,Point)
            self.assertListEqual(f.xyz,[0]*3)

    def testEllipseFociGetter(self):
        e = Ellipse()
        ff = e.foci
        self.assertIsInstance(ff,list)
        self.assertIsInstance(ff[0],Point)
        self.assertListEqual(ff[0].xyz,e.focus0.xyz)
        self.assertIsInstance(ff[1],Point)
        self.assertListEqual(ff[1].xyz,e.focus1.xyz)

    def testEllipseMajorAxisGetter(self):
        e = Ellipse(x_radius=2)
        major = e.majorAxis
        self.assertIsInstance(major,Segment)
        self.assertEqual(major.length,4)

        e = Ellipse(y_radius=2)
        major = e.majorAxis
        self.assertIsInstance(major,Segment)
        self.assertEqual(major.length,4)        

    def testEllipseMinorAxisGetter(self):
        e = Ellipse(x_radius=2)
        minor = e.minorAxis
        self.assertIsInstance(minor,Segment)        
        self.assertEqual(minor.length,2)

        e = Ellipse(y_radius=2)
        minor = e.minorAxis
        self.assertIsInstance(minor,Segment)
        self.assertEqual(minor.length,2)

    def testEllipseIsCircleProperty(self):
        e = Ellipse()
        self.assertTrue(e.isCircle)
        e = Ellipse(x_radius=2)
        self.assertFalse(e.isCircle)

    def testEllipseIsEllipseProperty(self):
        e = Ellipse()
        self.assertFalse(e.isEllipse)
        e = Ellipse(x_radius=2)
        self.assertTrue(e.isEllipse)

    def testEllipseEqualityInstanceMethod(self):
        a = Ellipse()
        b = Ellipse()
        
        self.assertFalse(a is b)
        self.assertTrue(a == b)
        self.assertFalse(a != b)

        b.center = Point.gaussian()
        self.assertFalse(a == b)
        self.assertTrue(a != b)

        b = Ellipse(x_radius=2)
        self.assertFalse(a == b)
        self.assertTrue(a != b)

        b = Ellipse(y_radius=2)
        self.assertFalse(a == b)
        self.assertTrue(a != b)

        b = Ellipse(Point([1,1,1]),2,3)
        self.assertFalse(a == b)
        self.assertTrue(a != b)

        b.center = None
        b.x_radius = 1
        b.y_radius = 1
        self.assertTrue(a == b)
        self.assertFalse(a != b)

    def testEllipseContainsInstanceMethodWithPointArgument(self):
        
        e = Ellipse(x_radius=2)
        self.assertTrue(e.f0 in e)
        self.assertTrue(e.f1 in e)
        self.assertTrue(e.center in e)
        for k,v in e.vertices.items():
            self.assertTrue(v in e,'{k} = {v}'.format(k=k,v=v))
            self.assertFalse(v * 2 in e,'{k} = {v}'.format(k=k,v=v))


    def testEllipseContainsInstanceMethodWithSegmentArgument(self):
        e = Ellipse(x_radius=2)
        s = Segment(e.f0,e.f1)
        self.assertTrue(s in e)
        self.assertTrue(e.majorAxis in e)
        self.assertTrue(e.minorAxis in e)
        s.B *= e.majorRadius
        self.assertFalse(s in e)
        s.A *= e.minorRadius
        self.assertFalse(s in e)
        
    def testEllipseContainsInstanceMethodWithEllipseArgument(self):
        e = Ellipse(x_radius=3,y_radius=2)
        a = Ellipse(Point(1,0),1,1)
        b = Ellipse(e.a)
        self.assertTrue(e in e)
        self.assertTrue(a in e)
        self.assertFalse(b in e)
        self.assertFalse(b in a)

    def testEllipseContainsInstanceMethodWithWrongTypeArgument(self):
        e = Ellipse()
        for fail in [ None, [], {}, (), set(), 1, 1.0, "fail" ]:
            with self.assertRaises(TypeError):
                fail in e
        
