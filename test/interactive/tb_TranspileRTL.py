# -*- coding: utf-8 -*-
"""
Created on Sun Apr  2 14:18:11 2023

@author: dcr
"""
import sys
sys.path.append('../..')

import py4hw
import py4hw.transpilation.python2verilog_transpilation as py2v
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
    module = py2v.getMethod(dut, 'clock')
    node = py2v.getBody(module)
    
    node = py2v.ReplaceIf().visit(node)        
    node = py2v.ReplaceWireGets().visit(node)
    node = py2v.ReplaceWirePrepare().visit(node)
    node = py2v.ReplaceExpr().visit(node)
    node = py2v.ReplaceBinOp().visit(node)
    node = py2v.ReplaceAttribute().visit(node)
    node = py2v.ReplaceConstant().visit(node)
    node = py2v.ReplaceAssign().visit(node)
    
    #xml = ast2xml.visit_node(node, ast_name='body')
    xml = ast2xml.visit_node(node)
    
    with open('c:\\temp\\test.xml', 'wb') as f:
        f.write(ast2xml.renderXml(xml))

if (True):    
    rtl = py2v.Python2VerilogTranspiler(dut, 'clock')
    str = rtl.transpileRTL()
    
    print('transpilation of clock method')
    print(str)

rtl = py4hw.rtl_generation.VerilogGenerator(dut)
str = rtl.getVerilog()

print(str)
