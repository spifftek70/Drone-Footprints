'''a broken pythonic Graph

Nodes and edges, not pretty colors and pitchers.
'''

import math

from .point import Point
from .line import Segment
from .exceptions import *


class Node(Point):
    '''
    XXX missing doc string
    '''
    pass

class Edge(Segment):
    '''
    XXX missing doc string
    '''

    @Segment.A.getter
    def A(self):
        try:
            return self._A
        except AttributeError:
            pass
        self._A = Node()
        return self._A

    @Segment.B.getter
    def B(self):
        try:
            return self._B
        except AttributeError:
            pass
        self._B = Node()
        return self._B

    def __hash__(self):
        # XOR is uh.. transitive? A^B == B^A
        # so edges AB and BA will hash to the same value.
        return hash(self.A) ^ hash(self.B)    


class Graph(object):
    '''
    XXX missing doc string
    '''
    
    @classmethod
    def randomGraph(cls,radius,nodes,origin=None):
        '''
        '''
        if origin is None:
            origin = Point()

        graph = cls()

        while len(graph) < nodes:
            try:
                graph.addNode(Node.randomLocation(radius,origin))
            except ValueError:
                pass

        return graph
    
    def __init__(self,nodes=None,edges=None):
        try:
            for node in nodes:
                self.nodes.add(Node(node))
        except TypeError:
            pass

        try:
            for edge in edges:
                self.nodes.add(edge.A)
                self.nodes.add(edge.B)
                self.edges.add(edge)
        except TypeError:
            pass

    @property
    def nodes(self):
        try:
            return self._nodes
        except AttributeError:
            pass
        self._nodes = set()
        return self._nodes

    @property
    def edges(self):
        try:
            return self._edges
        except AttributeError:
            pass
        self._edges = set()
        return self._edges

    def __len__(self):
        '''
        The number of nodes in the graph, integer.
        '''
        return len(self.nodes)

    def __str__(self):
        s = []
        s.append(repr(self))
        s.extend(['\t'+repr(n) for n in self.nodes])
        s.extend(['\t'+repr(e) for e in self.edges])
        return '\n'.join(s)

    def __repr__(self):
        fmt = '%s(nodes=%s,edges=%s)>'
        return fmt % (self.__class__.__name__,str(self.nodes),str(self.edges))

    def sortedNodes(self,func=None):
        '''
        '''
        if func is None:
            func = lambda x:x.distanceSquared(self.cg)

        nodes = list(self.nodes)
        nodes.sort(key=func)
        return nodes
        
    @property
    def cg(self):
        '''
        Center of gravity, Node.
        '''
        return Node(sum(self.nodes) // len(self.nodes))

    def __eq__(self,other):
        '''
        x == y iff:
          len(x) == len(y) 
          all nodes of x are in y
        '''

        if len(self) != len(other):
            return False
        
        return self in other

    def __contains__(self,other):
        otherType = type(other)
        
        if issubtype(otherType,Node):
            for node in self.nodes:
                if node == other:
                    return True
            return False

        if issubtype(otherType,Edge):
            for edge in self.edges:
                if edge == other:
                    return True
            return False

        if issubtype(otherType,Graph):
            # graphs need to match nodes AND edges

            if len(self.edges) != len(other.edges):
                return False

            for node in self.nodes:
                if node in other:
                    pass
                
        return True
    
    def disconnect(self):
        '''
        '''
        self.edges.clear()
        
    def connect(self,doDisconnect=True):
        '''
        '''
        if doDisconnect:
            self.disconnect()
        
        self.sortNodes()
        
        for A in self.nodes:
            for B in self.nodes:
                if A is B:
                    continue
                self.edges.append(Edge(A,B))

    def drawNodes(self,surface,color):
        for node in self.nodes:
            node.draw(surface,color)

    def drawEdges(self,surface,color):
        for edge in self.edges:
            edge.draw(surface,color)

    def draw(self,surface,nodeColor=(0,255,0),edgeColor=(0,0,255),cg=True):

        self.drawEdges(surface,edgeColor)
        self.drawNodes(surface,nodeColor)

        if cg:
            self.cg.draw(surface,(255,0,0))
