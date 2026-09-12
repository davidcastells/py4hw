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
        '''
        
        VGA Timings for 640 x 480 @ 60 Hz
        
             ____     ____________________
        SYNC     \___/                    \______
             _____________ ________ _____________
        RGB  _____________X________X_____________
        
                 | a | b |    c    |  d   |
        
        Horizontal
        
        a = 96 * (1/25 MHz) = 3.84 us  (HSYNC)
        b = 48 * (1/25 MHz) = 1.92 us  (BACK PORCH)
        c = 640 * (1/25 MHz) = 25.6 us (ACTIVE)
        d = 16 * (1/25 MHz) = 0.64 us  (FRONT PORCH)
        
        TOTAL = 800 * (1/25 MHz) = 32 us
        
        Vertical
        
        a = 2       (VSYNC) 
        b = 33      (BACK PORCH)
        c = 480     (ACTIVE)
        d = 10      (FRONT PORCH)
        
        TOTAL = 525 * 32 us = 16.8 ms

        Returns
        -------
        None.

        '''

        if (self.x < 640 and self.y < 480):
            divx = self.x // 80
            vr = ((divx >> 0) & 1) * 0xFF
            vg = ((divx >> 1) & 1) * 0xFF
            vb = ((divx >> 2) & 1) * 0xFF       

            self.vga_if.R.prepare(vr)
            self.vga_if.G.prepare(vg)
            self.vga_if.B.prepare(vb)
            self.vga_if.VE.prepare(1)
        else:
            self.vga_if.R.prepare(0)
            self.vga_if.G.prepare(0)
            self.vga_if.B.prepare(0)
            self.vga_if.VE.prepare(0)
        
                    
        if (self.y >= (480+10)) and (self.y < (480+10+2)):
            self.vga_if.VS.prepare(0)
        else:
            self.vga_if.VS.prepare(1)
            
        if (self.x >= (640+16)) and ( self.x < (640+16+96)):
            self.vga_if.HS.prepare(0)
        else:
            self.vga_if.HS.prepare(1)
        
        if (self.x == 799):
            self.x = 0
            if (self.y == 524):
                self.y = 0
            else:
                self.y += 1
        else:
            self.x += 1
              
                
sys = plt.Pynq_Z2()


inc = sys.wire('inc')
reset = sys.wire('reset')

N = 10000
binary_digits = int(math.ceil(math.log2(N)))
bcd_digits = int(math.ceil(math.log10(N)))

count = sys.wire('count', binary_digits)
count_bcd = sys.wire('count_bcd', 4*bcd_digits) # 2 digits are enough
carryout = sys.wire('carryout')

key = sys.getInputKey()
led = sys.getLEDs()

py4hw.Bit(sys, 'reset', key, 0, reset)
py4hw.Bit(sys, 'inc', key, 1, inc)


py4hw.UpCounter(sys, 'cout', reset, inc=inc, q=led)




vga_clk = sys.wire('vga_clk')

vga_if = sys.getVGAController(reset, vga_clk)


vga_pattern = VGATestPattern(sys, 'vga', vga_if)
vga_pattern.clockDriver = py4hw.ClockDriver('vga_clk', 25.175E6, wire=vga_clk)


py4hw.gui.Workbench(sys)

dir = '/tmp/testPynqZ2'
sys.build(dir)
sys.download(dir)
