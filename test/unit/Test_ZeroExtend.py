# -*- coding: utf-8 -*-
"""
Created on Sat Jan 22 14:23:08 2022

@author: dcr
"""

import py4hw
import pytest

class Test_ZeroExtend:
    

    def test_verilog_gen(self):
        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 12)
        r = sys.wire("r", 32)
        
        dut = py4hw.ZeroExtend(sys, "zext", a, r)

        rtl = py4hw.VerilogGenerator(dut)
        print(rtl.getVerilogForHierarchy(dut))
        
if __name__ == '__main__':
    pytest.main(args=['-s', 'Test_ZeroExtend.py'])