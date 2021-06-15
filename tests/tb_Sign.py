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

a = sys.wire("a", 32)
b = sys.wire("b", 32)
c = sys.wire("c", 32)
r1 = sys.wire("r1")
r2 = sys.wire("r2")
r3 = sys.wire("r3")

Constant(sys, "a", -10, a)
Constant(sys, "b", 0, b)
Constant(sys, "b", 10, c)

Sign(sys, "signTest1", a, r1)
Sign(sys, "signTest2", b, r2)
Sign(sys, "signTest2", c, r3)

Scope(sys, "r1", r1)
Scope(sys, "r2", r2)
Scope(sys, "r3", r3)

print('RESET')
sim = Simulator(sys)

print()
print('CLK')
sim.clk(1)