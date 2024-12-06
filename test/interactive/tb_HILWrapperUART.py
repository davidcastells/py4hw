# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 16:36:06 2024

@author: 2016570
"""

import py4hw


class DUT(py4hw.Logic):

    def __init__(self, parent, name, a, b, p, m):
        super().__init__(parent, name)

        self.addIn('a', a)
        self.addIn('b', b)
        self.addOut('p', p)
        self.addOut('m', m)

        py4hw.Add(self, 'add', a, b, p)
        py4hw.Sub(self, 'sub', a, b, m)


def createHILPlatform():
    import py4hw.external.platforms as plt

    de0= plt.DE0()

    gpio_in, gpio_out, gpio_oe = de0.getGPIO(0)
    py4hw.Constant(de0, 'tx_oe', 1, gpio_oe[0])
    
    de0.tx = gpio_out[0]
    de0.rx = gpio_in[1]

    return de0
    
    

hw = py4hw.HWSystem()

a = hw.wire('a', 32)
b = hw.wire('b', 32)

p = hw.wire('p', 32)
s = hw.wire('s', 32)

py4hw.Sequence(hw, 'a', [1,2,3,4,5,6,7], a)
py4hw.Sequence(hw, 'b', [0x1A00,0x2B00,0x3C00], b)

dut = DUT(hw, 'dut', a, b, p, s)

import py4hw.emulation.HILWrapperUART as hil
dir = '/tmp/testDE0'
hil_plt = hil.createHILUART(createHILPlatform(), dut, dir)
hil_plt.build()
hil_plt.download()

np = hw.wire('np', 32)
ns = hw.wire('ns', 32)

hil.createHILUARTProxy(dut, hw, 'dut_hw', a, b, np, ns)

wvf = py4hw.Waveform(hw, 'wvf', [a,b,p,s, np, ns])

hw.getSimulator().clk(20)

wvf.gui(shortNames=True)
