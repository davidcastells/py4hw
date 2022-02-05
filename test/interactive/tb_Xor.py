# -*- coding: utf-8 -*-
from py4hw.base import *
from py4hw.logic import *
import py4hw.debug
import py4hw.gui
import py4hw.schematic

sys = HWSystem()

a = sys.wire("a", 8)
b = sys.wire("b", 8)
r = sys.wire("r", 8)

Xor2(sys, "xor", a, b, r)

Constant(sys, "a", 0b10011100, a)
Constant(sys, "b", 0b00110100, b)
Scope(sys, "r", r)

py4hw.debug.printHierarchyWithValues(sys)

print('RESET')
sim = sys.getSimulator()

print()
print('CLK')
sim.clk(1)
