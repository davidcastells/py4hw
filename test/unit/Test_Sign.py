# -*- coding: utf-8 -*-
"""
Created on Sat Oct 31 11:19:05 2020

@author: dcr
"""
import py4hw
import py4hw.debug
import pytest


class Test_Sign:
    
    def test_random(self):
        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 32)
        r = sys.wire("r")
        
        py4hw.Sign(sys, "signTest1", a, r)

        import random
        
        for i in range(1000):
            v = random.randint(-((1<<31)-1), (1<<31)-1)
            a.put(v)
        
            sys.getSimulator().clk(1)
        
            assert(bool(r.get()) == (v<0))
            
    def test_verilog_gen(self):
        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 32)
        r = sys.wire("r")
        
        dut = py4hw.Sign(sys, "sign", a, r)

        rtl = py4hw.VerilogGenerator(dut)
        print(rtl.getVerilogForHierarchy(dut))

if __name__ == '__main__':
    pytest.main(args=['-s', 'Test_Sign.py'])