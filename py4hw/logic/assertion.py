# -*- coding: utf-8 -*-
"""
Created on Tue Nov  3 09:43:15 2026

@author: dcr
"""

from .. import *
from deprecated import deprecated


class AssertOneActive(Logic):
    
    def __init__(self, parent, name, ins):
        super().__init__(parent, name)
        
        self.ins = ins
        
        for idx, p in enumerate(ins):
            self.addIn(f'in{idx}', p)
            
    def monitor(self):
        diff_than_zero = 0
        active = []
        
        for p in self.ins:
            if (p.get() != 0):
                diff_than_zero += 1
                active.append(p)
                
        if (diff_than_zero > 1):
            active_msg = 'Many active wires: '
            link = ''
            for w in active:
                active_msg += link + w.name
                link = ', '
            raise Exception(active_msg)


class AssertAllActive(Logic):
    
    def __init__(self, parent, name, ins):
        super().__init__(parent, name)
        
        self.ins = ins
        
        for idx, p in enumerate(ins):
            self.addIn(f'in{idx}', p)
            
    def monitor(self):
        equals_zero = 0
        inactive = []
        
        for p in self.ins:
            if (p.get() == 0):
                equals_zero  += 1
                inactive.append(p)
                
        if (equals_zero > 0):
            active_msg = 'Some inactive wires: '
            link = ''
            for w in inactive:
                active_msg += link + w.name
                link = ', '
            raise Exception(active_msg)    
            
class AssertNotAllActive(Logic):
    
    def __init__(self, parent, name, ins):
        super().__init__(parent, name)
        
        self.ins = ins
        
        for idx, p in enumerate(ins):
            self.addIn(f'in{idx}', p)
            
    def monitor(self):
        diff_than_zero = 0
        active = []
        
        for p in self.ins:
            if (p.get() != 0):
                diff_than_zero  += 1
                active.append(p)
                
        if (diff_than_zero == len(self.ins)):
            active_msg = 'All wires active: '
            link = ''
            for w in active:
                active_msg += link + w.name
                link = ', '
            raise Exception(active_msg)        