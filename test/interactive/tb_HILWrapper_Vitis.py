import py4hw
import os
import sys
import py4hw.emulation.vitiswrapping as hil

class DUT(py4hw.Logic):

   def __init__(self, parent, name, a, b, p, m):
      super().__init__(parent, name)
 
      self.addIn('a', a)
      self.addIn('b', b)
      self.addOut('p', p)
      self.addOut('m', m)

      py4hw.Add(self, 'add', a, b, p)
      py4hw.Sub(self, 'sub', a, b, m)

class RGB2YCrCb(py4hw.Logic):
    
    def __init__(self, parent, name, reset, enable, a, b, ctrl, alu_result , result, done):
        
        super().__init__(parent, name)


        self.addIn('reset', reset)
        self.addIn('enable', enable)
        self.addIn('ctrl', ctrl)
        self.addIn('data0', a)
        self.addIn('data1', b)
        self.addIn('alu_result', alu_result)
        self.addOut('result', result)
        self.addOut('done', done)        
        
        r = self.wire('r', 8)
        g = self.wire('g', 8)
        b = self.wire('b', 8)
        
        py4hw.Range(self, 'r', a, 23, 16, r)
        py4hw.Range(self, 'g', a, 15, 8, g)
        py4hw.Range(self, 'b', a, 7, 0, b)
        
        yr = self.wire('yr', 32)
        yg = self.wire('yg', 32)
        yb = self.wire('yb', 32)

        crr = self.wire('crr', 32)
        crg = self.wire('crg', 32)
        crb = self.wire('crb', 32)

        cbr = self.wire('cbr', 32)
        cbg = self.wire('cbg', 32)
        cbb = self.wire('cbb', 32)

                
        yrc = self.wire('yrc', 32)
        ygc = self.wire('ygc', 32)
        ybc = self.wire('ybc', 32)
        
        crrc = self.wire('crrc', 32)
        crgc = self.wire('crgc', 32)
        crbc = self.wire('crbc', 32)

        cbrc = self.wire('cbrc', 32)
        cbgc = self.wire('cbgc', 32)
        cbbc = self.wire('cbbc', 32)

        ys1 = self.wire('ys1', 32)
        ys2 = self.wire('ys2', 32)
                        
        crs1 = self.wire('crs1', 32)
        crs2 = self.wire('crs2', 32)
        crs3 = self.wire('crs3', 32)
                                
        cbs1 = self.wire('cbs1', 32)
        cbs2 = self.wire('cbs2', 32)
        cbs3 = self.wire('cbs3', 32)

        y = self.wire('y', 8)
        cr = self.wire('cr', 8)
        cb = self.wire('cb', 8)
        
        k128 = self.wire('k128', 32)
        
        # Compute Y
        py4hw.Constant(self, 'yrc', 19595, yrc)
        py4hw.Constant(self, 'ygc', 38470, ygc)
        py4hw.Constant(self, 'ybc', 7471, ybc)
        
        py4hw.Mul(self, 'yr', r, yrc, yr)
        py4hw.Mul(self, 'yg', g, ygc, yg)
        py4hw.Mul(self, 'yb', b, ybc, yb)
        
        py4hw.Add(self, 'ys1', yr, yg, ys1)
        py4hw.Add(self, 'ys2', ys1, yb, ys2)
        py4hw.ShiftRightConstant(self, 'y', ys2, 16, y)
        
        # Compute Cr
        py4hw.Constant(self, 'k128', 128, k128)
        py4hw.Constant(self, 'crrc', 11059, crrc)
        py4hw.Constant(self, 'crgc', 21610, crgc)
        py4hw.Constant(self, 'crbc', 32768, crbc) # this could be a shift 
        
        py4hw.Mul(self, 'crr', r, crrc, crr)
        py4hw.Mul(self, 'crg', g, crgc, crg)
        py4hw.Mul(self, 'crb', b, crbc, crb)
        
        py4hw.Sub(self, 'crs1', crb, crg, crs1)
        py4hw.Sub(self, 'crs2', crs1, crr, crs2)
        py4hw.ShiftRightConstant(self, 'crs3', crs2, 16, crs3)
        #py4hw.Add(self, 'cr', k128, crs3, cr)
        #NEW:
        cr_full = self.wire('cr_full', 33)
        py4hw.Add(self, 'cr_add', k128, crs3, cr_full)
        py4hw.Range(self, 'cr_trunc', cr_full, 7, 0, cr)
                                       
        # Compute Cb
        py4hw.Constant(self, 'cbrc', 32768, cbrc) # this could be a shift                                        
        py4hw.Constant(self, 'cbgc', 27439, cbgc) 
        py4hw.Constant(self, 'cbbc', 5329, cbbc) 
        
        py4hw.Mul(self, 'cbr', r, cbrc, cbr)
        py4hw.Mul(self, 'cbg', g, cbgc, cbg)
        py4hw.Mul(self, 'cbb', b, cbbc, cbb)
        
        py4hw.Sub(self, 'cbs1', cbr, cbg, cbs1)
        py4hw.Sub(self, 'cbs2', cbs1, cbb, cbs2)
        py4hw.ShiftRightConstant(self, 'cbs3', cbs2, 16, cbs3)
        #py4hw.Add(self, 'cb', k128, cbs3, cb)
        #NEW:
        cb_full = self.wire('cb_full', 33)
        py4hw.Add(self, 'cb_add', k128, cbs3, cb_full)
        py4hw.Range(self, 'cb_trunc', cb_full, 7, 0, cb)
                
        # int yy = (19595 * r + 38470 * g + 7471 * b) >> 16;
        # int cr = 128 + ((-11059 * r - 21610 * g + 32768 * b) >> 16);
        # int cb = 128 + ((32768 * r - 27439 * g - 5329 * b) >> 16);
        
        zero8 = self.wire('zero8', 8)
        py4hw.Constant(self, 'zero8', 0, zero8)
        
        
        py4hw.ConcatenateMSBF(self, 'result', [zero8, y, cr, cb], result)        
        
        py4hw.Reg(self, 'done', d=enable, q=done, reset=reset)




