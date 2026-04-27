# -*- coding: utf-8 -*-
"""
Created on Mon Apr 27 19:41:02 2026

@author: 2016570
"""
import py4hw

hw = py4hw.HWSystem()

ins = hw.wires('wi', 3, 8)

py4hw.Constant(hw, 'i0', 3, ins[0])
py4hw.Constant(hw, 'i1', 7, ins[1])
py4hw.Constant(hw, 'i2', 3, ins[2])

r = hw.wire('r', 1)

py4hw.AnyEqual(hw, 'any', ins, r)

py4hw.gui.Workbench(hw)