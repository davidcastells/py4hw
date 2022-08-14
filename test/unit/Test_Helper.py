# -*- coding: utf-8 -*-
"""
Created on Thu Jul 21 12:20:28 2022

@author: dcr
"""

import py4hw
import pytest

class Test_Helper:

    def test_integrity(self):

        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 2)
        r = sys.wire("r", 1)
        
        py4hw.Constant(sys, "a", 0, a)
        
        eq = py4hw.EqualConstant(sys, 'equal', a, 0, r)
        
        wl = py4hw.helper.CircuitAnalysis.getAllPortWires(eq)
        
        assert(len(wl) == 2)

        for w in wl:
            print(w.getFullPath())
            
    def test_floating_point(self):
        import random
        import math
        
        # special case for zero
        sp = 0
        sp = sp * math.pow(10, int(random.uniform(0, 37)))
        ie = py4hw.helper.FloatingPointHelper.sp_to_ieee754(sp)
        sp2 = py4hw.helper.FloatingPointHelper.ieee754_to_sp(ie)

        assert(sp == sp2)
        
        for i in range(1000):
            sp = random.uniform(-1, 1)
            sp = sp * math.pow(10, int(random.uniform(0, 37)))
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

        for i in range(1000):
            av = random.uniform(-large, large)            
            rav = fp.ieee754_stored_internally(av)

            s,e,m = fp.sp_to_ieee754_parts(av)
            iv = fp.ieee754_parts_to_sp(s, e, m)
           
            #print('initial:',av, 'adjusted:', rav, 'diff:', abs(av-rav))
            
            assert(abs(av-rav) < max_error)
        #print('parts {:01b}-{:08b}-{:023b}'.format( s, e, m))        
        #print('recomposed', iv)
        
        
            
if __name__ == '__main__':
    pytest.main(args=['-s', '-q', 'Test_Helper.py'])