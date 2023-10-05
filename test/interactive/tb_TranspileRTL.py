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
import os

def getTempDir():
    if ('Linux' in os.uname()):
        return '/tmp/'
    else:
        return 'c:\\Temp\\'
    
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
        '''
        This is a doc
        '''
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

class VGATestPattern(py4hw.Logic):
    
    def __init__(self, parent, name, reset, hactive, vactive, r, g, b):
        super().__init__(parent, name)
        
        self.reset = self.addIn('reset', reset)
        self.hactive = self.addOut('hactive', hactive)
        self.vactive = self.addOut('vactive', vactive)
        self.r = self.addOut('r', r)
        self.g = self.addOut('g', g)
        self.b = self.addOut('b', b)
        self.x = 0
        self.y = 0
        
    def clock(self):
        
        divx = self.x // 80
        vr = ((divx >> 0) & 1) * 0xFF
        vg = ((divx >> 1) & 1) * 0xFF
        vb = ((divx >> 2) & 1) * 0xFF       

        self.r.prepare(vr)
        self.g.prepare(vg)
        self.b.prepare(vb)
        self.vactive.prepare(1 if self.y < 480 else 0)
        self.hactive.prepare(1 if self.x < 640 else 0)
        
        self.x += 1
        if (self.x >= 840):
            self.x = 0
            self.y += 1
            if (self.y >= 520):
                self.y = 0

if (True):
    # Test circuit
    hw = py4hw.HWSystem()
    a = hw.wire('a', 8)
    r = hw.wire('r', 8)
    
    py4hw.Sequence(hw, 'seq', [1,2,3], a)
    dut = TestCircuit(hw, 'test', a, r)
    #dut = FSM(hw, 'test', a, r)

if (False):
    # Test circuit
    hw = py4hw.HWSystem()
    ha = hw.wire('ha')
    va = hw.wire('va')
    r = hw.wire('r',8)
    g = hw.wire('g',8)
    b = hw.wire('b',8)
    
    reset = hw.wire('reset')
    py4hw.Constant(hw, 'reset', 0, reset)
    
    dut = VGATestPattern(hw, 'vga', reset, ha, va, r, g, b)
    #dut = FSM(hw, 'test', a, r)

if (False):
    hw = py4hw.HWSystem()
    x = hw.wire('x')
    y = hw.wire('y')
    ci = hw.wire('ci')
    s = hw.wire('s')
    co = hw.wire('co')
    
    py4hw.Sequence(hw, 'x', [0,1], x)
    py4hw.Sequence(hw, 'y', [0,0,1,1], y)
    py4hw.Sequence(hw, 'ci', [0,0,0,0,1,1,1,1], ci)
    dut = FullAdder(hw, 'test', x, y, ci, s, co)
    
if (True):
    module = py2v.getMethod(dut, '__init__')
    node = py2v.getBody(module, '*')
    
    node = py2v.ExtractInitializers().visit(node)        

    xml = ast2xml.visit_node(node)
    
    with open(getTempDir()+'init.xml', 'wb') as f:
        f.write(ast2xml.renderXml(xml))

if (True):
    # Low level tests
    module = py2v.getMethod(dut, 'clock')
    node = py2v.getBody(module, '*')
    
    # Save the AST before translation
    xml = ast2xml.visit_node(node)
    with open(getTempDir()+'clock_pre.xml', 'wb') as f:
        f.write(ast2xml.renderXml(xml))
    
    node = py2v.ReplaceIf().visit(node)        
    node = py2v.ReplaceWireCalls().visit(node)
    node = py2v.ReplaceExpr().visit(node)
    node = py2v.ReplaceOperators().visit(node)
    ports = {'r':py2v.VerilogWire('r'), 'g':py2v.VerilogWire('g')}
    variables = {'x':py2v.VerilogVariable('x', 'int'), 'y':py2v.VerilogVariable('y', 'int')}
    node = py2v.ReplaceWiresAndVariables(ports, variables).visit(node)
    node = py2v.ReplaceConstant().visit(node)
    node = py2v.ReplaceAssign().visit(node)
    node = py2v.ReplaceIfExp().visit(node)
    node = py2v.ReplaceDocStrings().visit(node)
    
    #node = py2v.FlattenOperators().loop_visit(node)
    
    #xml = ast2xml.visit_node(node, ast_name='body')
    xml = ast2xml.visit_node(node)
    
    with open(getTempDir()+'clock.xml', 'wb') as f:
        f.write(ast2xml.renderXml(xml))

if (False):    
    rtl = py2v.Python2VerilogTranspiler(dut)
    node = rtl.transpileSequential()
    str = rtl.toVerilog(node)
    
    print('transpilation of clock method')
    print(str)

if (False):    
    rtl = py2v.Python2VerilogTranspiler(dut, 'propagate')
    str = rtl.transpileRTL()
    
    print('transpilation of propagate method')
    print(str)

if (True):
    rtl = py4hw.rtl_generation.VerilogGenerator(dut)
    str = rtl.getVerilog()
    
    print(str)
