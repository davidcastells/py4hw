# -*- coding: utf-8 -*-
"""
Created on Sat Jan 29 16:28:57 2022

@author: dcr
"""

from .base import Wire
from .logic.arithmetic import *
from .logic.bitwise import *
from .logic.simulation import *
import math

class LogicHelper:
    """
    Helper class to create logic in a simpler way, 
    basically automatically creating the required output wires
    """
    
    def __init__(self, parent:Logic):
        self.parent = parent
        self.inum = 0   # instance number
        
    def hw_abs(self, a:Wire) -> Wire:
        w = a.getWidth()
        name = self._getNewName()
        r = self.parent.wire(name, w)
        Abs(self.parent, name, a, r)
        return r

    def hw_and2(self, a:Wire, b:Wire) -> Wire:
        w = a.getWidth()
        name = self._getNewName()
        r = self.parent.wire(name, w)
        And2(self.parent, name, a, b, r)
        return r

    def hw_and3(self, a:Wire, b:Wire, c:Wire) -> Wire:
        w = a.getWidth()
        name = self._getNewName()
        r = self.parent.wire(name, w)
        And(self.parent, name, [a, b, c], r)
        return r

    def hw_and4(self, a:Wire, b:Wire, c:Wire, d:Wire) -> Wire:
        w = a.getWidth()
        name = self._getNewName()
        r = self.parent.wire(name, w)
        And(self.parent, name, [a, b, c, d], r)
        return r

    def hw_and(self, a:list) -> Wire:
        w = a[0].getWidth()
        name = self._getNewName()
        r = self.parent.wire(name, w)
        And(self.parent, name, a, r)
        return r

    def hw_bit(self, a:Wire, bit:int) -> Wire:
        name = self._getNewName()
        r = self.parent.wire(name)
        Bit(self.parent, name, a, bit, r)
        return r

    def hw_buf(self, a:Wire) -> Wire:
        w = a.getWidth()
        name = self._getNewName()
        r = self.parent.wire(name, w)
        Buf(self.parent, name, a, r)
        return r

    def hw_concatenate_msbf(self, ins:list) -> Wire:
        name = self._getNewName()
        w = 0
        for inw in ins:
            w += inw.getWidth()
            
        r = self.parent.wire(name, w)
        ConcatenateMSBF(self.parent, name, ins, r)
        return r

    def hw_concatenate_lsbf(self, ins:list) -> Wire:
        name = self._getNewName()
        w = 0
        for inw in ins:
            w += inw.getWidth()
            
        r = self.parent.wire(name, w)
        ConcatenateLSBF(self.parent, name, ins, r)
        return r
    
    def hw_constant(self, width:int, v:int) -> Wire:
        name = self._getNewName()
        r = self.parent.wire(name, width)
        Constant(self.parent, name, v, r)
        return r

    def hw_equal(self, a:Wire, b:Wire) -> Wire:
        w = a.getWidth()
        name = self._getNewName()
        r = self.parent.wire(name)
        Equal(self.parent, name, a, b, r)
        return r
 
    def hw_equal_constant(self, a:Wire, b:int) -> Wire:
        w = a.getWidth()
        name = self._getNewName()
        r = self.parent.wire(name)
        EqualConstant(self.parent, name, a, b, r)
        return r
            
    def hw_not_equal_constant(self, a:Wire, b:int) -> Wire:
        w = a.getWidth()
        name = self._getNewName()
        r = self.parent.wire(name)
        NotEqualConstant(self.parent, name, a, b, r)
        return r
    
    def hw_gt_constant(self, a:Wire, b:int) -> Wire:
        w = a.getWidth()
        gt = self.parent.wire(self._getNewName())
        eq = self.parent.wire(self._getNewName())
        lt = self.parent.wire(self._getNewName())
        k = self.parent.wire(self._getNewName(), w)
        Constant(self.parent, self._getNewName(), b, k)
        Comparator(self.parent, self._getNewName(), a, k, gt, eq, lt)
        return gt
    
    def _getNewName(self)->str:
        while (True):
            name = 'i{}'.format(self.inum)
            self.inum += 1
            if not(name in self.parent.children.keys()):
                return name
    
    
    def hw_or2(self, a:Wire, b:Wire) -> Wire:
        w = a.getWidth()
        name = self._getNewName()
        r = self.parent.wire(name, w)
        Or2(self.parent, name, a, b, r)
        return r

    def hw_or(self, a:list) -> Wire:
        w = a[0].getWidth()
        name = self._getNewName()
        r = self.parent.wire(name, w)
        Or(self.parent, name, a, r)
        return r

    def hw_range(self, a:Wire, up:int, down:int) -> Wire:
        w = up - down + 1
        name = self._getNewName()
        r = self.parent.wire(name, w)
        Range(self.parent, name, a, up, down, r)
        return r
        
    def hw_xor2(self, a:Wire, b:Wire) -> Wire:
        w = a.getWidth()
        name = self._getNewName()
        r = self.parent.wire(name, w)
        Xor2(self.parent, name, a, b, r)
        return r

    
        
    def hw_mux2(self, sel:Wire, s0:Wire, s1:Wire) -> Wire:
        w = s0.getWidth()
        name = self._getNewName()
        r = self.parent.wire(name, w)
        Mux2(self.parent, name, sel, s0, s1, r)
        return r

    def hw_mux(self, sel:Wire, options:list) -> Wire:
        name = self._getNewName()
        w = options[0].getWidth()
        r = self.parent.wire(name, w)
        Mux(self.parent, name, sel, options, r)
        return r

    def hw_neg(self, a:Wire) -> Wire:
        w = a.getWidth()
        name = self._getNewName()
        r = self.parent.wire(name, w)
        Neg(self.parent, name, a, r)
        return r

    def hw_not(self, a:Wire) -> Wire:
        w = a.getWidth()
        name = self._getNewName()
        r = self.parent.wire(name, w)
        Not(self.parent, name, a, r)
        return r

    def hw_sub(self, a:Wire, b:Wire) -> Wire:
        w = a.getWidth()
        name = self._getNewName()
        r = self.parent.wire(name, w)
        Sub(self.parent, name, a, b, r)
        return r

    def hw_sign(self, a:Wire) -> Wire:
        w = 1
        name = self._getNewName()
        r = self.parent.wire(name, w)
        Sign(self.parent, name, a, r)
        return r
    
    def sim_sequence(self, width:int, seq:list) -> Wire:
        name = self._getNewName()
        r = self.parent.wire(name, width)
        Sequence(self.parent, name, seq, r)
        return r
 

