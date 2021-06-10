# -*- coding: utf-8 -*-
from py4hw.base import *
from py4hw.logic import *
import py4hw.debug
import py4hw.gui
import py4hw.schematic

sys = HWSystem()

a = sys.wire("a", 32)
b = sys.wire("b", 32)
c = sys.wire("c", 32)
r1 = sys.wire("r", 32)
r2 = sys.wire("r2", 32)

Mul(sys, "mul1", a,b, r1)
Mul(sys, "mul2", r1, c, r2)

Constant(sys, "a", 5, a)
Constant(sys, "b", 2, b)
Constant(sys, "c", 6, c)
Scope(sys, "r2", r2)

py4hw.debug.printHierarchyWithValues(sys)

print('RESET')
sim = sys.getSimulator()

print()
print('CLK')
sim.clk(1)



