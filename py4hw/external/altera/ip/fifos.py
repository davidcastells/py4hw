# -*- coding: utf-8 -*-
"""
Created on Mon Oct  5 23:58:41 2026

@author: dcr
"""
import py4hw

class dcfifo (py4hw.Logic):
    
    def __init__(self, parent, name, tx_clk, tx_data, tx_ready, tx_valid,
                 rx_clk, rx_data, rx_ready, rx_valid, numwords):
        
        super().__init__(parent, name)
        
        assert(tx_data.getWidth() == 8)
        
        self.tx_clk = self.addIn('tx_clk', tx_clk)
        self.tx_data = self.addIn('tx_data', tx_data)
        self.tx_valid = self.addIn('tx_valid', tx_valid)
        self.tx_ready = self.addOut('tx_ready', tx_ready)

        self.rx_clk = self.addIn('rx_clk', rx_clk)
        self.rx_data = self.addOut('rx_data', rx_data)
        self.rx_valid = self.addOut('rx_valid', rx_valid)
        self.rx_ready = self.addIn('rx_ready', rx_ready)
        
        self.numwords = numwords

    def structureName(self):
        return 'dc_fifo_wrapper'
    
    def propagate(self):
        pass
    
    def verilogBody(self):

        ret = ''
        
        ret += '// Internal Wires\n'
        ret += 'wire wrfull;\n'
        ret += 'wire rdempty;\n'
        ret += 'wire wrreq;\n'
        ret += 'wire rdreq;\n'
        ret += '// Ready/Valid to FIFO Control Handshaking\n'
        ret += 'assign wr_rdy = ~wrfull;\n'
        ret += 'assign wrreq  = tx_valid && tx_ready;\n'
        ret += 'assign rx_valid = ~rdempty;\n'
        ret += 'assign rdreq  = rx_valid && rx_ready;\n'
        ret += 'dcfifo #(\n'
        ret += f'.lpm_numwords({self.numwords}),'
        ret += '.lpm_showahead ("ON"),'
        ret += '.lpm_type ("dcfifo"),'
        ret += '.lpm_width (8),'
        ret += '.lpm_widthu (2),'
        ret += '.overflow_checking ("OFF"),'
        ret += '.rdsync_delaypipe(4),'
        ret += '.underflow_checking("OFF"),'
        ret += '.use_eab("ON"),'
        ret += '.wrsync_delaypipe(4)'
        ret += ')\n dcfifo_component ('
        ret += f'.wrclk(tx_clk),'
        ret += '.wrreq   (wrreq),'
        ret += '.data    (tx_data),'
        ret += '.wrfull  (wrfull),'
        ret += '.rdclk   (rx_clk),'
        ret += '.rdreq   (rdreq),'
        ret += '.q       (rx_data),'
        ret += '.rdempty (rdempty),'
        ret += ".aclr    (1'b0),"
        ret += '.rdfull  (),'
        ret += '.rdusedw (),'
        ret += '.wrempty (),'
        ret += '.wrusedw ()'
        ret += ');\n'

        return ret
