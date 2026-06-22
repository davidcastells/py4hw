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

design_name = 'FPAdder'
output_dir = f'/tmp/vitis_hil_{os.getlogin()}/test_fxpadder'
xclbin_path = os.path.join(output_dir, 'hil.xclbin')
time_path = os.path.join(output_dir, "compilation_time.txt")

class Test_FXPAdder:
    
    def test_create(self):
        hw = py4hw.HWSystem()

        a = hw.wire("a", 32)
        b = hw.wire("b", 32)
        r = hw.wire("r", 32)

        dut = py4hw.FixedPointAdd(hw, 'fpa', a=a, af=(1,15,16), b=b , bf=(1,15,16), r=r, rf=(1,15,16))


        if not(os.path.exists(xclbin_path)):
            t0 = time.time()
            hil_plt = hil.createHILVitis(dut, output_dir)
            hil_plt.build()
            
            tf = time.time()
            lap = int(tf - t0)
            minutes, seconds = divmod(lap, 60)
            hours, minutes = divmod(minutes, 60)

            

            msg = f'{design_name} compilation time: {lap} seconds = {hours} : {minutes:02d} : {seconds:02d}\n'

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
        
        dut = py4hw.FixedPointAdd(hw, 'fpa', a=a, af=(1,15,16), b=b , bf=(1,15,16), r=r, rf=(1,15,16))

        proxy_ins  = [pin.wire for pin in dut.inPorts]
        # fresh output wires for the proxy, matching the DUT's output widths
        proxy_outs = [hw.wire(pout.name + '_hw', pout.wire.getWidth()) for pout in dut.outPorts]

        hil.createHILVitisProxy(dut, hw, 'dut_hw', proxy_ins, proxy_outs, xclbin_path)

        # waveform: DUT inputs + DUT outputs (simulated) + proxy outputs (real HW)
        dut_outs = [pout.wire for pout in dut.outPorts]

        import random
        t0 = time.time()
        
        for i in range(1000):
            va = random.randint(-((1<<31)-1), (1<<31)-1)
            vb = random.randint(-((1<<31)-1), (1<<31)-1)
            a.put(va)
            b.put(vb)
            print('Testing', va, vb, end=' ')
        
            hw.getSimulator().clk(1)
        
            for k in range(len(dut_outs)):
                print(f'DUT[{k}]={dut_outs[k].get()}', f'FPGA[{k}]={proxy_outs[k].get()}')
                assert(dut_outs[k].get() == proxy_outs[k].get() )

        tf = time.time()
        lap = tf-t0
        sps = 1000/lap
        print(f'Run 1000 tests in {lap} seconds => {sps} samples / second')

            


if __name__ == '__main__':
    pytest.main(args=['-s', 'Test_FXPAdder.py'])
