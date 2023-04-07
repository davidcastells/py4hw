# -*- coding: utf-8 -*-
"""
Created on Fri Apr  7 10:03:22 2023

Copyright (C) 2023 Victor Suarez Rovere <suarezvictor@gmail.com>
Copyright (C) 2023 dcr

"""

import py4hw
import py4hw.code_generation

class FullAdder(py4hw.Logic):
    
    def __init__(self, parent, name, x, y, ci, s, co):
        super().__init__(parent, name)
        
        self.x = self.addIn('x', x)
        self.y = self.addIn('y', y)
        self.ci = self.addIn('ci', ci)
        self.s = self.addOut('s', s)
        self.co = self.addOut('co', co)

    def propagate(self):
        self.s.put((self.x.get() ^ self.y.get()) ^ self.ci.get())
        self.co.put((self.x.get() & self.y.get()) | ( (self.x.get() ^ self.y.get())  & self.ci.get()))
        
class TestCircuit(py4hw.Logic):
    def __init__(self, parent, name, a, r):
        super().__init__(parent, name)
        
        self.a = self.addIn('a', a)
        self.r = self.addOut('r', r)
        
    def clock(self):
        self.r.prepare(self.r.get() + self.a.get())
        
    
class FSM(py4hw.Logic):
    def __init__(self, parent, name, a, r):
        super().__init__(parent, name)
        
        self.a = self.addIn('a', a)
        self.r = self.addOut('r', r)
        
        self.state = 0
        self.count = 0
        
    def clock(self):
        
        if (self.state == 0):
            if (self.a.get() == 1):
                # 1 detected
                self.state = 1
                self.r.prepare(self.count)
            else:
                self.count += 1
                self.r.prepare(0)

        elif (self.state == 1):
            if (self.a.get() == 1):
                self.state = 0
                self.count = 0
            else:
                self.count += 1
                self.r.prepare(10+self.count)

if (True):
    # Test circuit
    hw = py4hw.HWSystem()
    a = hw.wire('a', 8)
    r = hw.wire('r', 8)
    
    py4hw.Sequence(hw, 'seq', [1,2,3], a)
    dut = TestCircuit(hw, 'test', a, r)
    #dut = FSM(hw, 'test', a, r)


if (True):
    rtl = py4hw.code_generation.CflexHDLGenerator(dut)
    str = rtl.getVerilog()
    
    print(str)
