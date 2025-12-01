# -*- coding: utf-8 -*-
"""
Created on Wed Feb  2 05:59:29 2022

@author: dcr
"""

import py4hw
import py4hw.debug
import pytest


class Test_Abs:
    
    def test_random(self):
        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 32)
        r = sys.wire("r", 32)
        
        py4hw.Abs(sys, "abs", a, r)

        import random
        
        for i in range(1000):
            v = random.randint(-((1<<31)-1), (1<<31)-1)
            a.put(v)
        
            sys.getSimulator().clk(1)
        
            assert(r.get() == abs(v))

    def test_random_inv(self):
        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 32)
        r = sys.wire("r", 32)
        n = sys.wire("n")
        
        py4hw.Abs(sys, "abs", a, r, inverted=n)

        import random
        
        for i in range(1000):
            v = random.randint(-((1<<31)-1), (1<<31)-1)
            a.put(v)
        
            sys.getSimulator().clk(1)
        
            assert(r.get() == abs(v))
            assert(bool(n.get()) == (v<0))
            
    def test_verilog_gen(self):
        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 32)
        r = sys.wire("r", 32)
        
        dut = py4hw.Abs(sys, "abs", a, r)

        rtl = py4hw.VerilogGenerator(dut)
        print(rtl.getVerilogForHierarchy(dut))


if __name__ == '__main__':
    pytest.main(args=['-s', 'Test_Abs.py'])