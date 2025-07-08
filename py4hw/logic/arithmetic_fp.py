# -*- coding: utf-8 -*-
"""
Created on Tue Aug  9 06:15:25 2022

Arithmetic Floating-Point blocks

@author: dcr
"""
from .. import *
from .bitwise import *
from .arithmetic import *
from deprecated import deprecated


class _FP_parts_raw(Logic):
    def __init__(self, parent:Logic, name:str, a:Wire, s:Wire, e:Wire, m:Wire):
        super().__init__(parent, name)

        from ..helper import LogicHelper
    
        self.addIn('a', a)

        if not(s is None):
            assert(s.getWidth() == 1)
            self.addOut('s', s)
            Bit(self, 's',a, 31, s)

        if not(e is None):
            assert(e.getWidth() == 8)
            self.addOut('e', e)
            Range(self, 'e', a, 30, 23, e)

        if not(m is None):
            assert(m.getWidth() == 23)        
            self.addOut('m', m)        
            Range(self, 'm', a, 22, 0, m)
        

class _FP_parts(Logic):
    def __init__(self, parent:Logic, name:str, a:Wire, s:Wire, e:Wire, m:Wire, isDenorm:Wire, isZero:Wire):
        super().__init__(parent, name)

        from ..helper import LogicHelper
    
        g = LogicHelper(self)
        
        self.addIn('a', a)

        pre_m = self.wire('pre_m', 23)
        pre_e = self.wire('pre_e', 8)
        
        if not(s is None):
            assert(s.getWidth() == 1)
            self.addOut('s', s)
            Bit(self, 's',a, 31, s)

        if not(e is None):
            assert(e.getWidth() == 8)
            self.addOut('e', e)
            # e2 = 32 + (e - 127)
            Sub(self, 'e', pre_e, g.hw_constant(8, 127), e)

        if not(m is None):
            assert(m.getWidth() == 24)
            self.addOut('m', m)

        if not(isDenorm is None):
            self.addOut('isDenorm', isDenorm)

        if not(isZero is None):
            self.addOut('isZero', isZero)
        
        Range(self, 'pre_e', a, 30, 23, pre_e)
        Range(self, 'pre_m', a, 22, 0, pre_m)
        
        hidden_bit = g.hw_not_equal_constant(pre_e, 0)        
        frac_is_not_0 = g.hw_not_equal_constant(pre_m, 0)

        And2(self, 'isDenorm', g.hw_not(hidden_bit), frac_is_not_0, isDenorm)
        And2(self, 'isZero', g.hw_not(hidden_bit), g.hw_not(frac_is_not_0), isZero)
        
        if not(m is None):
            ConcatenateMSBF(self, 'm', [hidden_bit, pre_m], m) 
        
        
                
