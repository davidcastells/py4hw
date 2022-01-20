# -*- coding: utf-8 -*-
"""
Created on Wed Jan 19 12:53:47 2022

@author: dcr
"""
from .. import *
from deprecated import deprecated


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
        Reg(self, 'reg', d, e_add, q)
        
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
        Reg(self, 'reg', d, e_add, q)
        EqualConstant(self, 'eq{}'.format(mod-1), q, mod-1, carryout)