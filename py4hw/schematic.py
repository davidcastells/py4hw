# -*- coding: utf-8 -*-
"""
Created on Thu Jun 17 18:59:19 2021

@author: dcr
"""
import matplotlib.pyplot as plt
import numpy as np
        
from matplotlib.lines import Line2D
from matplotlib.patches import *
from matplotlib import colors
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
portvaluemargin = 10

class MatplotlibRender:
    def __init__(self, shape, physical_shape=None, dpi=None):
        w = shape[1]
        h = shape[0]
        if (physical_shape is None):
            if (dpi is None):
                dpi = 100
            iw = w / dpi 
            ih = h / dpi
            #print('w/h = ',w,h, 'iw/ih', iw,ih)
        else:
            iw = physical_shape[1]
            ih = physical_shape[0]
            if (dpi is None):
                dpi = max(w / iw, h / ih)
            
        pmax = max(w,h)
        imax = max(iw, ih)
        f = plt.figure(figsize=(iw,ih), dpi=dpi)
        self.canvas = f.add_subplot()
        self.canvas.set_xlim(0, w)
        self.canvas.set_ylim(0, h)
        self.canvas.invert_yaxis()
        plt.axis('off')
        
        self.setForecolor('k')
        self.setFillcolor('k')
        self.linewidth = 2
        
    def setForecolor(self, color):
        #print('color {} = {}'.format(color, colors.rgb2hex(colors.to_rgb(color))))
        self.color = colors.rgb2hex(colors.to_rgb(color))
        
    def setFillcolor(self, color):
        #print('color {} = {}'.format(color, colors.rgb2hex(colors.to_rgb(color))))
        self.fillcolor = colors.rgb2hex(colors.to_rgb(color))
        
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
        
    def drawArc(self, x0, y0, x1, y1, start, stop):
        arc = Arc(((x0+x1)//2, (y0+y1)//2), x1-x0, y1-y0, angle=0, theta1=start, theta2=stop, linewidth=self.linewidth)
        self.canvas.add_patch(arc)

    def drawEllipse (self, x0, y0, x1, y1, outline=None, fill=None):
        el = Ellipse(((x0+x1)/2, (y0+y1)/2), x1-x0, y1-y0, edgecolor=self.color, facecolor='none', linewidth=self.linewidth)
        self.canvas.add_artist(el)
        
    def drawSpline(self, x, y):
        from scipy import interpolate
        tck,u     = interpolate.splprep( [x,y] ,s = 0 )
        xnew,ynew = interpolate.splev( np.linspace( 0, 1, 20 ), tck,der = 0)
        self.canvas.plot( xnew ,ynew , color=self.color, linewidth=self.linewidth)
        
    def drawImage(self, x, y, img ):
        w = img.shape[1]
        h = img.shape[0]
        self.canvas.imshow(img, extent=[x,x+w,y+h,y], origin='upper')
        

class TkinterRender:
    # check https://zetcode.com/tkinter/drawing/
    
    def __init__(self, parent, shape):
        from tkinter import Canvas
        self.canvas = Canvas(parent, bg='white')
        
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)

        self.start_x = None
        self.start_y = None
        
        w = shape[0]
        h = shape[1]
        dpi = 100
        iw = w / dpi 
        ih = h / dpi
        pmax = max(w,h)
        imax = max(iw, ih)
        # f = plt.figure(figsize=(imax,imax), dpi=dpi)
        # self.canvas = f.add_subplot()
        # self.canvas.set_xlim(0, pmax)
        # self.canvas.set_ylim(0, pmax)
        # self.canvas.invert_yaxis()
        # plt.axis('off')
        
        self.setForecolor('k')
        self.setFillcolor('k')
        self.linewidth = 2
        self.xmargin = 50
        self.ymargin = 50

    def on_press(self, event):
        self.start_x = int(self.canvas.canvasx(event.x))
        self.start_y = int(self.canvas.canvasy(event.y))

    def on_drag(self, event):
        if self.start_x is not None and self.start_y is not None:
            cur_x = int(self.canvas.canvasx(event.x))
            cur_y = int(self.canvas.canvasy(event.y))

            delta_x = cur_x - self.start_x
            delta_y = cur_y - self.start_y

            self.canvas.scan_mark(self.start_x, self.start_y)
            self.canvas.scan_dragto(cur_x, cur_y, gain=1)

    def reset_start_coords(self):
        self.start_x = None
        self.start_y = None
        
    def setForecolor(self, color):
        #print('color {} = {}'.format(color, colors.rgb2hex(colors.to_rgb(color))))
        self.color = colors.rgb2hex(colors.to_rgb(color))
        
    def setFillcolor(self, color):
        #print('color {} = {}'.format(color, colors.rgb2hex(colors.to_rgb(color))))
        self.fillcolor = colors.rgb2hex(colors.to_rgb(color))
        
    def setLineWidth(self, w):
        self.linewidth = w
        
    def drawText(self, x, y, text, anchor):
        if (anchor == 'w'):
            ha = 'left'
        elif (anchor == 'e'):
            ha = 'right'
        elif (anchor == 'c'):
            ha = 'center'
            
        self.canvas.create_text(x + self.xmargin, y+self.ymargin, anchor=anchor, text=text)
        
    def drawPolygon(self, x, y, fill=False):
        
        if (fill):
            points = []
            
            for i in range(len(x)):
                points.append(self.xmargin + x[i])
                points.append(self.ymargin + y[i])
            
        # #lines = Line2D(x,y, color=self.color, linewidth=self.linewidth)
        # # if (fill):
        # #    self.canvas.fill(x, y, self.fillcolor)

            self.canvas.create_polygon(points, outline=self.color, fill=self.fillcolor, width=self.linewidth)
            
        else:            
            x0 = x[0]
            y0 = y[0]
            for i in range(1, len(x)):
                x1 = x[i]
                y1 = y[i]
                self.drawLine(x0 , y0 , x1 , y1 )
                x0 = x1
                y0 = y1
        #     points.append(x[i])
        #     points.append(y[i])
        

    def drawLine(self, x0, y0, x1, y1):
        self.canvas.create_line(x0 + self.xmargin, y0 + self.ymargin, x1 + self.xmargin, y1 + self.ymargin, fill=self.color, width=self.linewidth)
        #self.drawPolygon([x0, x1], [y0, y1])
        
    def drawRectangle(self , x0, y0, x1, y1, fill=False):
        #print('rect', x0, y0, x1, y1)
        #self.drawPolygon([x0, x1, x1, x0, x0],[y0,y0, y1,y1, y0], fill)
        self.canvas.create_rectangle(x0 + self.xmargin, y0 + self.ymargin, x1 + self.xmargin, y1 + self.ymargin, width=self.linewidth)
        
    def drawRoundRectangle(self, x0, y0, x1, y1, radius=5, fill=False):
        #box = FancyBboxPatch((x0,y0), width=x1-x0, height=y1-y0,
        #      boxstyle=BoxStyle("Round", pad=radius), facecolor=self.fillcolor)
        #self.canvas.add_patch(box)
        print('[WARNING] round rectangle not supported yet')
        
    def drawArc(self, x0, y0, x1, y1, start, stop):
        import tkinter
        # arc = Arc(((x0+x1)//2, (y0+y1)//2), x1-x0, y1-y0, angle=0, theta1=start, theta2=extent, linewidth=self.linewidth)
        # self.canvas.add_patch(arc)
        self.canvas.create_arc(x0 + self.xmargin, y0 + self.ymargin, x1 + self.xmargin, y1 + self.ymargin, start=start, extent=stop-start, style=tkinter.ARC, width=self.linewidth)

    def drawEllipse (self, x0, y0, x1, y1, outline=None, fill=None):
        # el = Ellipse(((x0+x1)/2, (y0+y1)/2), x1-x0, y1-y0, edgecolor=self.color, facecolor='none', linewidth=self.linewidth)
        # self.canvas.add_artist(el)
        self.canvas.create_oval(x0 + self.xmargin, y0 + self.ymargin, x1 + self.xmargin, y1 + self.ymargin, width=self.linewidth)
        
    def drawSpline(self, x, y):
        from scipy import interpolate
        tck,u     = interpolate.splprep( [x,y] ,s = 0 )
        xnew,ynew = interpolate.splev( np.linspace( 0, 1, 20 ), tck,der = 0)
        self.drawPolygon( xnew ,ynew)

    def drawImage(self, x, y, np_img ):
        from tkinter import PhotoImage
        from PIL import Image, ImageTk
        w = np_img.shape[1]
        h = np_img.shape[0]
        
        #print('drawImage', np_img.shape, type(np_img), type(np_img[0][0][0]))

        pil_img = Image.fromarray(np_img)
        tk_img = ImageTk.PhotoImage(image=pil_img)
        # Display the image on the canvas
        self.canvas.create_image(x, y, anchor="nw", image=tk_img)
        self.canvas.image = tk_img
        
class Schematic:
    """
    Class that controls the schematic drawing
    """

    step_timeout = 10 # any step of the schematic rendering cannot take more than this value (seconds)

    mapping = {} # maaping from object class to symbol
    
    def __init__(self, obj:Logic, render='matplotlib', parent=None, placeAndRoute=True, showValues=False):
   
        if not(obj.isStructural()):
            raise Exception('Schematics are only available to structural circuits')

        self.sys = obj
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

        self.objs = []      # a list of the logic symbols displayed
        self.nets = []      # a list of the nets
        self.sources = []   # a list of net sources with tuples [symbol, x, y, port]
        self.sinks = []     # a list of net sinks with tuples   [symbol, x, y, port]
        
        Schematic.mapping[And2] = AndSymbol
        Schematic.mapping[And] = AndSymbol
        Schematic.mapping[Not] = NotSymbol
        Schematic.mapping[Or2] = OrSymbol
        Schematic.mapping[Or] = OrSymbol
        Schematic.mapping[Nor2] = NorSymbol
        Schematic.mapping[Xor2] = XorSymbol
        
        Schematic.mapping[Add] = AddSymbol
        Schematic.mapping[Sub] = SubSymbol
        Schematic.mapping[Mul] = MulSymbol
        
        Schematic.mapping[Reg] = RegSymbol
        Schematic.mapping[Scope] = ScopeSymbol
        Schematic.mapping[Buf] = BufSymbol
        Schematic.mapping[Bit] = BitSymbol
        Schematic.mapping[Mux2] = Mux2Symbol
        Schematic.mapping[Range] = RangeSymbol

        self.mapping[Waveform] = ScopeSymbol # Temp solution

        self.parent = parent
        self.render = render        
        self.canvas = None

        self.showValues = showValues

        if (placeAndRoute):
            self.placeAndRoute()
        
        
        # schematics are created but not directly drawn to allow 
        # the manipulation of the graphical objects
        
        #self.drawAll()
        
        #mainloop()

    def placeAndRoute(self, debug=False):
        self.placeInputPorts()
        self.placeInstances()
        self.placeOutputPorts()

        try:
            self.bruteForceSort()
            self.columnAssignment()
            
            self.createNets(debug=debug) 
            self.passthroughCreation()
            self.removeArrowsSpecialCases()
        except Exception as e:
            print(e)
            
        try:
            self.rowAssignment()
            
    
            self.trackAssignment()
            self.replaceAsColRow()
            
            #self.replaceByAdjacencyMatrix()
            
            # self.replaceByDependency()
            
            #self.replaceVerticalCompress()
            # #self.replaceHorizontalCompress()
            
    
            self.routeNets()
        except Exception as e:
            print(e)
        
    def draw(self):
        self.drawAll()
        import matplotlib.pyplot as plt
        return plt.show()
    
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
            if (isinstance(net.sink, Mux2Symbol)):
                if (net.wire == net.sink.obj.inPorts[0].wire):
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
        for colidx in range(0, numCols):
            track = 0
            netsInCol = [n for n in nets if n.sourcecol == colidx]
            
            # temporal object to check if several nets are created from the 
            # same source
            channeltracks = {}
            
            #print('Nets is column', colidx, netsInCol )
            for net in netsInCol:
                try:
                    existingtrack = channeltracks[net.wire]
                    
                except:
                    existingtrack = None
                    
                
                if (existingtrack == None):
                    # There is not track for this wire
                    net.track = track
                    track = track + 1
                    channeltracks[net.wire]={'num':net.track, 'nets':[net]}
                    #print('track:', net.track, 'channel tracks:', channeltracks)
                else:
                    net.track = existingtrack['num']
                    existingtrack['nets'].append(net)
                 
                # do not update the sourcecol
                #net.sourcecol = colidx - 1
                    
            #print('col:', colidx, ['{}->{}'.format(type(x.source).__name__, type(x.sink).__name__)  for x in netsInCol])
            #print('track:', track, 'channel tracks:', channeltracks)
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
                if (src['port'].wire == wire):
                    ret.append(src['symbol'])
        
        return ret
    
    def getAllInstanceSinks(self, sym:LogicSymbol):
        """
        Return all the instance objects that are connected
        as sinks to this symbol. 

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
            # an input port is a single driver
            outports = [obj]
        elif (isinstance(obj, OutPort)):
            # an output port cannot drive anything (at the circuit level)
            # so, no dependent instances 
            return []
        elif (isinstance(obj, InOutPort)):
            outports = [obj]
        else:
            if (not(hasattr(obj, 'outPorts'))):
                raise Exception('obj {} from type {} {} has not out ports'.format(obj.getFullPath(), type(obj), isinstance(obj, InPort)))
                
            outports = obj.outPorts
        
        for outp in outports:
            wire = outp.wire
            
            if not(wire in self.maxfanoutwires):
                # avoid to report elements connected by pruned wires
                for src in self.sinks:
                    if (src['port'].wire == wire):
                        ret.append(src['symbol'])
        
        # if multiple wires connect between two symbols, there will be repetitions
        # so remove duplicates
        ret = list(set(ret))
        
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
                          
    def columnManualAssignment(self, inlist, inslist, outlist):
        self.columns = []
        
        
        # Process inputs
        unsorted = {}
        currentCol = []
        for idx, obj in enumerate(self.objs):
            if (idx < self.numInputs):
                unsorted[obj.obj.name] = obj
                
        for name in inlist:
            currentCol.append(unsorted[name])
        self.columns.append(currentCol)
        
        # Process instances
        for inskeys in inslist:
            unsorted = {}
            currentCol = []
            for idx, obj in enumerate(self.objs):
                if (idx < self.numInputs):
                    pass
                elif (idx < self.firstOutput):
                    if (obj.obj.name in inskeys):
                        unsorted[obj.obj.name] = obj
            
            for name in inskeys:
                currentCol.append(unsorted[name])
            self.columns.append(currentCol)    
        
        # Process outputs
        unsorted = {}
        currentCol = []
        for idx, obj in enumerate(self.objs):
            if (idx >= self.firstOutput):
                unsorted[obj.obj.name] = obj
        for name in outlist:
            currentCol.append(unsorted[name])
        self.columns.append(currentCol)
        
    def columnAssignment(self):
        """
        Creates the columns structure and assigns inputs, instances and outputs 
        to a column

        Returns
        -------
        None.

        """
        self.columns = []
        currentCol = []
        
        # append inputs. We know that inputs are always at the start
        # of the object list
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
    
    def passthroughCreation(self, debug=False):
        """
        Create passthrough entities.
        For connected entities that are separated by more than 1 column
        we create passthrough entities.
        For entities connected to previous columns we create feedback 
        entities.

        Returns
        -------
        None.

        """

        for colidx, col in enumerate(self.columns):
            for obj in col:
                # We list the objects in the column 
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
                        #print('WARNING: passthrough required between: [{}]'.format(colidx), type(obj).__name__, '[{}]'.format(sinkcol), type(sink).__name__, )
                        self.insertPassthrough(obj, colidx, sink, sinkcol, debug)
                    if (sinkcol <= colidx):
                        #print('WARNING: feedback required between: [{}]'.format(colidx), type(obj).__name__, '[{}]'.format(sinkcol), type(sink).__name__)
                        self.insertFeedback(obj, colidx, sink, sinkcol, debug)

    def insertPassthrough(self, source:LogicSymbol, sourcecol:int, sink:LogicSymbol, sinkcol:int, debug=False):
        """
        A passthrough instance has to be inserted for every wire connecting 
        entities source and sink

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
            if (wire is None):
                continue
            
            # remove the original net
            removeNets = [x for x in self.nets if x.wire== wire and x.source == source and x.sink == sink]

            if (len(removeNets) == 0):
                self.dumpNets()
                raise Exception('Wire:{} with source:{} {} and sink:{} {} not in remove nets'.format(wire.getFullPath(), id(source), source.obj.getFullPath(), id(sink), sink.obj.getFullPath()))
            
            if (len(removeNets) > 1):
                self.dumpNets()
                raise Exception('Muliple nets between source:{} {} and sink:{} {}'.format( type(source).__name__, source.obj.getFullPath(), type(sink).__name__, sink.obj.getFullPath()))

            netToRemove = removeNets[0]
            self.nets.remove(netToRemove)
        
            lastSymbol = source
            lastSourcePort = netToRemove.sourcePort
            
            for col in range(sourcecol+1, sinkcol):
                pts = PassthroughSymbol()

                self.objs.append(pts)
                self.columns[col].append(pts)

                # raise Exception('TODO get the port of this wire')
                # self.sources.append({'symbol':pts, 'port':wire})
                # self.sinks.append({'symbol':pts, 'port':wire})
                
                # TODO what to do here with the port info ??
                net1 = NetSymbol(wire, lastSourcePort, None, lastSymbol, pts)
                net1.sourcecol = col-1
                net1.arrow = False
                self.nets.append(net1)
                
                lastSymbol = pts
                lastSourcePort = None
                
                
            if (lastSymbol != None):
                # TODO what to do here with the port info 
                net2 = NetSymbol(wire, None, netToRemove.sinkPort, pts, sink)
                net2.sourcecol = sinkcol-1
                self.nets.append(net2)
                                
    def dumpNets(self):
        for idx, net in enumerate(self.nets):
            print('Net {} wire:{} source:{} {}  sink:{} {}'.format(idx, net.wire.getFullPath(), id(net.source), type(net.source).__name__ , id(net.sink), type(net.sink).__name__))
            
    def insertFeedback(self, source:LogicSymbol, sourcecol:int, sink:LogicSymbol, sinkcol:int, debug=False):
        """
        Create feedback nets between source and sink

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
        
        # intersection wires are wires that connect source and sink
        # but take care, because the same wire can have multiple sink ports
        
        for wire in intersection:
            # remove the original net
            removeNets = [x for x in self.nets if x.wire == wire and x.source == source and x.sink == sink]
            
            if (len(removeNets) == 0):
                self.dumpNets()
                raise Exception('Wire:{} with source:{} {} and sink:{} {} not in remove nets'.format(wire.getFullPath(), type(source).__name__, source.obj.getFullPath(), type(sink).__name__, sink.obj.getFullPath()))

            if (len(removeNets) > 1):
                self.dumpNets()
                raise Exception('Muliple nets between source:{} {} and sink:{} {}'.format( type(source).__name__, source.obj.getFullPath(), type(sink).__name__, sink.obj.getFullPath()))

            netToRemove = removeNets[0]
            self.nets.remove(netToRemove)
        
            lastSymbol = source
            
            #insert feedback channel if necessary
            
            #self.channels[sourcecol+1]
            fb_start = FeedbackStartSymbol()
            fb_start.debug = debug
            self.objs.append(fb_start)
            self.columns[sourcecol].append(fb_start)
            #self.sources.append({'symbol':fb_start, 'wire':wire})
            #self.sinks.append({'symbol':fb_start, 'wire':wire})
            
            # TODO: what to do here with the port info ???
            net1 = NetSymbol(wire, netToRemove.sourcePort, None , lastSymbol, fb_start)
            net1.sourcecol = sourcecol
            net1.arrow = False
            self.nets.append(net1)            
            
            fb_end = FeedbackStopSymbol()
            fb_end.debug = debug
            self.objs.append(fb_end)
            self.columns[sinkcol].append(fb_end)
            #self.sources.append({'symbol':fb_start, 'wire':wire})
            #self.sinks.append({'symbol':fb_start, 'wire':wire})
            
            # TODO what to do here with the port info ????
            net2 = NetSymbol(wire, None, netToRemove.sinkPort, fb_end, sink)
            net2.sourcecol = sinkcol
            net2.arrow = True
            self.nets.append(net2)
            
            lastSymbol = fb_end
            
            
            for col in range(sinkcol+1, sourcecol):
                pts = PassthroughSymbol()
                self.objs.append(pts)
                self.columns[col].append(pts)

                #raise Exception('TODO get the port of this wire')
                #self.sources.append({'symbol':pts, 'port':wire})
                #self.sinks.append({'symbol':pts, 'port':wire})
              
                # TODO what to do here with the port info ???
                net1 = NetSymbol(wire, None, None, lastSymbol, pts)
                net1.sourcecol = col-1
                net1.arrow = False
                self.nets.append(net1)
              
                lastSymbol = pts
                
                
            if (lastSymbol != None):
                # TODO What to do here with the port info ???
                net2 = NetSymbol(wire, None, None, lastSymbol, fb_start)
                net2.sourcecol = sourcecol
                net2.arrow = False
                self.nets.append(net2)

    def getWiresFromSource(self, source):
        return [x['port'].wire for x in self.sources if x['symbol'] == source]

    def getWiresFromSink(self, sink):
        return [x['port'].wire for x in self.sinks if x['symbol'] == sink]
    
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
                sinks = self.findSinkTuples(sourceTuple['port'].wire)
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
        raise Exception('This counts wires, not ports')

        wiresFromSource = [source['port'].wire for source in self.sources if source['symbol'] == sourceSym]
        wiresToSink = [sink['port'].wire for sink in self.sinks if sink['symbol'] == sinkSym]
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
            self.y = self.y + gridsize * LogicSymbol.portSeparation
            self.sources.append({'symbol':isym, 'x':15, 'y':8+5, 'port':inp})
        
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
            ret = Schematic.mapping[type(obj)]
    
            #print('getSymbol -> good', obj)
                
        except:
            #print('getSymbol -> none for object', type(obj))
            return None

        return ret(obj, x, y)
        

    def placeInstance(self, child):
        isym = self.getSymbol(child, self.x, self.y)
        
        if (isym is None):
            isym = InstanceSymbol(child, self.x, self.y)
        
        self.objs.append(isym)
        self.y = self.y + isym.getHeight() + cellmargin * 2 

        i = 0
        for inp in child.inPorts:
            #print('adding inport ', child, inp.name)
            self.sinks.append({'symbol':isym, 'x':0, 'y':8+8+8+5+i*LogicSymbol.portpitch, 'port':inp})
            i = i+1
        i = 0
        for inp in child.outPorts:
            #print('adding outport ', child, inp.name)
            self.sources.append({'symbol':isym, 'x':isym.getWidth(), 'y':8+8+8+5+i*LogicSymbol.portpitch, 'port':inp})
            i = i+1
                
        return isym
    
    def placeInstances(self):
        maxx = 0
        self.y = gridsize*3
        
        #print('placeInstances', self.sys)
        if (self.showValues):
            self.x += portvaluemargin
        
        for child in self.sys.children.values():
            isym = self.placeInstance(child)
            maxx = max(maxx, isym.getWidth())
            
        self.x += maxx + gridsize*10 + cellmargin + portvaluemargin
        self.grid_yunits = self.y / gridsize
        self.grid_yunits = self.y / gridsize # @todo should this be x ??
        
    def placeOutputPorts(self):
        '''
        Place Output Ports and InOutPorts.
        This basically means creating an output port symbol for each port and
        assigning the its y coordinate 

        Returns
        -------
        None.

        '''
        #self.x = 1
        self.y = gridsize * 5
        
        self.firstOutput = len(self.objs)
        
        for inp in self.sys.outPorts:
            osym = OutPortSymbol(inp, self.x, self.y)
            self.objs.append(osym)
            self.y = self.y + gridsize * LogicSymbol.portSeparation
            self.sinks.append({'symbol':osym, 'x':0, 'y':8+5, 'port':inp})

        for inp in self.sys.inOutPorts:
            osym = InOutPortSymbol(inp, self.x, self.y)
            self.objs.append(osym)
            self.y = self.y + gridsize * LogicSymbol.portSeparation
            self.sinks.append({'symbol':osym, 'x':0, 'y':8+5, 'port':inp})
            self.sources.append({'symbol':osym, 'x':0, 'y':8+5, 'port':inp})

        #self.x = self.x + 3

        self.lastOutput = len(self.objs)

        
    def findSourceTuple(self, sinkWire:Wire):
        for source in self.sources:
            if (source['port'].wire == sinkWire):
                return source
            
        sourceNames = [x['wire'].getFullPath() for x in self.sources]
        raise Exception('Could not find a source to wire "{}" in the sources collection {}'.format(sinkWire.getFullPath(), sourceNames ) )
            
    def findSinkTuples(self, sourceWire):
        ret = []
        for sink in self.sinks:
            if (sink['port'].wire == sourceWire):
                ret.append(sink)
        return ret;
            
    def createNets(self, debug=False):
        """
        Create nets for all entities in the drawing.
        It populates the self.nets list by analyzing the sinks
        list which was collected in function createOutputPorts

        Returns
        -------
        None.

        """
        for sink in self.sinks:
            try:
                if (debug):
                    print('Sink:', sink)
                    
                wire = sink['port'].wire
                source = self.findSourceTuple(wire)
                sourcecol = self.getSymbolColumn(source['symbol'])
                sinkcol = self.getSymbolColumn(sink['symbol'])

                net = NetSymbol(wire, source['port'], sink['port'], source['symbol'], sink['symbol'])
                net.sourcecol = sourcecol
                net.sinkcol = sinkcol
                self.nets.append(net)   
            except Exception as err:
                print('Exception', err)
                
        self.maxfanoutwires = []

    # def createNetsWithJoints(self):
    #     """
    #     Create nets for all entities in the drawing.
    #     It populates the self.nets list by analyzing the sinks
    #     list which was collected in function createOutputPorts

    #     Returns
    #     -------
    #     None.

    #     """
        
    #     # build a list for all the sinks of a wire
    #     netSinks = {}
    #     for src in self.sinks:
    #         wire = src['wire']
    #         try:
    #             symlist = netSinks[wire]
    #         except:
    #             symlist = []
    #         symlist.append(src['symbol'])
    #         netSinks[wire] = symlist


    #     for sink in self.sinks:
    #         try:
    #             wire = sink['wire']
                
    #             wireSinks = netSinks[wire]
                
    #             if (len(wireSinks) == 1):
    #                 source = self.findSourceTuple(wire)
    #                 self.nets.append(NetSymbol(wire, source['symbol'], sink['symbol']))   
    #             else:
                    
    #         except Exception as err:
    #             print('Exception', err)
                
    #     self.maxfanoutwires = []

    def createNetsWithMaxFanout(self, maxfanout):
        """
        Create nets for all entities in the drawing.
        It populates the self.nets list by analyzing the sinks
        list which was collected in function createOutputPorts
    
        Returns
        -------
        None.
    
        """
        sourceWires = {}
        for src in self.sinks:
            wire = src['port'].wire
            try:
                symlist = sourceWires[wire]
            except:
                symlist = []
            symlist.append(src['symbol'])
            sourceWires[wire] = symlist
            
        self.maxfanoutwires = [x for x in sourceWires.keys() if len(sourceWires[x]) > maxfanout] 
            
        for sink in self.sinks:
            try:
                wire = sink['port'].wire
                
                fanout = len(sourceWires[wire])
                
                if (fanout <= maxfanout):
                    source = self.findSourceTuple(wire)
                    self.nets.append(NetSymbol(wire, source['port'], sink['port'], source['symbol'], sink['symbol']))   
                else:
                    print('skip wire {} fanout: {}'.format(wire.getFullPath(), fanout))
                    
            except Exception as err:
                print('Exception', err)
                
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

    def createRender(self, physical_shape=None, dpi=None) :
        """
        Creates the renderer object

        Parameters
        ----------
        physical_shape : tuple, optional
            Dimension of the physical canvas (in inches). The default is None.
        dpi : dots per inch, optional
            Dots per inch of the drawing canvas. The default is None, and it is calculated.

        Raises
        ------
        Exception
            DESCRIPTION.

        Returns
        -------
        None.

        """
        render = self.render
        if (render == 'matplotlib'):
            self.canvas = MatplotlibRender(self.getOccupancyGrid().shape, physical_shape, dpi)
        elif (render == 'tkinter'):
            self.canvas = TkinterRender(self.parent, self.getOccupancyGrid().shape)
        else:
            raise Exception('Unsupported render {}'.format(render))

    def drawValues(self, symbol):
        if (symbol.obj is None):
            #print('WARNING: no symbol for object', type(symbol))
            return
        if not(hasattr(symbol.obj, 'inPorts')):
            return
        
        for port in symbol.obj.inPorts:
            wire = port.wire
            pos = symbol.getPortSinkPos(port)
            self.canvas.drawText(symbol.x + pos[0] - portvaluemargin,
                                 symbol.y + pos[1] - gridsize * 2,
                                 '{:X}'.format(wire.get()), 'w')
        for port in symbol.obj.outPorts:
            wire = port.wire
            pos = symbol.getPortSourcePos(port)
            self.canvas.drawText(symbol.x + pos[0] + portvaluemargin,
                                 symbol.y + pos[1] - gridsize * 2,
                                 '{:X}'.format(wire.get()), 'e')


    def drawAll(self, debug=False):
        if (self.canvas is None):
            self.createRender()
            
        self.canvas.setForecolor('k')

        # Draw Instances
        
        # @todo the color and line properties should be assigned during creation 
        # so that they can later be manipulated by applications before drawing
        for obj in self.getNonNets():
            self.canvas.setForecolor('k')  
            self.canvas.setFillcolor('k')
            self.canvas.setLineWidth(2)
            if (debug):
                print('draw', type(obj))
            
            obj.draw(self.canvas, debug=debug)
            
            if (self.showValues):
                self.drawValues(obj)

        # Draw Nets
        for obj in self.getNets():
            
            self.canvas.setForecolor(obj.color)  
            self.canvas.setFillcolor(obj.color)
            self.canvas.setLineWidth(1)

            if (debug):
                print('draw', type(obj))
            
            obj.draw(self.canvas, debug=debug)
        
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
        """
        Sort the object list

        Returns
        -------
        am : TYPE
            DESCRIPTION.

        """
        am = self.getAdjacencyMatrix()
        nc = am.shape[0]

        timelimit = 10

        import time
        
        t0 = time.time()
        #print('adjacency matrix size', am.shape)

        if (nc > 50):
            # for circuits with more than 20 elements, avoid brute force
            print('avoiding brute force')
            return am
        
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

            #print('iter', k, 'cost:', cost, anychange)
                    
            if ((time.time() - t0) > timelimit):
                print('WARNING: time limit reached in sort')
                anychange = False
                
            if (not anychange):
                break

        am = self.getAdjacencyMatrix()
        return am

    def areSourceTarget(self, srcobj, trgobj):
        if (isinstance(srcobj, InPortSymbol)):
            outwires = [srcobj.obj.wire]
        elif (isinstance(srcobj, OutPortSymbol)):
            outwires = []
        elif (isinstance(srcobj, InOutPortSymbol)):
            outwires = [srcobj.obj.wire] # @todo is this what we should do ?
        else:
            outwires = [outport.wire for outport in srcobj.obj.outPorts]
        
        if (isinstance(trgobj, InPortSymbol)):
            inwires = []
        elif (isinstance(trgobj, OutPortSymbol)):
            inwires = [trgobj.obj.wire]
        elif (isinstance(trgobj, InOutPortSymbol)):
            inwires = [trgobj.obj.wire] # @todo check this, not sure if we should put more wires here
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
            
        #print('ocupancy grid = ', maxh, maxw)
        grid = np.zeros((maxh, maxw))
        
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
        
    def routeNetSquare(self, net:NetSymbol):
        """
        Route a single net. The process consist in assigning 
        a collection of points (path) to go from a source to a destination

        Parameters
        ----------
        net : NetSymbol
            DESCRIPTION.

        Returns
        -------
        None.

        """
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
            print('WARNING: net', net.source, 'with not track')
            net.track = 0

            
        if (isinstance(net.source, FeedbackStopSymbol)):
            # In stop symbols, the source and sink are in the same column
            if (isinstance(net.sink, FeedbackStartSymbol) or isinstance(net.sink, PassthroughSymbol)):
                # Normal case, midpoint is between both elements
                mp = (net.source.x + sw + netspacing + net.track * nettrackspacing, (p0[1]+pf[1])//2)                
                net.setPath([p0[0], mp[0], mp[0], pf[0]], [p0[1],p0[1],pf[1],pf[1]])
            else:
                mp = (net.source.x  - netspacing - net.track * nettrackspacing, -1)
    
                #print('Feedback-stop track:', net.track, mp[0])
                #net.setPath([mp[0], mp[0], pf[0]], [p0[1],pf[1],pf[1]])
                net.setPath([p0[0], mp[0], mp[0], pf[0]], [p0[1], p0[1], pf[1], pf[1]])
        elif (isinstance(net.sink, FeedbackStartSymbol)):
            # In start symbols, the source and sink are in the same column, 
            # midpoint is similar to normal case (in x)
            mp = (net.source.x + sw + netspacing + net.track * nettrackspacing, -1)                
            
            #print('Feedback-start track:', net.track, mp[0])
            net.setPath([p0[0], mp[0], mp[0], pf[0]], [p0[1], p0[1], pf[1], pf[1]])
        else:                 
            # Normal case, midpoint is between both elements
            mp = (net.source.x + sw + netspacing + net.track * nettrackspacing, (p0[1]+pf[1])//2)                
            net.setPath([p0[0], mp[0], mp[0], pf[0]], [p0[1],p0[1],pf[1],pf[1]])

        #mp[0] = p0[0] + net.track * nettrackspacing
        
        net.routed = True
    
    def routeNetDirect(self, net:NetSymbol):
        """
        Route a single net. The process consist in assigning 
        a collection of points (path) to go from a source to a destination

        Parameters
        ----------
        net : NetSymbol
            DESCRIPTION.

        Returns
        -------
        None.

        """
        p0 = net.getStartPoint()
        pf = net.getEndPoint()
        

        # sw = 0
        # try:
        #     sw = self.channels[net.sourcecol]['sourcewidth'] 
        #     #sw = sw - net.source['symbol'].getWidth() + netspacing
        #     #print('sw[{}]={}'.format(net.sourcecol, sw))
        # except:
        #     if (hasattr(net, 'sourcecol') == False):
        #         # this net was not assigned a sourcecol
        #         print('WARNING: net', net.source['wire'].getFullPath(), 'without source column')
        #         net.track = 0
        #     else:
        #         print('error sourcecol=', net.sourcecol)
        #         print('channels[{}]'.format(net.sourcecol), self.channels[net.sourcecol])
        #         print('source sym', net.source)
        
        # if (hasattr(net, 'track') == False):
        #     print('WARNING: net', net.source['wire'].getFullPath(), 'with not track')
        #     net.track = 0

        # mp = (net.source.x + sw + netspacing + net.track * nettrackspacing, (p0[1]+pf[1])//2)    
            
        # if (isinstance(net.source, FeedbackStopSymbol)):
        #     #print('Feedback-stop track:', net.track, mp[0])
        #     net.setPath([mp[0], mp[0], pf[0]], [p0[1],pf[1],pf[1]])
        # elif (isinstance(net.sink, FeedbackStartSymbol)):
        #     #print('Feedback-start track:', net.track, mp[0])
        #     net.setPath([p0[0], mp[0], mp[0]], [p0[1],p0[1],pf[1]])
        # else:                  
        #     net.setPath([p0[0], mp[0], mp[0], pf[0]], [p0[1],p0[1],pf[1],pf[1]])

        net.setPath([p0[0], pf[0]], [p0[1],pf[1]])

        #mp[0] = p0[0] + net.track * nettrackspacing
        
        net.routed = True
    
    def routeNets(self, mode='square'):
        """
        Route all the nets

        Returns
        -------
        None.

        """
        nets = self.getNets()
        
        if (mode == 'square'):
            for net in nets:
                # route net
                self.routeNetSquare(net)
        elif (mode == 'direct'):
            for net in nets:
                # route net
                self.routeNetDirect(net)
        else:
            raise Exception('Unsupported net routing mode {}'.format(mode))

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
