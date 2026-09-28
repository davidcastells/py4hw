# -*- coding: utf-8 -*-
"""
Created on Tue Aug  9 06:15:25 2022

Arithmetic Floating-Point blocks

@author: dcr
"""
from .. import Logic
from .. import Wire
from .. import AbstractLogic
from .bitwise import Bit
from .bitwise import Buf
from .bitwise import And2
from .bitwise import Or2
from .bitwise import Mux2
from .bitwise import Not
from .bitwise import Select
from .bitwise import Range
from .arithmetic import ShiftLeftConstant
from .bitwise import ConcatenateMSBF
from .arithmetic import ShiftLeft
from .arithmetic import ShiftRight
from .arithmetic import Sub
from .arithmetic import Add
from .arithmetic import Abs
from .arithmetic import Mul
from .arithmetic import CountLeadingZeros
from .relational import Swap
from .relational import FPComparator_SP
from .relational import Equal
from .relational import EqualConstant
from deprecated import deprecated

class _FP_parts_raw(Logic):
    def __init__(self, parent:Logic, name:str, a:Wire, s:Wire, e:Wire, m:Wire):
        super().__init__(parent, name)

    
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
    """
    Decode a binary32 operand into sign, exponent (effective biased or unbiased),
    significand, and class flags.

    e : exponent field:
        - If biased_exp=True (default): effective biased exponent
          (normals/zeros/Inf/NaN = raw exp, denormals = 1).
          value = m * 2^(e - 150)

        - If biased_exp=False: unbiased signed exponent (2's complement, 8 bits)
          (normals = exp - 127, denormals = 1 - 127 = -126 [0x82]).
          value = m * 2^(e - 23)

    m : 24-bit significand including the hidden bit: 1|frac for normals,
        0|frac for denormals, 0 for zeros.

    isDenorm / isZero / isInf / isNaN : operand class flags.
    All outputs are optional (pass None).
    """
    def __init__(self, parent:Logic, name:str, a:Wire,
                 s:Wire, e:Wire, m:Wire,
                 isDenorm:Wire, isZero:Wire, isInf:Wire, isNaN:Wire, biased_exp=True):
        super().__init__(parent, name)

        from ..helper import LogicHelper
        g = LogicHelper(self)

        self.addIn('a', a)

        pre_m = self.wire('pre_m', 23)
        pre_e = self.wire('pre_e', 8)

        if not (s is None):
            assert(s.getWidth() == 1)
            self.addOut('s', s)
            Bit(self, 's', a, 31, s)

        if not (e is None):
            assert(e.getWidth() == 8)
            self.addOut('e', e)

        if not (m is None):
            assert(m.getWidth() == 24)
            self.addOut('m', m)

        if not (isDenorm is None):
            self.addOut('isDenorm', isDenorm)
        if not (isZero is None):
            self.addOut('isZero', isZero)
        if not (isInf is None):
            self.addOut('isInf', isInf)
        if not (isNaN is None):
            self.addOut('isNaN', isNaN)

        Range(self, 'pre_e', a, 30, 23, pre_e)
        Range(self, 'pre_m', a, 22, 0, pre_m)

        e_is_0    = g.hw_not(g.hw_not_equal_constant(pre_e, 0))
        e_is_FF   = g.hw_not(g.hw_not_equal_constant(pre_e, 0xFF))
        frac_is_0 = g.hw_not(g.hw_not_equal_constant(pre_m, 0))
        frac_nz   = g.hw_not_equal_constant(pre_m, 0)

        # denorm is needed internally for the effective exponent even
        # when the isDenorm output itself is not requested
        denorm_i = self.wire('denorm_i')
        And2(self, 'denorm_i', e_is_0, frac_nz, denorm_i)

        if not (isDenorm is None):
            Buf(self, 'isDenorm', denorm_i, isDenorm)
        if not (isZero is None):
            And2(self, 'isZero', e_is_0, frac_is_0, isZero)
        if not (isInf is None):
            And2(self, 'isInf', e_is_FF, frac_is_0, isInf)
        if not (isNaN is None):
            And2(self, 'isNaN', e_is_FF, frac_nz, isNaN)

        if not (m is None):
            # hidden bit: 1 for normals (also Inf/NaN, which consumers
            # must special-case anyway), 0 for denormals and zeros
            hidden_bit = g.hw_not(e_is_0)
            ConcatenateMSBF(self, 'm', [hidden_bit, pre_m], m)

        if not (e is None):
            # Effective biased exponent: denormals use 1
            e_biased = self.wire('e_biased', 8)
            Mux2(self, 'e_biased', sel=denorm_i, sel1=g.hw_constant(8, 1), sel0=pre_e, r=e_biased)

            if biased_exp:
                Buf(self, 'e', e_biased, e)
            else:
                # Subtract IEEE-754 bias (127) for unbiased 8-bit signed exponent
                Sub(self, 'e', e_biased, g.hw_constant(8, 127), e)        
        
