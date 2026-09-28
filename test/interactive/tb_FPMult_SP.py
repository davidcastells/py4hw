# -*- coding: utf-8 -*-
"""
Created on Sun Aug 14 19:41:10 2022

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

#av = 97326422.09006774 
#bv = -84196012.54553068

av = 9.5
bv = -3.2

a = g.hw_constant(32, fp.sp_to_ieee754(av))
b = g.hw_constant(32, fp.sp_to_ieee754(bv))


fpa = py4hw.FPMult_SP(hw, 'fpa', a, b, r)

hw.getSimulator().clk()

fp = py4hw.helper.FloatingPointHelper()
print('Expected result: ', av*bv, '{:08X}'.format(fp.sp_to_ieee754(av*bv)))
print('Result         : ', fp.ieee754_to_sp(r.get()), '{:08X}'.format(r.get()))

py4hw.gui.Workbench(hw)