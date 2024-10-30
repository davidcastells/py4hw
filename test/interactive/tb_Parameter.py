# -*- coding: utf-8 -*-
"""
Created on Wed Oct 30 06:25:01 2024

@author: dcastel1
"""

import py4hw

sys = py4hw.HWSystem()

a = sys.wire("a", 32)
load = sys.wire("load")
r = sys.wire("r", 32)


class ParamReg(py4hw.Logic):
    def __init__(self, parent, name, a, load, r, init_value):
        super().__init__(parent, name)
        
        self.a = self.addIn('a', a)
        self.load = self.addIn('load', load)
        self.r = self.addOut('r', r)
        
        self.init_value = self.addParameter('INIT', init_value)
        
    def init(self):
        self.r.prepare(self.getParameterValue('INIT'))
        
    def structureName(self):
        return 'ParamReg_{}'.format(self.r.getWidth())
    
    def clock(self):
        if (self.load.get()):
            self.r.prepare(self.a.get())
            
class Test(py4hw.Logic):

    def __init__(self, parent, name, a, load, r):
        super().__init__(parent, name)
        
        self.addIn('a', a)
        self.addIn('load', load)
        self.addOut('r', r)
        
        r1 = self.wire('r1', r.getWidth())
        r2 = self.wire('r2', r.getWidth())
        
        ParamReg(self, 'p1', a, load, r1, 5)
        ParamReg(self, 'p2', a, load, r2, 3)
        
        py4hw.Add(self, 'add', r1, r2, r)


dut = Test(sys, 'test', a,  load, r)

rtl = py4hw.VerilogGenerator(dut)
print(rtl.getVerilogForHierarchy())