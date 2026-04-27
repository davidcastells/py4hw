# -*- coding: utf-8 -*-
"""
Created on Fri Apr 17 09:17:17 2026

@author: 2016570
"""
import py4hw
from py4hw.logic.bus.axi import *
from py4hw.emulation.vitiswrapping import Axi2Reg

sys = py4hw.HWSystem()

# Create signals
reset = sys.wire("reset", 1)
ap_start = sys.wire("ap_start", 1)
ap_reset = sys.wire("ap_reset", 1)
q = sys.wire("q", 64)
loaded = sys.wire("loaded", 1)

# Create AXI stream interface
stream = AXI4StreamInterface(sys, "stream", dw=64)

# Instantiate DUT
dut = Axi2Reg(sys, "axi2reg", reset, ap_start, ap_reset, stream, q, loaded)

reset.put(1)
sys.getSimulator().clk(1)

reset.put(0)
sys.getSimulator().clk(1)
                       
assert loaded.get() == 0, 'loaded should be zero'

# Test 1: Capture on valid data
test_data = 0x123456789ABCDEF0
stream.tvalid.put(1)
stream.tdata.put(test_data)

# Give time for signals to propagate
sys.getSimulator().clk(2)

stream.tvalid.put(0)
sys.getSimulator().clk(1)

# Should capture on first cycle with valid data
assert q.get() == test_data, 'unexpected test_data'
assert loaded.get() == 1, 'loaded should be one'

reset.put(1)
sys.getSimulator().clk(1)

py4hw.gui.Workbench(sys)