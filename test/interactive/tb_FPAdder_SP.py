# -*- coding: utf-8 -*-
"""
Created on Fri Aug  5 09:44:49 2022

@author: dcr
"""

from py4hw.base import *
from py4hw.logic import *
from py4hw.logic.storage import *
import py4hw.debug


hw = py4hw.HWSystem()
g = py4hw.LogicHelper(hw)
fp = py4hw.FloatingPointHelper()

r = hw.wire('r', 32)

if (False):
    av = 3.75
    bv = 0.0000

    a = g.hw_constant(32, fp.sp_to_ieee754(av))
    b = g.hw_constant(32, fp.sp_to_ieee754(bv))

else:
    a = g.hw_constant(32, 0x4B123456) 
    b = g.hw_constant(32, 0xCA654321)

fpa = py4hw.FPAdder_SP(hw, 'fpa', a, b, r)

hw.getSimulator().clk(1)

py4hw.gui.Workbench(hw)