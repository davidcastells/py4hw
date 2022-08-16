# -*- coding: utf-8 -*-
"""
Created on Mon Aug 15 17:38:54 2022

@author: dcr
"""
from tkinter import *
import py4hw

root = Tk()
root.title('Test Tkinter render')

canvas = py4hw.TkinterRender(root, (800, 800))

canvas.canvas.pack(expand=True, fill=BOTH)

x = 25
y = 25
w = 100
h = 50

canvas.drawRectangle(x, y, x+w, y+h)
canvas.drawLine(x, y, x+w, y+h)

y = 100

canvas.drawRectangle(x, y, x+w, y+h)
canvas.drawArc(x, y, x+w, y+h, -90, 90)

y = 200

canvas.drawSpline([x+2*w//10, x+3*w//10, x+4*w//10, x+5*w//10], [y,  y+2*h//10, y+3*h//10, y+4*h//10])
canvas.drawRectangle(x, y, x+w, y+h)

root.mainloop()