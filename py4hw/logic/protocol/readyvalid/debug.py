# -*- coding: utf-8 -*-
"""
Created on Sat Sep 19 06:55:28 2026

@author: 2016570
"""
import py4hw

class ReadyValidScope(py4hw.Logic):
    def __init__(self, parent, name, ready, valid, value):
        super().__init__(parent, name)

        self.ready = self.addIn('ready', ready)
        self.valid = self.addIn('valid', valid)
        self.value = self.addIn('value', value)

    def clock(self):
        if (self.ready.get() and self.valid.get()):
            v = self.value.get()
            if (v == 10):
                c = r'\n'
            else:
                c = chr(v)
            
            print('ASCII:', c, 'int:', v)