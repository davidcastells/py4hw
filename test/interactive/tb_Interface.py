# -*- coding: utf-8 -*-
"""
Created on Tue Apr 21 09:40:38 2026

@author: 2016570
"""

import py4hw

class Handsheake(py4hw.Interface):
    def __init__(self, parent, name):
        super().__init__(parent, name)
        
        self.B = self.addSourceToSink('B',1)
        self.C =  self.addSinkToSource('C',8)

class Source(py4hw.Logic):
    def __init__(self, parent, name, port0,inCode,outCode):
        super().__init__(parent, name)

        self.port0 = self.addInterfaceSource('src', port0)
        self.inCode = self.addIn('InCode',inCode)
        self.outCode = self.addOut('outCode',outCode)
    
    def clock(self):
        if self.inCode.get() == 1 :
            self.port0.B.prepare(1)
        else: 
            self.port0.B.prepare(0)
            
        self.outCode.prepare(self.port0.C.get())


class Sink(py4hw.Logic):
    
    def __init__(self, parent, name, port0):
        super().__init__(parent, name)

        self.port0 = self.addInterfaceSink('trg', port0)
    
    def clock(self):
        if self.port0.B.get() == 1:
            self.port0.C.prepare(60)
        else:
            self.port0.C.prepare(7)


sys =  py4hw.HWSystem()

inCode = py4hw.Wire(sys,'inCode',1)
outCode = py4hw.Wire(sys,'outCode',8)

port0 = Handsheake(sys, 'port0')

So = Source(sys, 'My Source', port0, inCode, outCode)
Si = Sink(sys,'My Sink', port0)

print("Circuit Created")

#py4hw.debug.checkIntegrity(sys)

sch =  py4hw.Schematic(sys)
#sch.drawAll(debug=True)
sch.draw()


#py4hw.Sequence(sys,'inCode',[0b0,0b0,0b1,0b1],inCode)

#wvf = py4hw.Waveform(sys, 'wvf',[inCode,outCode] )
#sys.getSimulator().clk(10)
#wvf.gui()