# -*- coding: utf-8 -*-
"""
Created on Mon Aug 15 19:42:15 2022

@author: dcr
"""

from py4hw.base import *
from py4hw.logic import *
import py4hw.debug
import py4hw.gui
import py4hw.schematic

sys = HWSystem()

a = sys.wire("a", 32)
b = sys.wire("b", 32)
c = sys.wire("c", 32)
d = sys.wire("r", 32)
e = sys.wire("r2", 32)

Constant(sys, "a", 5, a)
Constant(sys, "b", 2, b)
Constant(sys, "c", 6, c)
Constant(sys, "d", 5, d)
Constant(sys, "e", 7, e)

g = py4hw.LogicHelper(sys)

r2 = g.hw_and2(a, b)
r3 = g.hw_and([c,d,e])

Scope(sys, "r2", r2)
Scope(sys, "r3", r3)

py4hw.gui.Workbench(sys)
