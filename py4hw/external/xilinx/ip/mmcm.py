# -*- coding: utf-8 -*-
"""
Created on Wed Jul 29 15:15:54 2026

@author: dcr
"""

import py4hw
import math

def test(in_clk_freq, out_clk_freq):
    # VCO must be in 600-1200 MHz range
    vco_min = 600E6
    vco_max = 1200E6
    
    # we always assume a divide of 1
    vco_min_factor = vco_min / in_clk_freq 
    vco_max_factor = vco_max / in_clk_freq 
    
    min_error = math.inf
    
    for mult8 in range(int(vco_min_factor*8), int(vco_max_factor*8)+1):
        mult = mult8/8
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
            
class xilinx_mmcm(py4hw.Logic):
    
    
    def __init__(parent, name, in_clk, in_clk_freq, out_clk, out_clk_freq):
        super().__init__(parent, name)
        
        # VCO must be in 600-1200 MHz range
        vco_min = 600E6
        vco_max = 1200E6
        
        # we always assume a divide of 1
        vco_min_factor = vco_min / in_clk_freq 
        vco_max_factor = vco_max / in_clk_freq 
        
        error = math.inf
        
        for mult8 in range(int(vco_min_factor*8), int(vco_max_factor*8)+1):
            mult = mult8/8
            vco = in_clk_freq * mult
            
            if (vco < vco_min) or (vco > vco_max):
                continue
            
            factor = vco / out_clk_freq
            
            for div8 in range(int(factor*8)-1, int(factor*8)+2):
                div = div8 / 8
                
                freq = vco / div
                error = abs(freq - out_clk_freq)
                print(f'{mult}/{div} -> error {error:f}')
                
        '''
        MMCME2_BASE #(
    .BANDWIDTH("OPTIMIZED"),
    .CLKIN1_PERIOD(8.000),        // 125.0 MHz input clock (1/125MHz = 8.0ns)
    .DIVCLK_DIVIDE(1),            // PFD freq = 125 / 1 = 125.0 MHz
    .CLKFBOUT_MULT_F(8.25)     ,    // VCO freq = clk_in * mult (in 600-1200 MHz range)
    .CLKOUT0_DIVIDE_F(41),         // clk_mmcm_out = VCO freq / div  (~25.175 MHz)
    .CLKOUT0_DUTY_CYCLE(0.5),
    .CLKOUT0_PHASE(0.0),
    .CLKFBOUT_PHASE(0.0),
    .STARTUP_WAIT("FALSE")
) mmcm_inst (
    .CLKIN1(sysclk),
    .CLKOUT0(clk_mmcm_out),
    .CLKFBOUT(clk_fb),
    .CLKFBIN(clk_fb),
    .PWRDWN(1'b0),
    .RST(1'b0),             // Connect to system reset or 1'b0
    .LOCKED(mmcm_locked)
);

        '''