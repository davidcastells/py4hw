# -*- coding: utf-8 -*-
from py4hw.base import *
from py4hw.logic import *
import py4hw.debug
import py4hw.gui
import py4hw.schematic

sys = HWSystem()

a = sys.wire("a", 32)
b = sys.wire("b", 5)

r1 = sys.wire("r", 32)
r2 = sys.wire("r2", 32)

ShiftLeft(sys, "shift_left", a, b, r1)
ShiftRight(sys, "shift_right", a, b, r2, True)

Sequence(sys, "a", [1,2,3,4,5, 0XFFFFFFF0, 0XFFFFFF50, 0XFFFFF1F0, 0X80FF11F0], a)
Sequence(sys, "b", [1,3,5,7,11, 13], b)


py4hw.gui.Workbench(sys)


