# -*- coding: utf-8 -*-
"""
Created on Mon Dec  4 19:34:59 2023

@author: dcr
"""
import py4hw

class intel_lpm_counter(py4hw.Logic):
    def __init__(self, parent, name, reset, q):
        super().__init__(parent, name)
        
        if (reset):
            self.reset = self.addIn('reset', reset)
        else:
            self.reset = None
            
        self.q = self.addOut('q', q)
        
    def clock(self):
        if not(self.reset is None):
            if (self.reset.get() == 1):
                self.q.prepare(0)
                return

        self.q.prepare(self.q.get() + 1)

    def verilogBody(self):
        
        clkname = py4hw.getObjectClockDriver(self).name
        
        str = ' lpm_counter i0 ('
        str += '  .clock('+clkname+'),\n'
        str += '  .q(q),\n'
        
        if not(self.reset is None):
            str += '  .sclr(reset),\n'

        str += "  .updown(1'b1));\n"
        str += ' defparam\n'
        str += '   i0.lpm_direction = "UP",\n'
        str += '   i0.lpm_port_updown = "PORT_UNUSED",\n'
        str += '   i0.lpm_type = "LPM_COUNTER",\n'
        str += '   i0.lpm_width = {};\n'.format(self.q.getWidth())

        return str

#  lpm_counter	LPM_COUNTER_component (
# .clock (CLOCK_50),
# .q (sub_wire0),
# .aclr (1'b0),
# .aload (1'b0),
# .aset (1'b0),
# .cin (1'b1),
# .clk_en (1'b1),
# .cnt_en (1'b1),
# .cout (),
# .data ({64{1'b0}}),
# .eq (),
# .sclr (1'b0),
# .sload (1'b0),
# .sset (1'b0),
# .updown (1'b1));
# param
# M_COUNTER_component.lpm_direction = "UP",
# M_COUNTER_component.lpm_port_updown = "PORT_UNUSED",
# M_COUNTER_component.lpm_type = "LPM_COUNTER",
# M_COUNTER_component.lpm_width = 64;
