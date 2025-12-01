# -*- coding: utf-8 -*-
"""
Created on Sun Aug 17 11:30:56 2025

@author: 2016570
"""

import pytest

class Test_Stack:
    
    def test_push1_popl(self):
        import py4hw

        hw = py4hw.HWSystem()

        din = hw.wire('din', 8)
        dout = hw.wire('dout', 8)

        
        push = hw.wire('push')
        pop = hw.wire('pop')

        py4hw.Sequence(hw, 'din', [1,2,3,4,5], din)
        

        py4hw.Sequence(hw, 'push', [0,1,0,0,0], push)
        py4hw.Sequence(hw, 'pop', [0,0,1,0,0], pop)

        py4hw.Stack_ShiftRegister(hw, 'stack', din, dout, push, pop, None, None, 3)
        
        sim = hw.getSimulator()
        
        print()
        sim.clk(1)
        sim.clk(1)
        
        print('Push:', din.get())
        
        sim.clk(1)
        sim.clk(1)
        
        print('Pop:', dout.get())
        
        assert(dout.get() == 2)
        
    def test_push2_pop2(self):
        import py4hw

        hw = py4hw.HWSystem()

        din = hw.wire('din', 8)
        dout = hw.wire('dout', 8)

        
        push = hw.wire('push')
        pop = hw.wire('pop')

        py4hw.Sequence(hw, 'din', [1,2,3,4,5], din)
        

        py4hw.Sequence(hw, 'push', [0,1,1,0,0], push)
        py4hw.Sequence(hw, 'pop', [0,0,0,1,1], pop)

        py4hw.Stack_ShiftRegister(hw, 'stack', din, dout, push, pop, None, None, 3)
        
        sim = hw.getSimulator()
        
        print()
        sim.clk(1)
        sim.clk(1)
        
        print('Push:', din.get())
        sim.clk(1)
        
        print('Push:', din.get())
        
        sim.clk(1)
        sim.clk(1)
        
        print('Pop:', dout.get())
        assert(dout.get() == 3)
        
        sim.clk(1)
       
        print('Pop:', dout.get())
        assert(dout.get() == 2)
        
    
if __name__ == '__main__':
    pytest.main(args=['-s', 'Test_Stack.py'])            