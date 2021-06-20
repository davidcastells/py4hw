# -*- coding: utf-8 -*-
"""
Created on Thu Jun 17 18:59:19 2021

@author: dcr
"""
import matplotlib.pyplot as plt
import numpy as np
        
from matplotlib.lines import Line2D
from matplotlib.patches import Arc
from matplotlib.patches import Ellipse
from .base import Logic
from .logic import *
from .schematic_symbols import *

gridsize = 5
cellmargin = 20


class MatplotlibRender:
    def __init__(self):
        f = plt.figure(figsize=(8,8))
        self.canvas = f.add_subplot()
        self.canvas.set_xlim(0, 1440//2)
        self.canvas.set_ylim(0, 1440//2)
        self.canvas.invert_yaxis()
        plt.axis('off')
        
    def drawText(self, x, y, text, anchor):
        if (anchor == 'w'):
            ha = 'left'
        elif (anchor == 'e'):
            ha = 'right'
        elif (anchor == 'c'):
            ha = 'center'
            
        self.canvas.annotate(text, (x, y), horizontalalignment=ha)
        
    def drawPolygon(self, x, y, outline=None, fill=None):
        lines = Line2D(x,y)
        self.canvas.add_line(lines)

    def drawLine(self, x0, y0, x1, y1):
        self.drawPolygon([x0, x1], [y0, y1])
        
    def drawRectangle(self , x0, y0, x1, y1):
        print('rect', x0, y0, x1, y1)
        self.drawPolygon([x0, x1, x1, x0, x0],[y0,y0, y1,y1, y0])
        
    def drawArc(self, x0, y0, x1, y1, start, extent):
        arc = Arc(((x0+x1)/2, (y0+y1)/2), x1-x0, y1-y0, angle=0, theta1=start, theta2=extent)
        self.canvas.add_patch(arc)

    def drawEllipse (self, x0, y0, x1, y1, outline=None, fill=None):
        el = Ellipse(((x0+x1)/2, (y0+y1)/2), x1-x0, y1-y0, edgecolor='k', facecolor='none')
        self.canvas.add_artist(el)
        
class Schematic:
    
    
    def __init__(self, sys:Logic):
   
        if (len(sys.children) == 0):
            raise Exception('Schematics are only available to structural circuits')

        self.sys = sys
        self.x = 0
        self.y = 0
                
        # frame=Frame(root,width=640,height=480)
        # self.frame =frame
        # frame.pack(expand=True, fill=BOTH) #.grid(row=0,column=0)
        # canvas=Canvas(frame,bg='#FFFFFF',width=300,height=900,scrollregion=(0,0,500,900))
        
        self.canvas = MatplotlibRender()
        
        # hbar=Scrollbar(frame,orient=HORIZONTAL)
        # hbar.pack(side=BOTTOM,fill=X)
        # hbar.config(command=canvas.xview)
        # vbar=Scrollbar(frame,orient=VERTICAL)
        # vbar.pack(side=RIGHT,fill=Y)
        # vbar.config(command=canvas.yview)
        # canvas.config(width=300,height=900)
        # canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        # canvas.pack(side=LEFT,expand=True,fill=BOTH)

        self.objs = []      # a list of the objects displayed
        self.sources = []   # a list of net sources with tuples [symbol, x, y, wire]
        self.sinks = []     # a list of net sinks with tuples   [symbol, x, y, wire]
        
        self.mapping = {}
        self.mapping[And] = AndSymbol
        self.mapping[Not] = NotSymbol
        self.mapping[Or] = OrSymbol
        self.mapping[Add] = AddSymbol
        
        self.placeInputPorts()
        self.placeInstances()
        self.placeOutputPorts()
        self.replaceByDependency()
        
        self.replaceVerticalCompress()
        
        self.createNets()
        self.routeNets()
        
        
        self.drawAll()
        
        #mainloop()
        
    def replaceVerticalCompress(self):
        """
        Compress instances in the vertical axis, 
        avoiding unused space above

        Returns
        -------
        None.

        """
        grid = self.getOccupancyGrid()
        
        for obj in self.objs:
            # get the occupancy area of this block
            rect = obj.getOccupancy()

            minfree = -1            
            # check if if has free space above in the occupancy grid
            for y in range(rect['y'], (gridsize * 3)-1, -1):
                candidate = grid[y:y+rect['h'],rect['x']:rect['x']+rect['w']]
                if (np.max(candidate) == 0):
                    minfree = y
                    
            # if so, move it as much as possible
            if (minfree >= 0):
                obj.y = minfree
                
            # compute the occupancy grid again
            grid = self.getOccupancyGrid()
        
    def replaceByDependency(self):
        """
        do topological sort, start from sources
        and place sinks be in the right

        Returns
        -------
        None.

        """
        #grid = [[0] * self.grid_xunits] * self.grid_yunits
        
        changed = True
        
        while (changed):
            changed = False
            for sourceTuple in self.sources:
                sinks = self.findSinkTuples(sourceTuple['wire'])
                sourceObj = sourceTuple['symbol']
                
                print('Source Obj:', sourceObj.obj.name)
                
                for sinkTuple in sinks:
                    sinkObj = sinkTuple['symbol']
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
        wiresFromSource = [source['wire'] for source in self.sources if source['symbol'] == sourceSym]
        wiresToSink = [sink['wire'] for sink in self.sinks if sink['symbol'] == sinkSym]
        common = [wire for wire in wiresFromSource if wire in wiresToSink ]
        return len(common)
    
    def placeInputPorts(self):
        """
        Place the input ports of the module 

        Returns
        -------
        None.

        """
        self.x = gridsize
        self.y = gridsize * 5
        
        for inp in self.sys.inPorts:
            isym = InPortSymbol(inp, self.x, self.y)
            self.objs.append(isym)
            self.y = self.y + gridsize * portSeparation
            self.sources.append({'symbol':isym, 'x':15, 'y':8+5, 'wire':inp.wire})
        
        if (len(self.sys.inPorts) > 0):
            self.x = self.x + 25 * gridsize
        
    def getSymbol(self, obj, x, y):
        try:
            ret = self.mapping[type(obj)]
    
            print('getSymbol -> good', obj)
                
        except:
            print('getSymbol -> none for object', type(obj))
            return None

        return ret(obj, x, y)
        
    def placeInstances(self):
        maxx = 0
        self.y = gridsize*3
        
        print('placeInstances', self.sys)
        
        for child in self.sys.children:
            print('child', child)
            isym = self.getSymbol(child, self.x, self.y)
            
            if (isym is None):
                isym = InstanceSymbol(child, self.x, self.y)
            
            self.objs.append(isym)
            self.y = self.y + isym.getHeight() + cellmargin * 2 
 
            i = 0
            for inp in child.inPorts:
                print('adding inport ', child, inp.name)
                self.sinks.append({'symbol':isym, 'x':0, 'y':8+8+8+5+i*portpitch, 'wire':inp.wire})
                i = i+1
            i = 0
            for inp in child.outPorts:
                print('adding outport ', child, inp.name)
                self.sources.append({'symbol':isym, 'x':isym.getWidth(), 'y':8+8+8+5+i*portpitch, 'wire':inp.wire})
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
            self.y = self.y + gridsize * portSeparation
            self.sinks.append({'symbol':osym, 'x':0, 'y':8+5, 'wire':inp.wire})
        
        #self.x = self.x + 3
        
    def findSourceTuple(self, sinkWire:Wire):
        for source in self.sources:
            if (source['wire'] == sinkWire):
                return source
            
        raise Exception('No source to wire {} in {}'.format(sinkWire.name, self.sources) )
            
    def findSinkTuples(self, sourceWire):
        ret = []
        for sink in self.sinks:
            if (sink['wire'] == sourceWire):
                ret.append(sink)
        return ret;
            
    def createNets(self):
        for sink in self.sinks:
            source = self.findSourceTuple(sink['wire'])
            self.objs.append(NetSymbol(source, sink))   

    def getNets(self):
        oa = np.array(self.objs)
        ba = np.array([isinstance(x, NetSymbol) for x in self.objs])
        return list(oa[ba])
    
    def drawAll(self):
        for obj in self.objs:
            obj.draw(self.canvas)
        
        return self.canvas
    
    def getOccupancyGrid(self):
        grid = np.zeros((800,800))
        
        for obj in self.objs:
            if (isinstance(obj, NetSymbol)):
                pass
            else:
                x = obj.x
                y = obj.y
                w = obj.getWidth()
                h = obj.getHeight()
                grid[y:y+h,x:x+w]=1
            
        return grid
    
    def routeNets(self):
        nets = self.getNets()
        
        for net in nets:
            # route net
            p0 = net.getStartPoint()
            pf = net.getEndPoint()
            
            mp = ((p0[0]+pf[0])//2, (p0[1]+pf[1])//2)
            
            net.setPath([p0[0], mp[0], mp[0], pf[0]], [p0[1],p0[1],pf[1],pf[1]])
                        

class NetSymbol:
    def __init__(self, source, sink):
        self.source = source
        self.sink = sink
        
    def getStartPoint(self):
        objsource = self.source['symbol']
        portsource = objsource.getWireSourcePos(self.source['wire'])
        return (objsource.x + portsource[0], objsource.y + portsource[1]) 
    
    def getEndPoint(self):
        objsink = self.sink['symbol']
        portsink = objsink.getWireSinkPos(self.source['wire'])
        return (objsink.x + portsink[0], objsink.y + portsink[1]) 
    
    def setPath(self, x, y):
        self.x = x
        self.y = y
        
    def draw(self, canvas):
        canvas.drawPolygon(self.x, self.y)
        
