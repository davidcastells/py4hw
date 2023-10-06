# -*- coding: utf-8 -*-
"""
Created on Mon May  1 10:44:33 2023

@author: dcr
"""
from py4hw.base import *

class PullUpBus(Logic):
    def __init__(self, parent, name, i:list, en:list, o):
        super().__init__(parent, name)
        
        self.i = i
        self.en = en
        for idx, x in enumerate(i):
            self.addIn('i{}'.format(idx), x)
        for idx, x in enumerate(en):
            self.addIn('en{}'.format(idx), x)
        self.o = self.addOut('o', o)
        
    def propagate(self):
        setn = 0
        for idx in range(len(self.i)):
            i = self.i[idx]
            en = self.en[idx]
            
            if (en.get()):
                #print(idx, ' en:', en.get(), 'i:', i.get())
                self.o.put(i.get())
                setn += 1
        
        if (setn > 1):
            print('WARNING! multiple wires driving values')
        elif (setn == 0):
            self.o.put(1)
            
class I2CSlave(Logic):
    def __init__(self, parent, name, i2c_sda_in, i2c_sda_out, i2c_sda_oe, i2c_scl):
        super().__init__(parent, name)
        
        self.i2c_sda_in = self.addIn('i2c_sda_in', i2c_sda_in)
        self.i2c_sda_out = self.addOut('i2c_sda_out', i2c_sda_out)
        self.i2c_sda_oe = self.addOut('i2c_sda_oe', i2c_sda_oe)
        self.i2c_scl = self.addIn('i2c_scl', i2c_scl)
        
        self.v_i2c_sda_in = 0 
        self.v_i2c_sda_out = 0
        self.v_i2c_sda_oe = 0
        self.v_i2c_scl = 0
        
        self.co = self.run()
        
    def clock(self):
        # Inputs
        self.v_i2c_sda_in = self.i2c_sda_in.get()
        self.v_i2c_scl = self.i2c_scl.get()
        next(self.co)
        self.i2c_sda_out.prepare(self.v_i2c_sda_out)
        self.i2c_sda_oe.prepare(self.v_i2c_sda_oe)

    def waitStart(self):
        while (self.v_i2c_sda_in == 1):
            yield
            
        print("START detected in Slave")
        yield
        return
    
    def run(self):
        
        while (True):
            yield from self.waitStart()
            
            for i in range(7*2):
                print('Slave: scl={} ADDRESS[{}]={}'.format(self.v_i2c_scl, i, self.v_i2c_sda_in))
                yield
            yield
            
            # do the ack
            self.v_i2c_sda_out = 0
            self.v_i2c_sda_oe = 1
            yield
            self.v_i2c_sda_out = 0
            self.v_i2c_sda_oe = 1
            yield
            self.v_i2c_sda_out = 0
            self.v_i2c_sda_oe = 0
            yield
            
            for i in range(7*2):
                print('Slave: scl={} REG[{}]={}'.format(self.v_i2c_scl, i, self.v_i2c_sda_in))
                yield
            yield
                
            # do the ack
            self.v_i2c_sda_out = 0
            self.v_i2c_sda_oe = 1
            yield
            self.v_i2c_sda_out = 0
            self.v_i2c_sda_oe = 1
            yield
            self.v_i2c_sda_out = 0
            self.v_i2c_sda_oe = 0
            yield
            
            for i in range(7*2):
                print('Slave: scl={} DATA[{}]={}'.format(self.v_i2c_scl, i, self.v_i2c_sda_in))
                yield
            yield
            
            # do the ack
            self.v_i2c_sda_out = 0
            self.v_i2c_sda_oe = 1
            yield
            self.v_i2c_sda_out = 0
            self.v_i2c_sda_oe = 1
            yield
            self.v_i2c_sda_out = 0
            self.v_i2c_sda_oe = 0