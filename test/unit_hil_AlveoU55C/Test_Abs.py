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

output_dir = f'/tmp/vitis_hil_{os.getlogin()}/test_abs'

class Test_Abs:
    
    def test_create(self):
        sys = py4hw.HWSystem()

        a = sys.wire("a", 32)
        r = sys.wire("r", 32)

        dut = py4hw.Abs(sys, "abs", a, r)

        xclbin_path = os.path.join(output_dir, 'hil.xclbin')

        if not(os.path.exists(xclbin_path)):
            t0 = time.time()
            hil_plt = hil.createHILVitis(dut, output_dir)
            hil_plt.build()
            
            tf = time.time()
            lap = tf - t0
            minutes, seconds = divmod(lap, 60)
            hours, minutes = divmod(minutes, 60)

            msg = f'Abs compilation time: {lap} seconds = {hours} : {minutes:02d} : {seconds:02d}'

            with open("compilation_time.txt", "w", encoding="utf-8") as file:
                file.write(msg)

            print(msg)

        else:
            print('XCLBIN already compiled before')

            with open("output.txt", "r", encoding="utf-8") as file:
                content = file.read()

            print(content)









    def test_random(self):
        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 32)
        r = sys.wire("r", 32)
        
        py4hw.Abs(sys, "abs", a, r)

        import random
        
        for i in range(1000):
            v = random.randint(-((1<<31)-1), (1<<31)-1)
            a.put(v)
        
            sys.getSimulator().clk(1)
        
            assert(r.get() == abs(v))

    def test_random_inv(self):
        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 32)
        r = sys.wire("r", 32)
        n = sys.wire("n")
        
        py4hw.Abs(sys, "abs", a, r, inverted=n)

        import random
        
        for i in range(1000):
            v = random.randint(-((1<<31)-1), (1<<31)-1)
            a.put(v)
        
            sys.getSimulator().clk(1)
        
            assert(r.get() == abs(v))
            assert(bool(n.get()) == (v<0))
            


if __name__ == '__main__':
    pytest.main(args=['-s', 'Test_Abs.py'])
