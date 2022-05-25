# -*- coding: utf-8 -*-
"""
Created on Sun Nov  1 13:29:10 2020

@author: dcr
"""

from tkinter import *
from tkinter import ttk        
    
root = Tk()

panedwindow = ttk.Panedwindow(root, orient = HORIZONTAL)
panedwindow.pack(fill = BOTH, expand = True)

frame1 = ttk.Frame(panedwindow, width = 100, height = 300)
frame2 = ttk.Frame(panedwindow, width = 400, height = 400, relief = SUNKEN)
# panedwindow listed first as these are children of panedwindow.
panedwindow.add(frame1 )
panedwindow.add(frame2 )

# Forget doesn't destroy the frame, it still exists in the background and can
# be re-added to the paned window or used elsewhere in the GUI if desired.

root.mainloop()