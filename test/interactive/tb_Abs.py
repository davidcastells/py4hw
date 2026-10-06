# -*- coding: utf-8 -*-
"""
Created on Tue Sep 29 17:32:37 2026

@author: dcr
"""

import py4hw

class MonitorWire(py4hw.Logic):
    
    def __init__(self, parent, name, w:py4hw.Wire):
        super().__init__(parent, name)
        
        self.wire = self.addIn('in', w)
        self.toggle_bits = 0
        
    def monitor(self):
        #print('value', self.wire.name, hex(self.wire.get()))
        #w = self.wire.getWidth()
        self.toggle_bits = self.toggle_bits | self.wire.get()
        
        
hw = py4hw.HWSystem()

a = hw.wire("a", 32)
r = hw.wire("r", 32)

#py4hw.Sequence(hw, 'a', [0,1,2,3, 100, -1], a)
py4hw.RandomUniform(hw, 'a', a)

dut = py4hw.Abs(hw, "abs", a, r)

#py4hw.gui.Workbench(hw)

all_wires = list(dut._wires.values())
all_wires.extend([p.wire for p in dut.inPorts])
all_wires.extend([p.wire for p in dut.outPorts])
print(all_wires)

monitors = []
for w in all_wires:
    m = MonitorWire(dut, 'monitor_'+ w.name, w)
    monitors.append(m)
    
    
#py4hw.gui.Workbench(hw)    
hw.getSimulator().clk(10)

for i in range(len(monitors)):
    w = monitors[i].wire.getWidth() 
    toggled = monitors[i].toggle_bits
    mask = (1 << w) -1
    uncovered = mask ^ toggled
    uncovered_count = bin(uncovered).count('1')
    covered_count = w - uncovered_count 
    percent = covered_count * 100 / w
    
    print('Wire   ', monitors[i].wire.name, '->', percent, '%', 'uncovered:', bin(uncovered))
    #◙print('TOGGLED', bin(toggled))
    #print('MASK   ', bin(mask))
    #print('PERCENT', percent, '%')
    #print()