# -*- coding: utf-8 -*-
"""
Created on Sat Oct 31 11:07:23 2020

@author: dcr
"""
from py4hw.base import *
from py4hw.logic import *
from py4hw.simulation import Simulator
import py4hw.debug

import unittest

class tb_And(unittest.TestCase):

    def test_integrity(self):
        sys = HWSystem()

        a = sys.wire("a", 32)
        b = sys.wire("b", 32)
        c = sys.wire("c", 32)
        r1 = sys.wire("r1", 32)
        r2 = sys.wire("r2", 32)
        r3 = sys.wire("r3", 32)

        And2(sys, "and1", a, b, r1)
        And2(sys, "and2", a, c, r2)
        And2(sys, "and3", b, c, r3)
        
        Constant(sys, "a", 0xF, a)
        Constant(sys, "b", 0xA, b)
        Constant(sys, "c", 0x5, c)
        
        Scope(sys, "r1 (0xF & 0xA)", r1)
        Scope(sys, "r2 (0xF & 0x5)", r2)
        Scope(sys, "r3 (0xA & 0x5)", r3)

        py4hw.debug.checkIntegrity(sys)
        
    def test_1(self):
        sys = HWSystem()

        a = sys.wire("a", 32)
        b = sys.wire("b", 32)
        c = sys.wire("c", 32)
        r1 = sys.wire("r1", 32)
        r2 = sys.wire("r2", 32)
        r3 = sys.wire("r3", 32)

        And2(sys, "and1", a, b, r1)
        And2(sys, "and2", a, c, r2)
        And2(sys, "and3", b, c, r3)
        
        Constant(sys, "a", 0xF, a)
        Constant(sys, "b", 0xA, b)
        Constant(sys, "c", 0x5, c)
        
        Scope(sys, "r1 (0xF & 0xA)", r1)
        Scope(sys, "r2 (0xF & 0x5)", r2)
        Scope(sys, "r3 (0xA & 0x5)", r3)

        sys.getSimulator().clk(1)
        
        self.assertEqual(r1.get(), 10)
        self.assertEqual(r2.get(), 5)
        self.assertEqual(r3.get(), 0)


if __name__ == '__main__':
    unittest.main()