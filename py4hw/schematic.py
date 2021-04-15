# -*- coding: utf-8 -*-
import tkinter 
import tkinter.font
from tkinter import *
from tkinter import ttk

from .base import Logic

gridsize = 5
portpitch = 25
cellmargin = 8


class Schematic:
    
    
    def __init__(self, root, sys:Logic):
    
        self.sys = sys
        self.x = 0
        self.y = 0
                
        frame=Frame(root,width=640,height=480)
        self.frame =frame
        frame.pack(expand=True, fill=BOTH) #.grid(row=0,column=0)
        canvas=Canvas(frame,bg='#FFFFFF',width=300,height=900,scrollregion=(0,0,500,900))
        #frame.add(canvas)
        self.canvas = canvas
        hbar=Scrollbar(frame,orient=HORIZONTAL)
        hbar.pack(side=BOTTOM,fill=X)
        hbar.config(command=canvas.xview)
        vbar=Scrollbar(frame,orient=VERTICAL)
        vbar.pack(side=RIGHT,fill=Y)
        vbar.config(command=canvas.yview)
        canvas.config(width=300,height=900)
        canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        canvas.pack(side=LEFT,expand=True,fill=BOTH)

        self.objs = []
        self.sources = []   # a list of net sources with tuples [symbol, x, y, wire]
        self.sinks = []     # a list of net sinks with tuples   [symbol, x, y, wire]
        
        
        self.placeInputPorts()
        self.placeInstances()
        self.placeOutputPorts()
        self.replace()
        
        self.createNets()
        self.drawAll()
        
        #mainloop()
        
    def replace(self):
        #grid = [[0] * self.grid_xunits] * self.grid_yunits
        
        
        #do topological sort, start from sources
        # and make sinks be in the right
        changed = True
        
        while (changed):
            changed = False
            for sourceTuple in self.sources:
                sinks = self.findSinkTuples(sourceTuple[3])
                sourceObj = sourceTuple[0]
                
                print('Source Obj:', sourceObj.obj.name)
                
                for sinkTuple in sinks:
                    sinkObj = sinkTuple[0]
                    candidatex = sourceObj.x + sourceObj.getWidth() + cellmargin
    
                    print('Sink Obj:', sinkObj.obj.name)
                
                    # check if A -> B, B-> A happens
                    directCount = self.countNetsBetweenSymbols(sourceObj, sinkObj)
                    reverseCount = self.countNetsBetweenSymbols(sinkObj, sourceObj)
                    
                    print('direct', directCount, 'reverse', reverseCount)
                    
                    if (isinstance(sourceObj, Logic )):
                        print(sourceObj.obj.getFullPath())
                    
                    if (candidatex > sinkObj.x and directCount > reverseCount):
                        sinkObj.x = candidatex + cellmargin
                        changed = True
                
        
    def countNetsBetweenSymbols(self, sourceSym, sinkSym):
        wiresFromSource = [source[3] for source in self.sources if source[0] == sourceSym]
        wiresToSink = [sink[3] for sink in self.sinks if sink[0] == sinkSym]
        common = [wire for wire in wiresFromSource if wire in wiresToSink ]
        return len(common)
    
    def placeInputPorts(self):
        self.x = gridsize
        self.y = gridsize * 5
        
        for inp in self.sys.inPorts:
            isym = InPortSymbol(inp, self.x, self.y)
            self.objs.append(isym)
            self.y = self.y + gridsize * 5
            self.sources.append([isym, 15, 8+5, inp.wire])
        
        self.x = self.x + 25 * gridsize
        
    def placeInstances(self):
        maxx = 0
        self.y = gridsize*3
        
        for child in self.sys.children:
            if (child.hasSymbol()):
                isym = child.getSymbol(self.x, self.y)
            else:
                isym = InstanceSymbol(child, self.x, self.y)
            
            self.objs.append(isym)
            self.y = self.y + isym.getHeight() + cellmargin * 2 
 
            i = 0
            for inp in child.inPorts:
                self.sinks.append([isym, 0, 8+8+8+5+i*portpitch, inp.wire])
                i = i+1
            i = 0
            for inp in child.outPorts:
                self.sources.append([isym, isym.getWidth(), 8+8+8+5+i*portpitch, inp.wire])
                i = i+1
                    
    
            maxx = max(maxx, isym.getWidth())
            
        self.x = self.x + maxx + gridsize*10 + cellmargin
        self.grid_yunits = self.y / gridsize
        self.grid_yunits = self.y / gridsize
        
    def placeOutputPorts(self):
        #self.x = 1
        self.y = gridsize * 5
        
        for inp in self.sys.outPorts:
            osym = OutPortSymbol(inp, self.x, self.y)
            self.objs.append(osym)
            self.y = self.y + gridsize * 5
            self.sinks.append([osym, 0, 8+5, inp.wire])
        
        #self.x = self.x + 3
        
    def findSourceTuple(self, sinkWire):
        for source in self.sources:
            if (source[3] == sinkWire):
                return source
            
        raise Exception('No source')
            
    def findSinkTuples(self, sourceWire):
        ret = []
        for sink in self.sinks:
            if (sink[3] == sourceWire):
                ret.append(sink)
        return ret;
            
    def createNets(self):
        for sink in self.sinks:
            source = self.findSourceTuple(sink[3])
            self.objs.append(NetSymbol(source, sink))                    
    
    def drawAll(self):
        for obj in self.objs:
            obj.draw(self.canvas)
        

