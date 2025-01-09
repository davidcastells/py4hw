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


IEEE754_HP_PRECISION = 10
IEEE754_SP_PRECISION = 23
IEEE754_DP_PRECISION = 52

IEEE754_HP_EXPONENT_BITS = 5
IEEE754_SP_EXPONENT_BITS = 8
IEEE754_DP_EXPONENT_BITS = 11

IEEE754_HP_INF_MANTISA = 0x0
IEEE754_SP_INF_MANTISA = 0x0
IEEE754_DP_INF_MANTISA = 0x0

IEEE754_DP_INFNAN_EXPONENT = 0x7FF
IEEE754_DP_EXPONENT_BIAS = 0x3FF

IEEE754_HP_NAN_MANTISA = 0x200
IEEE754_SP_NAN_MANTISA = 0x400000
IEEE754_DP_NAN_MANTISA = 0x8000000000000

IEEE754_HP_SNAN_MANTISA = 0x001
IEEE754_SP_SNAN_MANTISA = 0x000001
IEEE754_DP_SNAN_MANTISA = 0x0000000000001

class LogicHelper:
    """
    Helper class to create logic in a simpler way, 
    basically automatically creating the required output wires
    """
    
    def __init__(self, parent:Logic):
        self.parent = parent
        self.inum = 0   # instance number
        
    def _getNewName(self)->str:
        while (True):
            name = 'i{}'.format(self.inum)
            self.inum += 1
            if not(name in self.parent.children.keys()):
                return name
        
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
    
    def hw_delay(self, a:Wire, en:Wire, delay:int) -> Wire:
        wa = a.getWidth()
        name = self._getNewName()
        r = self.parent.wire(name, wa)
        if (en is None):
            en = self.hw_constant(1,1)
        DelayLine(self.parent, name, a, en=en, reset=None, r=r, delay=delay)
        return r
    
    def hw_div(self, a:Wire, b:Wire) -> Wire:
        wa = a.getWidth()
        wb = b.getWidth()
        wr = max(wa,wb)
        name = self._getNewName()
        r = self.parent.wire(name, wr)
        Div(self.parent, name, a, b, r)
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



    

    

    def hw_mod(self, a:Wire, b:Wire) -> Wire:
        wa = a.getWidth()
        wb = b.getWidth()
        wr = max(wa,wb)
        name = self._getNewName()
        r = self.parent.wire(name, wr)
        Mod(self.parent, name, a, b, r)
        return r

    
    
    def hw_signed_div(self, a:Wire, b:Wire) -> Wire:
        wa = a.getWidth()
        wb = b.getWidth()
        wr = max(wa,wb)
        name = self._getNewName()
        r = self.parent.wire(name, wr)
        SignedDiv(self.parent, name, a, b, r)
        return r    

    
    def hw_if(self, cond:Wire, true_option:Wire, false_option:Wire) -> Wire:
        w = true_option.getWidth()
        name = self._getNewName()
        r = self.parent.wire(name, w)
        Mux2(self.parent, name, cond, false_option, true_option, r)
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
    
    def hw_repeat(self, a:Wire, n:int) -> Wire:
        w = n * a.getWidth()
        name = self._getNewName()
        r = self.parent.wire(name, w)
        Repeat(self.parent, name, a, r)
        return r

    def hw_select_default(self, sels:list, ins:list, default:Wire) -> Wire:
        name = self._getNewName()
        w = max([obj.getWidth() for obj in ins])
        r = self.parent.wire(name, w)        
        SelectDefault(self.parent, name, sels, ins, default, r)
        return r        
        
    def hw_signed_add(self, a:Wire, b:Wire) -> Wire:
        wa = a.getWidth()
        wb = b.getWidth()
        wr = max(wa,wb)
        name = self._getNewName()
        r = self.parent.wire(name, wr)
        Add(self.parent, name, a, b, r)
        return r

        
    def hw_shift_left_constant(self, a:Wire, n:int) -> Wire:
        w = a.getWidth()
        name = self._getNewName()
        r = self.parent.wire(name, w+n)
        ShiftLeftConstant(self.parent, name, a, n, r)
        return r


    def hw_sign(self, a:Wire) -> Wire:
        w = 1
        name = self._getNewName()
        r = self.parent.wire(name, w)
        Sign(self.parent, name, a, r)
        return r

    def hw_sub(self, a:Wire, b:Wire) -> Wire:
        w = max(a.getWidth(), b.getWidth())
        name = self._getNewName()
        r = self.parent.wire(name, w)
        Sub(self.parent, name, a, b, r)
        return r

    def hw_reg(self, a:Wire, enable=None, reset=None, reset_value=None) -> Wire:
        w = a.getWidth()
        name = self._getNewName()
        r = self.parent.wire(name, w)
        Reg(self.parent, name, d=a, q=r, enable=enable, reset=reset, reset_value=reset_value)
        return r

    def hw_xor2(self, a:Wire, b:Wire) -> Wire:
        w = a.getWidth()
        name = self._getNewName()
        r = self.parent.wire(name, w)
        Xor2(self.parent, name, a, b, r)
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
        v = v & ((1<<w)-1)
        
        sign = 1 << (w-1)
        if ((v & sign) > 0):
            # negative
            return (v - (1 << w))
        else:
            return v
        
