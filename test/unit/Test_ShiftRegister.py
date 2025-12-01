# -*- coding: utf-8 -*-
"""
Created on Sun Aug 17 10:07:59 2025

@author: dcr
"""

import pytest

class Test_ShiftRegister:
    
    def test_push1_popl_left(self):
        import py4hw

        hw = py4hw.HWSystem()

        lin = hw.wire('lin', 8)
        lout = hw.wire('lout', 8)

        rin = hw.wire('rin', 8)
        rout = hw.wire('rout', 8)


        sl = hw.wire('sl')
        sr = hw.wire('sr')

        py4hw.Sequence(hw, 'lin', [1,2,3,4,5], lin)
        py4hw.Sequence(hw, 'rin', [2,3,4,5], rin)


        py4hw.Sequence(hw, 'sl', [0,0,1,0,0], sl)
        py4hw.Sequence(hw, 'sr', [0,1,0,0,0], sr)

        py4hw.ShiftRegisterBidirectional(hw, 'shift', lin, rin, lout, rout, sl, sr, 3)
        
        sim = hw.getSimulator()
        
        print()
        
        
        sim.clk(1)
        sim.clk(1)
        
        print('Pushing:', lin.get())
        
        sim.clk(1)
        
        print('Left Head:', lout.get())
        
        assert(lout.get() == 2)
        
    def test_push1_popl_right(self):
        import py4hw

        hw = py4hw.HWSystem()

        lin = hw.wire('lin', 8)
        lout = hw.wire('lout', 8)

        rin = hw.wire('rin', 8)
        rout = hw.wire('rout', 8)


        sl = hw.wire('sl')
        sr = hw.wire('sr')

        py4hw.Sequence(hw, 'lin', [1,2,3,4,5], lin)
        py4hw.Sequence(hw, 'rin', [2,3,4,5], rin)


        py4hw.Sequence(hw, 'sl', [0,1,0,0,0], sl)
        py4hw.Sequence(hw, 'sr', [0,0,0,0,0], sr)

        py4hw.ShiftRegisterBidirectional(hw, 'shift', lin, rin, lout, rout, sl, sr, 3)
        
        sim = hw.getSimulator()
        
        print()
        
        
        sim.clk(1)
        sim.clk(1)
        
        print('Pushing:', rin.get())
        
        sim.clk(1)
        
        print('Left Head:', rout.get())
        
        assert(rout.get() == 3)
        
if __name__ == '__main__':
    pytest.main(args=['-s', 'Test_ShiftRegister.py'])        