import sys
sys.path.append('../..')

import py4hw

class Circuit(py4hw.Logic):
    def __init__(self, parent, name, a, b, r):
        super().__init__(parent, name)

        self.addIn('a', a)
        self.addIn('b', b)
        self.addOut('r', r)
        
        aux1 = self.wire('aux1', a.getWidth())
        aux2 = self.wire('aux2', a.getWidth())
        sel = self.wire('sel')

        py4hw.Add(self, 'add', a, b, aux1)
        py4hw.Mul(self, 'mul', a, b, aux2)

        py4hw.Bit(self, 'bit', a, 0, sel)
        
        py4hw.Mux2(self, 'mux', sel, aux1, aux2, r)
        
sys = py4hw.HWSystem()

a = sys.wire('a',8)
b = sys.wire('b',8)
r = sys.wire('r', 8)

c = Circuit(sys, 'c', a, b, r)
py4hw.Constant(sys, 'a', 3, a)
py4hw.Constant(sys, 'b', 3, b)
py4hw.Scope(sys, 'r', r)

py4hw.debug.checkIntegrity(sys)

sch = py4hw.Schematic(c)
