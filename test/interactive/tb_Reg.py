# -*- coding: utf-8 -*-
"""
Created on Sat Oct 31 12:28:11 2020

@author: dcr
"""
from py4hw.base import *
from py4hw.logic.storage import *
import py4hw.debug
import py4hw.gui as gui


sys = HWSystem()

one = sys.wire("one", 1)
e2 = sys.wire("e2", 1)
e3 = sys.wire("e2", 1)
q = sys.wire("q", 1)


TReg(sys, 'treg1', one, one, e2)
TReg(sys, 'treg2', e2, one, e3)

r3 = Reg(sys, 'reg', e3, q, enable=e2)

Constant(sys, 'one', 1, one)

#Scope(sys, 'd', e3)
#Scope(sys, 'e', e2)
#Scope(sys, 'q', q)
#Scope(sys, 'q2', q2)


# print('RESET')
# sim = Simulator(sys)

#py4hw.debug.printHierarchyWithValues(sys)

# print()
# print('CLK')
# sim.clk(4)

# py4hw.debug.printHierarchyWithValues(sys)

# print('CLK')
# sim.clk(1)

# py4hw.debug.printHierarchyWithValues(sys)

rtlgen = py4hw.VerilogGenerator(r3)
print(rtlgen.getVerilog())

#gui.Workbench(sys)