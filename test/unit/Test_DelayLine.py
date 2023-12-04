# -*- coding: utf-8 -*-
"""
Created on Thu Nov 23 12:39:09 2023

@author: dcastel1
"""
import py4hw
import py4hw.debug
import pytest

class Test_DelayLine:

    def test_integrity(self):
        sys = py4hw.HWSystem()
        
        reset = sys.wire('reset')
        en = sys.wire('en')
        a = sys.wire('a', 32)
        q = sys.wire('q', 32)
        
        py4hw.Constant(sys, 'reset', 0, reset)
        py4hw.Constant(sys, 'en', 1, en)
        py4hw.Constant(sys, 'a', 31, a)
        

        py4hw.DelayLine(sys, 'delay', a, en=en, reset=reset, r=q, delay=15 )       
        
        
        
        py4hw.debug.checkIntegrity(sys)
        
if __name__ == '__main__':
    pytest.main(args=['-q', 'Test_DelayLine.py'])