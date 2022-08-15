# -*- coding: utf-8 -*-
"""
Created on Sun Aug 14 19:41:10 2022

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

av = 97326422.09006774 
bv = -84196012.54553068

a = g.hw_constant(32, fp.sp_to_ieee754(av))
b = g.hw_constant(32, fp.sp_to_ieee754(bv))


fpa = py4hw.FPMult_SP(sys, 'fpa', a, b, r)

fp = FloatingPointHelper()
print('Expected result: ', av*bv, '{:08X}'.format(fp.sp_to_ieee754(av*bv)))
py4hw.gui.Workbench(sys)