# -*- coding: utf-8 -*-
"""
Created on Tue Feb  1 23:45:20 2022

@author: dcr
"""

import py4hw
import py4hw.debug

import pytest

class Test_Select:

    
    def test_integrity(self):
        sys = py4hw.HWSystem()

        a = sys.wire("a", 32)
        b = sys.wire("b", 32)
        c = sys.wire("c", 32)
        sa = sys.wire("sa")
        sb = sys.wire("sb")
        sc = sys.wire("sc")
        r = sys.wire("r", 32)
        
        
        py4hw.Sequence(sys, "a", [1,2,3], a)
        py4hw.Sequence(sys, "b", [1,2,3], b)
        py4hw.Sequence(sys, "c", [1,2,3], c)
        py4hw.Sequence(sys, "sa", [1,0,0], sa)
        py4hw.Sequence(sys, "sb", [0,1,0], sb)
        py4hw.Sequence(sys, "sc", [0,0,1], sc)
        
        py4hw.Select(sys, 'select', [sa,sb,sc], [a,b,c], r)
        
        py4hw.debug.checkIntegrity(sys)


if __name__ == '__main__':
    pytest.main(args=['-q', 'Test_Select.py'])