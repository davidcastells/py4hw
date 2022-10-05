# -*- coding: utf-8 -*-
"""
Created on Thu Oct 29 17:06:41 2020

@author: dcr
"""

from py4hw.base import *
from py4hw.logic import *
from py4hw.logic.storage import *
import py4hw.debug

class SAdd(Logic):
    def __init__(self, parent, instanceName, a , r):
        super().__init__(parent, instanceName)
        self.a = self.addIn('a', a)
        self.r = self.addOut('r', r)
        self.r.put(0)
        
    def clock(self):
        self.r.prepare(self.r.get() + self.a.get())

        
sys = HWSystem()

a = sys.wire("a", 3)
r = sys.wire("r", 3)


SAdd(sys, "add", a, r)

Constant(sys, "a", 1, a)


py4hw.gui.Workbench(sys)