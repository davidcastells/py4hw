# -*- coding: utf-8 -*-
"""
Created on Sat Aug 13 11:24:00 2022

@author: dcr
"""

import py4hw
import pytest
from py4hw.helper import *
import random 
import math

class Test_FPtoInt_SP:
    
    def test_1(self):
        
        sys = py4hw.HWSystem()
        g = LogicHelper(sys)
        fp = FloatingPointHelper()
        
        r = sys.wire('r', 32)
        p_lost = sys.wire('p_lost')
        denorm = sys.wire('denorm')
        invalid = sys.wire('invalid')
        
        av = 1.2
        a = g.hw_constant(32, fp.sp_to_ieee754(av))
        
        fpa = py4hw.FPtoInt_SP(sys, 'fp2i', a, r, p_lost, denorm, invalid)
        
        sys.getSimulator().clk(1)
        
        assert (r.get() == int(av))
        assert (p_lost.get() == int(abs(av- int(av)) > 0))
        assert (denorm.get() == 0)
        assert (invalid.get() == 0)

    def test_negative(self):
        
        sys = py4hw.HWSystem()
        g = LogicHelper(sys)
        fp = FloatingPointHelper()
        
        r = sys.wire('r', 32)
        p_lost = sys.wire('p_lost')
        denorm = sys.wire('denorm')
        invalid = sys.wire('invalid')
        
        av = -1.2
        a = g.hw_constant(32, fp.sp_to_ieee754(av))
        
        fpa = py4hw.FPtoInt_SP(sys, 'fp2i', a, r, p_lost, denorm, invalid)
        
        sys.getSimulator().clk(1)
        
        assert (r.get() == int(av) & 0xFFFFFFFF)
        assert (p_lost.get() == int(abs(av- int(av)) > 0))
        assert (denorm.get() == 0)
        assert (invalid.get() == 0)

    def test_random(self):
        sys = py4hw.HWSystem()
        g = LogicHelper(sys)
        fp = FloatingPointHelper()
        
        r = sys.wire('r', 32)
        p_lost = sys.wire('p_lost')
        denorm = sys.wire('denorm')
        invalid = sys.wire('invalid')

        a = sys.wire('a', 32)
        ca = py4hw.Constant(sys, 'a', 0, a)                
        fpa = py4hw.FPtoInt_SP(sys, 'fp2i', a, r, p_lost, denorm, invalid)

        print()
        for exp in [1, 10, 34]:
            large = int(math.pow(2, exp))

            for i in range(100):
                #max_int = int(math.pow(2, 31)-1)
                av = random.uniform(-large, large)
                av = fp.ieee754_stored_internally(av)
                ca.value = fp.sp_to_ieee754(av)
                
                if (abs(av) < 1):
                    bits = 0
                else:
                    bits = math.ceil(math.log2(int(abs(av))))

                if (av < 0):
                    bits += 1
                    
                
                exp_invalid = int(bits > 31)
                sys.getSimulator().clk(1)
                
                print('Testing', av, exp_invalid, bits)
                
                assert (invalid.get() == exp_invalid)
                if not(exp_invalid):
                    assert (r.get() == int(av) & 0xFFFFFFFF)
                    assert (p_lost.get() == int(abs(av- int(av)) > 0))
                    assert (denorm.get() == 0)
            
if __name__ == '__main__':
    #pytest.main(args=['-q', 'Test_FPAdder_SP.py'])
    pytest.main(args=['-s', 'Test_FPtoInt_SP.py'])