# -*- coding: utf-8 -*-
"""
Created on Thu Apr  6 06:49:04 2023

@author: dcr
"""

import py4hw

import time
import matplotlib.pyplot as plt
import numpy as np
        

class VGAScreen(py4hw.Logic):
    
    def __init__(self, parent, name, reset, hactive, vactive, r, g, b, live=False):
        super().__init__(parent, name)

        self.reset = self.addIn('reset', reset)
        self.hactive = self.addIn('hactive', hactive)
        self.vactive = self.addIn('vactive', vactive)
        self.r = self.addIn('r', r)
        self.g = self.addIn('g', g)
        self.b = self.addIn('b', b)
        
        self.x = 0
        self.y = 0
        self.inRow = False
        self.inFrame = False
        self.frame = np.zeros((480, 640, 3), dtype=int)
        
        self.live = live
        if (self.live):
            fig, ax = plt.subplots()
            
            self.ax = ax
            ax.imshow(self.frame)
            plt.show(block=False)
            self.t0 = time.time()

    def plot_frame(self):
        plt.imshow(self.frame)
        plt.show()        
        
    def plot_img_live(self, ax, img):
        tf = time.time()
        td = tf - self.t0 
        
        if (td > 1):     
            #print('range frame:', np.min(img), np.max(img))
            ax.imshow(img)
            #plt.draw()
            plt.pause(0.0000001) 
            self.t0 = time.time()

    def clock(self):
        
        if (self.reset.get()):
            self.x = 0
            self.y = 0
            self.inRow = False
            self.inFrame = False
            return

        if (self.vactive.get()):
            self.inFrame = True
        elif (self.inFrame):
            self.y = 0
            self.x = 0
            self.inFrame = False
            
            #plt.show()
        
        if (self.inFrame):

            if (self.hactive.get()):
                #print('x,y', self.x, self.y)
                if (self.x >= 640):
                    print('Invalid x value', self.x)
                else:
                    self.frame[self.y, self.x, 0] = self.r.get()
                    self.frame[self.y, self.x, 1] = self.g.get()
                    self.frame[self.y, self.x, 2] = self.b.get()

                    #print('draw', self.x, self.y, self.r.get(), self.g.get(), self.b.get())
                    if (self.live):
                        self.plot_img_live(self.ax, self.frame)
                
                self.x += 1
                self.inRow = True
                

            elif (self.inRow):
                self.inRow = False
                if (self.inFrame):
                    #print('y', self.y)
                    self.y += 1
                    self.x = 0


class VGATestPattern(py4hw.Logic):
    
    def __init__(self, parent, name, reset, hactive, vactive, r, g, b):
        super().__init__(parent, name)
        
        self.reset = self.addIn('reset', reset)
        self.hactive = self.addOut('hactive', hactive)
        self.vactive = self.addOut('vactive', vactive)
        self.r = self.addOut('r', r)
        self.g = self.addOut('g', g)
        self.b = self.addOut('b', b)
        self.x = 0
        self.y = 0
        
    def clock(self):
        
        divx = self.x // 80
        vr = ((divx >> 0) & 1) * 0xFF
        vg = ((divx >> 1) & 1) * 0xFF
        vb = ((divx >> 2) & 1) * 0xFF       

        self.r.prepare(vr)
        self.g.prepare(vg)
        self.b.prepare(vb)
        self.vactive.prepare(1 if self.y < 480 else 0)
        self.hactive.prepare(1 if self.x < 640 else 0)
        
        self.x += 1
        if (self.x >= 840):
            self.x = 0
            self.y += 1
            if (self.y >= 520):
                self.y = 0
            
    
sys = py4hw.HWSystem()

hactive = sys.wire('h')
vactive = sys.wire('v')
r = sys.wire('r', 8)
g = sys.wire('g', 8)
b = sys.wire('b', 8)
reset = sys.wire('reset')

py4hw.Constant(sys, 'reset', 0, reset)

vgatestpattern = VGATestPattern(sys, 'vgatest', reset, hactive, vactive, r,g,b)
vga = VGAScreen(sys, 'screen', reset, hactive, vactive, r,g,b)


# Draw schematic
if (True):
    sch = py4hw.Schematic(sys)
    sch.draw()

# Simulate    
if (True):
    #from Waveform import * 
    #wf = Waveform(sys, 'waves', [hactive, vactive])
    clks = 800*520
    t0 = time.time()
    sys.getSimulator().clk(clks)
    tf = time.time()
    td = tf-t0
    
    vga.plot_frame()
    
    print('Ellapsed time:', td, 'simulation speed:', clks//td, 'Hz FPS:', 1/td)
