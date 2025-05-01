# -*- coding: utf-8 -*-
"""
Created on Fri Dec 22 09:49:06 2023

@author: dcr
"""
from py4hw.base import *
from py4hw.logic import *
from py4hw.logic.storage import *
import py4hw.debug

class AndWrapper(Logic):
    def __init__(self, parent, name, a, b, r):
        super().__init__(parent, name)
        
        self.a = self.addIn('a', a)
        self.b = self.addIn('b', b)
        self.r = self.addOut('r', r)
        
        And2(self, 'and', a, b, r)
        
    def structureName(self):
        if ((self.a.getWidth() == self.r.getWidth()) and (self.b.getWidth() == self.r.getWidth())):
            return 'AndWrapper_{}'.format(self.r.getWidth())
        else:
            return 'AndWrapper_{}_{}_{}'.format(a.getWidth(), b.getWidth(), r.getWidth())
              
        
sys = HWSystem()

a = Wire(sys, "a", 4)
b = Wire(sys, "b", 4)
c = Wire(sys, "c", 4)
d = Wire(sys, "d", 4)

r1 = Wire(sys, "r1", 4)
r2 = Wire(sys, "r2", 4)
r3 = Wire(sys, "r3", 4)

Constant(sys, 'a', 3, a)
Constant(sys, 'b', 2, b)
Constant(sys, 'c', 2, c)

AndWrapper(sys, 'and1', a, b, r1)
AndWrapper(sys, 'and2', b, c, r2)
AndWrapper(sys, 'and3', c, d, r3)

#py4hw.gui.Workbench(sys)

rtlgen = py4hw.VerilogGenerator(sys)
print('First time', id(rtlgen))

rtl = rtlgen.getVerilogForHierarchy()

print(rtl)



rtlgen = py4hw.VerilogGenerator(sys)
print('Second time', id(rtlgen))

rtl = rtlgen.getVerilogForHierarchy()

print(rtl)

