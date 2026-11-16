# -*- coding: utf-8 -*-
"""
Created on Mon Nov 16 09:54:34 2026

@author: dcr
"""

import py4hw

hw = py4hw.HWSystem()

a = hw.wire('a', 10)
b = hw.wire('b', 10)
r = hw.wire('r', 10)

class ComplexSchematic(py4hw.Logic):
    def __init__(self, parent, name, a, b, r):
        super().__init__(parent, name)
        
        self.addIn('a', a)
        self.addIn('b', b)
        self.addOut('r', r)
    
    
        ab = self.wires('ab', a.getWidth(), 1 )
        bb = self.wires('bb', b.getWidth(), 1 )
        rb = self.wires('rb', r.getWidth(), 1 )
        
        ib = self.wires('ib', r.getWidth(), 1 )
        jb = self.wires('jb', r.getWidth(), 1 )
        
        py4hw.BitsLSBF(self, 'ab', a, ab)
        py4hw.BitsLSBF(self, 'bb', b, bb)
        py4hw.ConcatenateLSBF(self, 'rb', rb, r)
        
        w = a.getWidth()
        
        for i in range(w):
            py4hw.Xor2(self, f'xor{i}', ab[i], rb[i], ib[i])
            
            py4hw.Or2(self, f'or{i}', ib[i], ib[(i+1) % w], jb[i])
            py4hw.Reg(self, f'reg{i}', jb[i], rb[i], enable=bb[i])
            
            
dut = ComplexSchematic(hw, 'complex', a, b, r)

#py4hw.gui.Workbench(hw)

import time
t0 = time.time()
sch = py4hw.Schematic(dut)
sch.draw()

tf = time.time()

print('Original time is : 29.56 seconds')
print('Optimization: cache of adjencency matrices')
print(f'Creating the schematic took {tf-t0:.2f} seconds')


