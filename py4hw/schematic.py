# -*- coding: utf-8 -*-
"""
Created on Thu Jun 17 18:59:19 2021

@author: dcr
"""
import matplotlib.pyplot as plt
import numpy as np
        
from matplotlib.lines import Line2D
from matplotlib.patches import *
from .base import *
from .logic import *
from .logic.bitwise import *
from .logic.storage import *
from .schematic_symbols import *

gridsize = 5
cellmargin = 50
cellmargin_initial = 150
netmargin = 40
netspacing = 10
nettrackspacing = 10

class MatplotlibRender:
    def __init__(self, shape):
        w = shape[0]
        h = shape[1]
        dpi = 100
        iw = w / dpi 
        ih = h / dpi
        pmax = max(w,h)
        imax = max(iw, ih)
        f = plt.figure(figsize=(imax,imax), dpi=dpi)
        self.canvas = f.add_subplot()
        self.canvas.set_xlim(0, pmax)
        self.canvas.set_ylim(0, pmax)
        self.canvas.invert_yaxis()
        plt.axis('off')
        
        self.color = 'k'
        self.fillcolor = 'k'
        self.linewidth = 2
        
    def setForecolor(self, color):
        self.color = color
        
    def setFillcolor(self, color):
        self.fillcolor = color
        
    def setLineWidth(self, w):
        self.linewidth = w
        
    def drawText(self, x, y, text, anchor):
        """
        

        Parameters
        ----------
        x : TYPE
            DESCRIPTION.
        y : TYPE
            position of the lower part of the text bounding box
        text : TYPE
            DESCRIPTION.
        anchor : TYPE
            e for east, w for west, c for center.

        Returns
        -------
        None.

        """
        if (anchor == 'w'):
            ha = 'left'
        elif (anchor == 'e'):
            ha = 'right'
        elif (anchor == 'c'):
            ha = 'center'
            
        self.canvas.annotate(text, (x, y), horizontalalignment=ha)
        
    def drawPolygon(self, x, y, fill=False):
        
        lines = Line2D(x,y, color=self.color, linewidth=self.linewidth)

        if (fill):
            self.canvas.fill(x, y, self.fillcolor)

        self.canvas.add_line(lines)

    def drawLine(self, x0, y0, x1, y1):
        self.drawPolygon([x0, x1], [y0, y1])
        
    def drawRectangle(self , x0, y0, x1, y1, fill=False):
        #print('rect', x0, y0, x1, y1)
        self.drawPolygon([x0, x1, x1, x0, x0],[y0,y0, y1,y1, y0], fill)
        
    def drawRoundRectangle(self, x0, y0, x1, y1, radius=5, fill=False):
        box = FancyBboxPatch((x0,y0), width=x1-x0, height=y1-y0,
              boxstyle=BoxStyle("Round", pad=radius), facecolor=self.fillcolor)
        self.canvas.add_patch(box)
        
    def drawArc(self, x0, y0, x1, y1, start, extent):
        arc = Arc(((x0+x1)//2, (y0+y1)//2), x1-x0, y1-y0, angle=0, theta1=start, theta2=extent, linewidth=self.linewidth)
        self.canvas.add_patch(arc)

    def drawEllipse (self, x0, y0, x1, y1, outline=None, fill=None):
        el = Ellipse(((x0+x1)/2, (y0+y1)/2), x1-x0, y1-y0, edgecolor=self.color, facecolor='none', linewidth=self.linewidth)
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
        self.nets = []      # a list of the nets
        self.sources = []   # a list of net sources with tuples [symbol, x, y, wire]
        self.sinks = []     # a list of net sinks with tuples   [symbol, x, y, wire]
        
        self.mapping = {}
        self.mapping[And2] = AndSymbol
        self.mapping[Not] = NotSymbol
        self.mapping[Or2] = OrSymbol
        
        self.mapping[Add] = AddSymbol
        self.mapping[Sub] = SubSymbol
        self.mapping[Mul] = MulSymbol
        
        self.mapping[Reg] = RegSymbol
        self.mapping[Scope] = ScopeSymbol
        self.mapping[Buf] = BufSymbol
        self.mapping[Bit] = BitSymbol
        self.mapping[Mux2] = Mux2Symbol

        self.mapping[Waveform] = ScopeSymbol # Temp solution
        
        
        self.placeInputPorts()
        self.placeInstances()
        self.placeOutputPorts()

        self.bruteForceSort()
        self.columnAssignment()
        
        self.createNets()
        self.passthroughCreation()
        self.removeArrowsSpecialCases()
        
        self.rowAssignment()
        

        self.trackAssignment()
        self.replaceAsColRow()
        
        #self.replaceByAdjacencyMatrix()
        
        # self.replaceByDependency()
        
        #self.replaceVerticalCompress()
        # #self.replaceHorizontalCompress()
        

        self.routeNets()
        
        
        
        self.canvas = MatplotlibRender(self.getOccupancyGrid().shape)
        self.canvas.setForecolor('k')

        self.drawAll()
        
        #mainloop()
        
        
    def removeArrowsSpecialCases(self):
        """
        Remove the arrows from some nets like the ones
        connected to selection ports of muxes 
        (as they are drawed inside the symbol)
        

        Returns
        -------
        None.

        """    
        for net in self.nets:
            if (isinstance(net.sink['symbol'], Mux2Symbol)):
                if (net.sink['wire'] == net.sink['symbol'].obj.inPorts[0].wire):
                    net.arrow = False
        
    def trackAssignment(self):
        """
        Track assignment consist in assigning a track (vertical path to each net)

        Returns
        -------
        None.

        """
        nets = self.getNets()
        numCols = len(self.columns)
        self.channels = [] 
        
        #print('cols', self.columns)
        for colidx in range(1, numCols):
            track = 0
            netsInCol = [n for n in nets if n.sink['symbol'] in self.columns[colidx]]
            
            # temporal object to check if several nets are created from the same
            # source
            channeltracks = {}
            
            #print('Nets is column', colidx, netsInCol )
            for net in netsInCol:
                try:
                    existingtrack = channeltracks[net.source['wire']]
                except:
                    existingtrack = None
                    
                if (existingtrack == None):
                    net.track = track
                    track = track + 1
                    channeltracks[net.source['wire']]={'num':net.track, 'nets':[net]}
                else:
                    net.track = existingtrack['num']
                    existingtrack['nets'].append(net)
                    
                net.sourcecol = colidx - 1
                    
                
            self.channels.append({'tracks':track, 'track':channeltracks})
        
    def getAllInstanceSources(self, sym:LogicSymbol):
        """
        Return all the instance objects that are connected
        as sources to this symbol

        Parameters
        ----------
        sym : TYPE
            DESCRIPTION.

        Returns
        -------
        ret : TYPE
            DESCRIPTION.

        """
        obj = sym.obj
        
        ret = []
        
        for inp in obj.inPorts:
            wire = inp.wire
            
            for src in self.sources:
                if (src['wire'] == wire):
                    ret.append(src['symbol'])
        
        return ret
    
    def getAllInstanceSinks(self, sym:LogicSymbol):
        """
        Return all the instance objects that are connected
        as sinks to this symbol

        Parameters
        ----------
        sym : TYPE
            DESCRIPTION.

        Returns
        -------
        ret : TYPE
            A list of dictionaries with the symbols.

        """
        obj = sym.obj
        
        ret = []
        
        if (isinstance(obj, InPort)):
            outports = [obj]
        elif (isinstance(obj, OutPort)):
            # no instances 
            return []
        else:
            outports = obj.outPorts
        
        for outp in outports:
            wire = outp.wire
            
            for src in self.sinks:
                if (src['wire'] == wire):
                    ret.append(src['symbol'])
        
        return ret
        
    def getSymbolColumn(self, sym):
        """
        Find the column assigned to a symbol

        Parameters
        ----------
        src : TYPE
            DESCRIPTION.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        for colidx, col in enumerate(self.columns):
            if (sym in col):
                return colidx
            
        return -1
                            
    def columnAssignment(self):
        self.columns = []
        currentCol = []
        
        # append inputs
        for idx, obj in enumerate(self.objs):
            if (idx < self.numInputs):
                currentCol.append(obj)

        self.columns.append(currentCol)
                
        # append instances
        for idx, obj in enumerate(self.objs):
            if (idx < self.numInputs):
                pass
            elif (idx < self.firstOutput):
                # find the 
                maxcol = -1
                #print('Checking sources', obj)
                for src in self.getAllInstanceSources(obj):
                    #print('Source', src)
                    colidx = self.getSymbolColumn(src)

                    if (colidx > maxcol):
                        maxcol = colidx

                if (maxcol == -1):
                    maxcol = 0
                    
                maxcol = maxcol + 1
                
                while (maxcol >= len(self.columns)):
                    self.columns.append([])

                #print('Assigning ', obj, ' to column', maxcol)
                self.columns[maxcol].append(obj)
                
        currentCol = []
                
        for idx, obj in enumerate(self.objs):
            if (idx >= self.firstOutput):
                currentCol.append(obj)

        self.columns.append(currentCol)
        
        
    def rowAssignment(self):
        pass
    
    def replaceAsColRow(self):
        
        x = 0
        y = 0
        
        for colidx, col in enumerate(self.columns):
            # iterate over all columns we assign the x and y
            # of all column members, and we compute the maxw of
            # the column
            maxw = 0
            y = 0
            
            for obj in col:
                obj.x = x
                obj.y = y
                y = y + obj.getHeight() + cellmargin
                if (obj.getWidth() > maxw):
                    maxw = obj.getWidth()


            x = x + maxw  + cellmargin
            
            if (colidx < len(self.channels)):
                x = x + self.channels[colidx]['tracks'] * nettrackspacing

            if (colidx < len(self.channels)):
                self.channels[colidx]['sourcewidth'] = maxw
    
    def passthroughCreation(self):
        """
        Create passthrough entities

        Returns
        -------
        None.

        """

        for colidx, col in enumerate(self.columns):
            for obj in col:
                if (isinstance(obj, PassthroughSymbol)):
                    continue
                if (isinstance(obj, FeedbackStartSymbol)):
                    continue
                if (isinstance(obj, FeedbackStopSymbol)):
                    continue
                
                sinks = self.getAllInstanceSinks(obj)
                
                for sink in sinks:
                    sinkcol = self.getSymbolColumn(sink)
                    
                    if (sinkcol > colidx +1):
                        #print('WARNING: passthrough required between: [{}]'.format(colidx), obj, '[{}]'.format(sinkcol), sink)
                        self.insertPassthrough(obj, colidx, sink, sinkcol)
                    if (sinkcol <= colidx):
                        #print('WARNING: feedback required between: [{}]'.format(colidx), obj, '[{}]'.format(sinkcol), sink)
                        self.insertFeedback(obj, colidx, sink, sinkcol)

    def insertPassthrough(self, source:LogicSymbol, sourcecol:int, sink:LogicSymbol, sinkcol:int):
        """
        A passthrough instance has to be inserted for every wire connecting both entities

        Parameters
        ----------
        source : LogicSymbol
            DESCRIPTION.
        sourcecol : int
            DESCRIPTION.
        sink : LogicSymbol
            DESCRIPTION.
        sinkcol : int
            DESCRIPTION.

        Returns
        -------
        None.

        """
        #return
    
        source_wires = self.getWiresFromSource(source)
        sink_wires = self.getWiresFromSink(sink)
        intersection = Intersection(source_wires, sink_wires)
        
       
        
        for wire in intersection:
            # remove the original net
            removeNets = [x for x in self.nets if x.source['wire'] == wire and x.source['symbol'] == source and x.sink['symbol'] == sink]
            if (len(removeNets) == 0):
                #print('WARNING: no nets to remove')
                continue
            
            self.nets.remove(removeNets[0])
        
            lastSymbol = source
            
            for col in range(sourcecol+1, sinkcol):
                pts = PassthroughSymbol()
                self.objs.append(pts)
                self.columns[col].append(pts)
                self.sources.append({'symbol':pts, 'wire':wire})
                self.sinks.append({'symbol':pts, 'wire':wire})
                
                net1 = NetSymbol({'symbol':lastSymbol, 'wire':wire}, {'symbol':pts, 'wire':wire})
                net1.sourcecol = col-1
                net1.arrow = False
                self.nets.append(net1)
                
                lastSymbol = pts
                
                
            if (lastSymbol != None):
                net2 = NetSymbol({'symbol':pts, 'wire':wire}, {'symbol': sink, 'wire': wire})
                self.nets.append(net2)
                                
                
    def insertFeedback(self, source:LogicSymbol, sourcecol:int, sink:LogicSymbol, sinkcol:int):
        """
        A passthrough instance has to be inserted for every wire connecting both entities

        Parameters
        ----------
        source : LogicSymbol
            DESCRIPTION.
        sourcecol : int
            DESCRIPTION.
        sink : LogicSymbol
            DESCRIPTION.
        sinkcol : int
            DESCRIPTION.

        Returns
        -------
        None.

        """
        #return
    
        source_wires = self.getWiresFromSource(source)
        sink_wires = self.getWiresFromSink(sink)
        intersection = Intersection(source_wires, sink_wires)
        
       
        
        for wire in intersection:
            # remove the original net
            removeNets = [x for x in self.nets if x.source['wire'] == wire and x.source['symbol'] == source and x.sink['symbol'] == sink]
            self.nets.remove(removeNets[0])
        
            lastSymbol = source
            
            #insert feedback channel if necessary
            
            #self.channels[sourcecol+1]
            fb_start = FeedbackStartSymbol()
            self.objs.append(fb_start)
            self.columns[sourcecol+1].append(fb_start)
            #self.sources.append({'symbol':fb_start, 'wire':wire})
            #self.sinks.append({'symbol':fb_start, 'wire':wire})
            
            net1 = NetSymbol({'symbol':lastSymbol, 'wire':wire}, {'symbol':fb_start, 'wire':wire})
            net1.sourcecol = sourcecol
            net1.arrow = False
            self.nets.append(net1)
            
            
            fb_end = FeedbackStopSymbol()
            self.objs.append(fb_end)
            self.columns[sinkcol-1].append(fb_end)
            #self.sources.append({'symbol':fb_start, 'wire':wire})
            #self.sinks.append({'symbol':fb_start, 'wire':wire})
            
            net2 = NetSymbol({'symbol':fb_end, 'wire':wire}, {'symbol':sink, 'wire':wire})
            net2.sourcecol = sinkcol-1
            net2.arrow = True
            self.nets.append(net2)
            
            lastSymbol = fb_end
            
            
            for col in range(sinkcol, sourcecol+1):
                  pts = PassthroughSymbol()
                  self.objs.append(pts)
                  self.columns[col].append(pts)
                  self.sources.append({'symbol':pts, 'wire':wire})
                  self.sinks.append({'symbol':pts, 'wire':wire})
                
                  net1 = NetSymbol({'symbol':lastSymbol, 'wire':wire}, {'symbol':pts, 'wire':wire})
                  net1.sourcecol = col-1
                  net1.arrow = False
                  self.nets.append(net1)
                
                  lastSymbol = pts
                
                
            if (lastSymbol != None):
                 net2 = NetSymbol({'symbol':lastSymbol, 'wire':wire}, {'symbol': fb_start, 'wire': wire})
                 net2.arrow = False
                 self.nets.append(net2)

    def getWiresFromSource(self, source):
        return [x['wire'] for x in self.sources if x['symbol'] == source]

    def getWiresFromSink(self, sink):
        return [x['wire'] for x in self.sinks if x['symbol'] == sink]
    
    def replaceByAdjacencyMatrix(self):
        am = self.getAdjacencyMatrix()
        
        x = 0
        y = 0
        
        if (self.numInputs > 0):
            x = 10 + cellmargin_initial
        
        for i in range(self.numInputs, am.shape[0]):
            obj = self.objs[i]
            
            srcs = am[0:i,i]
            if (i == 0 or np.max(srcs) == 0):
                # no source
                obj.x = x
                obj.y = y
                y = y + obj.getHeight() + cellmargin

            else:
                lastsrc_aux = np.where(srcs>0) # more recent source
                pos = len(lastsrc_aux[0])
                lastsrc = lastsrc_aux[0][pos-1]
                
                dep = self.objs[lastsrc]
                obj.x = max(x, dep.x + dep.getWidth() + cellmargin_initial)
                obj.y = y
                x = obj.x
                y = y + obj.getHeight() + cellmargin
                
            
        
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

                if (candidate.shape[0]==0 or candidate.shape[1]==0):
                    #print('y',y,'skip obj', candidate.shape, obj)
                    pass
                elif (np.max(candidate) == 0):
                    minfree = y
                    
            # if so, move it as much as possible
            if (minfree >= 0):
                obj.y = minfree
                
            # compute the occupancy grid again
            grid = self.getOccupancyGrid()
            
    def replaceHorizontalCompress(self):
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
            # check if if has free space to the left in the occupancy grid
            for x in range(rect['x'], (gridsize * 3)-1, -1):
                candidate = grid[rect['y']:rect['y']+rect['h'],x:x+rect['w']]

                if (candidate.shape[0]==0 or candidate.shape[1]==0):
                    #print('y',y,'skip obj', candidate.shape, obj)
                    pass
                elif (np.max(candidate) == 0):
                    minfree = x
                    
            # if so, move it as much as possible
            if (minfree >= 0):
                obj.x = minfree
                
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
        iterNum = 0
        
        while (changed and iterNum < 2):
            iterNum = iterNum + 1
            changed = False
            for sourceTuple in self.sources:
                sinks = self.findSinkTuples(sourceTuple['wire'])
                sourceObj = sourceTuple['symbol']
                
                
                for sinkTuple in sinks:
                    sinkObj = sinkTuple['symbol']
                    candidatex = sourceObj.x + sourceObj.getWidth() + cellmargin
    
                    
                
                    # check if A -> B, B-> A happens
                    directCount = self.countNetsBetweenSymbols(sourceObj, sinkObj)
                    reverseCount = self.countNetsBetweenSymbols(sinkObj, sourceObj)
                    
                    
                    
                    #if (isinstance(sourceObj, Logic )):
                    #    print(sourceObj.obj.getFullPath())
                    
                    if (candidatex > sinkObj.x and directCount > reverseCount):
                        print('moving to',candidatex + cellmargin, sinkObj.obj.name, 'sink of', sourceObj.obj.name, '({}/{})'.format(directCount, reverseCount))
                        #print('Source Obj:', sourceObj.obj.name)
                        #print('Sink Obj:', sinkObj.obj.name)
                        #print('direct', directCount, 'reverse', reverseCount)
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
            
        # g = genGraph(self.sources)
        # g.add_edge(self.sources)
        # print("Executed")
        # g.col_assignment()
        # g.print_graph()
        self.numInputs = len(self.objs)
        
    def getSymbol(self, obj, x, y):
        try:
            ret = self.mapping[type(obj)]
    
            #print('getSymbol -> good', obj)
                
        except:
            #print('getSymbol -> none for object', type(obj))
            return None

        return ret(obj, x, y)
        

    def placeInstances(self):
        maxx = 0
        self.y = gridsize*3
        
        #print('placeInstances', self.sys)
        
        for child in self.sys.children:
            #print('child', child)
            isym = self.getSymbol(child, self.x, self.y)
            
            if (isym is None):
                isym = InstanceSymbol(child, self.x, self.y)
            
            self.objs.append(isym)
            self.y = self.y + isym.getHeight() + cellmargin * 2 
 
            i = 0
            for inp in child.inPorts:
                #print('adding inport ', child, inp.name)
                self.sinks.append({'symbol':isym, 'x':0, 'y':8+8+8+5+i*portpitch, 'wire':inp.wire})
                i = i+1
            i = 0
            for inp in child.outPorts:
                #print('adding outport ', child, inp.name)
                self.sources.append({'symbol':isym, 'x':isym.getWidth(), 'y':8+8+8+5+i*portpitch, 'wire':inp.wire})
                i = i+1
                    
    
            maxx = max(maxx, isym.getWidth())
            
        self.x = self.x + maxx + gridsize*10 + cellmargin
        self.grid_yunits = self.y / gridsize
        self.grid_yunits = self.y / gridsize
        
    def placeOutputPorts(self):
        #self.x = 1
        self.y = gridsize * 5
        
        self.firstOutput = len(self.objs)
        
        for inp in self.sys.outPorts:
            osym = OutPortSymbol(inp, self.x, self.y)
            self.objs.append(osym)
            self.y = self.y + gridsize * portSeparation
            self.sinks.append({'symbol':osym, 'x':0, 'y':8+5, 'wire':inp.wire})
        
        #self.x = self.x + 3

        self.lastOutput = len(self.objs)

        
    def findSourceTuple(self, sinkWire:Wire):
        for source in self.sources:
            if (source['wire'] == sinkWire):
                return source
            
        sourceNames = [x['wire'].getFullPath() for x in self.sources]
        raise Exception('No source to wire "{}" in {}'.format(sinkWire.getFullPath(), sourceNames ) )
            
    def findSinkTuples(self, sourceWire):
        ret = []
        for sink in self.sinks:
            if (sink['wire'] == sourceWire):
                ret.append(sink)
        return ret;
            
    def createNets(self):
        for sink in self.sinks:
            source = self.findSourceTuple(sink['wire'])
            self.nets.append(NetSymbol(source, sink))   

    def getNets(self):
        #oa = np.array(self.objs)
        #ba = np.array([isinstance(x, NetSymbol) for x in self.objs])
        #return list(oa[ba])
        return self.nets
    
    def getNonNets(self):
        #oa = np.array(self.objs)
        #ba = np.array([not isinstance(x, NetSymbol) for x in self.objs])
        #return list(oa[ba])
        return self.objs
    
    def drawAll(self):
        # Draw Instances
        for obj in self.getNonNets():
            self.canvas.setForecolor('k')  
            self.canvas.setFillcolor('k')
            self.canvas.setLineWidth(2)
            obj.draw(self.canvas)

        # Draw Nets
        for obj in self.getNets():
            self.canvas.setForecolor('blueviolet')  
            self.canvas.setFillcolor('blueviolet')
            self.canvas.setLineWidth(1)
            
            obj.draw(self.canvas)
        
        return self.canvas
    
    def getAdjacencyMatrix(self):
        """
        

        Returns
        -------
        adjacency matrix : numpy 2D array with the connections between 
            circuit instances

        """
        non_nets = self.getNonNets()
        nc = len(non_nets) # number of circuits
        am = np.zeros((nc, nc), dtype=int) # adjacency matrix
        
        for srcidx in range(nc):
            srcobj = non_nets[srcidx]
            
            for trgidx in range(nc):
                trgobj = non_nets[trgidx]
            
                am[srcidx, trgidx] = self.areSourceTarget(srcobj, trgobj)
            
        
        return am
        
    def computeAdjacencyMatrixCost(self):
        am = self.getAdjacencyMatrix()
        cost = 0
        for y in range(am.shape[0]):
            for x in range(y):
                cost = cost + am[y, x]

        return cost
    
    def swap(self, a, b):
        self.objs[a], self.objs[b] = self.objs[b], self.objs[a] 

    def bruteForceSort(self):
        am = self.getAdjacencyMatrix()
        nc = am.shape[0]


        objs = self.objs.copy()
        cost = self.computeAdjacencyMatrixCost()
        
        for k in range(self.numInputs, self.firstOutput):
            anychange = False
            for i in range(self.numInputs, self.firstOutput):
                for j in range(i, self.firstOutput):
                    if (i != j):
                        objs = self.objs.copy()
                        self.swap(i,j)
                        newcost = self.computeAdjacencyMatrixCost()
                        
                        #print('swap', i, j, 'cost=', newcost)

                        if (newcost >= cost):
                            # revert swap
                            self.objs = objs
                        else:
                            cost = newcost
                            anychange = True
                            
                            #print(self.getAdjacencyMatrix())

            print('iter', k, 'cost:', cost, anychange)
                         
            if (not anychange):
                break

        am = self.getAdjacencyMatrix()
        return am

    def areSourceTarget(self, srcobj, trgobj):
        if (isinstance(srcobj, InPortSymbol)):
            outwires = [srcobj.obj.wire]
        elif (isinstance(srcobj, OutPortSymbol)):
            outwires = []
        else:
            outwires = [outport.wire for outport in srcobj.obj.outPorts]
        
        if (isinstance(trgobj, InPortSymbol)):
            inwires = []
        elif (isinstance(trgobj, OutPortSymbol)):
            inwires = [trgobj.obj.wire]
        else:
            inwires = [inport.wire for inport in trgobj.obj.inPorts]
        
        inter = Intersection(inwires, outwires)
        
        #print('Intersection ', srcobj.obj.getFullPath(), trgobj.obj.getFullPath(), '=', len(inter))
        
        return len(inter) 
        
    def getOccupancyGrid(self, mode=None, discard=[]):
        """
        Compute the occupancy grid

        Parameters
        ----------
        mode : str, optional
            DESCRIPTION. The default is None.
        discard : TYPE, optional
            DESCRIPTION. The default is [].

        Returns
        -------
        grid : TYPE
            DESCRIPTION.

        """
        maxh = 0
        maxw = 0
        
        #print('-')
        
        for obj in self.getNonNets():
            w = obj.x + obj.getWidth() #+ cellmargin
            h = obj.y + obj.getHeight() + cellmargin
            if (w > maxw): maxw = w
            if (h > maxh): maxh = h
            
        if (mode == 'prerouting'):
            maxh = maxh*2
            
        grid = np.zeros((maxh,maxw))
        
        for obj in self.getNonNets():
            if (obj in discard):
                continue

            x = obj.x
            y = obj.y
            w = obj.getWidth() #+ cellmargin
            h = obj.getHeight() + cellmargin
            grid[y:y+h,x:x+w]=1
            #print('OG:', obj.obj.getFullPath(), x,y, x+w, y+h)
            
        if (mode == 'prerouting'):
            for obj in self.getNets():
                if (obj in discard):
                    continue
                if (obj.routed == False):
                    continue
                    
                x = obj.x
                y = obj.y
                
                if (x != None):
                    grid[y[0]-netspacing:y[1]+netspacing, x[0]:x[1]] = 2
                    grid[y[1]:y[2], x[1]-netspacing:x[2]+netspacing] = 2
                    grid[y[2]-netspacing:y[3]+netspacing, x[2]:x[3]] = 2
                    grid[y[3]:y[4], x[3]-netspacing:x[4]+netspacing] = 2
                    grid[y[4]-netspacing:y[5]+netspacing, x[4]:x[5]] = 2
                    
                #print('OG:', obj.obj.getFullPath(), x,y, x+w, y+h)
            
        return grid

    def isFreeRectangle(self, og, x0, y0, x1, y1):
        try:
            if (x0==x1 and y0==y1):
                return True
            
            
            if (y1 >= og.shape[0] or x1 >= og.shape[1]):
                return False
            
            if (x0 > x1):
                x0, x1 = x1, x0
            if (y0 > y1):
                y0, y1 = y1, y0
            
            v = np.max(og[y0:y1+1, x0:x1+1])
        except:
            return False
        
        return v == 0
        
    def routeNet(self, net:NetSymbol):
        p0 = net.getStartPoint()
        pf = net.getEndPoint()
        

        sw = 0
        try:
            sw = self.channels[net.sourcecol]['sourcewidth'] 
            #sw = sw - net.source['symbol'].getWidth() + netspacing
            #print('sw[{}]={}'.format(net.sourcecol, sw))
        except:
            if (hasattr(net, 'sourcecol') == False):
                # this net was not assigned a sourcecol
                print('WARNING: net', net.source['wire'].getFullPath(), 'without source column')
                net.track = 0
            else:
                print('error sourcecol=', net.sourcecol)
                print('channels[{}]'.format(net.sourcecol), self.channels[net.sourcecol])
                print('source sym', net.source)
        
        if (hasattr(net, 'track') == False):
            print('WARNING: net', net.source['wire'].getFullPath(), 'with not track')
            net.track = 0

        mp = (net.source['symbol'].x + sw + netspacing + net.track * nettrackspacing, (p0[1]+pf[1])//2)    
            
        if (isinstance(net.source['symbol'], FeedbackStopSymbol)):
            #print('Feedback-stop track:', net.track, mp[0])
            net.setPath([mp[0], mp[0], pf[0]], [p0[1],pf[1],pf[1]])
        elif (isinstance(net.sink['symbol'], FeedbackStartSymbol)):
            #print('Feedback-start track:', net.track, mp[0])
            net.setPath([p0[0], mp[0], mp[0]], [p0[1],p0[1],pf[1]])
        else:                  
            net.setPath([p0[0], mp[0], mp[0], pf[0]], [p0[1],p0[1],pf[1],pf[1]])

        #mp[0] = p0[0] + net.track * nettrackspacing
        
        net.routed = True
    
    
    def routeNets(self):
        nets = self.getNets()
        
        for net in nets:
            # route net
            self.routeNet(net)
                        

        # for inp in self.obj.outPorts:
        #     canvas.create_text(x+15-2, y, text=inp.name , anchor='e')
        #     y = y+8
        #     canvas.create_polygon(x, y, x+10, y, x+15, y+5, x+10, y+10, x, y+10)
        #     y = y+portpitch-8
        
        
    def getHeight(self):
        return max(len(self.obj.inPorts), len(self.obj.outPorts)) * portpitch + cellmargin * 2
    
    def getWidth(self):
        return 25 * gridsize

class AdjNode:
    def __init__(self, data):
        self.vertex = data
        self.next = None

# Generate graphs based on the ports and nets

rows,cols = (gridsize,gridsize)
matrix = [[0]*cols]*rows

class genGraph:

    def __init__(self,sources):
        self.V = len(sources)
        self.graph = [None]*self.V

    def add_edge(self,sources):
        for i in range(len(sources)-1):
            for j in range(i+1,len(sources)):
                if sources[j].parent == sources[i]:
                    node = AdjNode(sources[j])
                    node.next = self.graph[sources[i]]
                    self.graph[sources[i]] = next

    def print_graph(self):
        for i in range(self.V):
            print("Adjacency list of vertex {}\n head".format(i), end="")
            temp = self.graph[i]
            while temp:
                print(" -> {}".format(temp.vertex), end="")
                temp = temp.next
            print(" \n")
    
    def col_assignment(self):
        for i in range(self.V):
            k=0
            if(self.graph[i].isPrimitive()):
                matrix[0][k] = self.graph[i]
                k+=1
            else:
                matrix[self.graph[i].col][self.graph[i].row+1] = self.graph[i]

    def row_assignment(self):
        
        for i in range(self.V):
            for j in range(matrix.size()):
                count = 0
                count = matrix[j].size()
                for k in range(count):
                    matrix[k][0] = self.graph[i]


    def crossover_calc(self,matrix):
        
        numCross = 0
        
        for i in range(cols-1):
            for j in range(cols):
                for k in range(rows-1):
                    for l in range(rows):
                         numCross += Matrix[j][k]*Matrix[i][l]
        
        return numCross



def Intersection(lst1, lst2):
    return set(lst1).intersection(lst2)
