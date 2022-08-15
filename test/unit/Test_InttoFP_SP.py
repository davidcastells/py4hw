# -*- coding: utf-8 -*-
"""
Created on Sun Aug 14 09:56:24 2022

@author: dcr
"""

import py4hw
import pytest
from py4hw.helper import BitManipulation
import random 
import math

class Test_FPtoInt_SP:
    
    def test_1(self):
        
        sys = py4hw.HWSystem()
        g = py4hw.LogicHelper(sys)
        fp = py4hw.FloatingPointHelper()
        
        r = sys.wire('r', 32)
        p_lost = sys.wire('p_lost')
        
        av = 2345
        a = g.hw_constant(32, av)
        exp_a = fp.sp_to_ieee754(av)
        
        fpa = py4hw.InttoFP_SP(sys, 'fi2a', a, r, p_lost)
        
        sys.getSimulator().clk(1)
        
        ri = int(fp.ieee754_to_sp(r.get()))

        assert (r.get() == exp_a)        
        assert (p_lost.get() == int(abs(ri- av) > 0))

    def test_negative(self):
        
        sys = py4hw.HWSystem()
        g = py4hw.LogicHelper(sys)
        fp = py4hw.FloatingPointHelper()
        
        r = sys.wire('r', 32)
        p_lost = sys.wire('p_lost')
        
        av = -2345
        a = g.hw_constant(32, av)
        exp_a = fp.sp_to_ieee754(av)
        
        fpa = py4hw.InttoFP_SP(sys, 'fi2a', a, r, p_lost)
        
        sys.getSimulator().clk(1)
        
        ri = int(fp.ieee754_to_sp(r.get()))

        assert (r.get() == exp_a)        
        assert (p_lost.get() == int(abs(ri- av) > 0))

    def test_random(self):
        sys = py4hw.HWSystem()
        g = py4hw.LogicHelper(sys)
        fp = py4hw.FloatingPointHelper()
        
        r = sys.wire('r', 32)
        p_lost = sys.wire('p_lost')
        
        av = 2345
        a = sys.wire('a', 32)
        ca = py4hw.Constant(sys, 'a', 0, a)
        fpa = py4hw.InttoFP_SP(sys, 'fi2a', a, r, p_lost)
 
        print()
        for i in range(10):
            large = math.pow(2, 29)
            av = int(random.uniform(-large, large))

            rav = fp.ieee754_stored_internally(av)           
            exp_a = fp.sp_to_ieee754(rav)
        
            ca.value = av        
            sys.getSimulator().clk(1)
        
            ri = r.get()

            print('Testing', av, 'real', rav, 'expected', hex(exp_a), 'obtained', hex(ri))
            assert (abs(r.get() - exp_a) < 2)        
            assert (p_lost.get() == int(abs(av- rav) > 0))

            
if __name__ == '__main__':
    #pytest.main(args=['-q', 'Test_FPAdder_SP.py'])
    pytest.main(args=['-s', 'Test_InttoFP_SP.py'])