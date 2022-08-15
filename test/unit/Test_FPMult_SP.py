# -*- coding: utf-8 -*-
"""
Created on Sun Aug 14 19:31:11 2022

@author: dcr
"""

import py4hw
import pytest
from py4hw.helper import BitManipulation
import random
import math

class Test_FPMult_SP:
    
    def test_1(self):
        
        sys = py4hw.HWSystem()
        g = py4hw.LogicHelper(sys)
        fp = py4hw.FloatingPointHelper()
        
        r = sys.wire('r', 32)
        
        av = 3.2
        bv = 5.00002
        a = g.hw_constant(32, fp.sp_to_ieee754(av))
        b = g.hw_constant(32, fp.sp_to_ieee754(bv))
        
        fpa = py4hw.FPMult_SP(sys, 'fpm', a, b, r)
        
        sys.getSimulator().clk(1)
        
        print()
        print('Expected:', av*bv, '{:08X}'.format(fp.sp_to_ieee754(av*bv)))
        print('Obtained:', fp.ieee754_to_sp(r.get()), '{:08X}'.format(r.get()))
        err = fp.ieee754_to_sp(r.get()) - (av*bv)
        assert (abs(err) < 1E-5)
        
    def test_1_deep(self):
        
        sys = py4hw.HWSystem()
        g = py4hw.LogicHelper(sys)
        fp = py4hw.FloatingPointHelper()
        
        r = sys.wire('r', 32)
        
        av = 97326422.09006774 
        bv = -84196012.54553068
        a = g.hw_constant(32, fp.sp_to_ieee754(av))
        b = g.hw_constant(32, fp.sp_to_ieee754(bv))
        
        fpm = py4hw.FPMult_SP(sys, 'fpm', a, b, r)
        
        sys.getSimulator().clk(1)
        
        sa, ea, ma = fp.sp_to_fixed_point_parts(av)
        sb, eb, mb = fp.sp_to_fixed_point_parts(bv)
        
        assert(fpm.children['pa'].getOutPortByName('s').wire.get() == sa)
        assert(fpm.children['pa'].getOutPortByName('e').wire.get() == (ea + 127) ) # because we do not fix exponent
        assert(fpm.children['pa'].getOutPortByName('m').wire.get() == ma)
        assert(fpm.children['pb'].getOutPortByName('s').wire.get() == sb)
        assert(fpm.children['pb'].getOutPortByName('e').wire.get() == (eb + 127) ) # because we do not fix exponent
        assert(fpm.children['pb'].getOutPortByName('m').wire.get() == mb)
        
        assert(fpm.children['pre_er2'].getOutPortByName('r').wire.get() == (ea + eb) + 128 )
        
        print()
        print('Expected:', av*bv, '{:08X}'.format(fp.sp_to_ieee754(av*bv)))
        print('Obtained:', fp.ieee754_to_sp(r.get()), '{:08X}'.format(r.get()))
        rv = fp.ieee754_to_sp(r.get())
        rerr = abs(rv - (av*bv)) / (av*bv)
        assert (rerr < 1E-7)

    def test_random(self):
        
        sys = py4hw.HWSystem()
        g = py4hw.LogicHelper(sys)
        fp = py4hw.FloatingPointHelper()
        
        r = sys.wire('r', 32)

        large = math.pow(2, 29)        
        a = sys.wire('a', 32)
        b = sys.wire('b', 32)
        
        ca = py4hw.Constant(sys, 'a', 0, a)
        cb = py4hw.Constant(sys, 'b', 0, b)
        
        fpa = py4hw.FPMult_SP(sys, 'fpm', a, b, r)

        print()

        for i in range(100):
            av = random.uniform(-large, large)
            bv = random.uniform(-large, large)
    
            ca.value = fp.sp_to_ieee754(av)
            cb.value = fp.sp_to_ieee754(bv)
    
            sys.getSimulator().clk(1)
            
            print('Multiplying:', av, bv)
            print('Expected:', av*bv, '{:08X}'.format(fp.sp_to_ieee754(av*bv)))
            print('Obtained:', fp.ieee754_to_sp(r.get()), '{:08X}'.format(r.get()))
            
            rv = fp.ieee754_to_sp(r.get())
            rerr = abs(rv - (av*bv)) / (av*bv)
            assert (rerr < 1E-6)


if __name__ == '__main__':
    #pytest.main(args=['-q', 'Test_FPAdder_SP.py'])
    pytest.main(args=['-s', 'Test_FPMult_SP.py'])