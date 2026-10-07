# -*- coding: utf-8 -*-
"""
Created on Thu Oct  3 16:42:31 2024

@author: 2016570
"""

from py4hw.base import *
from py4hw.logic.clock import ClockDivider
from py4hw.logic.clock import EdgeDetector
from .serdes import UARTSerializer
            
import math

class MsgSequencer(Logic):
    def __init__(self, parent, name, reset, ready, valid, v, msg):
        super().__init__(parent, name)
        
        from py4hw.logic.bitwise import Constant
        from py4hw.logic.bitwise import And2
        from py4hw.logic.storage import Reg
        from py4hw.logic.storage import AsynchronousROM
        from py4hw.logic.arithmetic import ModuloCounter    
        
        self.addIn('reset', reset)
        self.addIn('ready', ready)
        self.addOut('valid', valid)
        self.addOut('v', v)
        
        msg_len = len(msg)
        aw = max(1, math.ceil(math.log2(msg_len)))
        
        transfer = self.wire('transfer', 1)
        address = self.wire('address', aw)
        rom_out = self.wire('rom_out', v.getWidth())
        
        # Valid signal is always 1
        Constant(self, 'valid', 1, valid)
                
        # transfer = ready AND valid
        And2(self, 'transfer', ready, valid, transfer)
        
        # Increments on transfer signal
        ModuloCounter(self, 'addr', reset=reset, inc=transfer, q=address, mod=msg_len, carryout=None)
        
        # 6. Asynchronous ROM: Stores ASCII values of msg characters
        ascii_msg = [ord(char) for char in msg]
        AsynchronousROM(self, 'rom', address, rom_out, ascii_msg)
        
        # 7. Output Register: Loads ROM data when transfer is asserted, drives 'v'
        Reg(self, 'v', d=rom_out, q= v, enable=transfer)
        
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