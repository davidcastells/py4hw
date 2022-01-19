# -*- coding: utf-8 -*-
"""
Created on Wed Jan 19 12:53:34 2022

@author: dcr
"""
from .. import *
from .bitwise import *
from deprecated import deprecated


class Equal(Logic):
    """
    An Equal comparator circuit
    """

    def __init__(self, parent, name: str, a: Wire, v: int, r: Wire):
        super().__init__(parent, name)

        a = self.addIn("a", a)
        r = self.addOut("r", r)

        w = a.getWidth()
        
        if (w == 1):
            # very simple case
            if (v == 0):
                Not(self, 'buf', a, r)
            else:
                Buf(self, 'not', a, r)
                
        else:
            bits = self.wires('b', a.getWidth(), 1)
            Bits(self, "bits", a, bits)
            Minterm(self, 'm{}'.format(v), bits, v, r)



class Comparator(Logic):
    """
    A Greater Than, Equal and Less Than comparator circuit
    """

    def __init__(self, parent, name: str, a: Wire, b: Wire, gt: Wire, eq: Wire, lt: Wire):
        super().__init__(parent, name)
        self.addIn("a", a)
        self.addIn("b", b)
        self.addOut("gt", gt)
        self.addOut("eq", eq)
        self.addOut("lt", lt)

        sub = Wire(self, "sub", a.getWidth())
        notLT = Wire(self, "~LT", 1)
        notEQ = Wire(self, "~EQ", 1)

        Sub(self, "Comparison", a, b, sub)

        # LT
        Sign(self, "LessThan", sub, lt)

        # EQ
        Equal(self, "Equal", sub, 0, eq)

        # GT
        Not(self, "~LT", lt, notLT)
        Not(self, "~EQ", eq, notEQ)
        And(self, "GreaterThan", notEQ, notLT, gt)