class FPAdder_SP(Logic):
    # This design is a very basic one, inspired in algorithm described in 
    # the 2.1 section of the paper 
    # Oberman, Stuart F., and Michael J. Flynn. "A variable latency pipelined 
    # floating-point adder." In European Conference on Parallel Processing, 
    # pp. 183-192. Springer, Berlin, Heidelberg, 1996.
    # https://link.springer.com/content/pdf/10.1007/bfb0024701.pdf
    #
    def __init__(self, parent:Logic, name:str, a:Wire, b:Wire, r:Wire):
        super().__init__(parent, name)
        
        
        # This is really cumbersome
        from ..helper import LogicHelper
                    
        a = self.addIn('a', a)
        b = self.addIn('b', b)
        r = self.addOut('r', r)
        
        igt = self.wire('igt')
        ieq = self.wire('ieq')
        ilt = self.wire('ilt')

        FPComparator_SP(self, 'cmp', a, b, igt, ieq, ilt, absolute=True)
        
        a2 = self.wire('a2', a.getWidth())
        b2 = self.wire('b2', b.getWidth())
        
        Swap(self, 'swap', a, b, ilt, a2, b2)
        
        a = a2
        b = b2
        
        sa = self.wire('sa')
        sb = self.wire('sb')
        ea = self.wire('ea', 8)
        eb = self.wire('eb', 8)
        ma = self.wire('ma', 24)
        mb = self.wire('mb', 24)
        isZeroa = self.wire('isZeroa')
        isZerob = self.wire('isZerob')
        isDenorma = self.wire('isDenorma')
        isDenormb = self.wire('isDenormb')
        
        _FP_parts(self, 'parts_a', a, sa, None, ma, isDenorma, isZeroa)
        _FP_parts(self, 'parts_b', b, sb, None, mb, isDenormb, isZerob)
        
        _FP_parts_raw(self, 'parts_a_raw', a, None, ea, None)
        _FP_parts_raw(self, 'parts_b_raw', b, None, eb, None)
        
        # Maximum possible shifting is 23 bits (of the mantisa), so
        # it is enough with 5 bits for ediff
        # Also we know ediff will be always positive

        ediff = self.wire('ediff', 5)
        Sub(self, 'ediff', ea, eb, ediff)
        
        mb3 = self.wire('mb3', mb.getWidth())
        
        ShiftRight(self, 'preshift', mb, ediff, mb3)
        
        mb = mb3
        
        s_eq = self.wire('s_eq')
        Equal(self, 's_eq', sa, sb, s_eq)
        
        m_a_plus_b = self.wire('m_a_plus_b', 25)
        m_a_minus_b = self.wire('m_a_minus_b', 25)
        #m_b_minus_a = self.wire('m_b_minus_a', ma.getWidth()+1)
        
        Add(self, 'm_a_plus_b', ma, mb, m_a_plus_b)
        Sub(self, 'm_a_minus_b', ma, mb, m_a_minus_b)
        
        
        # Result is composed by sr, er, mr
        mr = self.wire('mr', 25)
        sr = self.wire('sr')
        
        g = LogicHelper(self)
        #sel_apb = g.hw_buf(s_eq)
        sel_amb = g.hw_xor2(sa, sb)
        #sel_bma = g.hw_and2(g.hw_not(sa), sb)
        
        Mux2(self, 'select_mr', sel_amb, m_a_plus_b, m_a_minus_b, mr)
        
        # The bigger sign dominates the sign of the result
        Buf(self, 'sr', sa, sr)
                
        clz = self.wire('clz', 5)
        clzz = self.wire('clzz')
        
        # Normalize, so that MSB is always 1
        CountLeadingZeros(self, 'clz', mr, clz, clzz)
        
        mr2 = self.wire('mr2', mr.getWidth())
        ShiftLeft(self, 'shift_left', mr, clz, mr2)
        #Select(self, 'select_mr', [sel_apb, sel_amb, sel_bma], [m_a_plus_b, m_a_minus_b, m_b_minus_a], mr)
        #Select(self, 'select_sr', [sel_apb, sel_amb, sel_bma], [sa, sb, sa], sr)

        # Compute the result exponent
        pre_er = self.wire('pre_er', 8)
        er = self.wire('er', 8)
                
        Sub(self, 'pre_er', ea, clz, pre_er)
        Add(self, 'er', pre_er, g.hw_constant(8, 1), er)
        
        # Detect round up bit
        round_up = self.wire('round_up')
        Bit(self, 'round_up', mr2, 1, round_up)
        
        # Add 1 (actually b10) for rounding up mr2
        round_one = self.wire('round_one', 25)
        round_result = self.wire('round_result', 26)
        round_result_msb = self.wire('round_result_msb')
        Constant(self, 'round_one', 1, round_one)
        Add(self, 'round_result', mr2, round_one, round_result)
        Bit(self, 'round_result_msb', round_result, 25, round_result_msb)
        
        # invert result
        #inverted = self.wire('inverted')
        #mr2 = self.wire('mr2', mr.getWidth())
        #Abs(self, 'abs', mr, mr2, inverted)        
        #mr = mr2
        
        # invert the sign if necessary
        #sr = g.hw_xor2(inverted, sr)
        
        # shrink wire, we take from 23 to 1, as we assume that 24 is 1 
        mr3 = self.wire('mr3', 23)        
        Range(self, 'mr3', mr2, 23, 1, mr3)
                
        ConcatenateMSBF(self, 'final_r', [sr, er, mr3], r)
        
        
        
