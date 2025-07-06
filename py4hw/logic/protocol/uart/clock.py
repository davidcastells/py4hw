# -*- coding: utf-8 -*-
"""
Created on Thu Oct  3 16:41:16 2024

@author: 2016570
"""

from py4hw.base import *
                
class ClockSyncFSM(Logic):
    def __init__(self, parent, name, start, stop, sync, active):
        super().__init__(parent, name)
        
        self.start = self.addIn('start', start)
        self.stop = self.addIn('stop', stop)
        self.sync = self.addOut('sync', sync)
        self.active = self.addOut('active', active)
        
        self.state = 0 # IDLE
        
    def clock(self):
        if (self.state == 0):
            if (self.start.get()):
                self.state = 1 # Detected
                self.sync.prepare(1)
                self.active.prepare(1)
            else:
                self.sync.prepare(0)
                self.active.prepare(0)
                
        elif (self.state == 1):
            self.sync.prepare(0)
            
            if (self.stop.get()):
                self.state = 0
                self.active.prepare(0)
            else:
                self.active.prepare(1)
                

class ClockGenerationAndRecovery(Logic):
    ''' 
    The transmission clock (uartClk) is generated as a divisor of the original clock.
    However this signal is never used as a clock to any circuit, it is only used to detect positive edges that are used for transmission.
    Transmission clock is easy because it has not to be synchronized with anyone.
    
    The reception clock (syncUartClk) is generated similarly, with the difference that has a reset signal.
    The reset should occur when a negative rx pulse is seen and we are not in sync
    '''
    
    def __init__(self, parent, name, rx, desync, tx_clk_pulse, rx_sample, sysFreq, uartFreq):
        super().__init__(parent, name)
        
        from py4hw.logic.clock import ClockDivider
        from py4hw.logic.clock import EdgeDetector
        from py4hw.logic.bitwise import And2
        from py4hw.logic.bitwise import Not
        
        self.addIn('rx', rx)
        self.addIn('desync', desync)
        self.addOut('tx_clk_pulse', tx_clk_pulse)
        self.addOut('rx_sample', rx_sample)
        
        uartClk = self.wire('uart_clk')
        syncUartClk = self.wire('sync_uart_clk')
        pre_rx_sample = self.wire('pre_rx_sample')
        
        rx_neg = self.wire('rx_neg')
        start = self.wire('start')
        sync = self.wire('sync')
        
        active = self.wire('active')
        nactive = self.wire('nactive')

        ClockDivider(self, 'uart_clk', sysFreq, uartFreq, uartClk)
        ClockSyncFSM(self, 'clk_sync', start, desync, sync, active)
        ClockDivider(self, 'sync_uart_clk', sysFreq, uartFreq, syncUartClk, reset=start)
        
        Not(self, 'nactive', active, nactive)
        EdgeDetector(self, 'pos_edge', uartClk, tx_clk_pulse, 'pos')
        EdgeDetector(self, 'rx_neg', rx, rx_neg, 'neg')
        And2(self, 'start', rx_neg, nactive, start)
        
        # the RX synchonized clock is reset with the neg edge of RX and starts with value 0, then sample must occur at positive edge
        EdgeDetector(self, 'sample', syncUartClk, pre_rx_sample, 'pos') 
        
        And2(self, 'rx_sample', pre_rx_sample, active, rx_sample)