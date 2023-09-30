# -*- coding: utf-8 -*-
"""
Created on Fri Sep 29 23:38:52 2023

@author: dcr
"""

import py4hw

import py4hw.external.platforms as plt

sys = plt.DE1SoC()

inc = sys.wire('inc')
reset = sys.wire('reset')

count = sys.wire('count', 8)
carryout = sys.wire('carryout')

key = sys.getInputKey()

py4hw.Bit(sys, 'reset', key, 0, reset)
py4hw.Bit(sys, 'inc', key, 1, inc)

sys.addOut('count', count)

#py4hw.Constant(sys, 'inc', 1, inc)
#py4hw.Constant(sys, 'reset', 0, reset)
py4hw.ModuloCounter(sys, 'cout', 17, reset, inc, count, carryout)

py4hw.gui.Workbench(sys)

dir = '/tmp/testDE1SoC'
sys.build(dir)
sys.download(dir)