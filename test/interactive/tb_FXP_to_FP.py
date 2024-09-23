# -*- coding: utf-8 -*-
"""
Created on Sun Jun 16 12:55:21 2024

@author: dcastel1
"""

import py4hw

from py4hw.helper import FixedPoint
from py4hw.helper import FPNum
from py4hw.logic.arithmetic_fp import FixedPointtoFP_SP

ka = FixedPoint(1, 8, 8, 1.5)

hw = py4hw.HWSystem()

a = ka.createConstant(hw, 'a')

r = hw.wire('r', 32)
p_lost = hw.wire('p_lost')

FixedPointtoFP_SP(hw, 'fxp2fp', a, ka.getWidths(), r, p_lost)

hw.getSimulator().clk()
print()
print('a=', hex(a.get()), ka.dump(), 'width=', a.getWidth())

rv = FPNum(r.get(), 'sp')
print('r=', hex(r.get()), rv.to_float())        

e = FPNum(1.5)
print('e=', hex(e.convert('sp')), e.components())
py4hw.gui.Workbench(hw)
