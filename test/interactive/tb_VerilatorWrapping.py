import py4hw
from py4hw.emulation.verilatorwrapping import *


import os
import sys
import subprocess

try:
    import pybind11
except ImportError:
    print(
        "ERROR: pybind11 is not installed.\n"
        "Please install it using: pip install pybind11\n"
        "If you're using a virtual environment, make sure it's activated."
    )
    sys.exit(1)

# Check if the pybind11 headers are available
try:
    import pybind11.get_include
    include_dir = pybind11.get_include()
    print(f"pybind11 headers found at: {include_dir}")
except Exception as e:
    print(f"Warning: Could not find pybind11 headers: {e}")
    print("Make sure pybind11 is properly installed.")



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
an = py4hw.StreamCapture(hw, 'angle', angle_in)

#py4hw.gui.Workbench(hw)
hw.getSimulator().clk(300)

import matplotlib.pyplot as plt

# Create a figure with 2 rows and 1 column
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))

# Plot on the first subplot
ax1.plot(sc.data, label='sin wave', color='blue')
ax1.legend()
ax1.grid(True)

# Plot on the second subplot
ax2.plot(an.data, label='angle', color='orange')
ax2.legend()
ax2.grid(True)

plt.tight_layout()
plt.show()
