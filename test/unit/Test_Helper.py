# -*- coding: utf-8 -*-
"""
Created on Thu Jul 21 12:20:28 2022

@author: dcr
"""

import py4hw
import pytest
import math

class Test_Helper:

    def test_integrity(self):
        print('test_integrity')
        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 2)
        r = sys.wire("r", 1)
        
        py4hw.Constant(sys, "a", 0, a)
        
        eq = py4hw.EqualConstant(sys, 'equal', a, 0, r)
        
        wl = py4hw.helper.CircuitAnalysis.getAllPortWires(eq)
        
        assert(len(wl) == 2)

        for w in wl:
            print(w.getFullPath())
            
        print('integrity check complete')
            
    def test_sp_conversion(self):
        print('test_fp_conversion')

        # this is a list of pairs of single precision floating point and its ieee 754 representation value
        values = [[0.0, 0x00000000],
                  [1.40129846432e-45, 0x00000001],
                  [5.87747175411e-39, 0x00400000],
                  [1.17549449095e-38, 0x00800001],
                  [2.00000023842,     0x40000001],
                  [-2.00000023842,    0xc0000001],
                  [1.9999999403953552, 0x40000000],
                  [-math.inf, 0xff800000],
                  [math.inf,  0x7f800000],
                  [math.nan,  0x7fffffff]]
        
        for v in values:
            sp = v[0]
            ie =v[1]
            
            c_ie = py4hw.helper.FloatingPointHelper.sp_to_ieee754(sp)
            assert('{:08X}'.format(ie) == '{:08X}'.format(c_ie))
            
            c_sp = py4hw.helper.FloatingPointHelper.ieee754_to_sp(ie)
            if (sp == 0):
                assert(sp == c_sp)
            elif (math.isinf(sp)):
                assert(sp == c_sp)
            elif (math.isnan(sp)):
                assert(math.isnan(c_sp))
            else:
                assert(abs(sp - c_sp)/max(abs(sp), abs(c_sp)) < 1e-7)

        print('test_sp_conversion complete')

    def test_dp_conversion(self):
        print('test_dp_conversion')
    
        # this is a list of pairs of double precision floating point and its ieee 754 representation value
        values = [[0.0, 0x00000000],
                  [5.0000000000000000e-324, 0x0000000000000001],
                  [5.562684646268003e-309, 0x0004000000000000],
                  [1.112536929253601e-308, 0x0008000000000001],
                  [2.0000000000000004,     0x4000000000000001],
                  [-2.0000000000000004,    0xc000000000000001],
                  [2.0,                    0x4000000000000000],
                  # [math.nan,            0x7ff7ffffffffffff],
                  [math.inf,            0x7ff0000000000000],
                  [-math.inf,           0xfff0000000000000]]
        
        for v in values:
            dp = v[0]
            ie =v[1]
            
            print('Testing ', dp)
            
            c_ie = py4hw.helper.FloatingPointHelper.dp_to_ieee754(dp)
            assert('{:016X}'.format(ie) == '{:016X}'.format(c_ie))
            
            c_dp = py4hw.helper.FloatingPointHelper.ieee754_to_dp(ie)
            if (dp == 0):
                assert(dp == c_dp)
            elif (math.isinf(dp)):
                assert(dp == c_dp)
            else:
                assert(abs(dp - c_dp)/max(abs(dp), abs(c_dp)) < 1e-7)

        print('test_dp_conversion complete')            

    def test_floating_point(self):
        import random
        import math

        print('big range')
        
        # special case for zero
        sp = 0
        sp = sp * math.pow(10, int(random.uniform(0, 37)))
        
        print('sp=', sp)
        ie = py4hw.helper.FloatingPointHelper.sp_to_ieee754(sp)
        sp2 = py4hw.helper.FloatingPointHelper.ieee754_to_sp(ie)

        assert(sp == sp2)
        
        for i in range(100):
            sp = random.uniform(-1, 1)
            sp = sp * math.pow(10, int(random.uniform(0, 37)))
            #print('sp=', sp)

            ie = py4hw.helper.FloatingPointHelper.sp_to_ieee754(sp)
            sp2 = py4hw.helper.FloatingPointHelper.ieee754_to_sp(ie)
            diff = abs(sp - sp2)/abs(sp)
            #print('DIFF:', diff)
            assert(diff < 1e-7)
            
    def test_fp_2(self):
        import math
        import random
        fp = py4hw.helper.FloatingPointHelper()
        
        large = math.pow(2,30)
        max_error = 40

        print('big range')

        for i in range(100):
            av = random.uniform(-large, large)            
            rav = fp.ieee754_stored_internally(av)

            s,e,m = fp.sp_to_ieee754_parts(av)
            iv = fp.ieee754_parts_to_sp(s, e, m)
           
            #print('initial:',av, 'adjusted:', rav, 'diff:', abs(av-rav))
            
            assert(abs(av-rav) < max_error)
        #print('parts {:01b}-{:08b}-{:023b}'.format( s, e, m))        
        #print('recomposed', iv)
        
        
    def test_FPNum(self):
        from py4hw.helper import FPNum
        
        print()
        dp_data = [0x400921FB53C8D4F1, 0x4005BF0A89F1B0DD]
        
        for xa in dp_data:
            a = FPNum(xa, 'dp')
            nxa = a.convert('dp')

            print('checking dp {:016X} = {:016X}'.format(xa, nxa))    
            assert(xa == nxa)

        sp_data = [0x400001a3, 0x0000d959]

        for xa in sp_data:
            a = FPNum(xa, 'sp')
            nxa = a.convert('sp')

            print('checking sp {:016X} = {:016X}'.format(xa, nxa))    
    
            assert(xa == nxa)
            
    def test_FPNum_to_float(self):
        from py4hw.helper import FPNum
        
        print()
        dp_data = [10.0]

        for item in dp_data:
            
            r = FPNum(item)
            print('checking sp {} = {}'.format(item, r.to_float))        
            assert(item == r.to_float())

    def test_FPNum_mul(self):
        from py4hw.helper import FPNum
        sp_data = [(0x3F800000, 0x40200000, 0x40600000)]

        for item in sp_data:
            xa,xb,xe = item
            
            a = FPNum(xa, 'sp')
            b = FPNum(xb, 'sp')
            r = a.mul(b)
            xr = r.convert('sp')
            
            print('checking mul sp {:016X} = {:016X}'.format(xr, xe), r.to_float())        
            assert(xr == xe)

    def test_FPNum_fma(self):
        from py4hw.helper import FPNum
        sp_data = [(0x3F800000, 0x40200000, 0x3F800000, 0x40600000)]

        for item in sp_data:
            xa,xb,xc,xe = item
            
            a = FPNum(xa, 'sp')
            b = FPNum(xb, 'sp')
            c = FPNum(xc, 'sp')
            r = a.mul(b)
            r = r.add(c)
            xr = r.convert('sp')
            
            print('checking fma sp {:016X} = {:016X}'.format(xr, xe), r.to_float())        
            assert(xr == xe)
        
    def test_FPNum_add(self):
        from py4hw.helper import FPNum
        
        print()
        dp_data = [(0x400921FB53C8D4F1, 0x4005BF0A89F1B0DD, 0x401BB841776EA173)]

        for item in dp_data:
            xa,xb,xe = item
            
            a = FPNum(xa, 'dp')
            b = FPNum(xb, 'dp')
            r = a.add(b)
            xr = r.convert('dp')
            
            print('checking add dp {:016X} = {:016X}'.format(xr, xe), r.to_float())        
            assert(xr == xe)
            
            


    def test_FPNum_sub(self):
        from py4hw.helper import FPNum
        
        print()
        dp_data = [(0x400921FB53C8D4F1, 0x4005BF0A89F1B0DD, 0x3FD6C5E193AE4828)]
    
        for item in dp_data:
            xa,xb,xe = item
            
            a = FPNum(xa, 'dp')
            b = FPNum(xb, 'dp')
            r = a.sub(b)
            xr = r.convert('dp')
            
            print('checking sub sp {:016X} = {:016X}'.format(xr, xe), r.to_float())        
            assert(xr == xe)

    def test_FPNum_div2(self):
        from py4hw.helper import FPNum
        
        print()
        dp_data = [(4.0, 1, 2.0),
                   (10.0, 2, 2.5),]

        for item in dp_data:
            a,b,e = item
            
            a = FPNum(a)
            r = a.div2(b)
            r = r.to_float()
            
            print('checking div2 sp {} = {}'.format(r, e))        
            assert(r == e)
        
if __name__ == '__main__':
#    pytest.main(args=['-s', '-q', 'Test_Helper.py'])
    pytest.main(args=['-s', 'Test_Helper.py'])