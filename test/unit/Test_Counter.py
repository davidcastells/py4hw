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
        
class Test_ModuloCounter:

    def test_integrity(self):
        hw = py4hw.HWSystem()
        
        reset = hw.wire('reset')
        inc = hw.wire('inc')
        q = hw.wire('q', 32)
        carryout = hw.wire('carryout')
        
        py4hw.Constant(hw, 'reset', 0, reset)
        py4hw.Constant(hw, 'inc', 1, inc)

        py4hw.ModuloCounter(hw, 'counter', 5, reset,  inc, q, carryout )       
                
        py4hw.debug.checkIntegrity(hw)

    def test_count(self):
        hw = py4hw.HWSystem()
        
        reset = hw.wire('reset')
        inc = hw.wire('inc')
        q = hw.wire('q', 8)
        carryout = hw.wire('carryout')
        
        py4hw.Constant(hw, 'reset', 0, reset)
        py4hw.Constant(hw, 'inc', 1, inc)

        py4hw.ModuloCounter(hw, 'counter', 5, reset,  inc, q, carryout )       
                
        hw.getSimulator().clk()
        assert(q.get() == 1)
        hw.getSimulator().clk(3)
        assert(q.get() == 4)
        hw.getSimulator().clk()
        assert(q.get() == 0)


    def test_carryout(self):
        hw = py4hw.HWSystem()
        
        reset = hw.wire('reset')
        inc = hw.wire('inc')
        q = hw.wire('q', 8)
        carryout = hw.wire('carryout')
        
        py4hw.Constant(hw, 'reset', 0, reset)
        py4hw.Sequence(hw, 'inc', [0, 1], inc)

        py4hw.ModuloCounter(hw, 'counter', 5, reset,  inc, q, carryout )       
                
        hw.getSimulator().clk(2)
        assert(carryout.get() == 0)
        hw.getSimulator().clk(3*2)
        assert(carryout.get() == 0)
        hw.getSimulator().clk()
        assert(carryout.get() == 1)
        hw.getSimulator().clk()
        assert(carryout.get() == 1)
        
if __name__ == '__main__':
    pytest.main(args=['-q', 'Test_Counter.py'])