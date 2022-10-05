# -*- coding: utf-8 -*-
"""
Created on Fri Sep 30 19:03:48 2022

@author: dcr
"""
from py4hw.base import *
from py4hw.logic import *
from py4hw.logic.storage import *
import py4hw.debug


sys = py4hw.HWSystem()

a = sys.wire("a", 4)
b = sys.wire("b", 4)
r = sys.wire("r", 4)

py4hw.Constant(sys, "a", -7, a)
py4hw.Constant(sys, "b", -3, b)

py4hw.SignedDiv(sys, 'equal', a, b, r)

py4hw.gui.Workbench(sys)