# -*- coding: utf-8 -*-
"""
Created on Sun Jun 16 12:32:33 2024

@author: dcastel1
"""

import py4hw
import pytest
from py4hw.helper import *
import random 
import math

from py4hw.logic.arithmetic_fp import FixedPointtoFP_SP

class Test_FXPtoFP_SP:
    
    def test_1(self):
        ka = FixedPoint(1, 8, 8, 1.5)
        
        hw = py4hw.HWSystem()
        
        a = ka.createConstant(hw, 'a')
        
        r = hw.wire('r', 32)
        p_lost = hw.wire('p_lost')
        
        FixedPointtoFP_SP(hw, 'fxp2fp', a, ka.getWidths(), r, p_lost)

        hw.getSimulator().clk()
        print()
        print('a=', hex(a.get()), ka.dump(), 'width=', a.getWidth())

        rv = FPNum(r.get(), 'sp')
        print('r=', hex(r.get()), rv.to_float())        
        
        assert(rv.to_float() == 1.5)
        
    def test_2(self):
        data = [(1,8,8,2.5),
                (1,10,3,3.5),
                (1,3,10,4.5),
                (1,5,15,19.018951416015625), # we do no support rounding yet
                (1,5,5,-2.5)]
        
        for item in data:
            s, i, f, v = item
            hw = py4hw.HWSystem()
            
            ka = FixedPoint(s, i, f, v)
            a = ka.createConstant(hw, 'a')
            
            r = hw.wire('r', 32)
            p_lost = hw.wire('p_lost')
            
            FixedPointtoFP_SP(hw, 'fxp2fp', a, ka.getWidths(), r, p_lost)
    
            hw.getSimulator().clk()
            print()
            print('a=', hex(a.get()), ka.dump(), 'width=', a.getWidth())
    
            rv = FPNum(r.get(), 'sp')
            print('r=', hex(r.get()), rv.to_float())        
            
            assert(rv.to_float() == v)
            

if __name__ == '__main__':
    #pytest.main(args=['-q', 'Test_FXPSub.py'])
    pytest.main(args=['-s', 'Test_FXPtoFP.py'])        