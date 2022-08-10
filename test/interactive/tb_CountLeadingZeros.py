# -*- coding: utf-8 -*-
"""
Created on Tue Aug  9 11:22:45 2022

@author: dcr
"""

from py4hw.base import *
from py4hw.logic import *
from py4hw.logic.storage import *
import py4hw.debug


sys = py4hw.HWSystem()
g = py4hw.LogicHelper(sys)

r = sys.wire('r', 8)
z = sys.wire('z')

a = g.hw_constant(8, 5)


py4hw.CountLeadingZeros(sys, 'clz', a, r, z)

py4hw.gui.Workbench(sys)