class FPAdder_SP(Logic):
    """
    IEEE-754 binary32 adder, round-to-nearest-even, complete:

      * Zeros:     x + (+/-0) = x ; (-0)+(-0) = -0 ; (+0)+(-0) = +0 ;
                   exact cancellation x + (-x) = +0 (RNE rule).
      * NaN/Inf:   any NaN input, or (+Inf)+(-Inf), -> canonical qNaN
                   0x7FC00000; Inf + finite = Inf; Inf + Inf = Inf.
      * Denormal *inputs*: handled exactly via the effective-exponent
                   trick (a denormal is a normal with biased exponent 1
                   and a significand whose implicit bit is 0), so no
                   input normalization stage is needed.
      * Denormal *results* (gradual underflow), RNE-rounded, including
                   the carry from largest denormal to smallest normal.
      * Overflow:  any rounded result with biased exponent >= 255
                   saturates to Inf.

    Value model: a finite nonzero operand is an integer significand
    `sig` (24 bits, as produced by _FP_parts) plus an effective biased
    exponent E:

        value = sig * 2^(E - 150)

    (normal: sig = 1|frac, E = exp;  denormal: sig = 0|frac, E = 1).
    Both significands are aligned on this common grid with the exponent
    difference saturated at 25, so the dropped fraction is always
    strictly < 1 ulp of the grid. For the subtract path the sticky bit
    is added into the subtrahend (dropped bits are an implicit borrow,
    giving exactly floor(D)); for the add path it is NOT added (adding
    it rounds the dropped bits up to a full ulp and can push a sum
    across a rounding boundary). In both cases the sticky bit only
    feeds the rounding decision.
    """

    def __init__(self, parent:Logic, name:str, a:Wire, b:Wire, r:Wire):
        super().__init__(parent, name)

        # This is really cumbersome
        from ..helper import LogicHelper
        g = LogicHelper(self)

        EB, FB, SIG = 8, 23, 24
        XB  = SIG + 1        # 25-bit aligned significand (one extra low bit)
        MW  = XB + 1         # 26-bit add/subtract result

        a = self.addIn('a', a)
        b = self.addIn('b', b)
        r = self.addOut('r', r)

        # ------------------------------------------------------------------
        # 1. Order operands by magnitude: post-swap |a2| >= |b2|.
        # ------------------------------------------------------------------
        ilt = self.wire('ilt')
        FPComparator_SP(self, 'cmp', a, b, None, None, ilt, absolute=True)

        a2 = self.wire('a2', 32)
        b2 = self.wire('b2', 32)
        Swap(self, 'swap', a, b, ilt, a2, b2)

        # ------------------------------------------------------------------
        # 2. Field decode + class detection via _FP_parts.
        #    Ea/Eb are effective biased exponents (denormals -> 1) and
        #    sig_a/sig_b are 24-bit significands with the hidden bit
        #    (0 for zero operands), so value = sig * 2^(E - 150).
        # ------------------------------------------------------------------
        sa  = self.wire('sa')
        sb  = self.wire('sb')
        Ea  = self.wire('Ea', EB)
        Eb  = self.wire('Eb', EB)
        sig_a = self.wire('sig_a', SIG)
        sig_b = self.wire('sig_b', SIG)

        isInfa = self.wire('isInfa')
        isInfb = self.wire('isInfb')
        isNaNa = self.wire('isNaNa')
        isNaNb = self.wire('isNaNb')

        _FP_parts(parent=self, name='parts_a', a=a2, s=sa, e=Ea, m=sig_a, isInf=isInfa, isNaN=isNaNa, isDenorm=None, isZero=None)
        _FP_parts(parent=self, name='parts_b', a=b2, s=sb, e=Eb, m=sig_b, isInf=isInfb, isNaN=isNaNb, isDenorm=None, isZero=None)
        
        # ------------------------------------------------------------------
        # 4. Special-value results. Post-swap any Inf sits in a2 (Inf has
        #    the largest magnitude), so an Inf result takes sign sa.
        # ------------------------------------------------------------------
        SpecialValueResults = AbstractLogic('SpecialValueResults') # class name
        obj = SpecialValueResults(self, 'special_values') # here we define instance name (the same)
        
        og = LogicHelper(obj)
        
        special_val = self.wire('special_val', 32)
        special_sel = self.wire('special_sel')

        obj.addIn('sa', sa)
        obj.addIn('sb', sb)
        obj.addIn('isInfa', isInfa)
        obj.addIn('isInfb', isInfb)
        obj.addIn('isNaNa', isNaNa)
        obj.addIn('isNaNb', isNaNb)
        obj.addOut('sepecial_val', special_val)
        obj.addOut('sepecial_sel', special_sel)
        
        inf_opp = og.hw_and2(og.hw_and2(isInfa, isInfb), og.hw_xor2(sa, sb))
        res_nan = og.hw_or2(og.hw_or2(isNaNa, isNaNb), inf_opp)
        res_inf = og.hw_and2(og.hw_or2(isInfa, isInfb), og.hw_not(res_nan))
        Or2(obj, 'special_sel', res_nan, res_inf, special_sel)

        nan_val = obj.wire('nan_val', 32)
        inf_val = obj.wire('inf_val', 32)
        ConcatenateMSBF(obj, 'nan_val', [og.hw_constant(1, 0), og.hw_constant(EB, 0xFF), og.hw_constant(FB, 0x400000)], nan_val)
        ConcatenateMSBF(obj, 'inf_val', [sa, og.hw_constant(EB, 0xFF), og.hw_constant(FB, 0)], inf_val)
        Mux2(obj, 'special_val', sel=res_nan, sel1=nan_val, sel0=inf_val, r=special_val)

        # ------------------------------------------------------------------
        # 5. Alignment. ediff_full never underflows (|a2| >= |b2| and the
        #    effective exponents respect magnitude order). Saturated at 25
        #    so the dropped fraction d is always strictly < 1 grid ulp
        #    (d < u = 2^(Ea-151)); b is pre-extended to 25 bits ({sig_b,0})
        #    so the shift is exact.
        # ------------------------------------------------------------------
        sticky = self.wire('sticky')
        mb_aligned = self.wire('mb_aligned', XB)

        Alignment = AbstractLogic('Alignment')
        obj = Alignment(self, 'alignment')

        og = LogicHelper(obj)

        obj.addIn('Ea', Ea)
        obj.addIn('Eb', Eb)
        obj.addIn('sig_b', sig_b)
        obj.addOut('mb_aligned', mb_aligned)
        obj.addOut('sticky', sticky)

        # 1. Calculate exponent difference
        ediff_full = obj.wire('ediff_full', EB)
        Sub(obj, 'ediff_full', Ea, Eb, ediff_full)

        ediff_full_x = obj.wire('ediff_full_x', EB + 1)
        ConcatenateMSBF(obj, 'ediff_full_x', [og.hw_constant(1, 0), ediff_full], ediff_full_x)
        cmp25 = obj.wire('cmp25', EB + 1)
        Sub(obj, 'cmp25', ediff_full_x, og.hw_constant(EB + 1, XB), cmp25)
        cmp25_msb = obj.wire('cmp25_msb')
        Bit(obj, 'cmp25_msb', cmp25, EB, cmp25_msb)

        # is_full_shift == 1 <==> ediff_full >= 25
        is_full_shift = og.hw_not(cmp25_msb)

        ediff_low5 = obj.wire('ediff_low5', 5)
        Range(obj, 'ediff_low5', ediff_full, 4, 0, ediff_low5)
        ediff = obj.wire('ediff', 5)
        Mux2(obj, 'ediff', sel=is_full_shift, sel1=og.hw_constant(5, XB), sel0=ediff_low5, r=ediff)

        # 2. Prepare extended significand b
        b_ext = obj.wire('b_ext', XB)
        ConcatenateMSBF(obj, 'b_ext', [sig_b, og.hw_constant(1, 0)], b_ext)

        # 3. Perform main shift for mb_aligned
        mb_sh = obj.wire('mb_sh', XB)
        ShiftRight(obj, 'mb_sh', b_ext, ediff, mb_sh)
        Mux2(obj, 'mb_aligned', sel=is_full_shift, sel1=og.hw_constant(XB, 0), sel0=mb_sh, r=mb_aligned)

        # 4. Correct Sticky Bit Calculation (Mask lower ediff bits)
        shift_back = obj.wire('shift_back', 5)
        Sub(obj, 'shift_back', og.hw_constant(5, XB), ediff, shift_back)

        all_ones = og.hw_constant(XB, (1 << XB) - 1)
        mask_sh = obj.wire('mask_sh', XB)
        ShiftRight(obj, 'mask_sh', all_ones, shift_back, mask_sh)

        mb_lost = obj.wire('mb_lost', XB)
        And2(obj, 'mb_lost', b_ext, mask_sh, mb_lost)

        mb_lost_nz = og.hw_not_equal_constant(mb_lost, 0)
        sig_b_nz = og.hw_not_equal_constant(sig_b, 0)

        # If full shift, sticky = 1 if sig_b != 0; else sticky = (mb_lost != 0)
        Mux2(obj, 'sticky', sel=is_full_shift, sel1=sig_b_nz, sel0=mb_lost_nz, r=sticky)
        
        # ------------------------------------------------------------------
        # 6. Add/subtract.
        #    ADD:  mr = ma_x + B_al              (sticky NOT injected)
        #    SUB:  mr = ma_x - (B_al + sticky)   (floor of exact difference;
        #          the dropped bits are an implicit borrow)
        #    In both cases `sticky` feeds only the rounding decision.
        # ------------------------------------------------------------------

        mr = self.wire('mr', MW)

        AddSub = AbstractLogic('AddSub') # class name
        obj = AddSub(self, 'add_sub') # here we define instance name (the same)
        
        og = LogicHelper(obj)
        
        obj.addIn('sa', sa)
        obj.addIn('sb', sb)
        obj.addIn('sig_a', sig_a)
        #obj.addIn('sig_b', sig_b)
        obj.addIn('sticky', sticky)
        obj.addIn('mb_aligned', mb_aligned)
        obj.addOut('mr', mr)

        m_sum = obj.wire('m_sum', MW)
        m_dif = obj.wire('m_dif', MW)
        
        ma_x = obj.wire('ma_x', XB)
        ConcatenateMSBF(obj, 'ma_x', [sig_a, og.hw_constant(1, 0)], ma_x)

        sticky_ext = obj.wire('sticky_ext', XB)
        ConcatenateMSBF(obj, 'sticky_ext', [og.hw_constant(XB - 1, 0), sticky], sticky_ext)
        mb_x_sub = obj.wire('mb_x_sub', XB)
        Add(obj, 'mb_x_sub', mb_aligned, sticky_ext, mb_x_sub)

        Add(obj, 'm_sum', ma_x, mb_aligned, m_sum)
        Sub(obj, 'm_dif', ma_x, mb_x_sub, m_dif)

        sel_amb = og.hw_xor2(sa, sb)
        Mux2(obj, 'mr', sel=sel_amb, sel1=m_dif, sel0=m_sum, r=mr)
        sr = sa

        # ------------------------------------------------------------------
        # 7. Normalize + result exponent (9-bit signed):
        #        value = mr * 2^(Ea-151)
        #        Er = Ea + 1 - clz        in [-23, 255]
        # ------------------------------------------------------------------
        mr_is_zero = self.wire('mr_is_zero')
        mr2 = self.wire('mr2', MW)
        Er9 = self.wire('Er9', 9)
        denormal_sel = self.wire('denormal_sel')

        Normalizer = AbstractLogic('Normalizer') # class name
        obj = Normalizer(self, 'normalizer') # here we define instance name (the same)
        
        og = LogicHelper(obj)
        
        obj.addIn('mr', mr)
        obj.addIn('Ea', Ea)
        obj.addOut('mr2', mr2)
        obj.addOut('Er9', Er9)
        obj.addOut('mr_is_zero', mr_is_zero)
        obj.addOut('denormal_sel', denormal_sel)
        
        EqualConstant(obj, 'mr_is_zero', mr, 0, mr_is_zero)

        clz = obj.wire('clz', 5)
        clzz = obj.wire('clzz')
        CountLeadingZeros(obj, 'clz', mr, clz, clzz)
        clz_safe = obj.wire('clz_safe', 5)
        Mux2(obj, 'clz_safe', sel=clzz, sel1=og.hw_constant(5, 0), sel0=clz, r=clz_safe)

        ShiftLeft(obj, 'mr2', mr, clz_safe, mr2)

        Ea9 = obj.wire('Ea9', 9)
        ConcatenateMSBF(obj, 'Ea9', [og.hw_constant(1, 0), Ea], Ea9)
        ea_plus1 = obj.wire('ea_plus1', 9)
        Add(obj, 'ea_plus1', Ea9, og.hw_constant(9, 1), ea_plus1)
        clz9 = obj.wire('clz9', 9)
        ConcatenateMSBF(obj, 'clz9', [og.hw_constant(4, 0), clz_safe], clz9)
        Sub(obj, 'Er9', ea_plus1, clz9, Er9)

        er9_neg = obj.wire('er9_neg')
        Bit(obj, 'er9_neg', Er9, 8, er9_neg)
        er9_eq0 = obj.wire('er9_eq0')
        Equal(obj, 'er9_eq0', Er9, og.hw_constant(9, 0), er9_eq0)
        Or2(obj, 'denormal_sel', er9_neg, er9_eq0, denormal_sel)     # Er9 <= 0
        
        # ------------------------------------------------------------------
        # 8. Normal-path RNE rounding.
        #    mr2 = [ implicit 1 (bit 25) | fraction (bits 24:2)
        #          | guard (bit 1) | sticky (bit 0) ]
        # ------------------------------------------------------------------
        er_n = self.wire('er_n', EB)
        frac_n = self.wire('frac_n', FB)
        overflow_sel = self.wire('overflow_sel')
        
        NormalRounder = AbstractLogic('NormalRounder') # class name
        obj = NormalRounder(self, 'normal_rounder') # here we define instance name (the same)
        
        obj.addIn('mr2', mr2)
        obj.addIn('Er9', Er9)
        obj.addIn('sticky', sticky)

        obj.addOut('er_n', er_n)
        obj.addOut('frac_n', frac_n)
        obj.addOut('overflow_sel', overflow_sel)
        

        og = LogicHelper(obj)

        guard = obj.wire('guard')
        lsb_kept = obj.wire('lsb_kept')
        new_sticky = obj.wire('new_sticky')
        Bit(obj, 'guard', mr2, 1, guard)
        Bit(obj, 'lsb_kept', mr2, 2, lsb_kept)
        Bit(obj, 'new_sticky', mr2, 0, new_sticky)
        round_up = og.hw_and2(guard, og.hw_or2(sticky, og.hw_or2(new_sticky, lsb_kept)))

        round_amt = obj.wire('round_amt', MW + 1)
        Mux2(obj, 'round_amt', sel=round_up, sel1=og.hw_constant(MW + 1, 4), sel0=og.hw_constant(MW + 1, 0), r=round_amt)
        rr = obj.wire('rr', MW + 1)
        Add(obj, 'rr', mr2, round_amt, rr)
        rr_msb = obj.wire('rr_msb')
        Bit(obj, 'rr_msb', rr, MW, rr_msb)

        rr_msb_ext = obj.wire('rr_msb_ext', 9)
        ConcatenateMSBF(obj, 'rr_msb_ext', [og.hw_constant(8, 0), rr_msb], rr_msb_ext)
        er9_n = obj.wire('er9_n', 9)
        Add(obj, 'er9_n', Er9, rr_msb_ext, er9_n)    # in [1, 256]

        Range(obj, 'er_n', er9_n, 7, 0, er_n)
        Range(obj, 'frac_n', rr, 24, 2, frac_n)



        # 1. Detect if er9_n is negative (sign bit / bit 8 is set)
        er9_is_neg = obj.wire('er9_is_neg')
        Bit(obj, 'er9_is_neg', er9_n, 8, er9_is_neg)
        
        # 2. Check if the 8-bit magnitude portion reached 255
        er9_255 = obj.wire('er9_255')
        Equal(obj, 'er9_255', er9_n, og.hw_constant(9, 255), er9_255)
        
        # 3. Check if er9_n is strictly positive and >= 256 (e.g., er9_n bit 8 set while NOT negative)
        # Alternatively, check if er9_n >= 255 while explicitly NOT negative:
        er9_is_pos = og.hw_not(er9_is_neg)
        
        # er9_ge_255_pos is true when er9_n >= 255 AND er9_n > 0
        er9_ge_255_raw = og.hw_or2(er9_is_neg, er9_255) # or use a comparator against 255
        And2(obj, 'overflow_sel', er9_is_pos, er9_ge_255_raw, overflow_sel)

        # ------------------------------------------------------------------
        # 9. Denormal-result path (Er9 <= 0): right-shift by sh = 3 - Er
        #    (in [3, 26]) and RNE-round into 23 fraction bits with biased
        #    exponent 0. A carry out of bit 22 yields the smallest normal.
        # ------------------------------------------------------------------
        er_d = self.wire('er_d', EB)
        frac_d = self.wire('frac_d', FB)
        
        DenormalRounder = AbstractLogic('DenormalRounder')
        obj = DenormalRounder(self, 'denormal_rounder')

        obj.addIn('mr2', mr2)
        obj.addIn('Er9', Er9)
        obj.addIn('sticky', sticky)
        
        obj.addOut('er_d', er_d)
        obj.addOut('frac_d', frac_d)
        
        og = LogicHelper(obj)

        # 1. Calculate shift amount for denormal alignment
        rsh9 = obj.wire('rsh9', 9)
        Sub(obj, 'rsh9', og.hw_constant(9, 1), Er9, rsh9)       # 1 - Er
        sh9 = obj.wire('sh9', 9)
        Add(obj, 'sh9', rsh9, og.hw_constant(9, 2), sh9)        # 3 - Er
        sh = obj.wire('sh', 5)
        Range(obj, 'sh', sh9, 4, 0, sh)

        # 2. Main Right Shift
        F_sh = obj.wire('F_sh', MW)
        ShiftRight(obj, 'F_sh', mr2, sh, F_sh)
        sh9_eqMW = obj.wire('sh9_eqMW')
        EqualConstant(obj, 'sh9_eqMW', sh9, MW, sh9_eqMW)
        F = obj.wire('F', MW)
        Mux2(obj, 'F', sel=sh9_eqMW, sel1=og.hw_constant(MW, 0), sel0=F_sh, r=F)

        # 3. Compute Shifted-Out Sticky Bits
        # Mask out bits dropped during right shift by 'sh'
        all_ones = og.hw_constant(MW, (1 << MW) - 1)
        sh_back = obj.wire('sh_back', 5)
        Sub(obj, 'sh_back', og.hw_constant(5, MW), sh, sh_back)
        
        mask = obj.wire('mask', MW)
        ShiftRight(obj, 'mask', all_ones, sh_back, mask)
        
        dropped_bits = obj.wire('dropped_bits', MW)
        And2(obj, 'dropped_bits', mr2, mask, dropped_bits)
        
        dropped_nz = og.hw_not_equal_constant(dropped_bits, 0)
        combined_sticky = og.hw_or2(sticky, dropped_nz)

        # 4. Guard & LSB for Round-to-Nearest-Even (RNE)
        # Extract LSB of unshifted result (bit 0 of F) and Guard bit
        lsb = obj.wire('lsb')
        Bit(obj, 'lsb', F, 0, lsb)

        # RNE round up condition: guard AND (lsb OR sticky)
        # When sh == 0, no bits shifted, round_up = 0
        sh_is_0 = og.hw_not(og.hw_not_equal_constant(sh, 0))
        
        # If no shift occurred, don't round up
        round_up_raw = og.hw_and2(combined_sticky, lsb)
        round_up = obj.wire('round_up')
        Mux2(obj, 'round_up', sel=sh_is_0, sel1=og.hw_constant(1, 0), sel0=round_up_raw, r=round_up)

        # 5. Conditional Increment
        round_amt = obj.wire('round_amt', MW)
        Mux2(obj, 'round_amt', sel=round_up, sel1=og.hw_constant(MW, 1), sel0=og.hw_constant(MW, 0), r=round_amt)

        Fr = obj.wire('Fr', MW)
        Add(obj, 'Fr', F, round_amt, Fr)

        # 6. Check if rounding produced a normal number (overflow out of denormal range)
        denorm_to_normal = obj.wire('denorm_to_normal')
        Bit(obj, 'denorm_to_normal', Fr, SIG - 1, denorm_to_normal)
        Mux2(obj, 'er_d', sel=denorm_to_normal, sel1=og.hw_constant(EB, 1), sel0=og.hw_constant(EB, 0), r=er_d)
        
        Range(obj, 'frac_d', Fr, FB - 1, 0, frac_d)
        
        # ------------------------------------------------------------------
        # 10. Final assembly. Exact-zero sums (x + (-x), (+0)+(-0)) give
        #     +0 in RNE unless both operands are -0.
        # ------------------------------------------------------------------
        #Outputs: r
        
        ResultSelection = AbstractLogic('ResultSelection') # class name
        obj = ResultSelection(self, 'result_selection') # here we define instance name (the same)

        obj.addIn('sa', sa)
        obj.addIn('sb', sb)
        obj.addIn('sr', sr)
        obj.addIn('er_d', er_d)
        obj.addIn('frac_d', frac_d)
        obj.addIn('er_n', er_n)
        obj.addIn('frac_n', frac_n)
        obj.addIn('denormal_sel', denormal_sel)
        obj.addIn('overflow_sel', overflow_sel)
        obj.addIn('mr_is_zero', mr_is_zero)
        obj.addIn('special_sel', special_sel)
        obj.addIn('special_val', special_val)
        
        obj.addOut('r', r)
        
        og = LogicHelper(obj)


        szero = og.hw_and2(sa, sb)
        r_zero = obj.wire('r_zero', 32)
        r_den  = obj.wire('r_den', 32)
        r_norm = obj.wire('r_norm', 32)
        r_inf  = obj.wire('r_inf', 32)
        ConcatenateMSBF(obj, 'r_zero', [szero, og.hw_constant(EB, 0), og.hw_constant(FB, 0)], r_zero)
        ConcatenateMSBF(obj, 'r_den',  [sr, er_d, frac_d],  r_den)
        ConcatenateMSBF(obj, 'r_norm', [sr, er_n, frac_n],  r_norm)
        ConcatenateMSBF(obj, 'r_inf', [sr, og.hw_constant(EB, 0xFF), og.hw_constant(FB, 0)], r_inf)

        r_dp1 = obj.wire('r_dp1', 32)
        r_dp2 = obj.wire('r_dp2', 32)
        r_dp3 = obj.wire('r_dp3', 32)

        Mux2(obj, 'sel_denormal', sel=denormal_sel, sel1=r_den, sel0=r_norm, r=r_dp1)
        Mux2(obj, 'sel_overflow', sel=overflow_sel, sel1=r_inf, sel0=r_dp1, r=r_dp2)
        Mux2(obj, 'sel_zero', sel=mr_is_zero, sel1=r_zero, sel0=r_dp2, r=r_dp3)
        Mux2(obj, 'sel_special', sel=special_sel, sel1=special_val, sel0=r_dp3, r=r)
        
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
        
        _FP_parts(self, 'parts', a=a, s=sign, e=real_e, m=real_m, 
                  isDenorm=is_denorm, isZero=is_zero, isInf=None, isNaN=None, biased_exp=False)

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
    def __init__(self, parent: Logic, name: str, a: Wire, b: Wire, r: Wire):
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
        
        # 1. Single unified extraction via _FP_parts
        _FP_parts(self, 'pa', a, sa, ea, ma, isDenorma, isZeroa, None, None, biased_exp=True)
        _FP_parts(self, 'pb', b, sb, eb, mb, isDenormb, isZerob, None, None, biased_exp=True)

        from ..helper import LogicHelper        
        g = LogicHelper(self)
        
        # 2. Zero check & Result Sign
        isZeror = g.hw_or2(isZeroa, isZerob)
        sr = g.hw_xor2(sa, sb)
        
        # 3. Significand Multiplication (24 x 24 = 48 bits)
        pre_mr = self.wire('pre_mr', ma.getWidth() + mb.getWidth()) # 48 bits [47:0]
        Mul(self, 'mult', ma, mb, pre_mr)
        
        # 4. Exponent Addition: E_sum = Ea + Eb
        pre_er = self.wire('pre_er', 9)
        Add(self, 'add', ea, eb, pre_er)
        
        # Un-double the bias: E_unbiased = Ea + Eb - 127
        pre_er2 = self.wire('pre_er2', 8)
        Sub(self, 'pre_er2', pre_er, g.hw_constant(9, 127), pre_er2)
        
        # 5. Normalization Handling
        # If product >= 2.0 (bit 47 is 1), exponent shifts by +1
        select_mr = g.hw_bit(pre_mr, 47)
        
        pre_er3 = self.wire('pre_er3', 8)
        Add(self, 'pre_er3', pre_er2, g.hw_constant(8, 1), pre_er3)
        
        # Truncated fraction selection (bits [46:24] vs [45:23])
        pre_mr2 = g.hw_range(pre_mr, 46, 24)
        pre_mr3 = g.hw_range(pre_mr, 45, 23)
        
        pre_mr4 = self.wire('pre_mr4', 23)
        pre_er4 = self.wire('pre_er4', 8)
        Mux2(self, 'mux_mr4', sel=select_mr, sel1=pre_mr2, sel0=pre_mr3, r=pre_mr4)
        Mux2(self, 'mux_er4', sel=select_mr, sel1=pre_er3, sel0=pre_er2, r=pre_er4)
        
        # 6. Override output with 0 if either input is Zero
        final_er = self.wire('final_er', 8)
        final_mr = self.wire('final_mr', 23)
        Mux2(self, 'mux_final_er', sel=isZeror, sel1=g.hw_constant(8, 0), sel0=pre_er4, r=final_er)
        Mux2(self, 'mux_final_mr', sel=isZeror, sel1=g.hw_constant(23, 0), sel0=pre_mr4, r=final_mr)
        
        ConcatenateMSBF(self, 'r', [sr, final_er, final_mr], r)