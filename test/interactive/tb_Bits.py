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

BitsLSBF(sys, 'bits', a, bits)

Constant(sys, "a", 0x5, a)

for i in range(len(bits)):
    Scope(sys, 'b{}'.format(i), bits[i])

py4hw.debug.printHierarchy(sys)

print('RESET')
sim = Simulator(sys)

print()
print('CLK')
sim.clk(1)