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