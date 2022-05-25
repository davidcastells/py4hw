# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 14:25:01 2022

@author: dcr
"""
from py4hw.base import *
from py4hw.logic import *
from py4hw.simulation import Simulator
import py4hw.debug


sys = HWSystem()

a = sys.wire("a", 2)

r = sys.wires("r", 4, 1)

Constant(sys, "a", 1, a)

Decoder(sys, 'dec', a, r)

print('RESET')
sim = sys.getSimulator()

print()
print('CLK')
sim.clk(1)

print()
print('SYSTEM VALUES')
py4hw.debug.printHierarchyWithValues(sys)