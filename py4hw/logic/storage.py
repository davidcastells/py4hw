# -*- coding: utf-8 -*-
"""
Created on Thu Oct 29 17:10:01 2020

@author: dcr
"""
from .. import *
from .bitwise import Buf

from deprecated import deprecated

class Latch(Logic):
    '''
    This is an asynchronous LATCH
    '''
    def __init__(self, parent, name, d:Wire, q:Wire, enable:Wire):
        super().__init__(parent, name)
        self.d = self.addIn("d", d)
        self.q = self.addOut("q", q)
        self.e = self.addIn("e", enable)
        
    def propagate(self):
        
        if (self.e.get()):
            self.q.put(self.d.get())
            
    def structureName(self):
        msg = 'Latch{}'.format(self.q.getWidth())
        return msg
    
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
            
        self.value = self.reset_value
        
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

    def structureName(self):
        msg = 'Reg{}'.format(self.q.getWidth())
        
        if not(self.r is None): msg += 'R'
        if not(self.e is None): msg += 'E'
        if not(self.reset_value == 0): msg += '_v{}'.format(self.reset_value)
        
        return msg
            
class TReg(Logic):
    def __init__(self, parent, name:str, t:Wire, q:Wire, enable:Wire=None, reset:Wire=None ):
        from .bitwise import Not
        from .bitwise import Mux2
        
        super().__init__(parent, name)
        
        self.addIn("t", t)
        
        if not(enable is None):
            self.addIn("e", enable)

        if not(reset is None):
            self.addIn("r", reset)
        
        self.addOut("q", q)
        
        nq = self.wire('nq', 1)
        Not(self, 'nq', q, nq)
        
        d = self.wire('d', 1)
        Mux2(self, 'mux', t, q, nq, d)
        Reg(self, 'reg', d, q, enable=enable, reset=reset)
        
class DelayLine(Logic):
    def __init__(self, parent, name:str, a:Wire, en:Wire, reset:Wire, r:Wire, delay:int):
        """
        Daisy-chained number of registers, typically used to create a 
        fixed-length delay line
        
        Parameters
        ----------
        parent : Logic
            Parent entity.
        name : str
            instance name.
        a : Wire
            input.
        en : Wire
            enable signal.
        r : Wire
            output.
        delay : int
            number of registers in the delay line.

        Returns
        -------
        None.

        """
        
        super().__init__(parent, name)
        
        self.addIn('a', a)
        if not(en is None): self.addIn('en', en)
        if not(reset is None): self.addIn('reset', reset)
        self.addOut('r', r)

        last = a
        for i in range(delay):
            newlast = self.wire('r{}'.format(i), a.getWidth())
            Reg(self, 'r{}'.format(i), last, newlast, enable=en, reset=reset)
            last = newlast
            
        Buf(self, 'buf', last, r)
        
        
class PipelinePhase(Logic):
    def __init__(self, parent, name, reset, ins, outs):
        super().__init__(parent, name)
        assert(len(ins) == len(outs))
        
        self.addIn('reset', reset)
        
        for i in range(len(ins)):
            self.addIn('in{}'.format(i), ins[i])
            self.addOut('out{}'.format(i), outs[i])
            
            Reg(self, 'r{}'.format(i), ins[i], outs[i], reset=reset)