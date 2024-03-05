''' geometry exceptions

'''

class ZeroSlope(Exception):
    pass

class InfiniteSlope(Exception):
    pass

class CollinearPoints(Exception):
    pass

class CollinearLines(CollinearPoints):
    pass

class ParallelLines(Exception):
    pass

class InfiniteLength(Exception):
    pass


class UngrokkableObject(Exception):
    def __init__(self,obj):
        '''
        :param: the object that cannot be grokked
        '''
        self.obj = obj

    def __str__(self):
        fmt = "object {klass} is ungrokkable: {rep}"
        return fmt.format(klass=self.obj.__class__.__name__,rep=repr(self.obj))
    
class ExceededEpsilonError(Exception):
    def __init(self,x,y,epsilon):
        self.x,self.y,self.epsilon = x,y,epsilon
        
    def __str__(self):
        fmt = 'x={x} - y={y} {delta} > epsilon {epsilon}'
        return fmt.format(x=self.x,y=self.y,
                          delta=self.x-self.y,epsilon=self.epsilon)
