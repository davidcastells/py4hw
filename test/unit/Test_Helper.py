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
            
if __name__ == '__main__':
    pytest.main(args=['-s', '-q', 'Test_Helper.py'])