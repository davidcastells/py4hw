# -*- coding: utf-8 -*-
"""
Created on Wed Feb  2 05:59:29 2022

@author: dcr
"""

import py4hw
import py4hw.debug
import os
import pytest
import time
import py4hw.emulation.vitiswrapping as hil

output_dir = f'/tmp/vitis_hil_{os.getlogin()}/test_signedadd'
xclbin_path = os.path.join(output_dir, 'hil.xclbin')
time_path = os.path.join(output_dir, "compilation_time.txt")

class Test_SignedAdd:
    
    def test_create(self):
        hw = py4hw.HWSystem()

        a = hw.wire("a", 32)
        b = hw.wire("b", 32)
        r = hw.wire("r", 32)
        ci = hw.wire('ci')
        co = hw.wire('co')

        
        dut = py4hw.SignedAdd(hw, 'signedadd', a, b, r, ci=ci, co=co, width_check=False)
     


        if not(os.path.exists(xclbin_path)):
            t0 = time.time()
            hil_plt = hil.createHILVitis(dut, output_dir)
            hil_plt.build()
            
            tf = time.time()
            lap = int(tf - t0)
            minutes, seconds = divmod(lap, 60)
            hours, minutes = divmod(minutes, 60)

            

            msg = f'SignedAdd compilation time: {lap} seconds = {hours} : {minutes:02d} : {seconds:02d}\n'

            with open(time_path, "w", encoding="utf-8") as file:
                file.write(msg)

            print(msg)

        else:
            print('XCLBIN already compiled before')

            with open(time_path, "r", encoding="utf-8") as file:
                content = file.read()

            print(content)


    def test_random(self):
        hw = py4hw.HWSystem()
        
        a = hw.wire("a", 32)
        b = hw.wire("b", 32)
        r = hw.wire("r", 32)
        ci = hw.wire('ci')
        co = hw.wire('co')
        
        dut = py4hw.SignedAdd(hw, 'signedadd', a, b, r, ci=ci, co=co, width_check=False)

        proxy_ins  = [pin.wire for pin in dut.inPorts]
        # fresh output wires for the proxy, matching the DUT's output widths
        proxy_outs = [hw.wire(pout.name + '_hw', pout.wire.getWidth()) for pout in dut.outPorts]

        hil.createHILVitisProxy(dut, hw, 'dut_hw', proxy_ins, proxy_outs, xclbin_path)

        # waveform: DUT inputs + DUT outputs (simulated) + proxy outputs (real HW)
        dut_outs = [pout.wire for pout in dut.outPorts]

        import random
        
        for i in range(1000):
            va = random.randint(-((1<<31)-1), (1<<31)-1)
            vb = random.randint(-((1<<31)-1), (1<<31)-1)
            vci = random.randint(0, 2) % 2
            a.put(va)
            b.put(vb)
            ci.put(vci)
            print('Testing', va, vb, vci, end=' ')
        
            hw.getSimulator().clk(1)
        
            for k in range(len(dut_outs)):
                print(f'DUT[k]={dut_outs[k].get()}', f'FPGA[k]={proxy_outs[k].get()}')
                assert(dut_outs[k].get() == proxy_outs[k].get() )

            


if __name__ == '__main__':
    pytest.main(args=['-s', 'Test_SignedAdd.py'])
