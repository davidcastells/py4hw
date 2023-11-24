# -*- coding: utf-8 -*-
"""
Created on Sat Jan 29 16:28:57 2022

@author: dcr
"""

from .base import Wire
from .logic.arithmetic import *
from .logic.bitwise import *
from .logic.simulation import *
from .logic.storage import *
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

    def hw_add(self, a:Wire, b:Wire) -> Wire:
        wa = a.getWidth()
        wb = b.getWidth()
        wr = max(wa,wb)+1
        name = self._getNewName()
        r = self.parent.wire(name, wr)
        Add(self.parent, name, a, b, r)
        return r
    
    def hw_delay(self, a:Wire, en:Wire, delay:int) -> Wire:
        wa = a.getWidth()
        name = self._getNewName()
        r = self.parent.wire(name, wa)
        if (en is None):
            en = self.hw_constant(1,1)
        DelayLine(self.parent, name, a, en=en, reset=None, r=r, delay=delay)
        return r
    

    def hw_signed_add(self, a:Wire, b:Wire) -> Wire:
        wa = a.getWidth()
        wb = b.getWidth()
        wr = max(wa,wb)
        name = self._getNewName()
        r = self.parent.wire(name, wr)
        Add(self.parent, name, a, b, r)
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

    def hw_bits_msbf(self, a:Wire) -> list:
        w = a.getWidth()
        name = self._getNewName() + '_'
        r = self.parent.wires(name, w, 1)
        BitsMSBF(self.parent, name, a, r)
        return r
        
    def hw_bits_lsbf(self, a:Wire) -> list:
        w = a.getWidth()
        name = self._getNewName() + '_'
        r = self.parent.wires(name, w, 1)
        BitsLSBF(self.parent, name, a, r)
        return r

    def hw_reg(self, a:Wire, enable=None, reset=None) -> Wire:
        w = a.getWidth()
        name = self._getNewName()
        r = self.parent.wire(name, w)
        Reg(self.parent, name, d=a, q=r, enable=enable, reset=reset)
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

    def hw_mod(self, a:Wire, b:Wire) -> Wire:
        wa = a.getWidth()
        wb = b.getWidth()
        wr = max(wa,wb)
        name = self._getNewName()
        r = self.parent.wire(name, wr)
        Mod(self.parent, name, a, b, r)
        return r

    def hw_div(self, a:Wire, b:Wire) -> Wire:
        wa = a.getWidth()
        wb = b.getWidth()
        wr = max(wa,wb)
        name = self._getNewName()
        r = self.parent.wire(name, wr)
        Div(self.parent, name, a, b, r)
        return r
    
    def hw_signed_div(self, a:Wire, b:Wire) -> Wire:
        wa = a.getWidth()
        wb = b.getWidth()
        wr = max(wa,wb)
        name = self._getNewName()
        r = self.parent.wire(name, wr)
        SignedDiv(self.parent, name, a, b, r)
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
    
    def hw_lt_constant(self, a:Wire, b:int) -> Wire:
        w = a.getWidth()
        gt = self.parent.wire(self._getNewName())
        eq = self.parent.wire(self._getNewName())
        lt = self.parent.wire(self._getNewName())
        k = self.parent.wire(self._getNewName(), w)
        Constant(self.parent, self._getNewName(), b, k)
        Comparator(self.parent, self._getNewName(), a, k, gt, eq, lt)
        return lt
    
    def hw_ge_constant(self, a:Wire, b:int) -> Wire:
        w = a.getWidth()
        gt = self.parent.wire(self._getNewName())
        eq = self.parent.wire(self._getNewName())
        lt = self.parent.wire(self._getNewName())
        ge = self.parent.wire(self._getNewName())
        k = self.parent.wire(self._getNewName(), w)
        Constant(self.parent, self._getNewName(), b, k)
        Comparator(self.parent, self._getNewName(), a, k, gt, eq, lt)
        Or2(self.parent, self._getNewName(), gt, eq, ge)
        return ge
    
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

    def hw_or_bits(self, a) -> Wire:
        name = self._getNewName()
        r = self.parent.wire(name)
        OrBits(self.parent, name, a, r)
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

    
    def hw_mul(self, a:Wire, b:Wire) -> Wire:
        wa = a.getWidth()
        wb = b.getWidth()
        wr = wa+wb
        name = self._getNewName()
        r = self.parent.wire(name, wr)
        Mul(self.parent, name, a, b, r)
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
    
    def sign_extend(self, a:Wire, w) -> Wire:
        name = self._getNewName()
        r = self.parent.wire(name, w)
        SignExtend(self.parent, name, a, r)
        return r
    
    def zero_extend(self, a:Wire, w) -> Wire:
        name = self._getNewName()
        r = self.parent.wire(name, w)
        ZeroExtend(self.parent, name, a, r)
        return r
    
    def sim_sequence(self, width:int, seq:list) -> Wire:
        name = self._getNewName()
        r = self.parent.wire(name, width)
        Sequence(self.parent, name, seq, r)
        return r

