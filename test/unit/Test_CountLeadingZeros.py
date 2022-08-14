# -*- coding: utf-8 -*-
"""
Created on Tue Aug  9 10:50:59 2022

@author: dcr
"""

import py4hw
import py4hw.debug
from py4hw.helper import BitManipulation
import pytest

class Test_CountLeadingZeros:
    
    
    def test_8bit(self):
        sys = py4hw.HWSystem()
        w = 8
        a = sys.wire("a", w)
        r = sys.wire("r", w)
        z = sys.wire("z")

        v = 64
        
        py4hw.Constant(sys, "a", v, a)
        py4hw.CountLeadingZeros(sys, "clz", a, r, z)
        sys.getSimulator().clk(1);
        assert(r.get() == BitManipulation.countLeadingZeros(v, w))
        assert(z.get() == int(v == 0))

    def test_32bit(self):
        sys = py4hw.HWSystem()
        w = 32
        a = sys.wire("a", w)
        r = sys.wire("r", w)
        z = sys.wire("z")

        v = 0x3456
        
        py4hw.Constant(sys, "a", v, a)
        py4hw.CountLeadingZeros(sys, "clz", a, r, z)
        sys.getSimulator().clk(1);
        assert(r.get() == BitManipulation.countLeadingZeros(v, w))
        assert(z.get() == int(v == 0))


    def test_zero(self):
        sys = py4hw.HWSystem()
        a = sys.wire("a", 8)
        r = sys.wire("r", 8)
        z = sys.wire("z")

        py4hw.Constant(sys, "a", 0, a)
        py4hw.CountLeadingZeros(sys, "clz", a, r, z)
        sys.getSimulator().clk(1);
        assert(r.get() == 8)
        assert(z.get() == 1)

    def test_random(self):
        import random
        import math
        
        # @todo simulation is very slow, investigate the cause.
        # it seems to be related to excessive width
        for i in range(3):
            print('Creating ', i)
            sys = py4hw.HWSystem()
            w = int(random.uniform(2, 64))
            a = sys.wire("a", w)
            r = sys.wire("r", w)
            z = sys.wire("z")
    
            
            ca = py4hw.Constant(sys, "a", 0, a)
            py4hw.CountLeadingZeros(sys, "clz", a, r, z)
            print('Simulating')

            for j in range(10):
                v = int(random.uniform(0, int(math.pow(2, w))))
                ca.value = v
                sys.getSimulator().clk(1);
                
                print('Testing w:', w, 'v:', hex(v), 'expected clz:', 
                      BitManipulation.countLeadingZeros(v, w),
                      'result:', r.get())
                
                assert(r.get() == BitManipulation.countLeadingZeros(v, w))
                assert(z.get() == int(v == 0))
            
            del sys
        
    # def test_Integrity(self):
    #     sys = py4hw.HWSystem()
        
    #     a = sys.wire("a", 32)
    #     b = sys.wire("b", 32)
    #     c = sys.wire("c", 32)
    #     r1 = sys.wire("r", 32)
    #     r2 = sys.wire("r2", 32)
        
    #     py4hw.Add(sys, "add1", a,b, r1)
    #     py4hw.Add(sys, "add2", r1, c, r2)
        
    #     py4hw.Constant(sys, "a", 10, a)
    #     py4hw.Constant(sys, "b", 20, b)
    #     py4hw.Constant(sys, "c", 5, c)
    #     py4hw.Scope(sys, "r2", r2)
        
    #     py4hw.debug.checkIntegrity(sys)

if __name__ == '__main__':
    #pytest.main(args=['-q', 'Test_CountLeadingZeros.py'])
    pytest.main(args=['-s', 'Test_CountLeadingZeros.py'])