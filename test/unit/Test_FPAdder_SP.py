# -*- coding: utf-8 -*-
"""
Created on Wed Feb  2 11:41:01 2022

@author: dcr
"""
import py4hw
import pytest

class Test_FPAdder_SP:
    
    def test_1(self):
        
        sys = py4hw.HWSystem()
        g = py4hw.LogicHelper(sys)
        fp = py4hw.FloatingPointHelper()
        
        r = sys.wire('r', 32)
        
        av = 1.2
        bv = 0.0000002
        a = g.hw_constant(32, fp.sp_to_ieee754(av))
        b = g.hw_constant(32, fp.sp_to_ieee754(bv))
        
        fpa = py4hw.FPAdder_SP(sys, 'fpa', a, b, r)
        
        sys.getSimulator().clk(1)
        
        err = fp.ieee754_to_sp(r.get()) - (av+bv)
        assert (abs(err) < 1E-7)

    def test_2(self):
        
        sys = py4hw.HWSystem()
        g = py4hw.LogicHelper(sys)
        fp = py4hw.FloatingPointHelper()
        
        r = sys.wire('r', 32)
        
        av = 0.0000002
        bv = 1.2
        a = g.hw_constant(32, fp.sp_to_ieee754(av))
        b = g.hw_constant(32, fp.sp_to_ieee754(bv))
        
        print('TESTING: ', av, bv)

        fpa = py4hw.FPAdder_SP(sys, 'fpa', a, b, r)
        
        sys.getSimulator().clk(1)
        
        err = fp.ieee754_to_sp(r.get()) - (av+bv)
        assert (abs(err) < 1E-7)

    def test_3(self):
        
        sys = py4hw.HWSystem()
        g = py4hw.LogicHelper(sys)
        fp = py4hw.FloatingPointHelper()
        
        r = sys.wire('r', 32)
        
        av = -4.2
        bv = 3.5
        a = g.hw_constant(32, fp.sp_to_ieee754(av))
        b = g.hw_constant(32, fp.sp_to_ieee754(bv))
        
        print('TESTING: ', av, bv)

        fpa = py4hw.FPAdder_SP(sys, 'fpa', a, b, r)
        
        sys.getSimulator().clk(1)
        
        err = fp.ieee754_to_sp(r.get()) - (av+bv)
        assert (abs(err) < 1E-7)
        
if __name__ == '__main__':
    pytest.main(args=['-q', 'Test_FPAdder_SP.py'])