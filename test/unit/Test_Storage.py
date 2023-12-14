# -*- coding: utf-8 -*-
"""
Created on Wed Dec  6 21:27:55 2023

@author: dcastel1
"""

import py4hw
import py4hw.debug
import pytest


class Test_Sign:
    
    def test_reg(self):
        sys = py4hw.HWSystem()
        
        a = sys.wire('a', 8)
        r = sys.wire('r', 8)
        
        exp = [0, 1, 2]
        py4hw.Sequence(sys, 'a', exp, a)
        py4hw.Reg(sys, 'reg', a, r)

        sys.getSimulator().clk(1)

        #print()
        
        for i in range(len(exp)):      
            sys.getSimulator().clk(1)
            #print('sim', i, 'r:', r.get(), 'exp:', exp[i])
            assert(r.get() == exp[i])
        

    def test_treg(self):
        sys = py4hw.HWSystem()
        
        a = sys.wire('a', 8)
        r = sys.wire('r', 8)
        
        tin = [0, 1, 0, 1]
        exp = [0, 1, 1, 0]
        py4hw.Sequence(sys, 't', tin, a)
        py4hw.TReg(sys, 'reg', a, r)

        sys.getSimulator().clk(1)

        #print()
        
        for i in range(len(exp)):      
            sys.getSimulator().clk(1)
            #print('sim', i, 'r:', r.get(), 'exp:', exp[i])
            assert(r.get() == exp[i])


if __name__ == '__main__':
    pytest.main(args=['-s', 'Test_Storage.py'])