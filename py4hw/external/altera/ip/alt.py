# -*- coding: utf-8 -*-
"""
Created on Mon Oct  5 23:06:07 2026

@author: dcr
"""


import py4hw

class alt_jtag_atlantic (py4hw.Logic):
    
    def __init__(self, parent, name, reset, tx_data, tx_ready, tx_valid):
        
        super().__init__(parent, name)
        
        assert(tx_data.getWidth() == 8)
        
        self.reset = self.addIn('reset', reset)
        self.tx_data = self.addIn('tx_data', tx_data)
        self.tx_ready = self.addOut('tx_ready', tx_ready)
        self.tx_valid = self.addIn('tx_valid', tx_valid)

        
    def structureName(self):
        return 'alt_jtag_atlantic_wrapper'
    
    def clock(self):
        pass
    
    def verilogBody(self):
        
        clk_name = py4hw.getObjectClockDriver(self).name

        ret = ''
        
        ret += 'alt_jtag_atlantic #('
        ret += '.INSTANCE_ID(0),'
        ret += '.LOG2_RXFIFO_DEPTH(6),'
        ret += '.LOG2_TXFIFO_DEPTH(6),'
        ret += '.SLD_AUTO_INSTANCE_INDEX("YES")'
        ret += ')\n i_uart ('
        ret += f'.clk({clk_name}),'
        ret += '.rst_n   (~reset),'
        ret += '.r_dat  (tx_data),'
        ret += '.r_ena  (tx_valid),'
        ret += '.r_val  (tx_ready),\n'
        ret += '// Not interested in RX\n' 
        ret += '.t_dat  (),'
        ret += ".t_dav  (1'b1),"
        ret += '.t_ena  (),'
        ret += '.t_pause()'
        ret += ');'

        return ret