def signExtend(v, w, nw):
    # converts a signed or unsigned value to a c2 representation
    v = (v & ((1<<w)-1)) # first mask all possible additional bits
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
    
    def createConstant(self, parent, name):
        w = self.sw + self.iw + self.fw
        mask = ((1<<w)-1)
        wire = parent.wire(name, w)
        Constant(parent, name, self.v & mask, wire)
        return wire
    
    def dump(self):
        fmt = f'|[:0{self.sw}b]|[:0{self.iw}b]|[:0{self.fw}b]|'
        fmt = fmt.replace('[','{')
        fmt = fmt.replace(']','}')
        s = self.v >> (self.iw + self.fw) & 1
        i = self.v >> (self.fw) & ((1<<self.iw)-1)
        f = self.v & ((1<<self.fw)-1)
        return fmt.format(s,i,f)
        
class FixedPointHelper:
    pass

class FPNum:
    max_prec = 1 << 200
    
    def __init__(self, *args):
        self.inexact = False
        self.infinity = False
        self.nan = False
        
        if (len(args) == 0):
            pass
        elif len(args) == 1:
            # should be a float
            self.convert_float_to_semp(args[0])
        elif len(args) == 2:
            # should be a int + string (sp, dp)
            if (args[1] == 'hp'):
                self.from_ieee754_hp(args[0])
            elif (args[1] == 'sp'):
                self.from_ieee754_sp(args[0])
            elif (args[1] == 'dp'):
                self.from_ieee754_dp(args[0])
            else:
                raise Exception(f'unknown format {args[1]}')
        elif (len(args) == 3):
            # should be a sem
            self.adjust_sem(args[0], args[1], args[2])
        elif (len(args) == 4):
            # should be a sem
            self.set_semp(args[0], args[1], args[2], args[3])
            self.adjust_semp()
        else:
            raise Exception('invalid parameter')
    
    def components(self):
        return self.s, self.e, self.m, self.p
    
    def copy(self):
        r = FPNum()
        r.set_semp(self.s, self.e, self.m, self.p)
        r.infinity = self.infinity
        r.nan = self.nan
        r.inexact = self.inexact
        return r
    
    def isPositiveInfinity(self):
        return self.infinity and self.s == 1 
    
    def isNegativeInfinity(self):
        return self.infinity and self.s == -1 
    
    def to_float(self):
        if (self.infinity):
            if (self.s == 1): return math.inf
            elif (self.s == -1): return -math.inf
            else: raise Exception('no valid sign')
        if (self.nan):
            return math.nan
        
        from decimal import Decimal
        n2 = Decimal(2)
        r = n2 ** Decimal(self.e)
        r = r * Decimal(self.m)
        r = r / Decimal(self.p)
        r = r * Decimal(self.s)
        return float(r)
    
    def reduceExponentPrecision(self, prec):
        mask = (1 << prec) - 1
        e_bias = mask >> 1 
        
        if (self.e < -(e_bias-1)):
            # subnormal
            while (self.e < -(e_bias-1)):
                self.e += 1 
                self.p = self.p << 1
        elif (self.e >= e_mask):
            self.infinity = True
        
    def reducePrecisionWithRounding(self, prec):
        # prec is the number of bits of the precision
        p = 1 << prec
        r = 0
        i = 0
        
        if (p < self.p):
            while (p < self.p):
                r = (self.m & 1) << i | r
                self.p = self.p >> 1
                self.m = self.m >> 1
                i += 1
            self.inexact = True
            
            if (r > (1<<(i-1))):
                self.m += 1
            
    def reducePrecision(self, prec):
        p = 1 << prec
        
        if (p < self.p):
            while (p < self.p):
                self.p = self.p >> 1
                self.m = self.m >> 1
            self.inexact = True
    
    def compare(self, bref):
        if (self.nan or bref.nan): return 0 
        if (self.infinity and bref.infinity and (self.s == bref.s)): return 0
        if (self.infinity and bref.infinity and (self.s != bref.s)): return 1
        if (self.infinity or bref.infinity): 
            if (self.infinity): return self.s
            else: return -bref.s

        a = FPNum(self.s, self.e, self.m, self.p)
        b = FPNum(bref.s, bref.e, bref.m, bref.p)

        # ensure equal exponent         
        if (a.e > b.e): b.increase_exponent(a.e)
        elif (a.e < b.e): a.increase_exponent(b.e)
        
        assert(a.e == b.e)
        
        # ensure equal precision
        if (a.p > b.p): b.increase_precision(a.p)
        elif (a.p < b.p): a.increase_precision(b.p)
        
        assert(a.p == b.p)

        if (a.m == b.m):  abs_cmp  = 0
        elif (a.m > b.m): abs_cmp = 1
        elif (a.m < b.m): abs_cmp = -1
        else: raise Exception()
            
        if (a.s == 1 and b.s == 1): return abs_cmp
        elif (a.s == -1 and b.s == -1): return -abs_cmp
        elif (a.s == -1 and b.s == 1): return -1
        elif (a.s == 1 and b.s == -1): return 1
        else: raise Exception()

    def convert(self, fmt):
        s, e, m, p = self.s, self.e, self.m, self.p
        s = 0 if s > 0 else 1

        # deal with special cases        
        if (self.infinity) or (self.nan):
            if (fmt == 'hp'):
                e = 0x1F
                if (self.nan): 
                    s = 0
                    m = IEEE754_HP_NAN_MANTISA
                else:
                    m = IEEE754_HP_INF_MANTISA
                x = self.pack_ieee754_hp_parts(s, e, m)
            elif (fmt == 'sp'):
                e = 0xFF
                if (self.nan):
                    s = 0
                    m = IEEE754_SP_NAN_MANTISA
                else:
                    m = IEEE754_SP_INF_MANTISA
                x =  self.pack_ieee754_sp_parts(s, e, m)
            elif (fmt == 'dp'):
                e = 0x7FF
                if (self.nan):
                    s = 0
                    m = IEEE754_DP_NAN_MANTISA
                else:
                    m = IEEE754_DP_INF_MANTISA
                x = self.pack_ieee754_dp_parts(s, e, m)

            return x        
        
        if (m==0):
            if   (fmt == 'hp'): return self.pack_ieee754_hp_parts(s, 0, 0)
            elif (fmt == 'sp'): return self.pack_ieee754_sp_parts(s, 0, 0)
            elif (fmt == 'dp'): return self.pack_ieee754_dp_parts(s, 0, 0)
            
        
        if (fmt == 'hp'):
            e_bias = 15
            e_mask = 0x1F
            p_std = 1 << 10
        elif (fmt == 'sp'):
            e_bias = 127
            e_mask = 0xFF
            p_std = 1 << 23
        elif (fmt == 'dp'):
            e_bias = 1023
            e_mask = 0x7FF
            p_std = 1 << 52
        else:
            raise Exception(f'unknown format: {fmt}')
            
        
        if (e < -(e_bias-1)):
            # if exponent is smaller that e_bias-1, then it is a subnormal
            while (e < -(e_bias-1)):
                e += 1 
                p = p << 1
            e = 0
        else:
            if (e == -(e_bias-1)) and (p > m):
                # also a subnormal number
                e = 0
            else: e = e + e_bias   
            
        if (e < 0):
            # very small number
            e = 0
            m = 0            
        elif (e >= e_mask):
            # infinity
            e = e_mask
            m = 0
        else:
            if (e == 0):
                # subnormal numbers no not need further mantisa processing
                pass
            else:
                if (p > m):
                    m = m << 1
                    e -= 1
                if (m >= (p<<1)):
                    p = p << 1
                    e += 1
                    
                if not(m & p): print('ERROR converting', self.components(), 'to', fmt)
                assert(m & p)   # ensure higher bit is active
                m = m ^ p       # eliminate the higher bit
            
            # compute the standard precision
            while (p > p_std):
                p = p >> 1 
                m = m >> 1 
            while (p < p_std):
                p = p << 1 
                m = m << 1
            
        if (fmt == 'hp'):
            x = self.pack_ieee754_hp_parts(s, e, m)
        elif (fmt == 'sp'):
            x =  self.pack_ieee754_sp_parts(s, e, m)
        elif (fmt == 'dp'):
            x = self.pack_ieee754_dp_parts(s, e, m)

        return x            
        
    def increase_exponent(self, ne):
        while (self.e < ne):
            self.e += 1 
            self.p = self.p << 1

    def increase_precision(self, np):
        while (self.p < np):
            self.p = self.p << 1 
            self.m = self.m << 1
            
    def abs(self):
        return FPNum(1, self.e, self.m, self.p)
        
    def neg(self):
        return FPNum(self.s * -1, self.e, self.m, self.p)
        
    
    def sub(self, bref):
        if (self.nan or bref.nan): return FPNum(self.s, self.e, -1, 0) # nan
        if (self.infinity and bref.infinity and ((self.s * bref.s)==1)): return FPNum(self.s, self.e, -1, 0) # nan
        if (self.infinity or bref.infinity): 
            if (self.infinity): return self.copy() # normal
            if (bref.infinity): return FPNum(bref.s * -1, bref.e, 0, 0) # invert the sign of this infinity
            
        b = FPNum(bref.s * -1, bref.e, bref.m, bref.p)
        return self.add(b)
    
    def add(self, bref):
        if (self.nan or bref.nan): return FPNum(self.s, self.e, -1, 0) # nan
        if (self.infinity and bref.infinity and ((self.s * bref.s)==-1)): return FPNum(self.s, self.e, -1, 0) # nan
        if (self.infinity or bref.infinity): 
            if (self.infinity): return self.copy()
            if (bref.infinity): return bref.copy()
        
        a = FPNum(self.s, self.e, self.m, self.p)
        b = FPNum(bref.s, bref.e, bref.m, bref.p)

        # ensure equal exponent         
        if (a.e > b.e): b.increase_exponent(a.e)
        elif (a.e < b.e): a.increase_exponent(b.e)
        
        assert(a.e == b.e)
        
        # ensure equal precision
        if (a.p > b.p): b.increase_precision(a.p)
        elif (a.p < b.p): a.increase_precision(b.p)
        
        assert(a.p == b.p)
        
        if (a.s == 1 and b.s == 1) or (a.s == -1 and b.s == -1):
            s = a.s
            m = a.m + b.m 
        elif (a.s == 1 and b.s == -1):
            if (a.m > b.m): 
                s = a.s 
                m = a.m - b.m
            else:
                s = b.s
                m = b.m - a.m
        elif (a.s == -1 and b.s == 1):
            if (a.m > b.m):
                s = a.s
                m = a.m - b.m
            else:
                s = b.s 
                m = b.m - a.m
                
        return FPNum(s, a.e, m, a.p)
        
    def div(self, b):
        # Zeri is a special case
        if (b.m == 0):
            if (self.m == 0):
                return FPNum(self.s, self.e, -1, 0) # nan
            else:
                r = self.copy()
                r.infinity = True
                r.s = self.s * b.s
                return r
        
        rs = self.s * b.s
        re = self.e - b.e
        
        rm = int((self.m * b.p  * self.max_prec) / b.m)
        rp = self.p * self.max_prec
        
        return FPNum(rs, re, rm, rp)

    def mul(self, b):
        if (self.nan or b.nan): return FPNum(self.s, self.e, -1, 0) # nan
        if (self.infinity or b.infinity): return FPNum(self.s * b.s, self.e, 0, 0) # infinity
            
        rs = self.s * b.s
        re = self.e + b.e
        
        rm = self.m * b.m
        rp = self.p * b.p
        
        return FPNum(rs, re, rm, rp)
    
    def div2(self, n):
        s , e, m, p = self.s, self.e, self.m, self.p << n
        return FPNum(s, e, m, p)
    
    def sqrt(self, iterations=20):
        x1 = FPNum(self.s, self.e >> 1, self.m, self.p)
        
        # zero is an special case
        if (self.m == 0):
            return self.copy()
        
        if (self.s == -1):
            # sqrt of negative numbers is Nan
            r = self.copy()
            r.nan = True
            return r
        
        #print('computing sqrt({})'.format(self.to_float()))
        
        # Newton-Raphson method 
        for i in range(iterations):
            x2 = self.div(x1)      
            #print(self.to_float(), '/', x1.to_float() , '=', x2.to_float())
            x2 = x2.add(x1)
            #print('    +', x1.to_float() , '=', x2.to_float())
            x2 = x2.div2(1)
            er = x1.sub(x2)
            
            # print('x1:', x1.to_float(), 'x2:', x2.to_float(), 'er:', er.to_float(), er.components())
            
            x1 = x2.copy()
        
        return x2
        
    def from_ieee754_hp(self, v):
        s,e,m = self.unpack_ieee754_hp_parts(v)
        s = 1 if s == 0 else -1
        
        if (e == 0x1F):
            self.set_semp(s, e, m, 0) # special cases are signaled with p = 0 
            return
        
        if (e == 0):
            # subnormal numbers
            e = -16
            m = m
        else:
            e = e - 15            
            m = (1 << 10) | m

        p = 1 << 10
        
        self.set_semp(s, e, m, p)
        self.adjust_semp()

    
    def from_ieee754_sp(self, v):
        s,e,m = self.unpack_ieee754_sp_parts(v)
        s = 1 if s == 0 else -1
        
        if (e == 0xFF):
            self.set_semp(s, e, m, 0) # special cases are signaled with p = 0
            return
        
        if (e == 0):
            # subnormal numbers
            e = -126
            m = m
        else:
            e = e - 127            
            m = (1 << 23) | m

        p = 1 << 23
        
        self.set_semp(s, e, m, p)
        self.adjust_semp()

    def from_ieee754_dp(self, v):
        s,e,m = self.unpack_ieee754_dp_parts(v)
        s = 1 if s == 0 else -1
        
        if (e == 0x7FF):
            self.set_semp(s, e, m, 0) # special cases are signaled with p = 0
            return
        
        if (e == 0):
            # subnormal numbers
            e = -1022
            m = m
        else:
            e = e - 1023
            m = (1 << 52) | m
        p = 1 << 52
        
        self.set_semp(s, e, m, p)
        self.adjust_semp()
    
    @staticmethod
    def unpack_ieee754_hp_parts(v):
        s = (v >> 15) & 1
        e = (v >> 10) & 0x1F
        m = (v & ((1<<10)-1))          
        return s, e, m
    
    @staticmethod
    def unpack_ieee754_sp_parts(v):
        s = (v >> 31) & 1
        e = (v >> 23) & 0xFF
        m = (v & ((1<<23)-1))          
        return s, e, m
    
    @staticmethod
    def unpack_ieee754_dp_parts(v):
        s = (v >> 63) & 1
        e = (v >> 52) & 0x7FF
        m = (v & ((1<<52)-1))  
        return s, e, m

    @staticmethod
    def pack_ieee754_hp_parts(s, e, m):
        return ((s & 1) << 15) | ((e & 0x1F) << 10) | (m & ((1<<10)-1))  

    @staticmethod
    def pack_ieee754_sp_parts(s, e, m):
        return ((s & 1) << 31) | ((e & 0xFF) << 23) | (m & ((1<<23)-1))  

    @staticmethod
    def pack_ieee754_dp_parts(s, e, m):
        return ((s & 1) << 63) | ((e & 0x7FF) << 52) | (m & ((1<<52)-1))  

    def convert_float_to_semp(self, v):
        if (math.isinf(v)):
            self.s , self.e, self.m , self.p =  1 if v > 0 else -1, 0, 0, 0
            self.infinity , self.nan = True, False
            return
        elif (math.isnan(v)):
            self.s , self.e, self.m , self.p =  1, 0, -1, 0
            self.infinity , self.nan = False, True
            return
            
        s, e, m, p = 1, 0, v, 1
        
        if (v == 0) and (math.copysign(1, v) == -1): s = -1
        elif (v < 0):
            s, m = -s, -m
            
        self.adjust_sem(s, e, m)
        self.adjust_semp()
        
    def adjust_sem(self, s, e, m):
        # the goal is to have m in the range of 1 to 2
        self.s = s
        self.e = e
        self.m = m
        self.p = 1
        
        n0 = 0
        n1 = 1
        n2 = 2
        
        if (self.m == 0):
            self.m = int(m)
            return 
        
        # determine exponent
        if (self.m >= 2):
            while (self.m >= 2):
                self.m /= n2
                self.e += 1
        elif (self.m < 1):
            while (self.m < 1):
                self.m *= n2
                self.e -= 1
                
        # determine divisor
        while ((self.m - int(self.m)) > 0):
            self.m *= n2
            self.p *= n2
                
        self.m = int(self.m)
        self.p = int(self.p)
        
    def set_semp(self, s, e, m, p):
        self.s = s
        self.e = e
        self.m = m
        self.p = p
        
        if (p == 0):
            if (m == 0): self.infinity = True 
            else:  self.nan = True
            

    def adjust_semp(self):
        # eliminate decimal values from the mantisa
        assert(isinstance(self.m, int))
        
        if (self.p == 0): return # ignore it for special cases

        # reduce the precision 
        while ((self.m & 1)==0) and ((self.p & 1) == 0):
            self.m = self.m >> 1
            self.p = self.p >> 1
            #print('prec --:', math.log2(self.p))

        # adjust the exponent, mantisa has to be between p and 2p
        p2 = self.p << 1
        
        if (self.m >= p2):
            while (self.m >= p2):
                # increase the exponent and increase the precision
                self.p = self.p << 1
                p2 = self.p << 1
                self.e += 1
                #print('e ++:', self.e)

        elif (self.m < self.p):
            while (self.m < self.p):
                self.m = self.m << 1 
                self.e -= 1                
                #print('e --:', self.e, self.m)
                if (self.m == 0):
                    return
        
            

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

        s, e, m = FloatingPointHelper.unpack_ieee754_sp_parts(v)
                
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

        s,e,m = FloatingPointHelper.unpack_ieee754_dp_parts(v)
        
        if (e == 0x7FF):
            if (m == 0):
                return -math.inf if (s == 1) else math.inf 
            else:
                return math.nan

        return FloatingPointHelper.ieee754_parts_to_dp(s, e, m)

    @staticmethod
    def unpack_ieee754_sp_parts(v):
        s = v >> 31
        e = (v >> 23) & 0xFF
        m = (v & ((1<<23)-1))          
        return s, e, m
    
    @staticmethod
    def unpack_ieee754_dp_parts(v):
        s = v >> 63
        e = (v >> 52) & 0x7FF
        m = (v & ((1<<52)-1))  
        return s, e, m
    
    
    @staticmethod
    def pack_ieee754_sp_parts(s, e, m):
        return ((s & 1) << 31) | ((e & 0xFF) << 23) | (m & ((1<<23)-1))  

    @staticmethod
    def ieee754_sp_neg(v):
        s, e, m = FloatingPointHelper.unpack_ieee754_sp_parts(v)
        s = s ^ 1
        return FloatingPointHelper.pack_ieee754_sp_parts(s, e, m)
        
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