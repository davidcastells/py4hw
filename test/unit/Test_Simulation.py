# -*- coding: utf-8 -*-
"""
Created on Sat Jul 30 06:41:37 2022

@author: dcr
"""

import py4hw
import py4hw.debug

import pytest

class Test_Debug:

    
    def test_integrity(self):
        sys = py4hw.HWSystem()

        a = sys.wire("a", 32)
        b = sys.wire("b", 32)
        c = sys.wire("c", 32)
        r1 = sys.wire("r1", 32)
        r2 = sys.wire("r2", 32)
        r3 = sys.wire("r3", 32)

        py4hw.And2(sys, "and1", a, b, r1)
        py4hw.And2(sys, "and2", a, c, r2)
        py4hw.And2(sys, "and3", b, c, r3)
        
        py4hw.Constant(sys, "a", 0xF, a)
        py4hw.Constant(sys, "b", 0xA, b)
        py4hw.Constant(sys, "c", 0x5, c)
        
        py4hw.Scope(sys, "r1 (0xF & 0xA)", r1)
        py4hw.Scope(sys, "r2 (0xF & 0x5)", r2)
        py4hw.Scope(sys, "r3 (0xA & 0x5)", r3)

        py4hw.debug.checkIntegrity(sys)
