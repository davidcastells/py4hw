# -*- coding: utf-8 -*-
"""
Created on Wed Jul 31 11:40:07 2024

@author: 2016570
"""

from py4hw.base import *
from py4hw.logic import *
from py4hw.logic.storage import *
from py4hw.simulation import *
import py4hw.debug


class SerialAdder(Logic):
    def __init__(self, parent:Logic, name:str, a:Wire, r:Wire):
        super().__init__(parent, name)
        
        self.a = self.addIn("a", a)
        self.r = self.addOut("r", r)
        
        d = Wire(self, "d", a.getWidth())
        Add(self, "add", a, r, d)
        
        e = self.wire('e', 1)
        Constant(self, 'e', 1, e)
        Reg(self, "reg", d, r, enable=e)
 

class WrappedAnd(py4hw.Logic):
    def __init__(self, parent, name, a, b, r):
        super().__init__(parent, name)
        
        self.addIn('a', a)
        self.addIn('b', b)
        self.addOut('r', r)
        
        py4hw.And2(self, 'and', a, b, r)

class RandomValue(py4hw.Logic):
    def __init__(self, parent, name, r, mean, stddev):
        super().__init__(parent, name)
        
        self.r = self.addOut('r', r)
        
        self.mean = mean
        self.stddev = stddev
        self.state = '{} <- {}+-{}'.format(self.r.get(), self.mean, self.stddev)
        
    def clock(self):
        import numpy as np
        v = int(np.random.normal(self.mean, self.stddev))
        self.r.prepare(v)
        self.state = '{} <- {}+-{}'.format(v, self.mean, self.stddev)
        
    def update_mean(self, v):
        self.mean = float(v)
        self.label1.config(text="Mean: {}".format(self.mean))
        
    def update_stddev(self, v):
        self.stddev = float(v)
        self.label2.config(text="Stddev: {}".format(self.stddev))
        
    def tkinter_gui(self, parent):
        from tkinter import ttk
        import tkinter as tk
        frame = ttk.Frame(parent, padding="10")
        frame.grid(column=2, row=2, sticky=(tk.W, tk.E, tk.N, tk.S))

        maxv = (2 ** self.r.getWidth()) -1
        
        print('maxv : ', maxv)
        
        # Create sliders and labels
        
        self.label1 = ttk.Label(frame, text="Mean: {}".format(self.mean))
        self.label2 = ttk.Label(frame, text="Stddev: {}".format(self.stddev))

        slider1 = ttk.Scale(frame, from_=0, to=maxv, orient="horizontal", command=self.update_mean)
        slider1.set(self.mean)
        slider2 = ttk.Scale(frame, from_=0, to=maxv, orient="horizontal", command=self.update_stddev)
        slider2.set(self.stddev)
        
        

        # Grid layout for sliders and labels
        slider1.grid(column=0, row=0,  pady=10)
        slider2.grid(column=0, row=1,  pady=10)
        self.label1.grid(column=1, row=0, padx=5)
        self.label2.grid(column=1, row=1, padx=5)
        
        # Configure column weights to make the sliders and labels expandable
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        
        return frame
    



sys = HWSystem()

a = Wire(sys, "a", 4)
b = Wire(sys, "b", 4)
c = Wire(sys, "c", 4)
d = Wire(sys, "d", 4)
e = Wire(sys, "e", 4)

r = Wire(sys, "r", 4)

Constant(sys, 'inc', 3, a)
Constant(sys, 'b', 2, b)
sa = SerialAdder(sys, "sa", a, r)
#And2(sys, 'and', a, b, c)
WrappedAnd(sys, 'and', a, a, c)
WrappedAnd(sys, 'and2', a, c, d)
rnd = RandomValue(sys, 'random', e, 1, 1)

wires = py4hw.debug.getPorts(sa)
wires.append(FieldInspector(rnd, 'state'))

wvf = Waveform(sys, 'wvf', wires)
sys.getSimulator().clk(10)

#wvf.draw_tkinter()
wvf.gui()