hw = py4hw.HWSystem()

#comment/uncomment because I am changing the wires
#to test with another DUT

a = hw.wire('a', 32)
b = hw.wire('b', 32)

p = hw.wire('p', 32)
s = hw.wire('s', 32)


#reset      = hw.wire('reset')           # 1 bit
#enable     = hw.wire('enable')          # 1 bit
#ctrl       = hw.wire('ctrl', 32)
#a          = hw.wire('a', 32)           # -> port data0 (pixel)
#b          = hw.wire('b', 32)           # -> port data1 (not used)
#alu_result = hw.wire('alu_result', 32)  # -> not used
#result     = hw.wire('result', 32)      # out
#done       = hw.wire('done')            # 1 bit out




#comment/uncomment because I am changing the sequence
#to test with another DUT
py4hw.Sequence(hw, 'a', [1,2,3,4,5,6,7], a)
py4hw.Sequence(hw, 'b', [0x1A00,0x2B00,0x3C00], b)
#py4hw.Sequence(hw, 'reset',      [0], reset)
#py4hw.Sequence(hw, 'enable',     [0, 1], enable)
#py4hw.Sequence(hw, 'ctrl',       [0], ctrl)
#py4hw.Sequence(hw, 'a', [0xFF0000, 0x00FF00, 0x0000FF], a) 
#py4hw.Sequence(hw, 'a',          [0x87CEEB], a)   #0x87CEEB blue pixel 
#py4hw.Sequence(hw, 'b',          [0], b)
#py4hw.Sequence(hw, 'alu_result', [0], alu_result)


dut = DUT(hw, 'dut', a, b, p, s)
#to change the dut
#dut = RGB2YCrCb(hw, 'rgb2ycrcb', reset, enable, a, b, ctrl, alu_result, result, done)

#output_dir = f'/tmp/vitis_hil_{os.getlogin()}'
output_dir = f'/tmp/vitis_hil_{os.getlogin()}/dut_simp'


import py4hw.emulation.vitiswrapping as hil

hil_plt = hil.createHILVitis(dut, output_dir)
xclbin_path = os.path.join(output_dir, 'hil.xclbin')

if os.path.exists(xclbin_path):
    # xclbin already exists -> do NOT rebuild (build() would wipe the directory).
    # Just run on the board with the values from the command line (a=5 b=3 ...).
    values = hil.parse_input_values(sys.argv[1:])
    #hil_plt.download(values)
    
    # --- NEW: HIL redirector -- the FPGA runs INSIDE the py4hw simulation ---   
    # --- (generic -- works for any DUT) --- input wires already feeding the DUT
    proxy_ins  = [pin.wire for pin in dut.inPorts]
    # fresh output wires for the proxy, matching the DUT's output widths
    proxy_outs = [hw.wire(pout.name + '_hw', pout.wire.getWidth())for pout in dut.outPorts]

    hil.createHILVitisProxy(dut, hw, 'dut_hw', proxy_ins, proxy_outs, xclbin_path)

    # waveform: DUT inputs + DUT outputs (simulated) + proxy outputs (real HW)
    dut_outs = [pout.wire for pout in dut.outPorts]
    py4hw.Waveform(hw, 'wvf', proxy_ins + dut_outs + proxy_outs)
    py4hw.gui.Workbench(hw)
    
else:
    # First time: generate everything. There is no xclbin yet.
    hil_plt.build()
    print('\n[NEXT STEP] build the xclbin:')
    print('   bash', os.path.join(output_dir, 'build_xclbin.sh'))
    print('then run again with the values, e.g.:')
    print('   python tb_HILWrapper_Vitis.py a=5 b=3')
    


