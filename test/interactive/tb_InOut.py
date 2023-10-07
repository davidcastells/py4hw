#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct  7 08:20:21 2023

@author: dcr
"""

import py4hw



class IOBuf(py4hw.Logic):
    
    def __init__(self, parent, name, pin, pout, poe, bidir):
        super().__init__(parent, name)
        
        self.bidir = self.addInOut('bidir', bidir)
        self.pin = self.addOut('pin', pin)
        self.pout = self.addIn('pout', pout)
        self.poe = self.addIn('poe', poe)
        
    def propagate(self):
        if (self.poe.get() ==1):
            self.bidir.put(self.pout.get())
        else:
            self.pin.set(self.bidir.get())
            
sys = py4hw.HWSystem()
            
bidir = sys.bidir_wire('bidir')
poe = sys.wire('poe')   
pout = sys.wire('pout')
pin = sys.wire('pin')
         
py4hw.Sequence(sys, 'bidir', [0,0,0,1, 1], bidir)
py4hw.Sequence(sys, 'poe', [1,0,0], poe)
py4hw.Sequence(sys, 'pout', [0, 1], pout)

IOBuf(sys, 'iobuf', pin, pout, poe, bidir)

py4hw.gui.Workbench(sys)