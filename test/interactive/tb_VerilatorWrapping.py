import py4hw
from py4hw.emulation.verilatorwrapping import *

hw = py4hw.HWSystem()

rst_n = hw.wire('rst_n')
angle_in = hw.wire('angle_in', 16)
sin_out = hw.wire('sin_out', 16)
cos_out = hw.wire('cos_out', 16)

ports = {'rst_n':rst_n, 'angle_in':angle_in, 'sin_out':sin_out, 'cos_out':cos_out}

cordic = create_wrapper(hw, 'cordic_pipe.v',  'cordic_pipe', '/tmp/py4hw_verilator/', ports)


py4hw.Sequence(hw, 'rst_n', [1, 0, 1], rst_n, once=True)
py4hw.Sequence(hw, 'angle_in', [0x80, 0x81, 0x82, 0x83], angle_in)

py4hw.gui.Workbench(hw)


