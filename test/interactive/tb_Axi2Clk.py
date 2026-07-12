# -*- coding: utf-8 -*-
"""
Created on Sat Jun 27 18:13:24 2026

@author: dcr
"""

import py4hw
from py4hw.logic.bus.axi import *
from py4hw.emulation.vitiswrapping import Axi2Clk

sys = py4hw.HWSystem()

# Create signals

ap_start = sys.wire("ap_start", 1)
ap_reset = sys.wire("ap_reset", 1)
ap_done = sys.wire("ap_done")
clk_out = sys.wire("clk_out", 1)
load_outs = sys.wire("load_outs", 1)
active = sys.wire("active", 1)

# Create AXI stream interface
stream = AXI4StreamInterface(sys, "stream", dw=64)

# Instantiate DUT
dut = Axi2Clk(sys, "axi2reg",  ap_start, ap_reset, ap_done, stream, clk_out, load_outs, active)

py4hw.Sequence(sys, 'ap_start', [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], ap_start)
py4hw.Sequence(sys, 'ap_reset', [1, 0], ap_reset, once=True)
py4hw.Sequence(sys, 'ap_done', [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  0, 0, 0,  1, 0, 0, 0, 0], ap_done)
py4hw.Sequence(sys, 'tvalid', [0, 0, 1, 0, 0, 0, 0], stream.tvalid)
py4hw.Sequence(sys, 'tdata', [0, 1, 2, 3, 4], stream.tdata)

wvf = py4hw.Waveform(sys, 'wvf', [ap_start, ap_reset, ap_done,  stream.tvalid, stream.tready, stream.tdata,  dut._wires['clk_count'], clk_out, load_outs, active])


#py4hw.gui.Workbench(sys)


sys.getSimulator().clk(30)

wvf.gui()
