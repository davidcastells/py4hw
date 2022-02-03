# -*- coding: utf-8 -*-
"""
Created on Sat Jan 29 16:28:57 2022

@author: dcr
"""

from .base import Wire
from .logic.bitwise import *
from .logic.simulation import *

class LogicHelper:
    
    def __init__(self, parent:Logic):
        self.parent = parent
        self.inum = 0   # instance number
        
    def getNewName(self)->str:
        str = 'i{}'.format(self.inum)
        self.inum += 1
        return str
    
    def hw_constant(self, width:int, v:int) -> Wire:
        name = self.getNewName()
        r = self.parent.wire(name, width)
        Constant(self.parent, name, v, r)
        return r
    
    def hw_and2(self, a:Wire, b:Wire) -> Wire:
        w = a.getWidth()
        name = self.getNewName()
        r = self.parent.wire(name, w)
        And2(self.parent, name, a, b, r)
        return r

    def hw_or2(self, a:Wire, b:Wire) -> Wire:
        w = a.getWidth()
        name = self.getNewName()
        r = self.parent.wire(name, w)
        Or2(self.parent, name, a, b, r)
        return r

    def hw_xor2(self, a:Wire, b:Wire) -> Wire:
        w = a.getWidth()
        name = self.getNewName()
        r = self.parent.wire(name, w)
        Xor2(self.parent, name, a, b, r)
        return r

    def hw_and3(self, a:Wire, b:Wire, c:Wire) -> Wire:
        w = a.getWidth()
        name = self.getNewName()
        r = self.parent.wire(name, w)
        And(self.parent, name, [a, b, c], r)
        return r
    
    def hw_buf(self, a:Wire) -> Wire:
        w = a.getWidth()
        name = self.getNewName()
        r = self.parent.wire(name, w)
        Buf(self.parent, name, a, r)
        return r
    
    def hw_not(self, a:Wire) -> Wire:
        w = a.getWidth()
        name = self.getNewName()
        r = self.parent.wire(name, w)
        Not(self.parent, name, a, r)
        return r
        
    def hw_mux(self, sel:Wire, options:list) -> Wire:
        name = self.getNewName()
        w = options[0].getWidth()
        r = self.parent.wire(name, w)
        Mux(self.parent, name, sel, options, r)
        return r
    
    def sim_sequence(self, width:int, seq:list) -> Wire:
        name = self.getNewName()
        r = self.parent.wire(name, width)
        Sequence(self.parent, name, seq, r)
        return r
 

class FloatingPointHelper:

    @staticmethod
    def sp_to_ieee754_parts(v):
        e = 0
        vo = v
        s=0
        if (v < 0):
            s = 1
            v = -v
    
        while (v >= 2):
            v = v / 2
            e += 1
            #print('e:', e, 'v:', v)
        while (v < 1):
            v = v * 2
            e -= 1
            #print('e:', e, 'v:', v)
    
        m = v - 1
        #print('m:', m)
        re = 127 + e
        rm = int(round(m * (1<<23)))
    
        return s, re, rm

    @staticmethod
    def sp_to_ieee754(v):
        s,e,m = FloatingPointHelper.sp_to_ieee754_parts(v)
        
        r = s << 31
        r = r | (e << 23)
        r = r | (m)
        return r

    @staticmethod
    def ieee754_parts_to_sp(s, e, m):
        import math
        ef = math.pow(2, e-127)
        f = m / (1<<23)
        
        if (s > 0):
            s = -1
        else:
            s = 1
            
        return s * ef * f;
    
    @staticmethod
    def ieee754_to_sp(v):
        s = v >> 31
        e = (v >> 23) & 0xFF
        m = (v & ((1<<23)-1)) | (1<<23) 
        
        return FloatingPointHelper.ieee754_parts_to_sp(s, e, m)
        

    @staticmethod
    def zp_bin(v:int, vl:int) -> str:
        """        
        Generates a the binary representation of an integer value in a number
        of bits. Leading zeros are added as needed.
        
        Parameters
        ----------
        v : int
            value.
        vl : int
            length of the output.

        Returns
        -------
        TYPE
            the binary string.

        """
        if (v >= 0):
            str = bin(v)[2:]
        else:
            # bin function does not handle 2's complement,
            # so let's do it for them
            p = -v
            mask = (1 << vl) -1
            r = (mask - p + 1) & mask
            str = bin(r)[2:] 
            
        return ('0' * (vl-len(str))) + str
    
    

