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
        
        aux = parent.wire('aux', r.getWidth())
        
        ShiftLeftConstant(self, 'm2', a, 1, aux)
        Add(self, "add", a, aux, r)
        
sys = HWSystem()

a = sys.wire("a", 3)
r = sys.wire("r", 3)
vcc = sys.wire("r", 3)
p = sys.wire("p", 3)

Constant(sys, 'a', 3, a)
Constant(sys, 'vcc', 1, vcc)

m3 = Mult3(sys, "m3", a, r)
Reg(sys, "reg", r, vcc, p)

Scope(sys, "p", p)
#Scope(sys, "r", r)

debug.checkIntegrity(sys)
Schematic(sys)

