# -*- coding: utf-8 -*-
"""
Created on Thu Oct 29 17:10:01 2020

@author: dcr
"""
from .base import Logic
from .logic import Not
from .logic import Mux2
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
        