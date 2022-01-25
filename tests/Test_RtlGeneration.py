# -*- coding: utf-8 -*-
"""
Created on Sat Jan 22 11:16:16 2022

@author: dcr
"""

import py4hw
import py4hw.debug
import pytest


class Test_RtlGeneration:
    
    def test_1(self):
        sys = py4hw.HWSystem()
        
        reset = sys.wire('reset',1)
        inc = sys.wire('inc',1)
        count = sys.wire('count', 8)
        carry = sys.wire('carry', 1)
        
        py4hw.Constant(sys, 'inc', 0, reset)
        py4hw.Constant(sys, 'inc', 1, inc)

        counter = py4hw.ModuloCounter(sys, 'counter', 3, reset, inc, count, carry)
    
        rtlgen = py4hw.VerilogGenerator(counter)
        print(rtlgen.getVerilog())
    
if __name__ == '__main__':
    pytest.main(args=['-q', 'Test_RtlGeneration.py'])