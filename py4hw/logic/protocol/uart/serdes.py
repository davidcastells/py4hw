# -*- coding: utf-8 -*-
"""
Created on Thu Oct  3 16:20:56 2024

@author: 2016570
"""

from py4hw.base import *

class UARTSerializer(Logic):
    def __init__(self, parent, name, ready, valid, v, uart_clock_posedge, tx):
        super().__init__(parent, name)
        
        self.valid = self.addIn('valid', valid)
        self.ready = self.addOut('ready', ready)
        
        self.v = self.addIn('v', v)
        
        self.uart_clock_posedge = self.addIn('uart_clock_posedge', uart_clock_posedge)
        self.tx = self.addOut('tx', tx)
        
        self.state = 0 # IDLE
        self.count = 0
        self.txv = 0
        
    def clock(self):
        if (self.state == 0): # IDLE
            self.tx.prepare(1) # In UART 
            self.ready.prepare(1)
            self.state = 1
            
        elif (self.state == 1): # READY
            if (self.valid.get()):
                self.state = 2 # start
                self.ready.prepare(0)
                self.txv = self.v.get()
        
        elif (self.state == 2): # WAIT clock
            if (self.uart_clock_posedge.get()):
                self.state = 3
                
        elif (self.state == 3): # START
            self.tx.prepare(0)
            self.count = 7
            
            if (self.uart_clock_posedge.get()):
                self.state = 4; # regular bit
            
        elif (self.state == 4): # REGULAR BIT
            self.tx.prepare(self.txv & 0x1)
            
            if (self.uart_clock_posedge.get()):
                self.txv = (self.txv >> 1) 
                
                if (self.count == 0):
                    self.state = 5 # STOP BIT
                else:
                    self.count -= 1
            
        elif (self.state == 5):
            self.tx.prepare(1)
            
            if (self.uart_clock_posedge.get()):
                self.state = 0
                
class UARTDeserializer(Logic):
    # WARNING @todo this is wrong, wire order is LSB first, 
    # idle wire state is 1, and start bit is zero
    def __init__(self, parent, name, rx, rx_sample, ready, valid, v, clock_desync):
        super().__init__(parent, name)
        
        self.rx = self.addIn('rx', rx)
        self.ready = self.addIn('ready', ready)
        self.valid = self.addOut('valid', valid)
        self.v = self.addOut('v', v)
        
        self.rx_sample = self.addIn('rx_sample', rx_sample)
        self.clock_desync = self.addOut('clock_desync', clock_desync)
        
        self.state = 0
        self.count = 0
        
    def clock(self):
        if (self.state == 0): # IDLE
            self.valid.prepare(0)
            self.count = 0
            self.clock_desync.prepare(0)
            #self.v.prepare(0)
            
            if (self.rx_sample.get() and (self.rx.get() == 0)):
                self.state = 2 # START BIT, now go to Regular
                self.v.prepare(0)
                
        elif (self.state == 1): # START BIT
            if (self.rx_sample.get()):
                self.state = 2 # REGULAR BIT
                self.count = 0
        elif (self.state == 2): # REGULAR BIT
            if (self.rx_sample.get()):
                if (self.count == 8):
                    self.state = 3
                else:
                    self.v.prepare(self.v.get() << 1 | self.rx.get())
                    print('incorporating', self.rx.get(), 'to V ', self.v.next)
                    self.count += 1
        elif (self.state == 3): # STOP BIT
            if (self.rx_sample.get()):
                self.state = 4
        elif (self.state == 4):
            if (self.ready.get()):
                self.state = 5
                self.valid.prepare(1)
        elif (self.state == 5):
            self.state = 0
            self.valid.prepare(0)
            self.clock_desync.prepare(1)