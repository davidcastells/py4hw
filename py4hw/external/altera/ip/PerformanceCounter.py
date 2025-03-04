# -*- coding: utf-8 -*-
"""
Created on Wed Jan 29 15:17:55 2025

@author: 2016570
"""
import py4hw

class PerformanceCounter(py4hw.Logic):
    
    def __init__(self, parent, name, reset, chipselect, address, read, write, writedata, readdata):
        
        super().__init__(parent, name)
        
        self.addIn('reset', reset)
        self.addIn('chipselect', chipselect)
        self.addIn('address', address)
        self.addIn('read', read)
        self.addIn('write', write)
        self.addIn('writedata', writedata)
        self.addOut('readdata', readdata)
        
        bit0 = self.wire('bit0')
        
        py4hw.Bit(self, 'add0', address, 0, bit0)
        
        
        counter = self.wire('counter', 64)
        one = self.wire('one')
        
        py4hw.Constant(self, 'one', 1, one)
        py4hw.Counter(self, 'counter', reset, one, counter)
        
        counter_low = self.wire('counter_low', 32)
        counter_high = self.wire('counter_high', 32)
        
        py4hw.Range(self, 'counter_low', counter, 31, 0, counter_low)
        py4hw.Range(self, 'counter_high', counter, 63, 32, counter_high)
        
        py4hw.Mux2(self, 'mux', bit0, counter_low, counter_high, readdata)
        
        
def generateVerilog():
    
    hw = py4hw.HWSystem()
    
    reset = hw.wire('reset')
    chipselect = hw.wire('chipselect')
    address = hw.wire('address', 2)
    read = hw.wire('read')
    write = hw.wire('write')
    writedata = hw.wire('writedata', 32)
    readdata = hw.wire('readdata', 32)
    
    perf = PerformanceCounter(hw, 'counter', reset, chipselect, address, read, write, writedata, readdata)
    
    rtl = py4hw.VerilogGenerator(perf)
    
    return rtl.getVerilogForHierarchy()
    