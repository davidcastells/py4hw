# -*- coding: utf-8 -*-
"""
Created on Thu Oct 29 17:06:41 2020

@author: dcr
"""

from py4hw.base import *
from py4hw.logic import *
from py4hw.logic.storage import *
import py4hw.debug


sys = HWSystem()

a = sys.wire("a", 3)
r = sys.wire("r", 3)
p = sys.wire("p", 3)


Add(sys, "add", a,p, r)
Reg(sys, "reg", r, p)

Constant(sys, "a", 1, a)
#Scope(sys, "a", a)
Scope(sys, "p", p)
#Scope(sys, "r", r)


py4hw.debug.printHierarchy(sys)

print('RESET')
sim = sys.getSimulator()

print()
print('CLK')
sim.clk(20)