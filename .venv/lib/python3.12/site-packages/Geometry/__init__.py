"""support for geometric computation


"""

try:
    __import__('pkg_resources').declare_namespace(__name__)
except:
    from pkgutil import extend_path
    __path__ = extend_path(__path__,__name__)

__author__ = '\n'.join(["Erik O'Shaughnessy",
                        'erik.oshaughnessy@gmail.com',
                        'https://github.com/JnyJny/Geometry'])

__version__ = "0.0.23"

from .point import Point
from .ellipse import Ellipse, Circle
from .line import Line, Segment, Ray
from .triangle import Triangle
from .rectangle import Rectangle
from .graph import Node, Edge, Graph
from .constants import *
from .exceptions import *

__all__ =  [ 'Point',
             'Ellipse','Circle',
             'Line','Segment','Ray',
             'Triangle','Rectangle',
             'Graph','Node','Edge',
             'ZeroSlope','InfiniteSlope','CollinearPoints',
             'InfiniteLength','ParallelLines','CollinearLines',
             'UngrokkableObject',
             '__author__','__version__' ]
             



