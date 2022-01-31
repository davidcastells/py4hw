# -*- coding: utf-8 -*-
"""
Created on Sat Jan 29 16:28:57 2022

@author: dcr
"""

from .base import Wire
from .logic.bitwise import *
from .logic.simulation import *

class Helper():
    
    def __init__(self, parent:Logic):
        self.parent = parent
        self.inum = 0   # instance number
        
    def getNewName(self)->str:
        str = 'i{}'.format(self.inum)
        self.inum += 1
        return str
    
    def hw_constant(self, width:int, v:int) -> Wire:
        name = self.getNewName()
        r = self.parent.wire(name, width)
        Constant(self.parent, name, v, r)
        return r
    
    def hw_and2(self, a:Wire, b:Wire) -> Wire:
        w = a.getWidth()
        name = self.getNewName()
        r = self.parent.wire(name, w)
        And2(self.parent, name, a, b, r)
        return r

    def hw_and3(self, a:Wire, b:Wire, c:Wire) -> Wire:
        w = a.getWidth()
        name = self.getNewName()
        r = self.parent.wire(name, w)
        And(self.parent, name, [a, b, c], r)
        return r
    
    def hw_not(self, a:Wire) -> Wire:
        w = a.getWidth()
        name = self.getNewName()
        r = self.parent.wire(name, w)
        Not(self.parent, name, a, r)
        return r
        
    def hw_mux(self, sel:Wire, options:list) -> Wire:
        name = self.getNewName()
        w = options[0].getWidth()
        r = self.parent.wire(name, w)
        Mux(self.parent, name, sel, options, r)
        return r
    
    def sim_sequence(self, width:int, seq:list) -> Wire:
        name = self.getNewName()
        r = self.parent.wire(name, width)
        Sequence(self.parent, name, seq, r)
        return r
 