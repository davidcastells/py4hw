# -*- coding: utf-8 -*-
"""
Created on Thu Nov  7 17:39:10 2024

@author: 2016570
"""

import py4hw
import math

class xilinx_xpm_fifo_sync(py4hw.Logic):
    
    def __init__(self, parent, name, reset, wr_en, rd_en, din, dout, empty, full, prog_empty, prog_full,
                 FIFO_DEPTH, PROG_FULL_THRESH, PROG_EMPTY_THRESH):
        
        super().__init__(parent, name)
        
        self.addIn('reset', reset)
        self.addIn('wr_en', wr_en)
        self.addIn('rd_en', rd_en)
        self.addIn('din', din)
        
        self.addOut('dout', dout)
        self.addOut('empty', empty)
        self.addOut('full', full)
        
        self.addOut('prog_empty', prog_empty)
        self.addOut('prog_full', prog_full)
        
        self.FIFO_DEPTH = FIFO_DEPTH
        self.PROG_FULL_THRESH = PROG_FULL_THRESH
        self.PROG_EMPTY_THRESH = PROG_EMPTY_THRESH
        self.dw = din.getWidth()
        
    def clock(self):
        # No behavioural model yet
        pass
    
    def verilogBody(self):
        str = ''

        from py4hw.base import getObjectClockDriver            
        clk_name = getObjectClockDriver(self).name

        str += '// Xilinx Parameterized Macro, Version 2016.4\n'
        str += 'xpm_fifo_sync # (\n'
        str += '.FIFO_MEMORY_TYPE("auto"),           //string; "auto", "block", "distributed", or "ultra";\n'
        str += '.ECC_MODE("no_ecc"),         //string; "no_ecc" or "en_ecc";\n'
        str += f'.FIFO_WRITE_DEPTH({self.FIFO_DEPTH}),   //positive integer\n'
        str += '.WRITE_DATA_WIDTH({}),        //positive integer\n'.format(self.dw)
        str += '.WR_DATA_COUNT_WIDTH({}),       //positive integer, Not used\n'.format(int(math.ceil(math.log2(self.FIFO_DEPTH)))+1) # @todo this +1 does not make sense
        str += '.PROG_FULL_THRESH({}), //positive integer\n'.format(self.PROG_FULL_THRESH)
        str += '.FULL_RESET_VALUE(1), //positive integer; 0 or 1\n'        
        str += '.READ_MODE("fwft"), //string; "std" or "fwft";\n'
        str += '.FIFO_READ_LATENCY(1), //positive integer;\n'
        str += '.READ_DATA_WIDTH({}), //positive integer\n'.format(self.dw)
        str += '.RD_DATA_COUNT_WIDTH({}), //positive integer, not used\n'.format(int(math.ceil(math.log2(self.FIFO_DEPTH)))+1)# @todo this +1 does not make sense
        str += '.PROG_EMPTY_THRESH({}),               //positive integer\n'.format(self.PROG_EMPTY_THRESH)
        str += '.DOUT_RESET_VALUE          ("0"),              //string,\n'
        str += '.WAKEUP_TIME               (0)                 //positive integer; 0 or 2;\n'
        
        str += ') inst_rd_xpm_fifo_sync (\n'
        str += ".sleep(1'b0), .rst( reset) ,\n"
        str += f'.wr_clk        ( {clk_name}) ,\n'
        str += '.wr_en(wr_en), .din(din), .full(full), .prog_full(prog_full),\n'
        
        str += '''        
  .wr_data_count (                  ) ,
  .overflow      (                  ) ,
  .wr_rst_busy   (                  ) ,
  .rd_en         ( rd_en   ) ,
  .dout          ( dout    ) ,
  .empty         ( empty ) ,
  .prog_empty    ( prog_empty ) ,
  .rd_data_count (                  ) ,
  .underflow     (                  ) ,
  .rd_rst_busy   (                  ) ,
  .injectsbiterr ( 1'b0             ) ,
  .injectdbiterr ( 1'b0             ) ,
  .sbiterr       (                  ) ,
  .dbiterr       (                  ) 

);
        '''
        
        return str