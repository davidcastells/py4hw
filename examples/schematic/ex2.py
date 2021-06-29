import sys
sys.path.append('../..')

import py4hw

class Circuit(py4hw.Logic):
    def __init__(self, parent, name, a, b, r):
        super().__init__(parent, name)

        self.addIn('a', a)
        self.addIn('b', b)
        self.addOut('r', r)
        
        aux = self.wire('aux')
        py4hw.Add(self, 'add', a, b, aux)
        py4hw.Buf(self, 'buf', aux, r)

        
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
