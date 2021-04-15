# -*- coding: utf-8 -*-
"""
Created on Sat Oct 31 11:52:40 2020

@author: dcr
"""

# -*- coding: utf-8 -*-
"""
Created on Sat Oct 31 11:19:05 2020

@author: dcr
"""
from py4hw.base import *
from py4hw.logic import *
from py4hw.simulation import Simulator
import py4hw.debug


sys = HWSystem()

a = sys.wire("a", 3)

bits = sys.wires('b', 3, 1)
minterm = sys.wire('minterm',1)

Bits(sys, 'bits', a, bits)
Minterm(sys, 'minterm', bits, 5, minterm)
Constant(sys, "a", 0x5, a)

for i in range(len(bits)):
    Scope(sys, 'b{}'.format(i), bits[i])

Scope(sys, 'minterm_5', minterm)

py4hw.debug.printHierarchy(sys)

print('RESET')
sim = Simulator(sys)

print()
print('CLK')
sim.clk(1)

print()
print('SYSTEM VALUES')
py4hw.debug.printHierarchyWithValues(sys)