# -*- coding: utf-8 -*-
"""
Created on Thu Oct 29 17:06:41 2020

@author: dcr
"""

from py4hw.base import *
from py4hw.logic import *
from py4hw.logic.storage import *
from py4hw.simulation import Simulator
from py4hw import debug
from py4hw.schematic import Schematic


class Mult3(Logic):
    def __init__(self, parent:Logic, name:str, a:Wire, r:Wire):
        super().__init__(parent, name)

        self.addIn('a', a)
        self.addOut('r', r)
        
        aux = self.wire('aux', r.getWidth())
        
        ShiftLeftConstant(self, 'm2', a, 1, aux)
        Add(self, "add", a, aux, r)
        
class Mult3w(Logic):
    def __init__(self, parent:Logic, name:str, a:Wire, r:Wire):
        super().__init__(parent, name)

        self.addIn('very_long_a', a)
        self.addOut('very_long_r', r)
        
        aux = self.wire('aux', r.getWidth())
        
        ShiftLeftConstant(self, 'm2', a, 1, aux)
        Add(self, "add", a, aux, r)
        
sys = HWSystem()

a = sys.wire("a", 3)
r = sys.wire("r", 3)
r2 = sys.wire("r2", 3)
b = sys.wire('b')
c = sys.wire('c')
p = sys.wire("p", 3)

Constant(sys, 'a', 3, a)

m3 = Mult3(sys, "m3", a, r)
m3w = Mult3w(sys, "m3w", a, r2)
Reg(sys, "reg", r, p)
Bit(sys, 'bit', r, 0, b)
And2(sys, 'c', b, b, c)

bits = sys.wires('bits', r.getWidth(), 1)
BitsLSBF(sys, 'bits', r, bits)
Scope(sys, "p", p)
#Scope(sys, "r", r)

debug.checkIntegrity(sys)
sch = Schematic(sys)
sch.draw()

