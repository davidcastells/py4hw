# -*- coding: utf-8 -*-
from py4hw.base import *
from py4hw.logic import *
import py4hw.debug
import py4hw.gui
import py4hw.schematic

sys = HWSystem()

a = sys.wire("a", 64)
b = sys.wire("b", 6)
arit = sys.wire("arit", 1)

r1 = sys.wire("r", 64)
r2 = sys.wire("r2", 64)
r3 = sys.wire("r3", 64)
r4 = sys.wire("r4", 64)
r5 = sys.wire("r5", 64)

ShiftLeft(sys, "shift_left", a, b, r1)
ShiftRight(sys, "shift_right", a, b, r2, True)
ShiftRight(sys, "shift_righta", a, b, r3, arit)
RotateLeft(sys, "rotate_left", a, b, r4)
RotateRight(sys, "rotate_right", a, b, r5)

Sequence(sys, "a", [0x400, 1,2,3,4,5, 0XFFFFFFF0, 0XFFFFFF50, 0XFFFFF1F0, 0X80FF11F0], a)
Sequence(sys, "b", [52, 1,3,5,7,11, 13], b)
Sequence(sys, "arit", [0,1], arit)


py4hw.gui.Workbench(sys)


