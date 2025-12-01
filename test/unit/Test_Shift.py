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

class Test_Shift:

    def test_integrity(self):
        sys = py4hw.HWSystem()
        
        reset = sys.wire('reset')
        a = sys.wire('a', 32)
        b = sys.wire('b', 5)
        l = sys.wire('l', 32)
        r = sys.wire('r', 32)
        
        ca = py4hw.Constant(sys, 'a', 0, a)
        cb = py4hw.Constant(sys, 'b', 3, b)
        

        py4hw.ShiftLeft(sys, 'left', a, b, l )       
        py4hw.ShiftRight(sys, 'right', a, b, r )       
        
        py4hw.debug.checkIntegrity(sys)

    def test_shiftr_1(self):
        sys = py4hw.HWSystem()
        
        reset = sys.wire('reset')
        a = sys.wire('a', 56)
        b = sys.wire('b', 8)
        r = sys.wire('r', 64)
        
        av = 0x9020f800000000
        bv = 0x5
        py4hw.Constant(sys, 'a', av, a)
        py4hw.Constant(sys, 'b', bv, b)

        
        exp_r = (av >> bv) & ((1<<64)-1)

        print('Sifting {:08X} by {:3d}  right: {:08X}'.format(av, bv,  exp_r) )
        
        py4hw.ShiftRight(sys, 'right', a, b, r )   
        
        sys.getSimulator().clk(1)
        
        assert(r.get() == exp_r)
        
    def test_random(self):
        sys = py4hw.HWSystem()
        
        reset = sys.wire('reset')
        a = sys.wire('a', 32)
        b = sys.wire('b', 5)
        l = sys.wire('l', 32)
        r = sys.wire('r', 32)
        
        ca = py4hw.Constant(sys, 'a', 0, a)
        cb = py4hw.Constant(sys, 'b', 0, b)
        

        py4hw.ShiftLeft(sys, 'left', a, b, l )       
        py4hw.ShiftRight(sys, 'right', a, b, r )       
        
        print()
        
        for i in range(100):
            av = int(random.uniform(0x100, 0x00FFFF00))
            bv = int(random.uniform(0, 16))
            ca.value = av
            cb.value = bv
            
            sys.getSimulator().clk(1)
            
            exp_l = (av << bv) & 0xFFFFFFFF
            exp_r = (av >> bv) & 0xFFFFFFFF

            print('Sifting {:08X} by {:3d} left: {:08X} right: {:08X}'.format(av, bv, exp_l, exp_r) )
            
            assert(l.get() == exp_l)
            assert(r.get() == exp_r)
            
        
    def test_shiftrk_1(self):
        sys = py4hw.HWSystem()
        
        reset = sys.wire('reset')
        a = sys.wire('a', 56)
        r = sys.wire('r', 64)
        
        av = 0x9020f800000000
        bv = 0x5
        py4hw.Constant(sys, 'a', av, a)
        
        exp_r = (av >> bv) & ((1<<64)-1)

        print('Sifting {:08X} by {:3d}  right: {:08X}'.format(av, bv,  exp_r) )
        
        py4hw.ShiftRightConstant(sys, 'right', a, bv, r )   
        
        sys.getSimulator().clk(1)
        
        assert(r.get() == exp_r)
        
        
    def test_shiftlk_1(self):
        sys = py4hw.HWSystem()
        
        reset = sys.wire('reset')
        a = sys.wire('a', 56)
        r = sys.wire('r', 64)
        
        av = 0x9020f8
        bv = 0x5
        py4hw.Constant(sys, 'a', av, a)
        
        exp_r = (av << bv) & ((1<<64)-1)

        print('Sifting {:08X} by {:3d}  right: {:08X}'.format(av, bv,  exp_r) )
        
        py4hw.ShiftLeftConstant(sys, 'right', a, bv, r )   
        
        sys.getSimulator().clk(1)
        
        assert(r.get() == exp_r), f'{r.get():X} != {exp_r:X}'
        
    def test_shift_right_k_verilog_gen(self):
        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 32)
        bv = 5
        r = sys.wire("r", 32)
        
        dut = py4hw.ShiftRightConstant(sys, 'right', a, bv, r )   

        rtl = py4hw.VerilogGenerator(dut)
        print(rtl.getVerilogForHierarchy(dut))
        
    def test_shift_left_k_verilog_gen(self):
        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 32)
        bv = 5
        r = sys.wire("r", 32)
        
        dut = py4hw.ShiftLeftConstant(sys, 'left', a, bv, r )   

        rtl = py4hw.VerilogGenerator(dut)
        print(rtl.getVerilogForHierarchy(dut))
        
if __name__ == '__main__':
    pytest.main(args=['-s', 'Test_Shift.py'])