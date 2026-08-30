# -*- coding: utf-8 -*-
"""
Created on Sun Aug 16 06:07:27 2026

@author: dcr
"""

import py4hw


class FSM(py4hw.Logic):
    def __init__(self, parent, name, a, r):
        # detector of sequence 1011
        
        super().__init__(parent, name)
        
        self.a = self.addIn('a', a)
        self.r = self.addOut('r', r)
        
        self.state = 'IDLE'
        
    def clock(self):
        if (self.state == 'IDLE'):
            self.r.prepare(0)
            if (self.a.get()):
                self.state = '1'
        elif (self.state == '1'):
            self.r.prepare(0)
            if (self.a.get() == 0):
                self.state = '10'
            else:
                self.state = '1'
        elif (self.state == '10'):
            self.r.prepare(0)
            if (self.a.get()):
                self.state = '101'
            else:
                self.state = 'IDLE'
        elif (self.state == '101'):
            if (self.a.get()):
                self.state = '1011'
                self.r.prepare(1)
            else:
                self.state = '10'
                self.r.prepare(0)
                
        elif (self.state == '1011'):
            self.r.prepare(0)
            if (self.a.get()):
                self.state = '1'
            else:
                self.state = '10'
                

hw = py4hw.HWSystem()                

a = hw.wire('a')
r = hw.wire('r')

fsm = FSM(hw, 'fsm', a, r)

wvf = py4hw.Waveform(hw, 'wvf', [a,r, py4hw.FieldInspector(fsm, 'state')])


py4hw.Sequence(hw, 'a', [0,0,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,1], a)



hw.getSimulator().clk(20)

wvf.gui()