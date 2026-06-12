import py4hw
import os
import py4hw.emulation.vitiswrapping as hil

#from RGB2YCrCb import RGB2YCrCb      # <-- afegit

#la trec/afegeixo pq estic provant amb el dut RGB2YCrCb
class DUT(py4hw.Logic):

   def __init__(self, parent, name, a, b, p, m):
      super().__init__(parent, name)

      self.addIn('a', a)
      self.addIn('b', b)
      self.addOut('p', p)
      self.addOut('m', m)

      py4hw.Add(self, 'add', a, b, p)
      py4hw.Sub(self, 'sub', a, b, m)



    


hw = py4hw.HWSystem()

#comento pq canvio els wires per provar amb altre DUT
a = hw.wire('a', 32)
b = hw.wire('b', 32)

p = hw.wire('p', 32)
s = hw.wire('s', 32)
#reset      = hw.wire('reset')
#enable     = hw.wire('enable')
#ctrl       = hw.wire('ctrl', 32)
#a          = hw.wire('a', 32)
#b          = hw.wire('b', 32)
#alu_result = hw.wire('alu_result', 32)
#result     = hw.wire('result', 32)
#done       = hw.wire('done')

#comento pq canvio els sequence per provar amb altre DUT
py4hw.Sequence(hw, 'a', [1,2,3,4,5,6,7], a)
py4hw.Sequence(hw, 'b', [0x1A00,0x2B00,0x3C00], b)
#py4hw.Sequence(hw, 'reset',      [0], reset)
#py4hw.Sequence(hw, 'enable',     [0, 1], enable)
#py4hw.Sequence(hw, 'ctrl',       [0], ctrl)
#py4hw.Sequence(hw, 'a',          [0xFF0000, 0x00FF00, 0x0000FF], a)
#py4hw.Sequence(hw, 'b',          [0], b)
#py4hw.Sequence(hw, 'alu_result', [0], alu_result)


dut = DUT(hw, 'dut', a, b, p, s)
#canvio el dut
#dut = RGB2YCrCb(hw, 'rgb2ycrcb', reset, enable, a, b, ctrl, alu_result, result, done)

output_dir = f'/tmp/vitis_hil_{os.getlogin()}'


import py4hw.emulation.vitiswrapping as hil

if (True):
    hil_plt = hil.createHILVitis(dut, output_dir)
    #el poso mes avall
    #py4hw.gui.Workbench(hil_plt.platform)
    hil_plt.build()
    hil_plt.download()
       
    #py4hw.gui.Workbench(hil_plt.platform)
	
#import os
#os.makedirs(output_dir, exist_ok=True)

#hil.generate_connectivity(dut, output_dir)
#hil.generate_reader(dut, output_dir)
#hil.generate_writer(dut, output_dir)

#dut_files = hil.generate_verilog(dut, output_dir)

#hil.generate_package_tcl(dut, dut_files, output_dir)
#hil.generate_rtl_kernel(output_dir)
