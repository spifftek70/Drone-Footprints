
import unittest
import sys

from .. import Point
from ..exceptions import *

class NumberFactory(object):
    @classmethod
    def List(cls,n=3,v=0):
        if n == 0:
            return []
        return [v]*n

    @classmethod
    def Dict(cls,keys='xyz',v=0):
        if len(keys) == 0:
            return {}
        return dict(zip(keys,[v]*len(keys)))

    @classmethod
    def Tuple(cls,n=3,v=0):
        if n == 0:
            return ()
        return tuple([v]*n)

    @classmethod
    def Object(cls,keys='xyz',v=0):
        class TestObject(object):
            def __init__(self,x=None,y=None,z=None):
                if x is not None:
                    self.x = x
                if y is not None:
                    self.y = y
                if z is not None:            
                    self.z = z
                    
        if len(keys) == 0:
            return TestObject()
                    
        mapping = cls.Dict(keys,v)
        return TestObject(**mapping)

    @classmethod
    def Point(cls,keys='xyz',v=0):
        return Point(cls.Dict(keys,v))

    @classmethod
    def Herd(cls,keys='xyz',v=0):
        n = len(keys)

        return [cls.List(n,v), cls.Dict(keys,v),
                cls.Tuple(n,v), cls.Object(keys,v),
                cls.Point(keys,v)]

    @classmethod
    def KeyMutator(cls,keys='xyz'):
        '''
        Kinda broke string mutator.
        '''

        s = set()
        s.add(keys)
        kks = []
        for k in keys:
            s.add(k)
            kks.extend([a+b for a,b in zip(keys,[k]*len(keys)) if a != b])

        kks.sort()
        for kk in kks:
            if kk in s or kk[::-1] in s:
                continue
            s.add(kk)
                
        l = list(s)
        l.sort()
        return l