class NetSymbol:
    def __init__(self, source, sink):
        self.source = source
        self.sink = sink
        
    def draw(self, canvas):
        objsource = self.source[0]
        objsink = self.sink[0]
        
        x0 = objsource.x  + self.source[1]
        y0 = objsource.y + self.source[2]
        x1 = objsink.x + self.sink[1]
        y1 = objsink.y + self.sink[2]
        canvas.create_line(x0, y0, x1, y1)
        
class InPortSymbol:
    
    def __init__(self, inp, x, y):
        self.x = x
        self.y = y
        self.obj = inp
    
    def draw(self, canvas):
        x = self.x 
        y = self.y 
        canvas.create_text(x, y, text=self.obj.name , anchor='w')
        y = y+8
        canvas.create_polygon(x, y, x+10, y, x+15, y+5, x+10, y+10, x, y+10)

    def getWidth(self):
        return 10;
    
class OutPortSymbol:
    
    def __init__(self, inp, x, y):
        self.x = x
        self.y = y
        self.obj = inp
        
    def draw(self, canvas):
        x = self.x 
        y = self.y 
        canvas.create_text(x, y, text=self.obj.name , anchor='w')
        y = y+8
        canvas.create_polygon(x, y, x+10, y, x+15, y+5, x+10, y+10, x, y+10)

    def getWidth(self):
        return 10;
    
class InstanceSymbol:
    
    def __init__(self, obj, x, y):
        self.x = x
        self.y = y
        self.obj = obj
    
    def draw(self, canvas):
        x = self.x 
        y = self.y 
        
        canvas.create_text(x, y, text=self.obj.name, anchor='w')
        y = y+8
        canvas.create_rectangle(x, y, x + self.getWidth(), y + self.getHeight())
        y = y+8

        for inp in self.obj.inPorts:
            canvas.create_text(x+2, y, text=inp.name , anchor='w')
            y = y+8
            canvas.create_polygon(x, y, x+10, y, x+15, y+5, x+10, y+10, x, y+10)
            y = y+portpitch-8
            
        y = self.y + 8
        x = self.x + self.getWidth() - 15
        y = y+8

        for inp in self.obj.outPorts:
            canvas.create_text(x+15-2, y, text=inp.name , anchor='e')
            y = y+8
            canvas.create_polygon(x, y, x+10, y, x+15, y+5, x+10, y+10, x, y+10)
            y = y+portpitch-8
        
        
    def getHeight(self):
        return max(len(self.obj.inPorts), len(self.obj.outPorts)) * portpitch + cellmargin * 2
    
    def getWidth(self):
        return 25 * gridsize