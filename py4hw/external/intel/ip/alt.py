# -*- coding: utf-8 -*-
"""
Created on Tue Oct  8 15:12:40 2024

@author: 2016570
"""

import py4hw

class alt_io_buf (py4hw.Logic):
    
    def __init__(self, parent, name, pin, pout, poe, bidir):
        
        super().__init__(parent, name)
        
        assert(poe.getWidth() == 1)
        
        self.pin = self.addOut('pin', pin)
        self.pout = self.addIn('pout', pout)
        self.poe = self.addIn('poe', poe)
        
        self.bidir = self.addInOut('bidit', bidir)
        
    def structureName(self):
        return 'alt_io_buf_{}'.format(self.bidir.getWidth())
    
    def propagate(self):
        pass
    
    def verilogBody(self):
        ret = ''
        
        ret += f'ALTIOBUF i0 (\n'
        ret += '.i(pout),      // Data output from FPGA\n'
        ret += '.oe(poe),      // Output enable signal\n'
        ret += '.io(bidir),    // Bidirectional pin\n'
        ret += '.o(pin));      // Data input to FPGA\n'
        return ret
