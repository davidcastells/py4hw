# -*- coding: utf-8 -*-
"""
Created on Sat Feb  5 09:53:22 2022

@author: dcr
"""
import py4hw
import pytest
from py4hw.helper import *
import random 
import math

class Test_Rotate:

    def test_integrity(self):
        sys = py4hw.HWSystem()
        
        reset = sys.wire('reset')
        a = sys.wire('a', 32)
        b = sys.wire('b', 5)
        l = sys.wire('l', 32)
        r = sys.wire('r', 32)
        
        ca = py4hw.Constant(sys, 'a', 0, a)
        cb = py4hw.Constant(sys, 'b', 3, b)
        

        py4hw.RotateLeft(sys, 'left', a, b, l )       
        py4hw.RotateRight(sys, 'right', a, b, r )       
        
        py4hw.debug.checkIntegrity(sys)

    def test_random(self):
        sys = py4hw.HWSystem()
        
        reset = sys.wire('reset')
        a = sys.wire('a', 32)
        b = sys.wire('b', 5)
        l = sys.wire('l', 32)
        r = sys.wire('r', 32)
        
        ca = py4hw.Constant(sys, 'a', 0, a)
        cb = py4hw.Constant(sys, 'b', 0, b)
        

        py4hw.RotateLeft(sys, 'left', a, b, l )       
        py4hw.RotateRight(sys, 'right', a, b, r )       
        
        print()
        
        for i in range(100):
            av = int(random.uniform(0x100, 0x00FFFF00))
            bv = int(random.uniform(0, 16))
            ca.value = av
            cb.value = bv
            
            sys.getSimulator().clk(1)
            
            exp_l = ((av << bv) | (av >> (32-bv))) & 0xFFFFFFFF
            exp_r = ((av >> bv) | (av << (32-bv))) & 0xFFFFFFFF

            print('Rotating {:08X} by {:3d} left: {:08X} right: {:08X}'.format(av, bv, exp_l, exp_r) )
            
            assert(l.get() == exp_l)
            assert(r.get() == exp_r)
            
        
if __name__ == '__main__':
    pytest.main(args=['-s', 'Test_Rotate.py'])