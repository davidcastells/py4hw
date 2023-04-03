# -*- coding: utf-8 -*-
"""
Created on Sun Apr  2 14:18:11 2023

@author: dcr
"""
from py4hw.base import *
from py4hw.logic import *
from py4hw.logic.storage import *
import py4hw.debug
import inspect
import textwrap
import ast
import py4hw.transpilation.ast2xml as ast2xml
import py4hw.transpilation.python2verilog_transpilation as py2v
import webbrowser

class TestCircuit(Logic):
    def __init__(self, parent, name, a, r):
        super().__init__(parent, name)
        
        self.a = self.addIn('a', a)
        self.r = self.addOut('r', r)
        
    def clock(self):
        self.r.prepare(self.r.get() + self.a.get())
        
        
hw = HWSystem()
a = hw.wire('a', 8)
r = hw.wire('r', 8)

Sequence(hw, 'seq', [1,2,3], a)
dut = TestCircuit(hw, 'test', a, r)

if (True):
    # Low level tests
    module = py2v.getMethod(dut, 'clock')
    node = py2v.getBody(module)
    
    node = py2v.ReplaceWireGets().visit(node)
    node = py2v.ReplaceWirePrepare().visit(node)
    
    #xml = ast2xml.visit_node(node, ast_name='body')
    xml = ast2xml.visit_node(node)
    
    with open('c:\\temp\\test.xml', 'wb') as f:
        f.write(ast2xml.renderXml(xml))
    
rtl = py2v.Python2VerilogTranspiler(dut, 'clock')
str = rtl.transpile()

print(str)