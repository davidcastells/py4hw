#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  6 15:29:04 2023

@author: dcr
"""

import math
import py4hw

import py4hw.external.platforms as plt

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
        
        self.debugState = self.addOut('debug_state', self.wire('debug_state', 8))
        
    def clock(self):
        self.debugState.prepare(self.state)
        
        if (self.reset.get() == 1):
            self.state = 0
            self.start.prepare(0)
            self.device_address.prepare(0)
            self.register_address.prepare(0)
            self.data.prepare(0)
        else:
            if (self.state == 0):
                self.device_address.prepare(0x34)
                self.register_address.prepare(0<<1)
                self.data.prepare(0b00010111)
                self.start.prepare(1)
                self.after_done = 1
                self.state = 100
            elif (self.state == 1):
                self.device_address.prepare(0x34)
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
                self.error.prepare(1)
                self.done.prepare(1)
                
class WM8731Init(py4hw.Logic):
    def __init__(self, parent, name, reset, i2c_scl, i2c_sda_in, i2c_sda_out, i2c_sda_oe, error, done):
        super().__init__(parent, name)
        
        self.reset = self.addIn('reset', reset)
        self.i2c_sda_in = self.addIn('i2c_sda_in', i2c_sda_in)
        self.i2c_sda_out = self.addOut('i2c_sda_out', i2c_sda_out)
        self.i2c_sda_oe = self.addOut('i2c_sda_oe', i2c_sda_oe)
        self.i2c_scl = self.addOut('i2c_scl', i2c_scl)
        self.error = self.addOut('error', error)
        self.done = self.addOut('done', done)
        
        device_address = self.wire('dev_address', 8)
        register_address = self.wire('reg_address', 8)
        data = self.wire('data', 8)
        start = self.wire('start')
        busy = self.wire('busy')
        #error = self.wire('error')
        
        WM8731InitSequencer(self, 'seq', reset, device_address, register_address, data, start, busy, self.error, self.done)
        
        py4hw.logic.protocol.i2c.I2CMaster.I2CMasterWriter(self, 'i2c_master', reset, device_address, register_address, data, start, busy, 
                        error, i2c_sda_in, i2c_sda_out, i2c_sda_oe, i2c_scl)
        
        
sys = plt.DE1SoC()


py4hw.gui.Workbench(sys)
