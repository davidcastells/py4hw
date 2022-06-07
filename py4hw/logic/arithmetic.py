# -*- coding: utf-8 -*-
"""
Created on Wed Jan 19 12:53:47 2022

@author: dcr
"""
from .. import *
from .bitwise import *
from deprecated import deprecated


class Abs(Logic):
    """
    Absolute value
    """
    def __init__(self, parent, name: str, a: Wire, r: Wire, inverted:Wire=None):
        """
        Creates ans absolute value circuit r = abs(a), inverted=sign(a)

        Parameters
        ----------
        parent : TYPE
            parent.
        name : str
            name.
        a : Wire
            input.
        r : Wire
            absolute value of a.
        inverted : Wire, optional
            indicates wether a was negated. The default is None.

        Returns
        -------
        None.

        """
        super().__init__(parent, name)
        a = self.addIn("a", a)
        r = self.addOut("r", r)

        if not(inverted is None):
            s = self.addOut('inverted', inverted)
        else:
            s = self.wire('sign')

        zero = self.wire('zero', r.getWidth())
        neg = self.wire('neg', a.getWidth())
        Sign(self, 'sign', a, s)
        Sub(self, 'sub', zero, a, neg)
        Mux2(self, 'mux', s, a, neg, r)

class Sign(Logic):
    """
    Sign test.
    r = 0 if a >= 0 (positive)
    t = 1 if a < 0 (negative)
    """

    def __init__(self, parent, name: str, a: Wire, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.r = self.addOut("r", r)

        Bit(self, "signBit", a, a.getWidth() - 1, r)
        

class SignExtend(Logic):
    def __init__(self, parent: Logic, name: str, a: Wire, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn('a', a)
        self.r = self.addOut('r', r)

    def propagate(self):
        value = self.a.get()
        hb = value >> (self.a.getWidth() - 1)
        for i in range(self.a.getWidth(), self.r.getWidth()):
            value = value | (hb << i)

        self.r.put(value)


class ZeroExtend(Logic):
    def __init__(self, parent: Logic, name: str, a: Wire, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn('a', a)
        self.r = self.addOut('r', r)

    def propagate(self):
        value = self.a.get()
        self.r.put(value)



class Add(Logic):
    """
    Combinational Arithmetic Add
    """

    def __init__(self, parent, name: str, a: Wire, b: Wire, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)

    def propagate(self):
        self.r.put(self.a.get() + self.b.get())


class Mul(Logic):
    """
    Combinational Arithmetic Multiplier
    """

    def __init__(self, parent, name: str, a: Wire, b: Wire, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)

    def propagate(self):
        self.r.put(self.a.get() * self.b.get())


class Div(Logic):
    """
    Combinational Arithmetic Multiplier
    """

    def __init__(self, parent, name: str, a: Wire, b: Wire, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)

    def propagate(self):
        self.r.put(self.a.get() // self.b.get())


class Sub(Logic):
    """
    Arithmetic Add
    """

    def __init__(self, parent, name: str, a: Wire, b: Wire, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)

    def propagate(self):
        mask = (1 << self.r.getWidth()) - 1
        newValue = (self.a.get() - self.b.get()) & mask
        self.r.put(newValue)



class Counter(Logic):
    """
    Counts up to the value mod and returns to zero
    """
    def __init__(self, parent, name : str, reset:Wire , inc:Wire , q:Wire ):
        super().__init__(parent, name)
        
        from .bitwise import Constant
        from .bitwise import Or2
        from .bitwise import Mux2
        from .storage import Reg
        
        reset = self.addIn('reset', reset)
        inc = self.addIn('inc', inc)
        q = self.addOut('q', q)
    
        one = self.wire('one', q.getWidth())
        zero = self.wire('zero', q.getWidth())
        add = self.wire('add', q.getWidth())
        d = self.wire('d', q.getWidth())
        d1 = self.wire('d1', q.getWidth())
        e_add = self.wire('e_add', 1)
        
        Constant(self, 'one', 1, one)
        Constant(self, 'zero', 0, zero)
        
        Mux2(self, 'muxinc', inc, q, add, d1)
        Mux2(self, 'muxreset', reset, d1, zero, d)

        #py4hw.Select(self, 'select', [reset, inc], [zero, add], d)
        Or2(self, 'e_add', reset, inc, e_add)
        #py4hw.Mux(self, 'mux', )
        Add(self, 'add', q, one, add)
        Reg(self, 'reg', d, q, e_add)
        
class ModuloCounter(Logic):
    """
    Counts up to the value mod and returns to zero
    """
    def __init__(self, parent, name : str, mod : int, reset , inc , q , carryout):
        super().__init__(parent, name)
        
        from .bitwise import Constant
        from .bitwise import Or2
        from .bitwise import Mux2
        from .storage import Reg
        from .relational import EqualConstant
        
        reset = self.addIn('reset', reset)
        inc = self.addIn('inc', inc)
        q = self.addOut('q', q)
        carryout = self.addOut('carryout', carryout)
    
        one = self.wire('one', q.getWidth())
        zero = self.wire('zero', q.getWidth())
        add = self.wire('add', q.getWidth())
        d = self.wire('d', q.getWidth())
        d1 = self.wire('d1', q.getWidth())
        e_add = self.wire('e_add', 1)
        anyreset = self.wire('anyreset', 1)
        
        Constant(self, 'one', 1, one)
        Constant(self, 'zero', 0, zero)
        
        Or2(self, 'anyreset', reset, carryout, anyreset)
        Mux2(self, 'muxinc', inc, q, add, d1)
        Mux2(self, 'muxreset', anyreset,  d1,zero, d)

        #py4hw.Select(self, 'select', [reset, inc], [zero, add], d)
        Or2(self, 'e_add', reset, inc, e_add)
        #py4hw.Mux(self, 'mux', )
        Add(self, 'add', q, one, add)
        Reg(self, 'reg', d, q, enable=e_add)
        EqualConstant(self, 'eq{}'.format(mod-1), q, mod-1, carryout)
        
        
class ShiftRight(Logic):
    def __init__(self, parent:Logic, name:str, a, b, r):
        super().__init__(parent, name)

        a = self.addIn('a', a)
        b = self.addIn('b', b)
        r = self.addOut('r', r)
            
        wb = b.getWidth()
        
        num = int(math.pow(2, wb))
        ins = []
        
        for i in range(num):
            shifted = self.wire('shifted{}'.format(i), r.getWidth())
            ShiftRightConstant(self, 'shifted{}'.format(i), a, i, shifted)
            ins.append(shifted)
            
        Mux(self, 'mux', b, ins, r)
        
class BinaryToBCD(Logic):
    """
    Converts a binary number into BCD digits
    """
    
    def __init__(self, parent, name : str, a: Wire, r:Wire):
        super().__init__(parent, name)
        
        a = self.addIn('a', a)
        r = self.addOut('r', r)
    
class FPAdder_SP(Logic):
    
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
        m_b_minus_a = self.wire('m_b_minus_a', ma.getWidth()+1)
        
        Add(self, 'm_a_plus_b', ma, mb, m_a_plus_b)
        Sub(self, 'm_a_minus_b', ma, mb, m_a_minus_b)
        Sub(self, 'm_b_minus_a', mb, ma, m_b_minus_a)
        
        samb = self.wire('samb')
        sbma = self.wire('sbma')
        
        Sign(self, 'samb', m_a_minus_b, samb)
        Sign(self, 'sbma', m_b_minus_a, sbma)
        
        
        mr = self.wire('mr', m_a_plus_b.getWidth())
        sr = self.wire('sr')
        
        g = py4hw.helper.LogicHelper(self)
        sel_apb = g.hw_buf(s_eq)
        sel_amb = g.hw_and2(sa, g.hw_not(sb))
        sel_bma = g.hw_and2(g.hw_not(sa), sb)
        
        Select(self, 'select_mr', [sel_apb, sel_amb, sel_bma], [m_a_plus_b, m_a_minus_b, m_b_minus_a], mr)
        Select(self, 'select_sr', [sel_apb, sel_amb, sel_bma], [sa, sb, sa], sr)
        
        # invert result
        inverted = self.wire('inverted')
        mr2 = self.wire('mr2', mr.getWidth())
        Abs(self, 'abs', mr, mr2, inverted)
        
        mr = mr2
        
        # invert the sign if necessary
        sr = g.hw_xor2(inverted, sr)
        
        # shrink wire
        mr3 = self.wire('mr3', 23)
        Buf(self, 'mr3', mr, mr3)
        mr = mr3
        
        maxe = self.wire('maxe', ea.getWidth())
        Max2(self, 'maxe', ea, eb, maxe)
        
        ConcatenateMSBF(self, 'final_r', [sr, maxe, mr], r)