class FPtoInt_SP(Logic):
    # This design is inspired in algorithm described in 
    # section 9.2.1 of the book 
    # Computer Principles and design in Verilog
    def __init__(self, parent:Logic, name:str, a:Wire, r:Wire, p_lost:Wire, denorm:Wire, invalid:Wire):
        super().__init__(parent, name)

        # This is really cumbersome
        from ..helper import LogicHelper

        self.addIn('a', a)
        self.addOut('r', r)
        self.addOut('p_lost', p_lost)
        self.addOut('denorm', denorm)
        self.addOut('invalid', invalid)

        sign = self.wire('sign')
        real_e = self.wire('e', 8)
        real_m = self.wire('m', 24)
        is_denorm = self.wire('is_denorm')
        is_zero = self.wire('is_zero')
        
        _FP_parts(self, 'parts', a, sign, real_e, real_m, is_denorm, is_zero)

        g = LogicHelper(self)
        
        zero_tail = g.hw_constant(32, 0)

        frac0 = g.hw_concatenate_msbf([real_m, zero_tail]) # 56 bits
        
        sign_real_e = g.hw_sign(real_e)

        # if exponent is positive we have to shift left first by e
        # then shift right 23 bits. So the shift right will be 23-real_e
        # if the value is greater than 23 we will get a negative value
        shift_amount_right = g.hw_sub(g.hw_constant(8, 23), real_e)
        shift_amount_left = g.hw_sub(real_e, g.hw_constant(8, 23))
        shift_sign = g.hw_sign(shift_amount_right)

        shifted = self.wire('shifted', 64)
        shifted_right = self.wire('shifted_right', 64)
        shifted_left = self.wire('shifted_left', 64)
        ShiftRight(self, 'shifted_right', frac0, shift_amount_right, shifted_right)
        ShiftLeft(self, 'shifted_left', frac0, shift_amount_left, shifted_left)
        Mux2(self, 'shifted', shift_sign, shifted_right, shifted_left, shifted)
        too_big = g.hw_signed_gt_constant(real_e, 30)
        
        final_m_pos = g.hw_range(shifted, 32+32, 32)
        final_m_neg = g.hw_neg(final_m_pos)
        
        final_m = g.hw_if(sign, final_m_neg, final_m_pos)
        pos_ext_p_lost = g.hw_not_equal_constant(g.hw_range(shifted, 32, 0), 0)

        # if exponent is negative we have to shift right first by e 
        # then shift right 24 bits. But this will surelly be less than 1
        
        
        # for denorm values
        select_denorm = is_denorm
        p_lost_denorm = g.hw_constant(1,1)
        invalid_denorm = g.hw_constant(1,0)
        d_denorm = g.hw_constant(32, 0)
        
        # negative exponent
        select_small = sign_real_e
        p_lost_small = g.hw_not(is_zero) 
        invalid_small = g.hw_constant(1,0)
        d_small = g.hw_constant(32, 0)
        
        # positive exponent
        select_default = g.hw_or2(g.hw_not(select_denorm), g.hw_not(select_small))
        p_lost_default = pos_ext_p_lost
        invalid_default = too_big
        d_default = final_m

        Buf(self, 'denorm', is_denorm, denorm)
        Select(self, 'select_p_lost', [select_denorm, select_small, select_default], 
               [p_lost_denorm, p_lost_small, p_lost_default], p_lost)
        Select(self, 'select_invalid', [select_denorm, select_small, select_default],
               [invalid_denorm, invalid_small, invalid_default], invalid)
        Select(self, 'select_d', [select_denorm, select_small, select_default], 
               [d_denorm, d_small, d_default], r)


class InttoFP_SP(Logic):
    # This design is inspired in algorithm described in 
    # section 9.2.2 of the book 
    # Computer Principles and design in Verilog
    def __init__(self, parent:Logic, name:str, a:Wire, r:Wire, p_lost:Wire):
        super().__init__(parent, name)

        # This is really cumbersome
        from ..helper import LogicHelper

        assert(a.getWidth() == 32)        
        assert(r.getWidth() == 32)        

        self.addIn('a', a)
        self.addOut('r', r)
        self.addOut('p_lost', p_lost)

        g = LogicHelper(self)
        
        sign = self.wire('sign')
        f5 = self.wire('f5', a.getWidth())
        
        Abs(self, 'f5', a, f5, inverted=sign)

        clz = self.wire('clz', 5)
        is_zero = self.wire('is_zero')
        
        CountLeadingZeros(self, 'clz', f5, clz, is_zero)

        shifted = self.wire('shited', 32)
        ShiftLeft(self, 'shift', f5, clz, shifted)
        
        # we skip the first 1, as it is implicit
        fraction = g.hw_range(shifted, 30, 30-23+1)

        pre_p_lost = g.hw_not_equal_constant(g.hw_range(shifted, 30-23, 0), 0)
        Buf(self, 'p_lost', pre_p_lost, p_lost)

        exponent = g.hw_sub(g.hw_constant(8, 127+31), clz)

        #is_zero = g.hw_equal_constant(a, 0)
        pre_r = self.wire('pre_r', 32)
        ConcatenateMSBF(self, 'pre_r', [sign, exponent, fraction], pre_r)
        Mux2(self, 'r', is_zero, pre_r, g.hw_constant(32, 0), r)
        
        
