# -*- coding: utf-8 -*-
"""
Created on Wed Jul 29 09:08:37 2026

@author: dcr
"""

import py4hw
from edalize import edatool
import os


class Pynq_Z2(py4hw.HWSystem):
    def __init__(self):
        super().__init__(name='Pynq-Z2')
        
        clk125 = self.wire('sysclk')
        
        clockDriver = py4hw.ClockDriver('sysclk', 125E6, 0, wire=clk125)
        
        self.clockDriver = clockDriver