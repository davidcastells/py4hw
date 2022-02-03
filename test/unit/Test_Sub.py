# -*- coding: utf-8 -*-
"""
Created on Tue Feb  1 13:46:38 2022

@author: dcr
"""
import py4hw
import pytest

class Test_Sub:
    
    def test_sub1(self):
        sys = py4hw.HWSystem()

        a = sys.wire('a', 23)
        b = sys.wire('b', 23)
        r = sys.wire('r', 24)
        
        va = 1623049
        vb = 6146853
        vr  = (va - vb) & ((1<<24)-1)
        py4hw.Constant(sys, 'a', va, a)
        py4hw.Constant(sys, 'b', vb, b )
        
        py4hw.Sub(sys, 'r', a, b, r)
        
        sys.getSimulator().clk(1)
        
        assert(r.get() == vr)
        
if __name__ == '__main__':
    pytest.main(args=['-q', 'Test_Sub.py'])