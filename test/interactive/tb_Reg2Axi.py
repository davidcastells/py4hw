# -*- coding: utf-8 -*-
"""
Created on Thu Jun 25 07:18:47 2026

@author: dcr
"""


import py4hw
from py4hw.logic.bus.axi import *
from py4hw.emulation.vitiswrapping import Reg2Axi

sys = py4hw.HWSystem()

# Create signals

ap_start = sys.wire("ap_start", 1)
ap_reset = sys.wire("ap_reset", 1)
ap_done = sys.wire("ap_done")
reg_in = sys.wire("reg_in", 64)
load_outs = sys.wire("load_outs", 1)
sent = sys.wire("sent", 1)
active = sys.wire("active", 1)

# Create AXI stream interface
stream = AXI4StreamInterface(sys, "stream", dw=64, has_tkeep=True, has_tlast=True)

# Instantiate DUT
dut = Reg2Axi(sys, "reg2axi", ap_start, ap_reset, ap_done, load_outs, reg_in, stream, sent, active)

py4hw.Sequence(sys, 'ap_start', [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], ap_start)
py4hw.Sequence(sys, 'ap_reset', [1, 0], ap_reset, once=True)
py4hw.Sequence(sys, 'ap_done', [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0], ap_done)
py4hw.Sequence(sys, 'reg_in', [ 0, 1, 2, 3, 4], reg_in)
py4hw.Sequence(sys, 'load_outs', [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0], load_outs)
py4hw.Sequence(sys, 'tready', [0, 0, 1, 0, 0, 0, 0], stream.tready)


wvf = py4hw.Waveform(sys, 'wvf', [ap_start, ap_reset, ap_done,  stream.tvalid, stream.tready, stream.tdata, reg_in, load_outs, sent, active])


py4hw.gui.Workbench(sys)