class PointTestCase(unittest.TestCase):

    def assertIsOrigin(self,p):
        self.assertIsInstance(p,Point)
        self.assertListEqual(p.xyz,[0]*3)

    def assertPointsEqual(self,a,b):
        self.assertIsInstance(a,Point)
        self.assertIsInstance(b,Point)
        self.assertFalse(a is b)
        self.assertListEqual(a.xyz,b.xyz)

    def testPointCreationWithNoArgumentsOrKeywords(self):
        self.assertIsOrigin(Point())
        
    def testPointCreationFromNone(self):
        self.assertIsOrigin(Point(None))
        
    def testPointCreationFromEmptyTuple(self):
        self.assertIsOrigin(Point(()))
        
    def testPointCreationFromEmptyList(self):
        self.assertIsOrigin(Point([]))
        
    def testPointCreationFromEmptyDict(self):
        self.assertIsOrigin(Point({}))

    def testPointCreationFromEmptyObject(self):
        with self.assertRaises(UngrokkableObject):
            Point(NumberFactory.Object(keys=''))
        
    def testPointCreationFromAnotherDefaultPoint(self):
        a = Point()
        self.assertPointsEqual(Point(a),a)
        
    def testPointCreationFromAnotherInitializedPoint(self):
        a = Point(1,1,1)
        self.assertPointsEqual(Point(a),a)
        
    def testPointCreationFromDictionary(self):
        d = {'x':1,'y':1,'z':1}
        p = Point(d)
        self.assertListEqual(p.xyz,[d['x'],d['y'],d['z']])
        
    def testPointCreationFromConformingObject(self):
        o = NumberFactory.Object(v=1)
        p = Point(o)
        self.assertListEqual(p.xyz,[o.x,o.y,o.z])

    def testPointOrdinateW(self):
        p = Point()
        self.assertListEqual(p.xyzw,[0,0,0,1])
        self.assertIsInstance(p.w,float)
        self.assertEqual(p.w,1)
        with self.assertRaises(AttributeError):
            p.w = 2

    def testCreatePointWithRegularArguments(self):
        self.assertListEqual(Point(1).xyz,[1,0,0])
        self.assertListEqual(Point(1,1).xyz,[1,1,0])
        self.assertListEqual(Point(1,1,1).xyz,[1,1,1])
        
    def testCreatePointWithOnlyKeywords(self):
        self.assertListEqual(Point(x=1).xyz,[1,0,0])
        self.assertListEqual(Point(y=1).xyz,[0,1,0])
        self.assertListEqual(Point(z=1).xyz,[0,0,1])
        self.assertListEqual(Point(x=1,y=1).xyz,[1,1,0])
        self.assertListEqual(Point(x=1,z=1).xyz,[1,0,1])
        self.assertListEqual(Point(y=1,z=1).xyz,[0,1,1])
        self.assertListEqual(Point(x=1,y=1,z=1).xyz,[1,1,1])

    def testCreatePointWithArgumentsAndKeywords(self):

        self.assertListEqual(Point(1,x=2).xyz,[2,0,0])
        self.assertListEqual(Point(0,1,y=2).xyz,[0,2,0])
        self.assertListEqual(Point(0,0,1,z=2).xyz,[0,0,2])

        self.assertListEqual(Point(1,x=2,y=1).xyz,[2,1,0])
        self.assertListEqual(Point(0,1,y=2,x=1).xyz,[1,2,0])
        self.assertListEqual(Point(0,1,y=2,z=1).xyz,[0,2,1])
        self.assertListEqual(Point(0,0,1,z=2,x=1).xyz,[1,0,2])
        self.assertListEqual(Point(0,0,1,z=2,y=1).xyz,[0,1,2])
        
        self.assertListEqual(Point(1,x=2,y=1,z=1).xyz,[2,1,1])
        self.assertListEqual(Point(0,1,y=2,x=1,z=1).xyz,[1,2,1])
        self.assertListEqual(Point(0,1,y=2,z=1,x=1).xyz,[1,2,1])
        self.assertListEqual(Point(0,0,1,z=2,x=1,y=1).xyz,[1,1,2])
        self.assertListEqual(Point(0,0,1,z=2,y=1,x=1).xyz,[1,1,2])

        self.assertListEqual(Point(1,x=4,y=5,z=6).xyz,[4,5,6])
        self.assertListEqual(Point(1,2,x=4,y=5,z=6).xyz,[4,5,6])
        self.assertListEqual(Point(1,2,3,x=4,y=5,z=6).xyz,[4,5,6])
        

    def testCreatePointWithObjects(self):

        self.assertListEqual(Point(NumberFactory.List(v=1)).xyz,
                             NumberFactory.List(v=1))
        
        self.assertListEqual(Point(NumberFactory.Dict(v=1)).xyz,
                             NumberFactory.List(v=1))

        self.assertListEqual(Point(NumberFactory.Tuple(v=1)).xyz,
                             NumberFactory.List(v=1))
                                                      
        self.assertListEqual(Point(NumberFactory.Point(v=1)).xyz,
                             NumberFactory.List(v=1))
                                                      
        self.assertListEqual(Point(NumberFactory.Object(v=1)).xyz,
                             NumberFactory.List(v=1))

        with self.assertRaises(UngrokkableObject):
            Point(object())

    def testXYZSetter(self):
        
        p = Point(1,1,1)
        self.assertListEqual(p.xyz,NumberFactory.List(v=1))
                             
        p.xyz = None
        self.assertListEqual(p.xyz,NumberFactory.List(),'p.xyz = None')
        
        for thing in NumberFactory.Herd():
            msg = 'p.xyz = {t}({o})'.format(o=thing,t=thing.__class__.__name__)
            p = Point()
            p.xyz = thing
            self.assertListEqual(p.xyz,NumberFactory.List(),msg)

        with self.assertRaises(UngrokkableObject):
            p = Point()
            p.xyz = NumberFactory.Object(keys='')

        # scalars
        for value,result in [(1,[1,0,0]),((1,2),[1,2,0]),((1,2,3),[1,2,3])]:
            p = Point()
            p.xyz = value
            self.assertListEqual(p.xyz,result,'p.xyz = {v}'.format(v=value))

        # permuted list
        for n in range(0,4):
            p = Point()
            src = NumberFactory.List(n=n,v=1)
            p.xyz = src
            src.extend([0]*3)
            self.assertListEqual(p.xyz,src[:3])

        # permuted list
        for key in Point.ordinateNamesXYZ:
            p = Point()
            p.xyz = NumberFactory.Dict(key,v=1)
            self.assertEqual(getattr(p,key),1,
                             "p.{k} = dict('{k}':1)".format(k=key))
            
        # permuted object
        for key in 'xyz':
            p = Point()
            p.xyz = NumberFactory.Object(key,v=1)
            self.assertEqual(getattr(p,key),1,
                             'p.{k} = Object.{k} => 1'.format(k=key))
                
    def testXYSetterWithNone(self):

        p = Point(1,1,1)
        p.xy = None
        self.assertListEqual(p.xyz,[0,0,1],'p.xy = None')

    def testXYSetterFullyQualifiedObjects(self):

        for thing in NumberFactory.Herd(v=1):
            msg = 'p.xy = {t}({o})'.format(o=thing,t=thing.__class__.__name__)
            p = Point()
            p.xy = thing
            self.assertListEqual(p.xyz,[1,1,0],msg)

        with self.assertRaises(UngrokkableObject):
            p = Point()
            p.xy = NumberFactory.Object(keys='')
            
    def testXYSetterWithScalar(self):

        p = Point()
        p.xy = 1
        self.assertListEqual(p.xyz,[1,0,0])

    def testXYSetterWithPermutedList(self):        

        # permuted list
        for value,result in [([1],[1,0,0]),([1,2],[1,2,0])]:
            p = Point()
            p.xy = value
            self.assertListEqual(p.xyz,result,'p.xy = {v}'.format(v=value))

    def testXYSetterWithPermutedTuple(self):        
        # permuted tuple
        for value,result in [(1,[1,0,0]),((1,2),[1,2,0])]:
            p = Point()
            p.xy = value
            self.assertListEqual(p.xyz,result,'p.xy = {v}'.format(v=value))

    def testXYSetterWithPermutedDict(self):        
        # permuted dict
        for key in Point.ordinateNamesXYZ:
            p = Point()
            p.xy = NumberFactory.Dict(key,1)
            value = getattr(p,key)
            expected = int(key != 'z')
            self.assertEqual(value,expected,"p.{k} = dict('{k}':1)".format(k=key))
            
    def testXYSetterWithPermutedObject(self):        
        # permuted object
        for key in Point.ordinateNamesXYZ:
            p = Point()
            expected = int(key != 'z')
            if expected:
                p.xy = NumberFactory.Object(key,1)
                value = getattr(p,key)            
                self.assertEqual(value,expected,
                                 "p.{k} = obj('{k}':1)".format(k=key))
            else:
                with self.assertRaises(UngrokkableObject):
                    p.xy = NumberFactory.Object(key,1)
        

    def testYZSetterWithNone(self):

        p = Point(1,1,1)
        p.yz = None
        self.assertListEqual(p.xyz,[1,0,0],'p.yz = None')

    def testYZSetterWithFullyQualifiedObjects(self):        
        for thing in NumberFactory.Herd(v=1):
            msg = 'p.yz = {t}({o})'.format(o=thing,t=thing.__class__.__name__)
            p = Point()
            p.yz = thing
            self.assertListEqual(p.xyz,[0,1,1],msg)
            
        with self.assertRaises(UngrokkableObject):
            p = Point()
            p.yz = NumberFactory.Object(keys='')

    def testYZSetterWithScalar(self):
        p = Point()
        p.yz = 1
        self.assertListEqual(p.xyz,[0,1,0])

    def testYZSetterWithPermutedTuple(self):        
        for value,result in [(1,[0,1,0]),((1,2),[0,1,2])]:
            p = Point()
            p.yz = value
            self.assertListEqual(p.xyz,result,'p.xyz = {v}'.format(v=value))

        
    def testYZSetterWithPermutedDict(self):
        
        for key in Point.ordinateNamesXYZ:
            p = Point()
            expected = int(key != 'x')
            p.yz = NumberFactory.Dict(key,1)
            value = getattr(p,key)
            self.assertEqual(value,expected,
                             "p.{k} = dict('{k}':1)".format(k=key))

    def testYZSetterWithPermutedObject(self):            

        for key in Point.ordinateNamesXYZ:
            p = Point()
            expected = int(key != 'x')
            if expected:
                p.yz = NumberFactory.Object(key,1)
                self.assertEqual(getattr(p,key),expected,
                                 "p.{k} = obj('{k}'):1)".format(k=key))
            else:
                with self.assertRaises(UngrokkableObject):
                    p.yz = NumberFactory.Object(key,1)
    
    def testXZSetterWithNone(self):
        p = Point(1,1,1)
        p.xz = None
        self.assertListEqual(p.xyz,[0,1,0],'p.xz = None')

    def testXZSetterWithFullyQualifiedObjects(self):
        
        for thing in NumberFactory.Herd(v=1,keys='xz'):
            msg = 'p.xz = {t}({o})'.format(o=thing,t=thing.__class__.__name__)
            p = Point()
            p.xz = thing
            self.assertListEqual(p.xyz,[1,0,1],msg)

        with self.assertRaises(UngrokkableObject):
            p = Point()
            p.xz = NumberFactory.Object(keys='')

    def testXZSetterWithScalar(self):
        p = Point()
        p.xz = 1
        self.assertListEqual(p.xyz,[1,0,0])

    def testXZSetterWithPermutedTuple(self):            
        for value,result in [(1,[1,0,0]),((1,2),[1,0,2])]:
            p = Point()
            p.xz = value
            self.assertListEqual(p.xyz,result,'p.xyz = {v}'.format(v=value))

    def testXZSetterWithPermutedDict(self):            
        for key in Point.ordinateNamesXYZ:
            p = Point()
            p.xz = NumberFactory.Dict(key,1)
            expected = int(key != 'y')
            self.assertEqual(getattr(p,key),expected,
                             "p.{k} = dict('{k}':1)".format(k=key))

    def testXZSetterWithPermutedObject(self):            
        for key in Point.ordinateNamesXYZ:
            p = Point()
            expected = int(key != 'y')

            if expected:
                p.xz = NumberFactory.Object(key,1)
                self.assertEqual(getattr(p,key),expected,
                                 "p.{k} = dict('{k}':1)".format(k=key))
            else:
                with self.assertRaises(UngrokkableObject):
                    p.xz = NumberFactory.Object(key,1)
        
    def testPointCoordinateTypesForFloat(self):
        p = Point()
        self.assertIsInstance(p.x,float)
        self.assertIsInstance(p.y,float)
        self.assertIsInstance(p.z,float)

        for thing in NumberFactory.Herd():
            p = Point()
            p.xyz = thing
            self.assertIsInstance(p.x,float)
            self.assertIsInstance(p.y,float)
            self.assertIsInstance(p.z,float)

    def testPointAddition(self):

        p = Point()
        q = Point(1,1,1)

        r = p + p
        self.assertListEqual(r.xyz,[0]*3)

        r = p + q
        self.assertListEqual(r.xyz,[1]*3)

        r = q + q
        self.assertListEqual(r.xyz,[2]*3)

        r = q + 1
        self.assertListEqual(r.xyz,[2]*3)

        r += 1
        self.assertListEqual(r.xyz,[3]*3)

        r += q
        self.assertListEqual(r.xyz,[4]*3)
        

    def testPointSubtraction(self):
        
        p = Point()
        q = Point(1,1,1)

        r = p - q
        self.assertListEqual(r.xyz,[-1]*3)

        r = q - p
        self.assertListEqual(r.xyz,[1]*3)

        r = q - 1
        self.assertListEqual(r.xyz,[0]*3)

        r -= 1
        self.assertListEqual(r.xyz,[-1]*3)

        r -= q
        self.assertListEqual(r.xyz,[-2]*3)
        

    def testPointMultiplication(self):

        p = Point()
        q = Point(1,1,1)

        r = p * p
        self.assertListEqual(r.xyz,[0]*3)

        r = p * q
        self.assertListEqual(r.xyz,[0]*3)

        r = q * q
        self.assertListEqual(r.xyz,[1]*3)

        r = p * 1
        self.assertListEqual(r.xyz,[0]*3)

        r = q * 1
        self.assertListEqual(r.xyz,[1]*3)

        r *= q
        self.assertListEqual(r.xyz,[1]*3)

        r *= 1
        self.assertListEqual(r.xyz,[1]*3)

        r *= 0
        self.assertListEqual(r.xyz,[0]*3)

        
        

    def testPointTrueDivision(self):

        n = 2.
        m = 3.
        
        p = Point([n]*3)
        q = Point([m]*3)

        r = q / p
        self.assertListEqual(r.xyz,[m/n]*3)

        r = p / p
        self.assertListEqual(r.xyz,[1]*3) 

        r = p / q
        self.assertListEqual(r.xyz,[n/m]*3)

        r = p / NumberFactory.Object(v=1)
        self.assertListEqual(r.xyz,[n]*3)

        r = p / 2
        self.assertListEqual(r.xyz,[1]*3)

        r = p / 1
        self.assertListEqual(r.xyz,[n]*3)

        r /= 1
        self.assertListEqual(r.xyz,[n]*3)

        r /= n
        self.assertListEqual(r.xyz,[n/n]*3)

        with self.assertRaises(ZeroDivisionError):
            p = Point(1,1,1)
            q = Point()
            r = p / q

        with self.assertRaises(ZeroDivisionError):
            p = Point(1,1,1)
            r = q / 0

        with self.assertRaises(ZeroDivisionError):
            p = Point(1,1,1)
            r = q / NumberFactory.Object(v=0) 

        with self.assertRaises(ZeroDivisionError):
            p = Point(1,1,1)
            p /= Point()

        with self.assertRaises(ZeroDivisionError):
            p = Point(1,1,1)
            p /= 0            

    def testPointFloorDivision(self):

        n = 2.
        m = 3.
        
        p = Point([n]*3)
        q = Point([m]*3)

        r = p // p
        self.assertListEqual(r.xyz,[1]*3)

        r = q // p
        self.assertListEqual(r.xyz,[m//n]*3)

        r = p // q
        self.assertListEqual(r.xyz,[n//m]*3)

        r = p // NumberFactory.Object(v=1)
        self.assertListEqual(r.xyz,[n//1]*3)

        r = p // n
        self.assertListEqual(r.xyz,[n//n]*3)

        r = p // 1
        self.assertListEqual(r.xyz,[n]*3)

        r //= n
        self.assertListEqual(r.xyz,[1]*3)

        with self.assertRaises(ZeroDivisionError):
            r = p // NumberFactory.Point()

        with self.assertRaises(ZeroDivisionError):
            r = p // 0

        with self.assertRaises(ZeroDivisionError):
            p = Point(1,1,1)
            p //= Point()            

        with self.assertRaises(ZeroDivisionError):
            p = Point(1,1,1)
            p //= 0

    def testPointModulus(self):

        p = Point([2]*3)
        q = Point([4]*3)

        r = p % p
        self.assertListEqual(r.xyz,[0]*3)
        
        r = p % q
        self.assertListEqual(r.xyz,[2]*3)
        
        r = q % p
        self.assertListEqual(r.xyz,[0]*3)

        with self.assertRaises(ZeroDivisionError):
            z = Point()
            r = p % z

        with self.assertRaises(ZeroDivisionError):
            r = p % NumberFactory.Object()

        with self.assertRaises(ZeroDivisionError):
            r = p % 0

        with self.assertRaises(ZeroDivisionError):
            p = Point(1,1,1)
            p %= 0

        with self.assertRaises(ZeroDivisionError):
            p = Point(1,1,1)
            p %= Point()                 

        r = q % 3
        self.assertListEqual(r.xyz,[1]*3)
        
        r %= 2
        self.assertListEqual(r.xyz,[1]*3)


    def testPointPow(self):

        p = Point()
        q = Point(2,2,2)

        r = p ** p
        self.assertListEqual(r.xyz,[1]*3)

        r = q ** p
        self.assertListEqual(r.xyz,[1]*3)

        r = p ** q
        self.assertListEqual(r.xyz,[0]*3)
        
        r = q ** p
        self.assertListEqual(r.xyz,[1]*3)

        r = p ** 0
        self.assertListEqual(r.xyz,[1]*3)

        r = p ** 1
        self.assertListEqual(r.xyz,[0]*3)

        r = q ** 0
        self.assertListEqual(r.xyz,[1]*3)

        r = q ** 1
        self.assertListEqual(r.xyz,[2]*3)

        r **= 2
        self.assertListEqual(r.xyz,[4]*3)

        r **= Point([2]*3)
        self.assertListEqual(r.xyz,[16]*3)

    def testPointMiscOps(self):

        p = Point(1,1,1)
        
        q = -p
        self.assertListEqual(q.xyz,[-1]*3)

        q = +p
        self.assertEqual(p,q)
        self.assertTrue(q is p)

        q = ~p
        self.assertListEqual(q.xyz,[-2]*3)

        q = abs(Point(-1,-1,-1))
        self.assertEqual(p,q)
        
        self.assertEqual(hash(p),hash(q))
        self.assertTrue(p is not q)

        q = Point()
        self.assertNotEqual(p,q)
        self.assertNotEqual(hash(p),hash(q))
        self.assertTrue(p is not q)
        
    def testPointIteration(self):
        
        pts =[1,2,3]
        p = Point(pts)
        
        for n,v in enumerate(p):
            self.assertEqual(p[n],pts[n])

        self.assertEqual(p[3],1)

        with self.assertRaises(IndexError):
            p[4]

        with self.assertRaises(IndexError):
            p[-5]

    def testPointStrings(self):
        p = Point()
        s = str(p)
        self.assertTrue('x=' in s)
        self.assertTrue('y=' in s)
        self.assertTrue('z=' in s)
        
        r = repr(p)
        self.assertTrue(r.startswith(Point.__name__))
        self.assertTrue('x=' in r)
        self.assertTrue('y=' in r)
        self.assertTrue('z=' in r)

    def testPointBytes(self):
        p = Point()
        self.assertIsInstance(p.bytes,bytes)
        self.assertEqual(p.bytes,bytes(repr(p),'utf-8'))

    def testPointPropertyMapping(self):
        p = Point()
        m = p.mapping
        self.assertEqual(len(m),4)
        for key in Point.ordinateNamesAll:
            self.assertEqual(getattr(p,key),m[key])        

    def testPointCCW(self):
        
        a = Point()
        self.assertListEqual(a.xyz,[0]*3)
        b = Point(1,0)
        self.assertListEqual(b.xyz,[1,0,0])
        c = Point(1,1)
        self.assertListEqual(c.xyz,[1,1,0])
        d = Point(2,2)
        self.assertListEqual(d.xyz,[2,2,0])

        self.assertEqual(a.ccw(b,c),1)
        self.assertEqual(a.ccw(c,d),0)
        self.assertEqual(c.ccw(b,a),-1)

        self.assertTrue(a.isCCW(b,c))
        self.assertFalse(c.isCCW(b,a))

        with self.assertRaises(CollinearPoints):
            a.isCCW(c,d)

        self.assertTrue(a.isCollinear(c,d))
        self.assertFalse(a.isCollinear(b,c))

    def testPointCrossProduct(self):

        i,j,k = Point.units()

        self.assertEqual(i.cross(i),0)
        self.assertEqual(j.cross(j),0)
        self.assertEqual(k.cross(k),0)
        
        self.assertEqual(i.cross(j),1)
        self.assertEqual(i.cross(k),-1)

        self.assertEqual(j.cross(k),1)
        self.assertEqual(j.cross(i),-1)

        self.assertEqual(k.cross(i),1)
        self.assertEqual(k.cross(j),-1)

    def testPointDotProduct(self):
        
        i,j,k = Point.units()

        self.assertEqual(i.dot(i),1)
        self.assertEqual(j.dot(j),1)
        self.assertEqual(k.dot(k),1)

        self.assertEqual(i.dot(j),0)
        self.assertEqual(i.dot(k),0)

        self.assertEqual(j.dot(i),0)
        self.assertEqual(j.dot(k),0)

        self.assertEqual(k.dot(i),0)
        self.assertEqual(k.dot(j),0)

    def testPointDistance(self):

        i,j,k = Point.units()

        self.assertEqual(i.distance(),1)
        self.assertEqual(j.distance(),1)
        self.assertEqual(k.distance(),1)

        self.assertEqual(i.distance(j),j.distance(i))
        self.assertEqual(i.distance(k),k.distance(i))
        self.assertEqual(j.distance(k),k.distance(j))

        self.assertEqual(i.distanceSquared(j),j.distanceSquared(i))
        self.assertEqual(i.distanceSquared(k),k.distanceSquared(i))
        self.assertEqual(j.distanceSquared(k),k.distanceSquared(j))

    def testPointMidpoint(self):
        i,j,k = Point.units()
        m = i.midpoint(j)
        self.assertIsInstance(m,Point)
        self.assertTrue(m.isCollinear(i,j))
        self.assertEqual(m.distance(i),m.distance(j))
        self.assertEqual(i.distance(m),j.distance(m))
        self.assertEqual(m,(i+j)/2)
        
    def testPointBetween(self):
        
        i,j,k = Point.units()
        
        a = (i+j+k) / 2

        self.assertTrue(a.isBetweenX(i,j))
        self.assertTrue(a.isBetweenX(j,i))
        self.assertTrue(a.isBetweenX(i,k))
        self.assertTrue(a.isBetweenX(k,i))
        self.assertFalse(a.isBetweenX(j,k))
        self.assertFalse(a.isBetweenX(k,j))

        self.assertTrue(a.isBetweenY(i,j))
        self.assertTrue(a.isBetweenY(j,i))
        self.assertTrue(a.isBetweenY(j,k))
        self.assertTrue(a.isBetweenY(k,j))
        self.assertFalse(a.isBetweenY(i,k))
        self.assertFalse(a.isBetweenY(k,i))
        
        self.assertTrue(a.isBetweenZ(k,i))
        self.assertTrue(a.isBetweenZ(i,k))
        self.assertTrue(a.isBetweenZ(k,j))
        self.assertTrue(a.isBetweenZ(j,k))
        self.assertFalse(a.isBetweenZ(i,j))
        self.assertFalse(a.isBetweenZ(j,i))

        a = (i+j+k) * 2
        
        self.assertListEqual(a.xyz,[2]*3)

        self.assertFalse(a.isBetweenX(i,j))
        self.assertFalse(a.isBetweenX(j,i))
        self.assertFalse(a.isBetweenX(i,k))
        self.assertFalse(a.isBetweenX(k,i))
        self.assertFalse(a.isBetweenX(j,k))
        self.assertFalse(a.isBetweenX(k,j))

        self.assertFalse(a.isBetweenY(i,j))
        self.assertFalse(a.isBetweenY(j,i))
        self.assertFalse(a.isBetweenY(j,k))
        self.assertFalse(a.isBetweenY(k,j))
        self.assertFalse(a.isBetweenY(i,k))
        self.assertFalse(a.isBetweenY(k,i))
        
        self.assertFalse(a.isBetweenZ(k,i))
        self.assertFalse(a.isBetweenZ(i,k))
        self.assertFalse(a.isBetweenZ(k,j))
        self.assertFalse(a.isBetweenZ(j,k))
        self.assertFalse(a.isBetweenZ(i,j))
        self.assertFalse(a.isBetweenZ(j,i))

    def testPointClassmethodGaussian(self):
        p = Point.gaussian()
        self.assertIsInstance(p,Point)

    def testPointClassmethodRandomXY(self):
        p = Point.randomXY()
        self.assertIsInstance(p,Point)
        self.assertLessEqual(p.distance(),1)
        
        p = Point.randomXY(Point(5,5,0),2)
        self.assertIsInstance(p,Point)
        self.assertLessEqual(p.distance(Point(5,5,0)),2)

    def testPointClassmethodRandomXYZ(self):
        p = Point.randomXYZ()
        self.assertIsInstance(p,Point)
        self.assertLessEqual(p.distance(),1)

        o = Point(5,5,0)
        r = 2
        p = Point.randomXYZ(o,r)
        self.assertIsInstance(p,Point)

        l = p.distance(o)

        # XXX horrible bandaid
        if abs(l-r)/r <= sys.float_info.epsilon:
            self.assertTrue(True)
        else:
            self.assertLessEqual(l,r)

    def testPointClassmethodRandomLocationInRectangle(self):
        i,j,_ = Point.units()
        p = Point.randomInRectangle()
        self.assertIsInstance(p,Point)
        self.assertTrue(p.isBetweenX(i,j))
        self.assertTrue(p.isBetweenY(i,j))

        o = Point(2,2)
        p = Point.randomInRectangle(o,2,2)
        self.assertIsInstance(p,Point)
        self.assertTrue(p.isBetweenX(o,o+2))
        self.assertTrue(p.isBetweenY(o,o+2))

    def testPointClassmethodUnits(self):
        i,j,k = Point.units()
        self.assertListEqual(i.xyz,[1,0,0])
        self.assertListEqual(j.xyz,[0,1,0])
        self.assertListEqual(k.xyz,[0,0,1])

    def testPointClassmethodUnitize(self):

        a,b = Point.gaussian(), Point.gaussian()

        c = Point.unitize(a,b)

        self.assertIsInstance(c,Point)
        self.assertAlmostEqual(c.distance(),1.0,delta=sys.float_info.epsilon)

        for u in Point.units():
            r = Point.unitize(Point(),u)
            msg = 'unitize(O,{u}) => {r} != {u}'
            self.assertListEqual(u.xyz,r.xyz,msg.format(u=u,r=r))
                                 
