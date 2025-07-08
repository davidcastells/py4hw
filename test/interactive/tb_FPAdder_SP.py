# -*- coding: utf-8 -*-
"""
Created on Fri Aug  5 09:44:49 2022

@author: dcr
"""

from py4hw.base import *
from py4hw.logic import *
from py4hw.logic.storage import *
import py4hw.debug


sys = py4hw.HWSystem()
g = py4hw.LogicHelper(sys)
fp = py4hw.FloatingPointHelper()

r = sys.wire('r', 32)

av = 1.2
bv = 0.0000002


a = g.hw_constant(32, fp.sp_to_ieee754(av))
b = g.hw_constant(32, fp.sp_to_ieee754(bv))


fpa = py4hw.FPAdder_SP(sys, 'fpa', a, b, r)

py4hw.gui.Workbench(sys)