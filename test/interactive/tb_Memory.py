# -*- coding: utf-8 -*-
"""
Created on Fri Mar 28 18:48:37 2025

@author: 2016570
"""

from py4hw.base import *
from py4hw.logic import *
import py4hw.debug
import py4hw.gui
import py4hw.schematic

hw = HWSystem()

address = hw.wire("address", 8)
write = hw.wire("write")
readdata_async = hw.wire("readdata_async", 32)
readdata_sync = hw.wire("readdata_sync", 32)
readdata_sync_a = hw.wire("readdata_sync_a", 32)
readdata_sync_b = hw.wire("readdata_sync_b", 32)
writedata = hw.wire("writedata", 32)

Sequence(hw, "address", [1, 2, 3, 4, 5, 6, 7, 8], address)
Sequence(hw, "write",  [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0], write)
Sequence(hw, "writedata", [0X1001, 0X1002, 0X1003, 0X1004, 0X1005, 0X1006, 0X1007, 0X1008], writedata)

async_mem = py4hw.AsynchronousMemory(hw, 'async_mem', address, address, write, readdata_async, writedata)

wvf = py4hw.Waveform(hw, 'wvf', [address,  write, writedata, readdata_async])

hw.getSimulator().clk(20)

#◙wvf.gui()


rtl = py4hw.VerilogGenerator(async_mem)

print(rtl.getVerilogForHierarchy())


sync_mem = py4hw.SynchronousMemory(hw, 'sync_mem', address, address, write, readdata_sync, writedata)

rtl = py4hw.VerilogGenerator(sync_mem)

print(rtl.getVerilogForHierarchy())

dp_sync_mem = py4hw.DualPortSynchronousMemory(hw, 'dp_sync_mem', address, address, write, readdata_sync_a, writedata,
                                              address, address, write, readdata_sync_b, writedata)

rtl = py4hw.VerilogGenerator(dp_sync_mem)

print(rtl.getVerilogForHierarchy())
