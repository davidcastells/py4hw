# -*- coding: utf-8 -*-
"""
Created on Mon Aug  8 09:35:29 2022

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

av = -4.2
bv = 3.5
a = g.hw_constant(32, fp.sp_to_ieee754(av))
b = g.hw_constant(32, fp.sp_to_ieee754(bv))
gt = sys.wire('gt')
eq= sys.wire('eq')
lt = sys.wire('lt')

py4hw.FPComparator_SP(sys, 'cmp', a, b, gt, eq, lt)


py4hw.gui.Workbench(sys)