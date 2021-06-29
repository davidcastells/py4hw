import sys
sys.path.append('../..')

import py4hw


sys = py4hw.HWSystem()

a = sys.wire('a',8)
b = sys.wire('b',8)
r = sys.wire('r', 8)

py4hw.Constant(sys, 'a', 3, a)
py4hw.Constant(sys, 'b', 3, b)
py4hw.Add(sys, 'add', a, b, r)
py4hw.Scope(sys, 'r', r)

py4hw.debug.checkIntegrity(sys)

sch = py4hw.Schematic(sys)