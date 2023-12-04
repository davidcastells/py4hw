#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  6 15:29:04 2023

@author: dcr
"""

import math
import py4hw

import py4hw.external.platforms as plt
from py4hw.logic.protocol.i2c.I2CMaster import I2CMasterWriter

class WM8731InitSequencer(py4hw.Logic):
    def __init__(self, parent, name, reset, device_address, register_address,
                 data, start, busy, error, done):
        super().__init__(parent, name)
        
        self.reset = self.addIn('reset', reset)
        self.device_address = self.addOut('device_address', device_address)
        self.register_address = self.addOut('register_address', register_address)
        self.data = self.addOut('data', data)
        self.start = self.addOut('start', start)
        self.busy = self.addIn('busy', busy)
        self.error = self.addIn('error', error)
        self.done = self.addOut('done', done)
        self.state = 0
        self.after_done = 0
        
        self.debugState = self.addOut('debugState', parent.wire('{}_debug_state'.format(name), 8))
        
    def clock(self):
        self.debugState.prepare(self.state)
        
        WM8731_ADDR = 0x34 >> 1 # 0x34
        
        if (self.reset.get() == 1):
            self.state = 0
            self.start.prepare(0)
            self.device_address.prepare(0)
            self.register_address.prepare(0)
            self.data.prepare(0)
        else:
            if (self.state == 0):
                self.device_address.prepare(WM8731_ADDR)
                self.register_address.prepare(0<<1)
                self.data.prepare(0b00010111)
                self.start.prepare(1)
                self.after_done = 1
                self.state = 100
            elif (self.state == 1):
                self.device_address.prepare(WM8731_ADDR)
                self.register_address.prepare(1<<1)
                self.data.prepare(0b00010111)
                self.start.prepare(1)
                self.after_done = 2
                self.state = 100
            elif (self.state == 100): 
                self.start.prepare(0)
                self.state = 101
            elif (self.state == 101): # wait for not busy
                if (self.busy.get() == 0):
                    # continue
                    self.state = self.after_done
                elif (self.error.get() == 1):
                    self.state = 102 # error
                    
            elif (self.state == 102):
                # ERROR state
                self.done.prepare(1)
                
class WM8731Init(py4hw.Logic):
    def __init__(self, parent, name, reset, 
                 i2c, 
                 error, done):
        super().__init__(parent, name)
        
        self.reset = self.addIn('reset', reset)
        self.i2c = self.addInterfaceSource('i2c', i2c)
        self.error = self.addOut('error', error)
        self.done = self.addOut('done', done)
        
        device_address = self.wire('dev_address', 8)
        register_address = self.wire('reg_address', 8)
        data = self.wire('data', 8)
        start = self.wire('start')
        busy = self.wire('busy')
        #error = self.wire('error')
        
        WM8731InitSequencer(self, 'seq', reset, device_address, register_address, data, start, busy, self.error, self.done)
        
        I2CMasterWriter(self, 'i2c_master', reset, device_address, register_address, data, start, busy, 
                        error, i2c)
        
        
sys = plt.DE1SoC()

i2c = sys.getI2C()
audio = sys.getAudio()

reset = sys.wire('reset')
error = sys.wire('error')
done = sys.wire('done')

key = sys.getInputKey()
py4hw.Bit(sys, 'reset', key, 0, reset)

clk_i2c = sys.wire('clk_i2c')
py4hw.ClockDivider(sys, 'clk_i2c', sys.clockDriver.freq, 200E3, clk_i2c)

py4hw.Buf(sys, 'AUD_XCK', clk_i2c, audio.AUD_XCK)

clk_signal_tap = sys.wire('clk_signal_tap')
py4hw.ClockDivider(sys, 'clk_signal_tap', sys.clockDriver.freq, 400E3, clk_signal_tap)

wm8731 = WM8731Init(sys, 'wm8731',  reset, i2c, error, done)
wm8731.clockDriver = py4hw.ClockDriver('clk_i2c', 200E3, wire=clk_i2c)

py4hw.gui.Workbench(sys)


dir = '/tmp/testDE1SoC'
sys.build(dir)
sys.download(dir)