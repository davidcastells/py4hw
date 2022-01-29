# -*- coding: utf-8 -*-
"""
Created on Sat Oct 31 11:19:05 2020

@author: dcr
"""
import py4hw
import py4hw.debug
import pytest


class Test_Sign:
    
    def test_1(self):
        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 32)
        b = sys.wire("b", 32)
        c = sys.wire("c", 32)
        r1 = sys.wire("r1")
        r2 = sys.wire("r2")
        r3 = sys.wire("r3")
        
        py4hw.Constant(sys, "a", -10, a)
        py4hw.Constant(sys, "b", 0, b)
        py4hw.Constant(sys, "c", 10, c)
        
        py4hw.Sign(sys, "signTest1", a, r1)
        py4hw.Sign(sys, "signTest2", b, r2)
        py4hw.Sign(sys, "signTest3", c, r3)
        
        py4hw.Scope(sys, "r1", r1)
        py4hw.Scope(sys, "r2", r2)
        py4hw.Scope(sys, "r3", r3)
        
        print('RESET')
        sim = sys.getSimulator()
        
        print()
        print('CLK')
        sim.clk(1)

if __name__ == '__main__':
    pytest.main(args=['-q', 'Test_Add.py'])