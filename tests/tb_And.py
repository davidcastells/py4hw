# -*- coding: utf-8 -*-
"""
Created on Sat Oct 31 11:07:23 2020

@author: dcr
"""
from py4hw.base import *
from py4hw.logic import *
from py4hw.simulation import Simulator
import py4hw.debug

sys = HWSystem()

a = sys.wire("a", 32)
b = sys.wire("b", 32)
c = sys.wire("c", 32)
r1 = sys.wire("r1", 32)
r2 = sys.wire("r2", 32)
r3 = sys.wire("r3", 32)

And(sys, "and1", a, b, r1)
And(sys, "and2", a, c, r2)
And(sys, "and3", b, c, r3)

Constant(sys, "a", 0xF, a)
Constant(sys, "b", 0xA, b)
Constant(sys, "c", 0x5, c)

Scope(sys, "r1 (0xF & 0xA)", r1)
Scope(sys, "r2 (0xF & 0x5)", r2)
Scope(sys, "r3 (0xA & 0x5)", r3)

py4hw.debug.printHierarchy(sys)

print('RESET')
sim = Simulator(sys)

print()
print('CLK')
sim.clk(1)