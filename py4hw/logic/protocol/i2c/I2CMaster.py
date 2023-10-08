# -*- coding: utf-8 -*-
"""
Created on Mon May  1 09:57:04 2023

@author: dcr
"""

from py4hw.base import *

class I2CMasterWriter(Logic):
    def __init__(self, parent, name, reset, dev_address, dev_reg, dev_data, 
                 write_start, write_busy, write_error,
                 i2c):
        super().__init__(parent, name)
        
        self.reset = self.addIn('reset', reset)
        self.write_start = self.addIn('write_start', write_start)
        self.write_busy = self.addOut('write_busy', write_busy)
        self.write_error = self.addOut('write_error', write_error)
        
        self.dev_address = self.addIn('dev_address', dev_address)
        self.dev_reg = self.addIn('dev_reg', dev_reg)
        self.dev_data = self.addIn('dev_data', dev_data)
        
        self.i2c = self.addInterfaceSource('', i2c)
        self.state = 0 # IDLE
        self.v_address = 0
        self.v_reg = 0
        self.v_data = 0
        self.count = 0
        self.debugState = self.addOut('debug_state', self.wire('debug_state', 8))
        
    def clock(self):
        self.debugState.prepare(self.state)
        
        if (self.reset.get() == 1):
            self.state = 0
            self.count = 0
            self.i2c.SCL.prepare(1) 
            self.i2c.SDA_OE.prepare(0) # do not drive sda
            self.write_busy.prepare(0)
            self.write_error.prepare(0)
        else:
            if (self.state == 0):
                if ((self.write_start.get() == 1) and (self.i2c.SDA_IN.get() == 1)):
                    # bus available
                    self.state = 1
                    self.i2c.SCL.prepare(1) 
                    self.i2c.SDA_OE.prepare(1)
                    self.i2c.SDA_OUT.prepare(0)
                    self.v_address = self.dev_address.get()
                    self.v_reg = self.dev_reg.get()
                    self.v_data = self.dev_data.get()
                    self.write_busy.prepare(1)
                    assert(self.v_address < 0x80)
                else:
                    self.write_busy.prepare(0)
            elif (self.state == 1): # ADDRESS LOW
                self.i2c.SCL.prepare(0) 
                self.i2c.SDA_OE.prepare(1)
                self.i2c.SDA_OUT.prepare(self.v_address >> 6)
                self.state = 2
            elif (self.state == 2): # ADDRESS HIGH
                self.i2c.SCL.prepare(1) 
                self.i2c.SDA_OE.prepare(1)
                self.i2c.SDA_OUT.prepare(self.v_address >> 6)
                print('ADD[{}]={}'.format(6-self.count, (self.v_address >> 6) & 1))
                self.v_address = self.v_address << 1
                self.count += 1
                print('count=', self.count)
                if (self.count >= 7):
                    self.state = 3
                else:
                    self.state = 1
            elif (self.state == 3): # OP LOW
                self.i2c.SCL.prepare(0) 
                self.i2c.SDA_OE.prepare(1)
                self.i2c.SDA_OUT.prepare(0)
                self.count = 0
                self.state = 4
            elif (self.state == 4): # OP HIGH
                self.i2c.SCL.prepare(1) 
                self.i2c.SDA_OE.prepare(1)
                self.i2c.SDA_OUT.prepare(0)
                self.count = 0
                self.state = 5
            elif (self.state == 5): # ACK1 LOW
                self.i2c.SCL.prepare(0) 
                self.i2c.SDA_OE.prepare(0)
                self.i2c.SDA_OUT.prepare(0)
                self.state = 6
            elif (self.state == 6): # ACK1 HIGH
                self.i2c.SCL.prepare(1) 
                self.state = 7
            elif (self.state == 7): # ACK CHECK
                self.i2c.SCL.prepare(0) 
                if (self.i2c_sda_in.get()):
                    # NACK
                    self.state = 100 # ERROR
                else:
                    self.i2c.SDA_OE.prepare(1)
                    self.i2c.SDA_OUT.prepare(self.v_reg >> 7)
                    self.count = 0
                    self.state = 9
            elif (self.state == 8): # REG LOW
                self.i2c.SCL.prepare(0) 
                self.i2c.SDA_OE.prepare(1)
                self.i2c.SDA_OUT.prepare(self.v_reg >> 7)
                self.state = 9
            elif (self.state == 9): # REG HIGH
                self.i2c.SCL.prepare(1) 
                self.i2c.SDA_OE.prepare(1)
                self.i2c.SDA_OUT.prepare(self.v_reg >> 7)
                print('REG[{}]={}'.format(7-self.count, (self.v_reg >> 7) & 1))
                self.v_reg = self.v_reg << 1
                self.count += 1
                
                if (self.count >= 8):
                    self.state = 10
                else:
                    self.state = 8
            elif (self.state == 10): # ACK2 LOW
                self.i2c.SCL.prepare(0) 
                self.i2c.SDA_OE.prepare(0)
                self.i2c.SDA_OUT.prepare(0)
                self.state = 11
            elif (self.state == 11): # ACK2 HIGH
                self.i2c.SCL.prepare(1) 
                self.state = 12
            elif (self.state == 12): # ACK2 CHECK
                self.i2c.SCL.prepare(0) 
                if (self.i2c_sda_in.get()):
                    # NACK
                    self.state = 100 # ERROR
                else:
                    self.i2c.SDA_OE.prepare(1)
                    self.i2c.SDA_OUT.prepare(self.v_reg >> 7)
                    self.state = 14
                    self.count = 0
            elif (self.state == 13): # DATA LOW
                self.i2c.SCL.prepare(0) 
                self.i2c.SDA_OE.prepare(1)
                self.i2c.SDA_OUT.prepare(self.v_data >> 7)
                self.state = 14
            elif (self.state == 14): # DATA HIGH
                self.i2c.SCL.prepare(1) 
                self.i2c.SDA_OE.prepare(1)
                self.i2c.SDA_OUT.prepare(self.v_data >> 7)
                print('DATA[{}]={}'.format(7-self.count, (self.v_data >> 7) & 1))
                self.v_data = self.v_data << 1
                self.count += 1
                
                if (self.count >= 8):
                    self.state = 15
                else:
                    self.state = 13
            elif (self.state == 15): # ACK2 LOW
                self.i2c.SCL.prepare(0) 
                self.i2c.SDA_OE.prepare(0)
                self.i2c.SDA_OUT.prepare(0)
                self.state = 16
            elif (self.state == 16): # ACK2 HIGH
                self.i2c.SCL.prepare(1) 
                self.state = 17
            elif (self.state == 17): # ACK2 CHECK
                self.i2c.SCL.prepare(0) 
                if (self.i2c_sda_in.get()):
                    # NACK
                    self.state = 100 # ERROR
                else:
                    self.i2c.SDA_OE.prepare(1)
                    self.i2c.SDA_OUT.prepare(0)
                    self.state = 18
            elif (self.state == 18): # STOP
                self.i2c.SCL.prepare(1) 
                self.i2c.SDA_OE.prepare(1)
                self.i2c.SDA_OUT.prepare(1)
                self.state = 0
                    
            elif (self.state == 100): # ERROR
                self.i2c.SCL.prepare(1) 
                self.i2c.SDA_OE.prepare(0)
                self.i2c.SDA_OUT.prepare(0)
                self.write_error.prepare(1)
                self.state = 0