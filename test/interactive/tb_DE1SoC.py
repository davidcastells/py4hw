# -*- coding: utf-8 -*-
"""
Created on Fri Sep 29 23:38:52 2023

@author: dcr
"""
import math
import py4hw

import py4hw.external.platforms as plt

class VGATestPattern(py4hw.Logic):
    
    def __init__(self, parent, name, vga_if):
        super().__init__(parent, name)
        
        
        self.vga_if = self.addInterfaceSource('', vga_if)
        self.x = 0
        self.y = 0
        
        
        
    def clock(self):
        
        divx = self.x // 80
        vr = ((divx >> 0) & 1) * 0xFF
        vg = ((divx >> 1) & 1) * 0xFF
        vb = ((divx >> 2) & 1) * 0xFF       

        self.vga_if.R.prepare(vr)
        self.vga_if.G.prepare(vg)
        self.vga_if.B.prepare(vb)
        self.vga_if.VS.prepare(1 if self.y < 480 else 0)
        self.vga_if.HS.prepare(1 if self.x < 640 else 0)
        
        self.x += 1
        if (self.x >= 840):
            self.x = 0
            self.y += 1
            if (self.y >= 520):
                self.y = 0
                
sys = plt.DE1SoC()

print('DE1SoC clk driver', sys.clockDriver.name)

inc = sys.wire('inc')
reset = sys.wire('reset')

N = 100000
binary_digits = int(math.ceil(math.log2(N)))
bcd_digits = int(math.ceil(math.log10(N)))

count = sys.wire('count', binary_digits)
count_bcd = sys.wire('count_bcd', 4*bcd_digits) # 2 digits are enough
carryout = sys.wire('carryout')

key = sys.getInputKey()

py4hw.Bit(sys, 'reset', key, 0, reset)
py4hw.Bit(sys, 'inc', key, 1, inc)

# sys.addOut('count', count)

#py4hw.Constant(sys, 'inc', 1, inc)
#py4hw.Constant(sys, 'reset', 0, reset)
py4hw.ModuloCounter(sys, 'cout', N, reset, inc, count, carryout)
py4hw.BinaryToBCD(sys, 'bcd', count, count_bcd)

hexs = [sys.getOutputHex(i) for i in range(6)]
bcds = [None] * bcd_digits

for i in range(bcd_digits):
    bcd_name = 'bcd{}'.format(i)
    hex_name = 'hex{}'.format(i)
    bcds[i] = sys.wire(bcd_name, 4)
    py4hw.Range(sys, bcd_name, count_bcd, 4*i+3, 4*i, bcds[i])

    py4hw.Digit7Segment(sys, hex_name, bcds[i], hexs[i])


for i in range(bcd_digits, 6):
    py4hw.Constant(sys, 'hex{}'.format(i), 0, hexs[i])


vga_clk = sys.wire('VGA_CLK')
py4hw.ClockDivider(sys, 'VGA_CLK', sys.clockDriver.freq, 25E6, vga_clk)

vga_if = sys.getVGAController(vga_clk)


vga_pattern = VGATestPattern(sys, 'vga', vga_if)
vga_pattern.clockDriver = py4hw.ClockDriver('clk25', 25E6, wire=vga_clk)


py4hw.gui.Workbench(sys)

dir = '/tmp/testDE1SoC'
sys.build(dir)
#sys.download(dir)