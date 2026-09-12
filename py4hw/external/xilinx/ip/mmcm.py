# -*- coding: utf-8 -*-
"""
Created on Wed Jul 29 15:15:54 2026

@author: dcr
"""

import py4hw
import math

def select_best_mult_div(in_clk_freq, out_clk_freq, mult=None, vco_min = 600E6, vco_max = 1200E6):
    # By default VCO must be in 600-1200 MHz range
    
    # we always assume a divide of 1
    vco_min_factor = vco_min / in_clk_freq 
    vco_max_factor = vco_max / in_clk_freq 
    
    min_error = math.inf
    min_mult = None
    min_div = None
    

    if mult is None:
        mults = [mult8/8 for mult8 in range(int(vco_min_factor*8), int(vco_max_factor*8)+1)]
    else:
        mults = [mult]

    print(f'checking mult {mults}')
                    
    for mult in mults:
        vco = in_clk_freq * mult
        
        if (vco < vco_min) or (vco > vco_max):
            continue
        
        factor = vco / out_clk_freq
        
        for div8 in range(int(factor*8)-1, int(factor*8)+2):
            div = div8 / 8
            
            freq = vco / div
            error = abs(freq - out_clk_freq)
            
            if (error < min_error):
                rel_error = error * 100 / out_clk_freq
                print(f'{mult}/{div} vco: {vco} freq: {freq} -> error {rel_error:f}')
                min_error = error
                min_mult = mult
                min_div = div
                
    return min_mult, min_div
            
class xilinx_mmcm(py4hw.Logic):
    
    
    def __init__(self, parent, name, in_clk_freq, out_clk1, out_clk2, out_clk1_freq=None, out_clk2_freq=None, vco_min = 600E6, vco_max = 1200E6, mult=None, div1=None, div2=None):
        super().__init__(parent, name)
        
        self.in_clk_freq = in_clk_freq
        
        if not(mult is None):
            self.mult = mult
            
            self.div1 = div1
            self.div2 = div2
            
            self.addOut('clk0', out_clk1)
            self.addOut('clk1', out_clk2)
            
            return 
        
        print('Selecting best MULT/DIV for clk 1')
        mult1, div1 = select_best_mult_div(in_clk_freq, out_clk1_freq, vco_min=vco_min, vco_max=vco_max, mult=mult)
        
        self.mult = mult1
        self.div1 = div1
        
        self.addOut('clk0', out_clk1)
        
        if not(out_clk2_freq is None):
            print('Selecting best MULT/DIV for clk 2')
            _, div2 = select_best_mult_div(in_clk_freq, out_clk2_freq, mult=mult1, vco_min=vco_min, vco_max=vco_max)
        
            self.div2 = div2
            self.addOut('clk1', out_clk2)
        else:
            self.div2 = None
        
    def clock(self):
        # dummy to force a sequential logic circuit
        pass
        
    def verilogBody(self):
        # provide a custom implementation of the circuit

        clkDrv = py4hw.getObjectClockDriver(self)
                
        period_ns = 1E9 / self.in_clk_freq

        s = 'wire clk_fb;\n'
        s += 'wire mmcm_locked;\n'
        
        s += 'MMCME2_ADV #(\n'
        s += '.BANDWIDTH("OPTIMIZED"),\n'
        s += f'.CLKIN1_PERIOD({period_ns}),        // ns\n'
        s += '.DIVCLK_DIVIDE(1), \n'
        s += f'.CLKFBOUT_MULT_F({self.mult}), \n'
        s += f'.CLKOUT0_DIVIDE_F({self.div1}),\n'
        s += '.CLKOUT0_DUTY_CYCLE(0.5),\n'
        s += '.CLKOUT0_PHASE(0.0),\n'

        if not(self.div2 is None):
            s += f'.CLKOUT1_DIVIDE({self.div2}),\n'
            s += '.CLKOUT1_DUTY_CYCLE(0.5),\n'
            s += '.CLKOUT1_PHASE(0.0),\n'
    
        s += '.CLKFBOUT_PHASE(0.0),\n'
        s += '.STARTUP_WAIT("FALSE")\n'
        s += ') mmcm_inst (\n'
        s += f'.CLKIN1({clkDrv.name}),\n'
        s += '.CLKOUT0(clk0),\n'
        
        if not(self.div2 is None):
            s += '.CLKOUT1(clk1),\n'
            
        s += '.CLKFBOUT(clk_fb),\n'
        s += '.CLKFBIN(clk_fb),\n'
        s += ".PWRDWN(1'b0),\n"
        s += ".RST(1'b0),\n"
        s += '.LOCKED(mmcm_locked));\n'

        
        
        return s
