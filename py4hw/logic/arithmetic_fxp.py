# -*- coding: utf-8 -*-
"""
Created on Sun Mar 19 09:52:07 2023

Arithmetic fixed point blocks

@author: dcr
"""
from .. import *
from ..helper import *
from .bitwise import *
from .arithmetic import *
from deprecated import deprecated

class FixedPointAdd(Logic):
    def __init__(self, parent, name, a, af, b, bf, r, rf):
        super().__init__(parent, name)
        
        assert(a.getWidth() == sum(af))
        assert(b.getWidth() == sum(bf))
        assert(r.getWidth() == sum(rf))
        
        a = self.addIn('a', a)
        b = self.addIn('b', b)
        r = self.addOut('r', r)
                
        # @todo by now we only support same format
        assert(af == bf)
        assert(af == rf)
        
        Add(self, 'q', a, b, r)
      
class FixedPointSign(Logic):
    def __init__(self, parent, name, a, af, s):
        super().__init__(parent, name)
        
        assert(a.getWidth() == sum(af))
        assert(af[0] == 1)
        
        a = self.addIn('a', a)
        s = self.addOut('s', s)
    
        Bit(self, 'sign', a, af[1]+af[2], s)
        
class FixedPointSub(Logic):
    def __init__(self, parent, name, a, af, b, bf, r, rf):
        super().__init__(parent, name)
        
        assert(a.getWidth() == sum(af))
        assert(b.getWidth() == sum(bf))
        assert(r.getWidth() == sum(rf))
        
        a = self.addIn('a', a)
        b = self.addIn('b', b)
        r = self.addOut('r', r)
                
        # @todo by now we only support same format
        assert(af == bf)
        assert(af == rf)
        
        Sub(self, 'q', a, b, r)
        
class FixedPointMult(Logic):
    def __init__(self, parent, name, a, af, b, bf, r, rf):
        super().__init__(parent, name)
        
        assert(a.getWidth() == sum(af))
        assert(b.getWidth() == sum(bf))
        assert(r.getWidth() == sum(rf))
        
        a = self.addIn('a', a)
        b = self.addIn('b', b)
        r = self.addOut('r', r)
        
        sa = self.wire('sa', a.getWidth()+b.getWidth())
        sb = self.wire('sb', a.getWidth()+b.getWidth())
        
        SignExtend(self, 'sa', a, sa)
        SignExtend(self, 'sb', b, sb)
                
        m = self.wire('m', a.getWidth()+b.getWidth())
        Mul(self, 'm', sa, sb, m)
        
        # Range(self, 'r', m, r.getWidth()+rf[2], rf[2], r)
        low = af[2]+bf[2]-rf[2]
        high = low + r.getWidth()
        Range(self, 'r', m, high, low, r)