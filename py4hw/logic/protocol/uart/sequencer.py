# -*- coding: utf-8 -*-
"""
Created on Thu Oct  3 16:42:31 2024

@author: 2016570
"""

from py4hw.base import *
from py4hw.logic.clock import ClockDivider
from py4hw.logic.clock import EdgeDetector
from .serdes import UARTSerializer
            
class MsgSequencer(Logic):
    def __init__(self, parent, name, ready, valid, v, msg):
        super().__init__(parent, name)
        
        self.ready = self.addIn('ready', ready)
        self.valid = self.addOut('valid', valid)
        self.v = self.addOut('v', v)
        self.state = 0
        self.count = 0
        self.msg = msg
        
    def clock(self):
        if (self.state == 0): # IDLE
            
            if (self.ready.get()):
                self.state = 1
                self.valid.prepare(1)
            else:
                self.valid.prepare(0)    
                
        elif (self.state == 1): # VALID
            self.v.prepare(ord(self.msg[self.count]))
            
            if (self.ready.get() == 0): 
                # if ready was deactivated wait here
                self.valid.prepare(1)
            else:
                self.valid.prepare(0)
                self.count = (self.count + 1) % len(self.msg)
                self.state = 0
            
    def verilogBody(self):
        import math
        ret = ''
        ret += 'reg state = 0;\n'
        mlen = len(self.msg)
        wcount = int(math.ceil(math.log2(mlen)))
        ret += f'reg [{wcount-1}:0] count = 0;\n'
        ret += 'reg rvalid = 0;\n'
        ret += 'reg [7:0] rv = 0;\n'
        
        ret += 'assign valid = rvalid;\n'
        ret += 'assign v = rv;\n'
        
        ret += f'reg [7:0] msg [0:{mlen-1}];\n'
        ret += 'initial begin\n'
        
        for idx, c in enumerate(self.msg):
            ret += f"   msg[{idx}] =  8'h{ord(c):02X};\n"
            link = ', '
        ret += 'end\n'
        
        drv = py4hw.getObjectClockDriver(self)
        
        ret += f'always @(posedge {drv.name}) begin\n'
        ret += '   if (state == 0) begin\n'
        ret += '      if (ready == 1) begin\n'
        ret += '             state <= 1;\n'
        ret += '             rvalid <= 1;\n'
        ret += '          end\n'
        ret += '      else begin\n'
        ret += '             rvalid <= 0;\n'
        ret += '          end \n'
        ret += '   end else if (state == 1) begin\n'
        ret += '      rv <= msg[count];\n'
        ret += '      rvalid <= 1;\n'
        ret += '      if (ready == 1) begin\n'
        ret += '             rvalid <= 1;\n'
        ret += '          end \n'
        ret += '      else begin\n'
        ret += '             rvalid <= 0;\n'
        ret += f'            count <= (count + 1) % {mlen};\n'
        ret += '             state <= 0;\n'
        ret += '          end\n'
        ret += '      end\n'
        ret += 'end\n'
        
        return ret
    
class ReadyFlowControl(Logic):
    #
    #  | msg |-> valid ------------> | in_valid      out_valid |-------------> valid ->| ser |
    #  |     |<- ready --------------| in_ready      out_ready |<------------- ready <-|     |
    #
    # we propagate the out_ready=0 inmediately to in_ready but
    # take a number (count) of pulses to propagate the out_ready=1
    #
    def __init__(self, parent, name, in_ready, in_valid, clk_enable, out_ready, out_valid, count):
        super().__init__(parent, name)        
        
        import math
        from py4hw.logic.bitwise import Not
        from py4hw.logic.bitwise import Buf
        from py4hw.logic.arithmetic import Counter
        from py4hw.logic.arithmetic import EqualConstant
        from py4hw.logic.storage import Reg
        
        self.addIn('in_valid', in_valid)
        self.addOut('in_ready', in_ready)
        self.addIn('out_ready', out_ready)
        self.addOut('out_valid', out_valid)
        self.addIn('clk_enable', clk_enable)
        
        nout_ready = self.wire('nout_ready')
        
        wcount = int(math.ceil(math.log2(count)))
        q = self.wire('q', wcount)
        iseq = self.wire('iseq')
        
        Not(self, 'nout_ready', out_ready, nout_ready)
        Counter(self, 'count', reset=nout_ready, inc=clk_enable, q=q)
        EqualConstant(self, 'iseq', q, count, iseq)
        
        Reg(self, 'in_ready', d=iseq, q=in_ready, enable=iseq, reset=nout_ready)
        
        Buf(self, 'out_valid', in_valid, out_valid)
        
        
class UARTMsgGenerator(Logic):
    def __init__(self, parent, name, tx, sysFreq, uartFreq, msg):
        super().__init__(parent, name)
        
        self.addOut('tx', tx)
        
        msg_ready = self.wire('msg_ready')
        msg_valid = self.wire('msg_valid')
        ser_ready = self.wire('ser_ready')
        ser_valid = self.wire('ser_valid')
        v = self.wire('v', 8)
        
        
        MsgSequencer(self, name, msg_ready, msg_valid, v,  msg)
        
        uartClk = self.wire('uart_clk')
        tx_clk_pulse = self.wire('tx_clk_pulse')
        
        ClockDivider(self, 'uart_clk', sysFreq, uartFreq, uartClk)
        EdgeDetector(self, 'pos_edge', uartClk, tx_clk_pulse, 'pos')
        
        UARTSerializer(self, 'ser', ser_ready, ser_valid, v, tx_clk_pulse, tx)
        ReadyFlowControl(self, 'flowcontrol', msg_ready, msg_valid, tx_clk_pulse, ser_ready, ser_valid, 20)