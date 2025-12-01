# -*- coding: utf-8 -*-
"""
Created on Fri Mar 10 15:29:57 2023

@author: dcr
"""


import py4hw
import py4hw.debug
import pytest


class Test_Abs:
    
    def test_pos(self):
        sys = py4hw.HWSystem()
        w = 32
        r = sys.wire("a", w)
        
        v = 0x22
        
        py4hw.Constant(sys, "abs", v, r)

        sys.getSimulator().clk(1)
        
        assert(r.get() == v & ((1<<w)-1))
            
        
    def test_neg(self):
        sys = py4hw.HWSystem()
        
        w = 32
        r = sys.wire("a", 32)
        
        v = -0x22
        
        py4hw.Constant(sys, "abs", v, r)

        sys.getSimulator().clk(1)
        
        assert(r.get() == v & ((1<<w)-1))

    def test_verilog_gen(self):
        sys = py4hw.HWSystem()
        
        r = sys.wire("r", 32)
        
        dut = py4hw.Constant(sys, "k", 0x25, r)

        rtl = py4hw.VerilogGenerator(dut)
        print('RTL:', rtl.getVerilogForHierarchy(dut))
            
if __name__ == '__main__':
    pytest.main(args=['-s', 'Test_Constant.py'])