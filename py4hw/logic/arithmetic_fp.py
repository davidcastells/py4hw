# -*- coding: utf-8 -*-
"""
Created on Tue Aug  9 06:15:25 2022

@author: dcr
"""
from .. import *
from .bitwise import *
from .arithmetic import *
from deprecated import deprecated


class FPAdder_SP(Logic):
    # This design is a very basic one, inspired in algorithm described in 
    # the 2.1 section of the paper 
    # Oberman, Stuart F., and Michael J. Flynn. "A variable latency pipelined 
    # floating-point adder." In European Conference on Parallel Processing, 
    # pp. 183-192. Springer, Berlin, Heidelberg, 1996.
    # https://link.springer.com/content/pdf/10.1007/bfb0024701.pdf
    def __init__(self, parent:Logic, name:str, a:Wire, b:Wire, r:Wire):
        super().__init__(parent, name)
        
        
        # This is really cumbersome
        import sys
        if not('..' in sys.path):
            sys.path.append ('..')
            
        import py4hw.helper
        
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
        ma = self.wire('ma', 23)
        mb = self.wire('mb', 23)
        
        Bit(self, 'sa',a, 31, sa)
        Bit(self, 'sb',b, 31, sb)
        Range(self, 'ea', a, 30, 23, ea)
        Range(self, 'eb', b, 30, 23, eb)
        Range(self, 'ma', a, 22, 0, ma)
        Range(self, 'mb', b, 22, 0, mb)
        
        one = self.wire('one', 1)
        Constant(self, 'one', 1, one)
        
        ma2 = self.wire('ma2', ma.getWidth()+1)
        mb2 = self.wire('mb2', ma.getWidth()+1)
        
        ConcatenateMSBF(self, 'ma2', [one, ma], ma2)
        ConcatenateMSBF(self, 'mb2', [one, mb], mb2)
        
        ma = ma2
        mb = mb2
        
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
        
        m_a_plus_b = self.wire('m_a_plus_b', ma.getWidth()+1)
        m_a_minus_b = self.wire('m_a_minus_b', ma.getWidth()+1)
        #m_b_minus_a = self.wire('m_b_minus_a', ma.getWidth()+1)
        
        Add(self, 'm_a_plus_b', ma, mb, m_a_plus_b)
        Sub(self, 'm_a_minus_b', ma, mb, m_a_minus_b)
        #Sub(self, 'm_b_minus_a', mb, ma, m_b_minus_a)
        
        # this is unnecessary since a > b
        #samb = self.wire('samb')
        #sbma = self.wire('sbma')
        
        #Sign(self, 'samb', m_a_minus_b, samb)
        #Sign(self, 'sbma', m_b_minus_a, sbma)
        
        
        mr = self.wire('mr', m_a_plus_b.getWidth())
        sr = self.wire('sr')
        
        g = py4hw.helper.LogicHelper(self)
        #sel_apb = g.hw_buf(s_eq)
        sel_amb = g.hw_xor2(sa, sb)
        #sel_bma = g.hw_and2(g.hw_not(sa), sb)
        
        Mux2(self, 'select_mr', sel_amb, m_a_plus_b, m_a_minus_b, mr)
        Buf(self, 'sr', sa, sr)
        
        
        clz = self.wire('clz', 5)
        clzz = self.wire('clzz')
        
        CountLeadingZeros(self, 'clz', mr, clz, clzz)
        
        mr2 = self.wire('mr2', mr.getWidth())
        ShiftLeft(self, 'shift_left', mr, clz, mr2)
        #Select(self, 'select_mr', [sel_apb, sel_amb, sel_bma], [m_a_plus_b, m_a_minus_b, m_b_minus_a], mr)
        #Select(self, 'select_sr', [sel_apb, sel_amb, sel_bma], [sa, sb, sa], sr)

        # Compute the result exponent
        pre_er = self.wire('pre_er', 8)
        er = self.wire('er', 8)
                
        Sub(self, 'pre_er', ea, clz, pre_er)
        Add(self, 'er', pre_er, one, er)
        
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