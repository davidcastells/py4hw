# -*- coding: utf-8 -*-
"""
Created on Thu Oct 29 17:06:41 2020

@author: dcr
"""

from py4hw.base import *
from py4hw.logic import *
from py4hw.storage import *
from py4hw.simulation import Simulator
import py4hw.debug


sys = HWSystem()

a = sys.wire("a", 3)
r = sys.wire("r", 3)
p = sys.wire("p", 3)

vcc = sys.wire('one', 1)
Constant(sys, 'one', 1, vcc)

Add(sys, "add", a,p, r)
Reg(sys, "reg", r, vcc, p)

Constant(sys, "a", 1, a)
#Scope(sys, "a", a)
Scope(sys, "p", p)
#Scope(sys, "r", r)


py4hw.debug.printHierarchy(sys)

print('RESET')
sim = Simulator(sys)

print()
print('CLK')
sim.clk(20)