# -*- coding: utf-8 -*-
"""
Created on Wed Jan 19 18:28:12 2022

@author: dcr
"""

import py4hw
import pytest


class TestAnyEqual:
    
    def test_oneEqual(self):
        sys = py4hw.HWSystem()
        
        ins = sys.wires('wi', 3, 8)
        
        py4hw.Constant(sys, 'i0', 3, ins[0])
        py4hw.Constant(sys, 'i1', 7, ins[1])
        py4hw.Constant(sys, 'i2', 3, ins[2])
        
        r = sys.wire('r', 1)
        
        py4hw.AnyEqual(sys, 'any', ins, r)
        
        sys.getSimulator().clk(1)
        assert (r.get() == 1)

    def test_noneEqual(self):
        sys = py4hw.HWSystem()
        
        ins = sys.wires('wi', 3, 8)
        
        py4hw.Constant(sys, 'i0', 3, ins[0])
        py4hw.Constant(sys, 'i1', 7, ins[1])
        py4hw.Constant(sys, 'i2', 9, ins[2])
        
        r = sys.wire('r', 1)
        
        py4hw.AnyEqual(sys, 'any', ins, r)
        
        sys.getSimulator().clk(1)
        assert (r.get() == 0)
        
if __name__ == '__main__':
    pytest.main(args=['-q', 'Test_AnyEqual.py'])