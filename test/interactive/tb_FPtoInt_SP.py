# -*- coding: utf-8 -*-
"""
Created on Sat Aug 13 10:06:08 2022

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
p_lost = hw.wire('p_lost')
denorm = hw.wire('denorm')
invalid = hw.wire('invalid')

av = -2003144064.0

a = g.hw_constant(32, fp.sp_to_ieee754(av))


fpa = py4hw.FPtoInt_SP(hw, 'fpa', a, r, p_lost, denorm, invalid)

print('Expecting', hex(int(av) & ((1<<32)-1)))

hw.getSimulator().clk()


py4hw.gui.Workbench(hw)