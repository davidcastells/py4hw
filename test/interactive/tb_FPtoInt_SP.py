# -*- coding: utf-8 -*-
"""
Created on Sat Aug 13 10:06:08 2022

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
p_lost = sys.wire('p_lost')
denorm = sys.wire('denorm')
invalid = sys.wire('invalid')

av = 0.4413984417915344

a = g.hw_constant(32, fp.sp_to_ieee754(av))


fpa = py4hw.FPtoInt_SP(sys, 'fpa', a, r, p_lost, denorm, invalid)

py4hw.gui.Workbench(sys)