class FloatingPointHelper:

    @staticmethod
    def sp_to_parts(v):
        e = 0
        s=0
        m = v
        if (m < 0):
            # if v is negative activate the sign, and change the value
            s = 1
            m = -m
    
        if (m > 0.0):
            while (m >= 2):
                # iterate until v is < 2 to determine the exponent
                m = m / 2
                e += 1
                #print('e:', e, 'v:', v)
            while (m < 1):
                m = m * 2
                e -= 1
                #print('e:', e, 'v:', v)
            
        return s, e, m

    @staticmethod
    def sp_to_fixed_point_parts(v):
        s,e,m = FloatingPointHelper.sp_to_parts(v)

        if (m == 0):
            return 0,0,0
        else:
            re = e
            rm = int(round(m * (1<<23)))

            return s, re, rm
    
    @staticmethod
    def sp_to_ieee754_parts(v):
        """
        Return the parts of the IEEE 754 representation of v

        Parameters
        ----------
        v : TYPE
            DESCRIPTION.

        Returns
        -------
        int
            sign.
        int
            biased representation of exponent (e+127)
        int
            representation of mantissa int((m-1)<<23) 

        """
        s,e,m = FloatingPointHelper.sp_to_parts(v)

        if (m == 0):
            return 0,0,0
        else:
            re = 127 + e
            rm = int(round((m-1) * (1<<23)))

            return s, re, rm

    @staticmethod
    def sp_to_ieee754(v):
        s,e,m = FloatingPointHelper.sp_to_ieee754_parts(v)
        
        r = s << 31
        r = r | (e << 23)
        r = r | (m)
        return r

    @staticmethod
    def parts_to_sp(s, e, m):
        return math.pow(-1, s) * math.pow(2, e) * m

    @staticmethod
    def ieee754_parts_to_sp(s, e, m):
        """
        We build a floating point number from is sign/exponent/mantisa representation
        as it is store in the IEEE754 format

        Parameters
        ----------
        s : int
            sign.
        e : int
            exponent.
        m : TYPE
            mantisa.

        Returns
        -------
        float
            floating point number r = (-1)^s * 2^e * m

        """
        
        # zero is a special case
        if (e == 0 and m == 0):
            if (s == 1):
                return -0.0
            else:
                return 0.0
            
        ef = e-127
        mf = ((1 << 23) | m) / (1<<23)
        
        return FloatingPointHelper.parts_to_sp(s , ef , mf)
    
    @staticmethod
    def ieee754_to_sp(v):
        if (v == 0):
            return 0.0
        
        s = v >> 31
        e = (v >> 23) & 0xFF
        m = (v & ((1<<23)-1))  
        
        return FloatingPointHelper.ieee754_parts_to_sp(s, e, m)

    @staticmethod
    def ieee754_stored_internally(v):
        s,e,m = FloatingPointHelper.sp_to_ieee754_parts(v)
        iv = FloatingPointHelper.ieee754_parts_to_sp(s, e, m)
        return iv

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
    
    
class BitManipulation:
    @staticmethod
    def getFirstBit(v:int) -> int:
        # returns the position of the first active bit
        n = 0
        while (True):
            if (v == 0):
                return n
            n += 1
            v = v >> 1
    
    @staticmethod
    def countLeadingZeros(v:int, w:int) -> int:
        return w - BitManipulation.getFirstBit(v)

    @staticmethod
    def getBit(v:int, bit:int) -> int:
        return (v >> bit) & 0x1
    