class FixedPointtoFP_SP(Logic):
    def __init__(self, parent:Logic, name:str, a:Wire, f, r:Wire, p_lost:Wire):
        # @todo by now we do a dirty implementation
        # we really should do something similar to the above method
        super().__init__(parent, name)

        # This is really cumbersome
        from ..helper import LogicHelper

        assert(a.getWidth() <= 32)  # by now we need w <= 32, when covering this case 
                                    # 
        assert(r.getWidth() == 32)        
        
        self.addIn('a', a)
        self.addOut('r', r)
        
        if not(p_lost is None):
            self.addOut('p_lost', p_lost)

        g = LogicHelper(self)
        
        sign = self.wire('sign')
        f5 = self.wire('f5', a.getWidth())
        
        Abs(self, 'f5', a, f5, inverted=sign)
        
        #ai = self.wire('ai', a.getWidth() - f[2])
        #af = self.wire('af', f[2])

        #py4hw.Range(self, 'ai', a.getWidth()-1, a.getWidth() - f[2])
        #py4hw.Range(self, 'af', f[2]-1, 0)
        
        clz = self.wire('clz', 5)
        is_zero = self.wire('is_zero')
        CountLeadingZeros(self, 'clz', f5, clz, is_zero)

        pre_shifted = self.wire('pre_shifted', 32)
        ShiftLeftConstant(self, 'pre_shifted', f5, 32-a.getWidth(), pre_shifted)

        shifted = self.wire('shited', 32)
        ShiftLeft(self, 'shift', pre_shifted, clz, shifted)

        # we skip the first 1, as it is implicit
        fraction = g.hw_range(shifted, 30, 30-23+1)

        if not(p_lost is None):        
            pre_p_lost = g.hw_not_equal_constant(g.hw_range(shifted, 30-23, 0), 0)
            Buf(self, 'p_lost', pre_p_lost, p_lost)
        
        exponent = g.hw_sub(g.hw_constant(8, 127+f[1]), clz)
        
        #is_zero = g.hw_equal_constant(a, 0)
        pre_r = self.wire('pre_r', 32)
        ConcatenateMSBF(self, 'pre_r', [sign, exponent, fraction], pre_r)
        Mux2(self, 'r', is_zero, pre_r, g.hw_constant(32, 0), r)

        

class FPMult_SP(Logic):
    # 
    def __init__(self, parent:Logic, name:str, a:Wire, b:Wire, r:Wire):
        super().__init__(parent, name)
        
        self.addIn('a', a)
        self.addIn('b', b)
        self.addOut('r', r)
        
        sa = self.wire('sa')
        sb = self.wire('sb')
        ea = self.wire('ea', 8)
        eb = self.wire('eb', 8)
        ma = self.wire('ma', 24)
        mb = self.wire('mb', 24)
        isZeroa = self.wire('isZeroa')
        isZerob = self.wire('isZerob')
        isDenorma = self.wire('isDenorma')
        isDenormb = self.wire('isDenormb')
        
        _FP_parts(self, 'pa', a, sa, None, ma, isDenorma, isZeroa)
        _FP_parts(self, 'pb', b, sb, None, mb, isDenormb, isZerob)

        _FP_parts_raw(self, 'pa_raw', a, None, ea, None )
        _FP_parts_raw(self, 'pb_raw', b, None, eb, None )

        from ..helper import LogicHelper        
        g = LogicHelper(self)
        
        # a * b = sa * sb * 2^ea * 2^eb * ma * mb
        # a * b = (sa*sb) * 2 ^(ea+eb) + (ma*mb)
        
        isZeror = g.hw_or2(isZeroa, isZerob)
        
        sr = g.hw_xor2(sa, sb)
        
        pre_mr = self.wire('pre_mr', ma.getWidth() + mb.getWidth())
        Mul(self, 'mult', ma, mb, pre_mr)
        
        pre_er = self.wire('pre_er', 9)
        Add(self, 'add', ea, eb, pre_er)
        pre_er2 = self.wire('pre_er2', 8)
        pre_er3 = self.wire('pre_er3', 8)
        Sub(self, 'pre_er2', pre_er, g.hw_constant(9, 127-1), pre_er2)
        Sub(self, 'pre_er3', pre_er2, g.hw_constant(9,1), pre_er3)
        
        # result of ma*mb must be 0 <= mr < 4, it seems the first bit will be always 1
        select_mr = g.hw_bit(pre_mr, 47)
        pre_mr2 = g.hw_range(pre_mr, 46, 24)
        pre_mr3 = g.hw_range(pre_mr, 45, 23)
        
        pre_mr4 = g.hw_mux2(select_mr, pre_mr3, pre_mr2)
        pre_er4 = g.hw_mux2(select_mr, pre_er3, pre_er2)
        
        ConcatenateMSBF(self, 'r', [sr, pre_er4, pre_mr4], r)