# -*- coding: utf-8 -*-
"""
Created on Sat Jan 22 11:16:16 2022

@author: dcr
"""

import py4hw
import py4hw.debug
import pytest


class Test_RtlGeneration:
    
    def test_1(self):
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
        
    def test_2(self):
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
        
    def test_3(self):
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
        
        
    def test_4(self):
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
        
if __name__ == '__main__':
    pytest.main(args=['-s', '-q', 'Test_RtlGeneration.py'])