# -*- coding: utf-8 -*-
from py4hw.base import *
from py4hw.logic import *
from py4hw.storage import RegSR
from py4hw.simulation import Simulator
import py4hw.debug

sys = HWSystem()

BusB = Wire(sys, "Bus", 32)
qS = Wire(sys, "S Out", 32)
qR = Wire(sys, "R Out", 32)
ld_s = Wire(sys, "Load S", 1)
ld_r = Wire(sys, "Load R", 1)
inic_rs = Wire(sys, "Iniciar R/S", 1)
zero = Wire(sys, "Zero", 1)

Constant(sys, "0", 0, zero)

s = RegSR(sys, "S", BusB, ld_s, qS, inic_rs, zero, 1)
r = RegSR(sys, "R", BusB, ld_r, qR, zero, inic_rs)

Scope(sys, "S Out", qS)
Scope(sys, "R Out", qR)

py4hw.debug.printHierarchy(sys)

print('RESET')
sim = Simulator(sys)

print()
print('CLK')
inic_rs.put(1)
ld_r.put(0)
ld_s.put(0)
sim.clk(1)

print()
print('CLK')
inic_rs.put(0)
ld_r.put(0)
ld_s.put(0)
BusB.put(42)
sim.clk(1)

print()
print('CLK')
ld_r.put(1)
ld_s.put(1)
sim.clk(1)

print()
print('CLK')
sim.clk(1)