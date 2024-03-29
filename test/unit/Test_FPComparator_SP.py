# -*- coding: utf-8 -*-
"""
Created on Tue Feb  1 10:22:14 2022

@author: dcr
"""
import py4hw
import pytest

class Test_FPComparator_SP:
    
    def test_1(self):
        sys = py4hw.HWSystem()
        
        fp = py4hw.FloatingPointHelper()
        
        a = sys.wire('a', 32)
        b = sys.wire('b', 32)

        gt = sys.wire('gt')
        eq= sys.wire('eq')
        lt = sys.wire('lt')
        
        py4hw.FPComparator_SP(sys, 'cmp', a, b, gt, eq, lt)
        
        av = 305.531528442573 
        bv = 443.5870680854455
        
        a.put(fp.sp_to_ieee754(av))
        b.put(fp.sp_to_ieee754(bv))
        
        print('TESTING: ', av, bv, fp.zp_bin(fp.sp_to_ieee754(av), 32), fp.zp_bin(fp.sp_to_ieee754(bv), 32))
        
        sys.getSimulator().clk(1)

        assert(bool(gt.get()) == (av > bv))
        assert(bool(eq.get()) == (av == bv))
        assert(bool(lt.get()) == (av < bv))
            
    def test_3(self):
        
        sys = py4hw.HWSystem()
        g = py4hw.LogicHelper(sys)
        fp = py4hw.FloatingPointHelper()
        
        r = sys.wire('r', 32)
        
        av = -4.2
        bv = 3.5
        a = g.hw_constant(32, fp.sp_to_ieee754(av))
        b = g.hw_constant(32, fp.sp_to_ieee754(bv))
        
        gt = sys.wire('gt')
        eq= sys.wire('eq')
        lt = sys.wire('lt')
        
        py4hw.FPComparator_SP(sys, 'cmp', a, b, gt, eq, lt)
        
        sys.getSimulator().clk(1)
        
        assert (gt.get() == 0)
        assert (eq.get() == 0)
        assert (lt.get() == 1)
        
    def test_abs(self):
        sys = py4hw.HWSystem()
        
        fp = py4hw.FloatingPointHelper()
        
        a = sys.wire('a', 32)
        b = sys.wire('b', 32)
        gt = sys.wire('gt')
        eq= sys.wire('eq')
        lt = sys.wire('lt')
        
        py4hw.FPComparator_SP(sys, 'cmp', a, b, gt, eq, lt, absolute=True)
        
        av = -971.0587159810018
        bv = -353.1498041093273

        a.put(fp.sp_to_ieee754(av))
        b.put(fp.sp_to_ieee754(bv))
        
        print('TESTING: ', av, bv, fp.zp_bin(fp.sp_to_ieee754(av), 32), fp.zp_bin(fp.sp_to_ieee754(bv), 32))
        
        sys.getSimulator().clk(1)

        assert(bool(gt.get()) == (abs(av) > abs(bv)))
        assert(bool(eq.get()) == (abs(av) == abs(bv)))
        assert(bool(lt.get()) == (abs(av) < abs(bv)))
        
    def test_random(self):
        
        import random
        
        sys = py4hw.HWSystem()
        
        fp = py4hw.FloatingPointHelper()
        
        a = sys.wire('a', 32)
        b = sys.wire('b', 32)
        gt = sys.wire('gt')
        eq= sys.wire('eq')
        lt = sys.wire('lt')
        
        py4hw.FPComparator_SP(sys, 'cmp', a, b, gt, eq, lt)
        
        for i in range(1000):
            av = (random.random()-0.5) * 2000 
            bv = (random.random()-0.5) * 2000
            
            a.put(fp.sp_to_ieee754(av))
            b.put(fp.sp_to_ieee754(bv))
            
            print('TESTING: ', av, bv)
            
            sys.getSimulator().clk(1)

            assert(bool(gt.get()) == (av > bv))
            assert(bool(eq.get()) == (av == bv))
            assert(bool(lt.get()) == (av < bv))
        
    def test_random_abs(self):
        
        import random
        
        sys = py4hw.HWSystem()
        
        fp = py4hw.FloatingPointHelper()
        
        a = sys.wire('a', 32)
        b = sys.wire('b', 32)
        gt = sys.wire('gt')
        eq= sys.wire('eq')
        lt = sys.wire('lt')
        
        py4hw.FPComparator_SP(sys, 'cmp', a, b, gt, eq, lt, absolute=True)
        
        for i in range(100):
            av = (random.random()-0.5) * 2000 
            bv = (random.random()-0.5) * 2000
            
            a.put(fp.sp_to_ieee754(av))
            b.put(fp.sp_to_ieee754(bv))
            
            print('TESTING: ', av, bv)
            
            sys.getSimulator().clk(1)

            assert(bool(gt.get()) == (abs(av) > abs(bv)))
            assert(bool(eq.get()) == (abs(av) == abs(bv)))
            assert(bool(lt.get()) == (abs(av) < abs(bv)))
        
if __name__ == '__main__':
    pytest.main(args=['-q', 'Test_FPComparator_SP.py'])