class IntegerHelper:
    @staticmethod
    def sign(v):
        if (v < 0):
            return -1
        else:
            return 1
        
    @staticmethod
    def signed_to_c2(v, w):
        mask = (1<<w)-1
        return v & mask

    @staticmethod
    def c2_to_signed(v, w):
        sign = 1 << (w-1)
        if ((v & sign) > 0):
            # negative
            return (v - (1 << w))
        else:
            return v
        
def signExtend(v, w, nw):
    s = (v >> (w-1)) & 1
    ns = 0
    if (s == 1):
        ns = (1 << (nw-w)) - 1
    return v | (ns << w)

class FixedPoint:
    def __init__(self, sign_bit, int_bits, frac_bits, v):
        self.sw = sign_bit
        self.iw = int_bits
        self.fw = frac_bits
        self.v = 0
        
        if (type(v) == int):
            self.intToFixedPoint(v)
        elif (type(v) == float):
            self.floatToFixedPoint(v)
        else:
            raise Exception('Unsupported type {}'.format(type(v)))
        
    def getWidths(self):
        return (self.sw, self.iw, self.fw)
        
    def intToFixedPoint(self, v):
        if (v < 0 and self.sw == 0):
            raise Exception('negative values not supported')
            
        w = self.sw + self.iw + self.fw
        
        maxv = 1 << (self.iw -1)
        
        if (v > maxv):
            raise Exception('Value {} greater than max value: {}'.format(v, maxv))
        
        self.v = (v << self.fw) & ((1<<w)-1)
            
    def floatToFixedPoint(self, v):
        if (v < 0 and self.sw == 0):
            raise Exception('negative values not supported')
        
        w = self.sw + self.iw + self.fw
        self.v = int(v * (1 << self.fw)) & ((1<<w)-1)
        
    def add(self, b):
        if (not(isinstance(b, FixedPoint))):
            b = FixedPoint(self.sw, self.iw, self.fw, b)
            
        r = FixedPoint(self.sw, self.iw, self.fw , 0)
        w = self.sw + self.iw + self.fw
        r.v = (self.v + b.v) & ((1<<w)-1)
        return r

    def sub(self, b):
        if (not(isinstance(b, FixedPoint))):
            b = FixedPoint(self.sw, self.iw, self.fw, b)

        r = FixedPoint(self.sw, self.iw, self.fw , 0)
        w = self.sw + self.iw + self.fw
        r.v = (self.v - b.v) & ((1<<w)-1)
        return r

    def mult(self, b):
        if (not(isinstance(b, FixedPoint))):
            oldb = b
            b = FixedPoint(self.sw, self.iw, self.fw, b)
            #print('old b is ', oldb, 'new b is {:08X}'.format( b.v))
    
        r = FixedPoint(self.sw, self.iw, self.fw , 0)
        w = self.sw + self.iw + self.fw
        av = signExtend(self.v, w, w*2)
        bv = signExtend(b.v, w, w*2)
        r.v = ((av * bv)>>self.fw)  & ((1<<w)-1)
        return r

    def toFloatingPoint(self):
        if (((self.v >> (self.iw+self.fw)) & 1) == 1):
            w = self.sw + self.iw + self.fw
            mask = ((1<<w)-1)
            v = ((self.v ^ mask) + 1) & mask
            return -v / (1<<self.fw)
        return self.v / (1<<self.fw)
        
    def copy():
        return FixedPoint(self.sw, self.iw, self.fw , self.v)
    
    @staticmethod
    def fromRawValue(sw, iw, fw, v):
        r = FixedPoint(sw,iw,fw,0)
        r.v = v
        return r
    
class FixedPointHelper:
    pass

