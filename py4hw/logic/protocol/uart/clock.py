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
                

class ClockGenerationAndRecovery(Logic):
    def __init__(self, parent, name, rx, desync, tx_clk_pulse, rx_sample, sysFreq, uartFreq):
        super().__init__(parent, name)
        
        self.addIn('rx', rx)
        self.addIn('desync', desync)
        self.addOut('tx_clk_pulse', tx_clk_pulse)
        self.addOut('rx_sample', rx_sample)
        
        uartClk = self.wire('uart_clk')
        syncUartClk = self.wire('sync_uart_clk')
        pre_rx_sample = self.wire('pre_rx_sample')
        
        start = self.wire('start')
        sync = self.wire('sync')
        active = self.wire('active')

        py4hw.ClockDivider(self, 'uart_clk', sysFreq, uartFreq, uartClk)
        ClockSyncFSM(self, 'clk_sync', start, desync, sync, active)
        py4hw.ClockDivider(self, 'sync_uart_clk', sysFreq, uartFreq, syncUartClk, reset=start)
        
        py4hw.EdgeDetector(self, 'pos_edge', uartClk, tx_clk_pulse, 'pos')
        py4hw.EdgeDetector(self, 'start', rx, start, 'pos')
        py4hw.EdgeDetector(self, 'sample', syncUartClk, pre_rx_sample, 'neg')
        
        py4hw.And2(self, 'rx_sample', pre_rx_sample, active, rx_sample)