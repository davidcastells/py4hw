import py4hw
from py4hw.emulation.verilatorwrapping import *

hw = py4hw.HWSystem()

rst_n = hw.wire('rst_n')
reset = hw.wire('reset')
inc = hw.wire('inc')
step = hw.wire('step', 16)
angle_in = hw.wire('angle_in', 16)
sin_out = hw.wire('sin_out', 16)
cos_out = hw.wire('cos_out', 16)


req_freq = 440E3 
clk_freq = 50E6 # 50 MHz

FTW = int(req_freq/clk_freq * 2**16)

ports = {'rst_n':rst_n, 'angle_in':angle_in, 'sin_out':sin_out, 'cos_out':cos_out}

cordic = create_wrapper(hw, 'cordic_pipe.v',  'cordic_pipe', '/tmp/py4hw_verilator/', ports)


py4hw.Sequence(hw, 'rst_n', [1, 0, 1], rst_n, once=True)

py4hw.Not(hw, 'reset', rst_n, reset)
py4hw.StepUpCounter(hw, 'count', inc=inc, step=step, q=angle_in, reset=reset)
py4hw.Constant(hw, 'step', FTW, step)
py4hw.Constant(hw, 'inc', 1, inc)

sc = py4hw.StreamCaptureSigned(hw, 'sin', sin_out)

py4hw.gui.Workbench(hw)

import matplotlib.pyplot as plt
plt.plot(sc.data)
plt.show()
