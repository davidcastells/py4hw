import sys
sys.path.append('../..')

import py4hw

class Circuit(py4hw.Logic):
    def __init__(self, parent, name, a, c, r):
        super().__init__(parent, name)

        self.addIn('a', a)
        
        self.addIn('c', c)
        self.addOut('r', r)
        
        aux1 = self.wire('aux1', a.getWidth())
        aux2 = self.wire('aux2', a.getWidth())
        aux3 = self.wire('aux3', a.getWidth())
        sel = self.wire('sel')

        gnd = self.wire('gnd')
        
        py4hw.Constant(self, 'gnd', 0, gnd)
        py4hw.storage.Reg(self, 'm', aux2, gnd, aux3)
        py4hw.Add(self, 'add', a, aux3, aux1)
        py4hw.Mul(self, 'mul', aux1, c, aux2)

        py4hw.Bit(self, 'bit', a, 0, sel)
        
        py4hw.Mux2(self, 'mux', sel, aux1, aux2, r)
        
sys = py4hw.HWSystem()

a = sys.wire('a',8)
c = sys.wire('c',8)
r = sys.wire('r', 8)

obj = Circuit(sys, 'obj', a, c, r)
py4hw.Constant(sys, 'a', 3, a)
py4hw.Constant(sys, 'c', 3, c)
py4hw.Scope(sys, 'r', r)

py4hw.debug.checkIntegrity(sys)

sch = py4hw.Schematic(obj)
