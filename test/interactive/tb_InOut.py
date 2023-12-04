#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct  7 08:20:21 2023

@author: dcr
"""

import py4hw



            
sys = py4hw.HWSystem()
            
bidir = sys.bidir_wire('bidir')
poe = sys.wire('poe')   
pout = sys.wire('pout')
pin = sys.wire('pin')
         
py4hw.Sequence(sys, 'bidir', [0,0,0,1, 1], bidir)
py4hw.Sequence(sys, 'poe', [1,0,0,0,0,0,0], poe)
py4hw.Sequence(sys, 'pout', [0, 1], pout)

py4hw.BidirBuf(sys, 'iobuf', pin, pout, poe, bidir)

wvf = py4hw.Waveform(sys, 'wvf', [pin, pout, poe, bidir])

py4hw.gui.Workbench(sys)

sys.getSimulator().clk(30)
wvf.gui()

