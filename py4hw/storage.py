# -*- coding: utf-8 -*-
"""
Created on Thu Oct 29 17:10:01 2020

@author: dcr
"""
from math import log2
from .base import Logic
from .logic import Not, Or
from .logic import Mux2, Constant
from .base import Wire

class Reg(Logic):
    """
    This is a D flip flop
    """
    def __init__(self, parent, name:str, d:Wire, e:Wire, q:Wire, ):
        super().__init__(parent, name)
        self.d = self.addIn("d", d)
        self.e = self.addIn("e", e)
        self.q = self.addOut("q", q)
        self.value = 0
        
    def clock(self):
        if (self.e.get() & 1):
            self.value = self.d.get()
            self.q.prepare(self.value)
            
            #print(self.name, 'sel', self.e.get(), self.d.get(), 'value prepared=', self.value)
            
            port = self.d.getSource()
            #print('d source', port.name, port.parent.getFullPath())
        else:
            #maintain the same value
            self.q.prepare(self.value)
            
class RegSR(Logic):
    """
    This is a D flip flop + Set/Reset feature
    """

    def __init__(self, parent, name:str, d:Wire, e:Wire, q:Wire, s:Wire, r:Wire, sVal:int = 0):
        super().__init__(parent, name)
        self.d = self.addIn("d", d)
        self.e = self.addIn("e", e)
        self.q = self.addOut("q", q)
        self.s = self.addIn("s", s)
        self.r = self.addIn("r", r)
        self.value = 0
        
        if (sVal > 0 and d.getWidth() < int(log2(sVal))+1):
            raise Exception('Invalid set value')

        self.sVal = Wire(self, "setValue", 1)
        self.zero = Wire(self, "zero", 1)
        self.muxToMux = Wire(self, "muxToMux", self.d.getWidth())
        self.muxToReg = Wire(self, "muxToReg", self.d.getWidth())
        self.orWire = Wire(self, "orWire", 1)
        self.eWire = Wire(self, "enable", 1)

        Constant(self, "setValue", sVal, self.sVal)
        Constant(self, "0", 0, self.zero)
    
        self.muxS = Mux2(self, "muxS", self.s, self.d, self.sVal, self.muxToMux)
        self.muxR = Mux2(self, "muxr", self.r, self.muxToMux, self.zero, self.muxToReg)

        Or(self, "or0", self.s, self.r, self.orWire)
        Or(self, "or1", self.orWire, self.e, self.eWire)

        self.reg = Reg(self, "reg", self.muxToReg, self.eWire, self.q)     
            
class TReg(Logic):
    def __init__(self, parent, name:str, t:Wire, e:Wire, q:Wire, ):
        super().__init__(parent, name)
        self.t = self.addIn("t", t)
        self.e = self.addIn("e", e)
        self.q = self.addOut("q", q)
        
        nq = self.wire('nq', 1)
        Not(self, 'nq', q, nq)
        
        d = self.wire('d', 1)
        Mux2(self, 'mux', t, q, nq, d)
        Reg(self, 'reg', d, e, q)
        