class CircuitAnalysis:

    @staticmethod
    def getAllPorts(obj:Logic) -> list:
        ret = []
        
        ret.extend(obj.inPorts)
        ret.extend(obj.outPorts)
            
        return ret
    
    def getAllWireNames(obj:Logic) -> list:
        """
        Return the list of wire names

        Parameters
        ----------
        obj : Logic
            DESCRIPTION.

        Returns
        -------
        None.

        """
        return [x for x in obj._wires.keys()]
    
    @staticmethod
    def getAllPortNames(obj:Logic) -> list:
        """
        Get all port names of an object

        Parameters
        ----------
        obj : Logic
            DESCRIPTION.

        Returns
        -------
        list
            DESCRIPTION.

        """
        ret = []
        
        for p in obj.inPorts:
            ret.append(p.name)
            
        for p in obj.outPorts:
            ret.append(p.name)
            
        return ret

    @staticmethod
    def has_clk_enable(obj:Logic) -> bool:
        input_port_names = [p.name for p in obj.inPorts]
        return 'clk_enable' in input_port_names
        
    @staticmethod
    def getAllPortWires(obj:Logic) -> list:
        """
        Returns a list of the wires connected to all the ports of a circuit

        Parameters
        ----------
        obj : Logic
            the object to analyze.

        Returns
        -------
        list
            list with all the wires connected to the circuit ports.

        """
        ret = []
        
        for p in obj.inPorts:
            ret.append(p.wire)
            
        for p in obj.outPorts:
            ret.append(p.wire)
            
        return ret