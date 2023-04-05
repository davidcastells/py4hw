# -*- coding: utf-8 -*-
"""
Created on Tue Apr  4 19:50:05 2023

@author: dcastel1
"""

# -*- coding: utf-8 -*-
"""
Created on Sun Apr  2 14:18:11 2023

@author: dcr
"""
import sys
sys.path.append('../..')

import py4hw
import py4hw.transpilation.python2structural as py2s
import py4hw.transpilation.ast2xml as ast2xml
import inspect
import textwrap
import ast
import webbrowser

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
        
hw = py4hw.HWSystem()
a = hw.wire('a', 8)
r = hw.wire('r', 8)

py4hw.Sequence(hw, 'seq', [1,2,3], a)
dut = TestCircuit(hw, 'test', a, r)
#dut = FSM(hw, 'test', a, r)

if (True):
    # Low level tests
    module = py2s.getMethod(dut, 'clock')
    
    node = py2s.ReplaceBasic1().visit(module)        
    node = py2s.ReplaceBasic2().visit(node)        
     
    #xml = ast2xml.visit_node(node, ast_name='body')
    xml = ast2xml.visit_node(node)
    
    with open('c:\\temp\\test.xml', 'wb') as f:
        f.write(ast2xml.renderXml(xml))
        
    

if (True):    
    hls = py2s.Python2Structural(dut, 'clock')
    dut2 = hls.generateStructural('dut2')

    sch = py4hw.Schematic(dut2)
    sch.draw()    
    
    watch = []
    watch.extend(dut.outPorts)
    watch.extend(dut2.outPorts)
    
    print(watch)
    
    wvf = py4hw.Waveform(hw, 'wvf', watch)
    
    hw.getSimulator().clk(15)
    
    wvf.draw()

if (False):
    rtl = py4hw.rtl_generation.VerilogGenerator(dut)
    str = rtl.getVerilog()
    
    print(str)
