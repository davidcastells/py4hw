# -*- coding: utf-8 -*-
"""
Created on Thu Jul 21 12:20:28 2022

@author: dcr
"""

import py4hw
import pytest
import math
from py4hw.helper import FPNum
from py4hw.helper import IEEE754_HP_PRECISION
from py4hw.helper import IEEE754_SP_PRECISION
from py4hw.helper import IEEE754_DP_PRECISION

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
        data = [('hp', 0x4000),
                ('sp', 0x3F800000),
                ('sp', 0x400001a3),
                ('sp', 0x0000d959),
                ('dp', 0x400921FB53C8D4F1),
                ('dp', 0x4005BF0A89F1B0DD)]
        
        for item in data:
            fmt, xa = item
            a = FPNum(xa, fmt)
            nxa = a.convert(fmt)

            print('checking {} {:016X} = {:016X}'.format(fmt, xa, nxa))    
            assert(xa == nxa)

    def test_FPNum_convert(self):
        from py4hw.helper import FPNum
        
        print()
        data = [('hp', 2, 0x4000),
                ('hp', 0x80002002, 0x7c00),
                ('sp', 1, 0x3F800000),
                ('sp', 2.0000998973846436, 0x400001a3),
                ('sp', 7.797e-41, 0x0000d959),
                ('dp', 3.14159265, 0x400921FB53C8D4F1),
                ('dp', 2.71828182, 0x4005BF0A89F1B0DD)]
        
        for item in data:
            fmt, xa, xb = item
            a = FPNum(xa)
            nxb = a.convert(fmt)

            print('checking convert {} = {:016X} exp: {:016X}'.format(fmt, nxb, xb))    
            assert(xb == nxb)
            
    def test_FPNum_to_float(self):
        from py4hw.helper import FPNum
        
        print()
        dp_data = [1.0, 2.0, 10.0]

        for item in dp_data:
            
            r = FPNum(item)
            print('checking sp {} = {}'.format(item, r.to_float))        
            assert(item == r.to_float())

    def test_FPNum_mul(self):
        sp_data = [(0x3F800000, 0x40200000, 0x40200000)]

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
        data = [('f', 2.9999999999998197 , 3.0000000000001803, 6.0), 
                ('hp', 0x4100, 0x3C00, 0x4300),
                ('sp', 0xC49A6333, 0x3F8CCCCD, 0xC49A4000),
                ('dp', 0x400921FB53C8D4F1, 0x4005BF0A89F1B0DD, 0x40177082eedd42e7)]

        for item in data:
            fmt, xa,xb,xe = item
            
            if (fmt == 'f'):
                a = FPNum(xa)
                b = FPNum(xb)
                e = FPNum(xe)
                r = a.add(b)
                
                assert(r.to_float() == e.to_float())
            else:
                a = FPNum(xa, fmt)
                b = FPNum(xb, fmt)
                e = FPNum(xe, fmt)
                
                if (fmt == 'hp'):
                    a.reducePrecision(10)
                    b.reducePrecision(10)
                    e.reducePrecision(10)
                elif (fmt == 'sp'):
                    a.reducePrecision(23)
                    b.reducePrecision(23)
                    e.reducePrecision(23)
                
                r = a.add(b)
                
                if (fmt == 'hp'):
                    r.reducePrecisionWithRounding(10)
                elif (fmt == 'sp'):
                    r.reducePrecisionWithRounding(23)
                elif (fmt == 'dp'):
                    r.reducePrecisionWithRounding(52)
                    
                xr = r.convert(fmt)
                
                print('checking add {} {:016X} = {:016X}'.format(fmt, xr, xe), r.to_float())        
                assert(xr == xe)
            


    def test_FPNum_sub(self):
        print()
        dp_data = [('hp', 0x7C00, 0x7C00, 0x7E00),
                   ('dp', 0x400921FB53C8D4F1, 0x4005BF0A89F1B0DD, 0x3fdb17864eb920a0),
                   ('dp', 0x4005BF0A89F1B0DD, 0x400921FB53C8D4F1, 0xbfdb17864eb920a0)]
    
        for item in dp_data:
            fmt, xa,xb,xe = item
            
            if (fmt == 'f'):
                a = FPNum(xa)
                b = FPNum(xb)
                e = FPNum(xe)
                r = a.sub(b)
                
                assert(r.to_float() == e.to_float())
            else:
                a = FPNum(xa, fmt)
                b = FPNum(xb, fmt)
                e = FPNum(xe, fmt)
                
                if (fmt == 'hp'):
                    a.reducePrecision(IEEE754_HP_PRECISION)
                    b.reducePrecision(IEEE754_HP_PRECISION)
                    e.reducePrecision(IEEE754_HP_PRECISION)
                elif (fmt == 'sp'):
                    a.reducePrecision(IEEE754_SP_PRECISION)
                    b.reducePrecision(IEEE754_SP_PRECISION)
                    e.reducePrecision(IEEE754_SP_PRECISION)
                
                r = a.sub(b)
                
                if (fmt == 'hp'):
                    r.reducePrecisionWithRounding(IEEE754_HP_PRECISION)
                elif (fmt == 'sp'):
                    r.reducePrecisionWithRounding(IEEE754_SP_PRECISION)
                elif (fmt == 'dp'):
                    r.reducePrecisionWithRounding(IEEE754_DP_PRECISION)
                    
                xr = r.convert(fmt)
                
                print('checking add {} {:016X} = {:016X}'.format(fmt, xr, xe), r.to_float())        
                assert(xr == xe)

    def test_FPNum_div(self):
        from py4hw.helper import FPNum
        
        print()
        data = [('f', 2.9999999999998197 , 3.0000000000001803, 0.9999999999998798), 
                ('f', 2.0, 32.0, 0.0625),
                ('sp', 0xC49A6333, 0x3F8CCCCD, 0xC48C5A2E),
                ('dp', 0x400921FB53C8D4F1, 0x4005BF0A89F1B0DD, 0x3FF27DDBF6C383EC)]
    
        for item in data:
            fmt, xa,xb,xe = item
            
            if (fmt == 'f'):
                a = FPNum(xa)
                b = FPNum(xb)
                e = FPNum(xe)
                r = a.div(b)
                
                print('checking div {} {} = {}'.format(fmt, r.to_float(), e.to_float()))        
                assert(r.to_float() == e.to_float())
            else:
                a = FPNum(xa, fmt)
                b = FPNum(xb, fmt)
                e = FPNum(xe, fmt)
                
                if (fmt == 'sp'):
                    a.reducePrecision(23)
                    b.reducePrecision(23)
                    e.reducePrecision(23)
                
                r = a.div(b)
                
                if (fmt == 'sp'):
                    r.reducePrecisionWithRounding(23)
                elif (fmt == 'dp'):
                    r.reducePrecisionWithRounding(52)
                    
                xr = r.convert(fmt)
                
                print('checking div {} {:016X} = {:016X}'.format(fmt, xr, xe), r.to_float())        
                assert(xr == xe)
            
    def test_FPNum_sqrt(self):
        from py4hw.helper import FPNum
        
        print()
        data = [('f', 4 , 2), 
                ('f', 81, 9),
                ('sp', 0x40490FDB, 0x3FE2DFC5),
                ('sp', 0x461C4000, 0x42C80000),
                ('dp', 0x400921FB53C8D4F1, 0x3FFC5BF8916F587B)]
        
        
    
        for item in data:
            fmt, xa,xe = item
            
            if (fmt == 'f'):
                a = FPNum(xa)
                e = FPNum(xe)
                r = a.sqrt()
                
                print('checking sqrt {} {} = {}'.format(fmt, r.to_float(), e.to_float()))        
                assert(r.to_float() == e.to_float())
            else:
                a = FPNum(xa, fmt)
                e = FPNum(xe, fmt)
                
                if (fmt == 'sp'):
                    a.reducePrecision(23)
                    e.reducePrecision(23)
                
                r = a.sqrt()
                
                if (fmt == 'sp'):
                    r.reducePrecisionWithRounding(23)
                elif (fmt == 'dp'):
                    r.reducePrecisionWithRounding(52)
                    
                xr = r.convert(fmt)
                
                print('checking sqrt {} {:016X} = {:016X}'.format(fmt, xr, xe), r.to_float())        
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
        
    def test_FPNum_compare(self):
        print()
        dp_data = [('hp', 0x7C00, 0x7C00, 0),
                   ('sp', 0xFF800000, 0x40400000, -1),
                   ('dp', 0x400921FB53C8D4F1, 0x4005BF0A89F1B0DD, 1),
                   ('dp', 0x4005BF0A89F1B0DD, 0x400921FB53C8D4F1, -1),
                   ('dp', 0xFFFFFFFFFFFFBD7B, 0xFFFFFFFFFFFFBD71, -1)]
    
        for item in dp_data:
            fmt, xa,xb,e = item
            
            if (fmt == 'f'):
                a = FPNum(xa)
                b = FPNum(xb)
                
                r = a.compare(b)
                
                assert(r == e)
            else:
                a = FPNum(xa, fmt)
                b = FPNum(xb, fmt)
                
                if (fmt == 'hp'):
                    a.reducePrecision(IEEE754_HP_PRECISION)
                    b.reducePrecision(IEEE754_HP_PRECISION)
                elif (fmt == 'sp'):
                    a.reducePrecision(IEEE754_SP_PRECISION)
                    b.reducePrecision(IEEE754_SP_PRECISION)
                
                r = a.compare(b) 
                
                print('checking compare {} {} with {} = {} exp:{}'.format(fmt, a.to_float(), b.to_float(), r, e))        
                assert(r == e)
                
if __name__ == '__main__':
#    pytest.main(args=['-s', '-q', 'Test_Helper.py'])
    pytest.main(args=['-s', 'Test_Helper.py'])