# -*- coding: utf-8 -*-
"""
Created on Thu Jan 27 14:06:19 2022

@author: dcr
"""
from .. import *

class GatedClock(Logic):
    
    def __init__(self, parent:Logic, name:str, enin:Wire , enout:Wire, drv:ClockDriver):
        super().__init__(parent, name)
        
        self.enin = self.addIn('enin', enin)
        self.enout = self.addOut('enout', enout)
        self.drv = drv
        
    def propagate(self):
        # this is fake, just to make simulator work
        self.enout.put(self.enin.get())
        
        
class ClockDivider(Logic):
    def __init__(self, parent, name, freq_in, freq_out, clkout, reset=None):
        from py4hw.helper import LogicHelper
        from py4hw.logic.arithmetic import ModuloCounter
        from py4hw.logic.storage import TReg
        import math
        super().__init__(parent, name)
            
        req_freq_out = freq_out
        hlp = LogicHelper(self)
        
        self.addOut('clkout', clkout)
        
        n = freq_in / (2*freq_out)
        
        qw = int(math.log2(n)) + 1
        
        n = int(n)
        
        freq_out = freq_in / (2*n)
        
        #print('n', n, 'qw', qw, 'freq_out', freq_out)
        if (freq_out != req_freq_out):
            print('WARNING: Real Output Frequency:', freq_out, 'required:', req_freq_out)
        
        assert(qw > 0)
        q = self.wire('q', qw)
        t = self.wire('t')
        inc = hlp.hw_constant(1,1)
        if (reset is None):
            reset = hlp.hw_constant(1,0)
        else:
            reset = self.addIn('reset', reset)
            
        dut = ModuloCounter(self, 'count', mod=n, inc=inc, reset=reset, q=q, carryout=t)
    
        TReg(self, 'clkout', t, enable=inc, q=clkout, reset=reset)

        
        
class EdgeDetector(Logic):
    def __init__(self, parent, name, a, r, direction):
        from py4hw.logic.storage import Reg
        from py4hw.logic.bitwise import Not
        from py4hw.logic.bitwise import And2
        from py4hw.logic.bitwise import Xor2
        
        super().__init__(parent, name)
        
        if a.getWidth() != 1:
            raise Exception('by now only 1 bit wires supported')
            
        self.addIn('a', a)
        self.addOut('r', r)
        
        z1 = self.wire('z1')
        na = self.wire('na')
        nz1 = self.wire('nz1')
        
        Reg(self, 'z1', a, z1)
        
        if (direction == 'pos'):
            Not(self, 'nz1', z1, nz1)
            And2(self, 'r', a, nz1, r)
        elif (direction == 'neg'):
            Not(self, 'na', a, na)
            And2(self, 'r', na, z1, r)
        elif (direction == 'both'):
            Xor2(self, 'r', a, z1, r)
        else:
            raise Exception(f'direction {direction} not supported' )
