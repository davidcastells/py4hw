# -*- coding: utf-8 -*-
"""
Created on Sat Jan 22 11:16:16 2022

@author: dcr
"""

import py4hw
import py4hw.debug
import pytest

class CounterBehavioural(py4hw.Logic):
    def __init__(self, parent, name, inc, q):
        super().__init__(parent, name)
    
        self.inc = self.addIn('inc', inc)
        self.q = self.addOut('q', q)
        
        
    def clock(self):
        if (self.inc.get() == 1):
            self.q.prepare(self.q.get()+1)
            
class SelectType(py4hw.Logic):
    def __init__(self, parent, name, opcode, imm_typ):
        super().__init__(parent, name)

        assert(opcode.getWidth() == 7)
        
        self.opcode = self.addIn ('opcode',  opcode)
        self.imm_type = self.addOut('imm_typ', imm_typ)

    def propagate(self):
        a = (self.opcode.get() >> 4)  & ((1<<3)-1);
        b = (self.opcode.get() )  & ((1<<4)-1);

        if (a == 0): self.imm_type.put(0) # I Type
        elif (a == 1): 
            if (b == 3): self.imm_type.put(0) # I Type
            else: self.imm_type.put(3)
        elif (a == 2):
            self.imm_type.put(1)
        elif (a == 3):
            self.imm_type.put(3)
        elif (a == 6):
            if (b == 3): self.imm_type.put(2)
            elif (b==7): self.imm_type.put(0)
            elif (b==0xF): self.imm_type.put(4)
            else: self.imm_type.put(7)                

            
            
class Test_RtlGeneration:
    
    def test_structural_verilog_1(self):
        sys = py4hw.HWSystem()
        
        reset = sys.wire('reset',1)
        inc = sys.wire('inc',1)
        count = sys.wire('count', 8)
        carry = sys.wire('carry', 1)
        
        py4hw.Constant(sys, 'reset', 0, reset)
        py4hw.Constant(sys, 'inc', 1, inc)

        counter = py4hw.ModuloCounter(sys, 'counter', 3, reset, inc, count, carry)
    
        rtlgen = py4hw.VerilogGenerator(counter)
        print(rtlgen.getVerilog())
        
    def test_structural_verilog_2(self):
        sys = py4hw.HWSystem()
        
        reset = sys.wire('reset',1)
        a= sys.wire('a', 8)
        b= sys.wire('b', 8)
        c= sys.wire('c', 8)
        
        py4hw.Constant(sys, 'reset', 0, reset)
        py4hw.Constant(sys, 'a', 10, a)
        py4hw.Constant(sys, 'b', 3, b)

        dut = py4hw.Div(sys, 'div', a, b, c)
    
        
        rtlgen = py4hw.VerilogGenerator(sys)
        
        assert(rtlgen.isInlinable(dut))
        
        #print(rtlgen.inlinePrimitive(dut))
        
        print(rtlgen.getVerilogForHierarchy())
        
    def test_structural_verilog_3(self):
        sys = py4hw.HWSystem()
        
        reset = sys.wire('reset',1)
        inc = sys.wire('inc',1)
        count = sys.wire('count', 8)
        carry = sys.wire('carry', 1)
        
        py4hw.Constant(sys, 'reset', 0, reset)
        py4hw.Constant(sys, 'inc', 1, inc)

        counter = py4hw.ModuloCounter(sys, 'counter', 3, reset, inc, count, carry)
    
        err_wire = None # sys.wire('error')
        
        #manipulate a ports wire to introduce an error
        counter.children['reg'].inPorts[0].wire = err_wire
        
        try:
            rtlgen = py4hw.VerilogGenerator(sys)
            print(rtlgen.getVerilogForHierarchy())
        except Exception:
            # thats the expected result
            return
    
        pytest.fail('Exception not thrown')
        
        
    def test_structural_verilog_4(self):
        sys = py4hw.HWSystem()
        
        reset = sys.wire('reset',1)
        inc = sys.wire('inc',1)
        count = sys.wire('count', 8)
        carry = sys.wire('carry', 1)
        
        py4hw.Constant(sys, 'reset', 0, reset)
        py4hw.Constant(sys, 'inc', 1, inc)

        counter = py4hw.ModuloCounter(sys, 'counter', 3, reset, inc, count, carry)
    
        err_wire = None # sys.wire('error')
        
        #manipulate a ports wire to introduce an error
        counter.children['reg'].outPorts[0].wire = err_wire
        
        try:
            rtlgen = py4hw.VerilogGenerator(sys)
            print(rtlgen.getVerilogForHierarchy())
        except Exception:
            # thats the expected result
            return
    
        pytest.fail('Exception not thrown')
        
    def test_SignExtend(self):
        sys = py4hw.HWSystem()
        
        a = sys.wire('a', 8)
        sa = sys.wire('sa', 16)
        py4hw.Constant(sys, 'a', 0xFF, a)
        block = py4hw.SignExtend(sys, 'sa', a, sa)
        
        rtlgen = py4hw.VerilogGenerator(sys)
        print(rtlgen.getVerilogForHierarchy())

    def test_behavioural_Counter(self):
        sys = py4hw.HWSystem()
        
        q = sys.wire('q', 32)
        inc = sys.wire('inc')
        py4hw.Constant(sys, 'inc', 1, inc)
        dut = CounterBehavioural(sys, 'counter', inc, q)
        
        rtlgen = py4hw.VerilogGenerator(sys)
        print(rtlgen.getVerilogForHierarchy(dut))
        
    
    def test_behavioural_SelectType(self):
        sys = py4hw.HWSystem()
        
        q = sys.wire('q', 3)
        op = sys.wire('op', 7)
        
        
        dut = SelectType(sys, 'select', op, q)
        
        rtlgen = py4hw.VerilogGenerator(sys)
        print(rtlgen.getVerilogForHierarchy(dut))
        
    
        
if __name__ == '__main__':
    pytest.main(args=['-s', '-q', 'Test_RtlGeneration.py'])