# -*- coding: utf-8 -*-
"""
Created on Mon Dec  4 20:09:45 2023

@author: dcr
"""

import py4hw
import py4hw.debug
import pytest
import py4hw.external.intel as intel

class Test_LPM:

    def test_lpm_counter1(self):
        sys = py4hw.HWSystem()
        
        reset = None
        q = sys.wire('q', 64)
        intel.intel_lpm_counter(sys, 'counter', reset, q)
        
        sim = sys.getSimulator()

        sim.clk(1)
        assert(q.get() == 1)
        sim.clk(1)
        assert(q.get() == 2)
    
    def test_lpm_counter2(self):
        sys = py4hw.HWSystem()
        
        reset = None
        q = sys.wire('q', 64)
        dut = intel.intel_lpm_counter(sys, 'counter', reset, q)
        
        rtl = py4hw.VerilogGenerator(dut)
        
        print(rtl.getVerilog(noInstanceNumber=True))
        
if __name__ == '__main__':
    pytest.main(args=['-s', 'Test_LPM.py'])