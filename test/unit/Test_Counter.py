# -*- coding: utf-8 -*-
"""
Created on Tue Jun  7 08:55:35 2022

@author: dcr
"""

import py4hw
import py4hw.debug
import pytest


class Test_Counter:

    def test_integrity(self):
        sys = py4hw.HWSystem()
        
        reset = sys.wire('reset')
        inc = sys.wire('inc')
        q = sys.wire('q', 32)
        
        py4hw.Constant(sys, 'reset', 0, reset)
        py4hw.Constant(sys, 'inc', 1, inc)
        

        py4hw.Counter(sys, 'counter', reset, inc, q )       
        
        
        
        py4hw.debug.checkIntegrity(sys)
        
    def test_1(self):
        sys = py4hw.HWSystem()
        
        reset = sys.wire('reset')
        inc = sys.wire('inc')
        q = sys.wire('q', 32)
        
        py4hw.Sequence(sys, 'reset', [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], reset)
        py4hw.Sequence(sys, 'inc', [0, 1, 1, 1, 0, 1, 1, 1, 0, 1], inc)
        

        py4hw.Counter(sys, 'counter', reset, inc, q )       
        
        py4hw.Scope(sys, 'q', [q])
        sys.getSimulator().clk(20)
        
if __name__ == '__main__':
    pytest.main(args=['-q', 'Test_Counter.py'])