class FloatingPointHelper:

    @staticmethod
    def min(a, b):
        if (a == 0.0 and b == 0.0):
            sa = math.copysign(1, a)
            sb = math.copysign(1, b)
            
            if (sa < sb):
                return a
            else:
                return b
        return min(a, b)

    @staticmethod
    def max(a, b):
        if (a == 0.0 and b == 0.0):
            sa = math.copysign(1, a)
            sb = math.copysign(1, b)
            
            if (sa > sb):
                return a
            else:
                return b
        return max(a, b)
    
    @staticmethod
    def fp_to_parts(v):
        if (math.isinf(v) or math.isnan(v)):
            raise Exception('invalid value {}'.format(v))
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
        s,e,m = FloatingPointHelper.fp_to_parts(v)

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
        if (math.isinf(v)):
            s = 0 if v > 0 else 1
            e = 255
            m = 0
            return s,e,m
        
        if (math.isnan(v)):
            s = 0 
            e = 255
            m = (1<<23)-1
            return s,e,m
        
        s,e,m = FloatingPointHelper.fp_to_parts(v)

        if (m == 0):
            return 0,0,0
        else:
            if (e >= 128):
                return s,255,0  # infinity
                
            if (e <= -127):
                # denormalized values
                div = math.pow(2, (-127-e))
                #print('e',e,'div', div)
                m = m / div
                re = 0
                rm = int(round(m * (1 << 22)))
            else:
                im = int(round((m-1) * (1<<23)))
                if (im >= (1<<23)):
                    e += 1
                    m /= 2
                    
                re = 127 + e
                rm = int(round((m-1) * (1<<23)))
    
            return s, re, rm

    def dp_to_ieee754_parts(v):
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
            biased representation of exponent (e+1023)
        int
            representation of mantissa int((m-1)<<52) 

        """
        if (math.isinf(v)):
            s = 0 if v > 0 else 1
            e = 2047
            m = 0
            return s,e,m

        if (math.isnan(v)):
            s = 0 
            e = 2047
            m = (1<<51)-1
            return s,e,m

            
        s,e,m = FloatingPointHelper.fp_to_parts(v)

        if (m == 0):
            v = math.copysign(1, v)
            s = 0 if v > 0 else 1
            return s,0,0
        else:
            if (e >= 1024):
                return s,2047,0  # infinity
                
            if (e <= -1023):
                # denormalized values
                div = math.pow(2, (-1023-e))
                #print('e',e,'div', div)
                m = m / div
                re = 0
                rm = int(round(m * (1 << 51)))
            else:
                im = int(round((m-1) * (1<<52)))
                if (im >= (1<<52)):
                    e += 1
                    m /= 2
                    
                re = 1023 + e
                rm = int(round((m-1) * (1<<52)))
    
            return s, re, rm

    @staticmethod
    def sp_to_ieee754(v):
        s,e,m = FloatingPointHelper.sp_to_ieee754_parts(v)
        
        r = s << 31
        r = r | (e << 23)
        r = r | (m)
        return r
    
    @staticmethod
    def dp_to_ieee754(v):
        s,e,m = FloatingPointHelper.dp_to_ieee754_parts(v)
        
        r = s << 63
        r = r | (e << 52)
        r = r | (m)
        return r

    @staticmethod
    def parts_to_fp(s, e, m):
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
            
        if (e == 0):
            ef = -126
            mf = m / (1<<23)
        else:
            ef = e-127
            mf = ((1 << 23) | m) / (1<<23)
        
        return FloatingPointHelper.parts_to_fp(s , ef , mf)
    
    @staticmethod
    def ieee754_parts_to_dp(s, e, m):
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
            
        if (e == 0):
            ef = -1022
            mf = m / (1<<52)
        else:
            ef = e-1023
            mf = ((1 << 52) | m) / (1<<52)
        
        return FloatingPointHelper.parts_to_fp(s , ef , mf)
    
    @staticmethod
    def ieee754_to_sp(v):
        if (v == 0):
            return 0.0
        
        s = v >> 31
        e = (v >> 23) & 0xFF
        m = (v & ((1<<23)-1))  
        
        if (e == 255):
            if (m == 0):
                return -math.inf if (s == 1) else math.inf
            else:
                return math.nan
        
        return FloatingPointHelper.ieee754_parts_to_sp(s, e, m)

    @staticmethod
    def ieee754_to_dp(v):
        if (v == 0):
            return 0.0
        
        s = v >> 63
        e = (v >> 52) & 0x7FF
        m = (v & ((1<<52)-1))  
        
        if (e == 0x7FF):
            if (m == 0):
                return -math.inf if (s == 1) else math.inf 
            else:
                return math.nan

        return FloatingPointHelper.ieee754_parts_to_dp(s, e, m)

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