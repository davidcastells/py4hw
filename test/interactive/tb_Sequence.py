# -*- coding: utf-8 -*-
"""
Created on Mon Jan 12 12:04:13 2026

@author: 2016570
"""

import py4hw

import numpy as np



# Generate random integers between 2500 and 4500 (3500 ± 1000)
rx_values = np.random.randint(low=2500, high=4501, size=10)

hw = py4hw.HWSystem()

rx = hw.wire('rx', 16)
py4hw.Sequence(hw, 'seq', rx_values, rx)
py4hw.

for _ in range(10):
    hw.getSimulator().clk(1)
    print('rx=', rx.get())

