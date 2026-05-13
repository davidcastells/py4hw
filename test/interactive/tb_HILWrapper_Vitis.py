import py4hw

import py4hw.emulation.vitiswrapping as hil


class DUT(py4hw.Logic):

    def __init__(self, parent, name, a, b, p, m):
        super().__init__(parent, name)

        self.addIn('a', a)
        self.addIn('b', b)
        self.addOut('p', p)
        self.addOut('m', m)

        py4hw.Add(self, 'add', a, b, p)
        py4hw.Sub(self, 'sub', a, b, m)




hw = py4hw.HWSystem()

a = hw.wire('a', 32)
b = hw.wire('b', 32)

p = hw.wire('p', 32)
s = hw.wire('s', 32)

py4hw.Sequence(hw, 'a', [1,2,3,4,5,6,7], a)
py4hw.Sequence(hw, 'b', [0x1A00,0x2B00,0x3C00], b)

dut = DUT(hw, 'dut', a, b, p, s)

hil.generate_connectivity(dut, '.')
hil.generate_reader(dut, '.')
hil.generate_writer(dut, '.')