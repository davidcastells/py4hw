# -*- coding: utf-8 -*-
"""
Created on Sun Mar 19 11:03:26 2023

@author: dcr
"""

import py4hw
import pytest
from py4hw.helper import *
import random

class Test_FXPAdder:
    
    def test_1(self):
        
        sys = py4hw.HWSystem()
        g = py4hw.LogicHelper(sys)
        #fxp = py4hw.FloatingPointHelper()
        
        
        av = FixedPoint(1,16,16, 1.2)
        bv = FixedPoint(1,16,16, 0.0000002)
        rv = FixedPoint(1,16,16, 1.2 - 0.0000002)
        
        aw = g.hw_constant(33, av.v)
        bw = g.hw_constant(33, bv.v)
        rw = sys.wire('r', 33)
        
        fpa = py4hw.FixedPointSub(sys, 'fpa', a=aw, af=av.getWidths(), b=bw , bf=bv.getWidths(),
                                    r=rw, rf=(1,16,16))
        
        sys.getSimulator().clk(1)
        
        assert (rw.get() == rv.v)


if __name__ == '__main__':
    #pytest.main(args=['-q', 'Test_FXPSub.py'])
    pytest.main(args=['-s', 'Test_FXPSub.py'])