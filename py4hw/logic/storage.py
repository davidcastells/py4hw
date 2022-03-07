# -*- coding: utf-8 -*-
"""
Created on Thu Oct 29 17:10:01 2020

@author: dcr
"""
from .. import *
from .. import *
from deprecated import deprecated


class Reg(Logic):
    """
    This is a D flip flop with (optional) enable and (optional) reset
    """
    def __init__(self, parent, name:str, d:Wire, q:Wire, enable:Wire=None, reset:Wire=None, reset_value:int=None ):
        """
        
        D flip flop with (optional) enable and (optional) reset

        Parameters
        ----------
        parent : TYPE
            parent.
        name : str
            name.
        d : Wire
            input.
        q : Wire
            output.
        enable : Wire, optional
            Enable signal. The default is None.
        reset : Wire, optional
            Synchronous reset signal. The default is None.

        Returns
        -------
        the object.

        """
        super().__init__(parent, name)
        self.d = self.addIn("d", d)
        self.q = self.addOut("q", q)

        if not(enable is None):
            self.e = self.addIn("e", enable)
        else:
            self.e = None
            
        if not(reset is None):
            self.r = self.addIn("r", reset)
        else:
            self.r = None
            
        if not(reset_value is None):
            self.reset_value = reset_value
        else:
            self.reset_value = 0
            
        self.value = 0
        
    def clock(self):
        setValue = True
        resetValue = False

        if not(self.e is None):
            if (self.e.get() == 0):
                setValue = False
        if not(self.r is None):
            if (self.r.get() == 1):
                resetValue = 1
                
        if (resetValue):
            self.value = self.reset_value
        elif (setValue):
            self.value = self.d.get()
        #else:
        #   maintain the same value            
            
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
        Reg(self, 'reg', d, q, enable=e)
        