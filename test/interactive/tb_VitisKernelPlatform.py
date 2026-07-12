# -*- coding: utf-8 -*-
"""
Created on Sun Jun 28 14:53:46 2026

@author: 2016570
"""

import py4hw
from py4hw.logic.bus.axi import *
from py4hw.emulation.vitiswrapping import *

hw = VitisRTLKernel()

# Create signals

ap_start = hw.wire("ap_start", 1)
ap_reset = hw.wire("ap_reset", 1)
ap_done = hw.wire("ap_done")
ap_ready = hw.wire("ap_ready")
ap_idle = hw.wire("ap_idle")

inc = hw.wire("inc")
q = hw.wire("q", 64)
loaded = hw.wire("loaded", 1)
load_outs = hw.wire("load_outs", 1)
sent = hw.wire("sent", 1)
clk_out = hw.wire('clk_out')

axi2clk_active = hw.wire("axi2clk_active", 1)
axi2reg_active = hw.wire("axi2reg_active", 1)
reg2axi_active = hw.wire("reg2axi_active", 1)

# Create AXI stream interface
clk_stream = AXI4StreamInterface(hw, "clk_stream", dw=64, has_tkeep=True, has_tlast=True)
in_stream = AXI4StreamInterface(hw, "in_stream", dw=64, has_tkeep=True, has_tlast=True)
out_stream = AXI4StreamInterface(hw, "out_stream", dw=64, has_tkeep=True, has_tlast=True)

reset = hw.wire('reset')
py4hw.Constant(hw, 'reset', 0, reset)

# Instantiate DUT
dut = py4hw.Counter(hw, 'count', reset, inc=inc, q=q)
dut.clockDriver = py4hw.ClockDriver(name='clk_dut', base=hw.clockDriver, wire=clk_out, enable=clk_out)

axi2clk = Axi2Clk(hw, 'axi2clk',  ap_start, ap_reset, ap_done, clk_stream, clk_out, load_outs, axi2clk_active)
axi2reg = Axi2Reg(hw, "axi2reg",  ap_start, ap_reset, ap_done, in_stream, inc, loaded, axi2reg_active)

reg2axi = Reg2Axi(hw, "reg2axi", ap_start, ap_reset, ap_done, load_outs, q, out_stream, sent, reg2axi_active)


VitisKernelFSM(hw, 'kernel_fsm', ap_start, ap_reset, ap_done, ap_idle, ap_ready, load_outs, sent)

py4hw.Sequence(hw, 'ap_start', [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], ap_start)
py4hw.Sequence(hw, 'ap_reset', [1, 0], ap_reset, once=True)

py4hw.Sequence(hw, 'in_tvalid', [0, 0, 1, 0, 0, 0, 0], in_stream.tvalid)
py4hw.Sequence(hw, 'in_tdata', [1], in_stream.tdata)
py4hw.Sequence(hw, 'clk_tvalid', [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], clk_stream.tvalid)
py4hw.Sequence(hw, 'clk_tdata', [ 1], clk_stream.tdata)
py4hw.Sequence(hw, 'out_tready', [0, 0, 0, 0, 0, 1], out_stream.tready)

wvf = py4hw.Waveform(hw, 'wvf', [ap_start, ap_reset, ap_done, ap_idle, ap_ready, 
                                 clk_stream.tvalid, clk_stream.tready, clk_stream.tdata,
                                 in_stream.tvalid, in_stream.tready, in_stream.tdata, 
                                 inc, q,
                                 loaded, 
                                 sent,
                                 load_outs, clk_out,
                                 axi2clk_active,
                                 axi2reg_active,
                                 reg2axi_active])


#py4hw.gui.Workbench(hw)

hw.getSimulator().clk(40)
wvf.gui()


rtl = py4hw.VerilogGenerator(hw)

verilog = rtl.getVerilogForHierarchy(axi2clk)