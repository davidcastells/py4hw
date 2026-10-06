# -*- coding: utf-8 -*-
"""
Created on Tue Sep 29 10:38:50 2026

@author: dcr
"""

import py4hw
import py4hw.external.drawio as drawio


hw = py4hw.HWSystem()

a = hw.wire('a', 32)
b = hw.wire('b', 32)
r = hw.wire('r', 32)

dut = py4hw.FPAdder_SP(hw, 'fpa', a, b, r)



newfile = py4hw.helper.FileSystem.createTempFile(suffix='.drawio')
newfile = str(newfile) # convert path to string

print('Created new file:', newfile)

drawer = drawio.DrawIoDiagramGenerator()
drawer.generate(dut, newfile)

