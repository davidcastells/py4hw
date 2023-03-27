# -*- coding: utf-8 -*-
"""
Created on Tue Feb  1 13:46:38 2022

@author: dcr
"""
import py4hw
import pytest

class Test_Sub:
    
    def get_result_unsigned(self, w, va, vb):
        sys = py4hw.HWSystem()

        a = sys.wire('a', w)
        b = sys.wire('b', w)
        r = sys.wire('r', w)
        
        py4hw.Constant(sys, 'a', va, a)
        py4hw.Constant(sys, 'b', vb, b )
        
        py4hw.Sub(sys, 'r', a, b, r)
        
        sys.getSimulator().clk(1)
        return r.get()
    
    def get_result_signed(self, w, va, vb):
        sys = py4hw.HWSystem()

        a = sys.wire('a', w)
        b = sys.wire('b', w)
        r = sys.wire('r', w)
        
        py4hw.Constant(sys, 'a', va, a)
        py4hw.Constant(sys, 'b', vb, b )
        
        py4hw.SignedSub(sys, 'r', a, b, r)
        
        sys.getSimulator().clk(1)
        return r.get()
    
    def test_sub_unsigned(self):
        battery = [[32, 1, 1, 0],
                   [32, 2, 1, 1],
                   [32, 0, 1, -1],
                   [8, 1<<7, 127, 1]]
        
        for t in battery:
            w = t[0]
            va = t[1]
            vb = t[2]
            vr = t[3] & ((1<<w)-1) # (va-vb) & ((1<<w)-1)
        
            assert(self.get_result_unsigned(w, va, vb) == vr)
            
    def test_sub_signed(self):
        battery = [[32, 1, 1, 0],
                   [32, 2, 1, 1],
                   [8, 1<<7, -1, -127]]
        
        for t in battery:
            w = t[0]
            va = t[1]
            vb = t[2]
            vr = t[3] & ((1<<w)-1)
        
            assert(self.get_result_signed(w, va, vb) == vr)
        
if __name__ == '__main__':
    pytest.main(args=['-q', 'Test_Sub.py'])