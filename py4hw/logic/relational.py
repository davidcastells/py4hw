# -*- coding: utf-8 -*-
"""
Created on Wed Jan 19 12:53:34 2022

@author: dcr
"""
from .. import *

from deprecated import deprecated

class AnyEqual(Logic):
    """
    Checks whether there are any equal values in the inputs
    """
    
    def __init__(self, parent, name, ins, r:Wire):
        super().__init__(parent, name)
        
        from .bitwise import Or
        from .bitwise import Not
        
        r = self.addOut('r',r)
        lins = []
        for idx, inv in enumerate(ins):
            lins.append(self.addIn('in{}'.format(idx), inv))
            
        num = len(ins)
        checks = []
        for i in range(num):
            for j in range(num):
                if (i != j):
                    rp = self.wire('eq_{}_{}'.format(i,j), 1)
                    Equal(self, 'eq_{}_{}'.format(i,j), lins[i], lins[j], rp)
                    checks.append(rp)

        Or(self, 'anyEqual', checks, r)
                
class EqualConstant(Logic):
    """
    An Equal comparator circuit
    """

    def __init__(self, parent, name: str, a: Wire, v: int, r: Wire):
        super().__init__(parent, name)

        from .bitwise import Bits
        from .bitwise import Minterm
        from .bitwise import Buf

        # we save the values for Verilog generation
        self.a = self.addIn("a", a)
        self.r = self.addOut("r", r)
        self.v = v

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



class Equal(Logic):
    """
    An Equal comparator circuit
    """

    def __init__(self, parent, name: str, a: Wire, b: Wire, r: Wire):
        super().__init__(parent, name)

        from .bitwise import Bits
        from .bitwise import Minterm
        from .bitwise import Buf
        from .bitwise import Xor2
        from .bitwise import Nor


        a = self.addIn("a", a)
        b = self.addIn("b", b)
        r = self.addOut("r", r)

        # save them for RTL 
        self.a = a
        self.b = b
        self.r = r

        w = a.getWidth()
        
        xor = self.wire('xor', w)
        
        Xor2(self, 'xor', a, b, xor)
        
        bits = self.wires('bits', w, 1)
        Bits(self, 'bits', xor, bits)
        
        Nor(self, 'nor', bits, r)
        
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
