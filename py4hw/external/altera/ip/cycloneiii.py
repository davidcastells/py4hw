# -*- coding: utf-8 -*-
"""
Created on Tue Oct  8 16:20:12 2024

@author: 2016570
"""

import py4hw

class cycloneiii_io_buf (py4hw.Logic):
    
    def __init__(self, parent, name, pin, pout, poe, bidir):
        
        super().__init__(parent, name)
        
        assert(poe.getWidth() == 1)
        
        self.pin = self.addOut('pin', pin)
        self.pout = self.addIn('pout', pout)
        self.poe = self.addIn('poe', poe)
        
        self.bidir = self.addInOut('bidir', bidir)
        
    def structureName(self):
        return 'cycloneiii_io_buf_{}'.format(self.bidir.getWidth())
    
    def propagate(self):
        pass
    
    def verilogBody(self):
        ret = ''
        
        ret += '    cycloneiii_io_ibuf   ibufa_0(.i(bidir),	.o(pin) );\n'
        
        ret += '    cycloneiii_io_obuf   obufa_0(.i(pout),	.o(bidir),	.oe(poe));\n'
    
        return ret