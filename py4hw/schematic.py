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
netmargin = 40
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
        
    def drawText(self, x, y, text, anchor, color=None):
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

        kwargs = {'horizontalalignment': ha}
        if color is not None:
            kwargs['color'] = color            
            
        self.canvas.annotate(text, (x, y), **kwargs)
        
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

def countCrossings(am):
    nr, nc = am.shape
    lr = 0
    pcr = -1 # previous column max row
    n = 0
    for c in range(nc):
        fr = -1 # first one in the row
        
        for r in range(nr):
            if (am[r,c] != 0):
                if (fr == -1):
                    fr = r
                    lr = r
                    
                if (r < pcr):
                    n += 1
                elif (r > lr):
                    n += 1
                lr = r
                
            pcr = max(pcr, lr)
    return n


def permutationColumnsFromAdjacency(am):
    """
    Sorts columns by treating each column as a binary number.
    Row 0 is the least significant bit (2^0).
    """
    nr, nc = am.shape
    
    col_values = []
    for c in range(nc):
        value = 0
        for r in range(nr):
            if am[r, c]:  # If the cell is non-zero/True
                # Use bitwise OR and shift for efficiency
                value |= (1 << r)
        col_values.append((value, c))
        
    print('Col values (value, col)=', col_values)
    
    # Sort by the calculated binary value
    col_values.sort()
    
    # Return only the original column indices
    return [j for value, j in col_values]

def permutationRowsFromAdjacency(am):
    """
    Sorts rows by treating each row as a binary number.
    Col 0 is the most significant bit (2^(nc-1)).
    """
    nr, nc = am.shape
    
    row_values = []
    for r in range(nr):
        value = 0
        for c in range(nc):
            if am[r, c]:  # If the cell is non-zero/True
                # Use bitwise OR and shift for efficiency
                value |= (1 << (nc-1-c))
        row_values.append((value, r))
        
    print('Row values (value, row)=', row_values)
    
    # Sort by the calculated binary value
    row_values.sort(reverse=True)
    
    # Return only the original column indices
    return [j for value, j in row_values]
        
class Schematic:
    """
    Class that controls the schematic drawing
    """
    # Layout constants
    GRID_SIZE = gridsize
    CELL_MARGIN_VERTICAL = 15
    CELL_MARGIN_HORIZONTAL = 5
    NET_SPACING = 15
    NET_TRACK_SPACING = 10 # horizontal spacing of nets
    PORT_SEPARATION = LogicSymbol.portSeparation
    
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
        self.sources = []   # a list of net sources with a dictionary [symbol, x, y, port]
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

        self.maxfanoutwires = []
        self.channels = [] 

        self._reset_symbol_matrix()
        
        if (placeAndRoute):
            self.placeAndRoute()
        
        
        # schematics are created but not directly drawn to allow 
        # the manipulation of the graphical objects
        
        #self.drawAll()
        
        #mainloop()

    def _reset_symbol_matrix(self):
        self.symbol_matrix = np.empty((0,0), dtype=object) # initialize symbol matrix


    def _expand_symbol_matrix(self, num_rows, num_cols):        
        cr, cc= self.symbol_matrix.shape
        
        if num_rows > cr or num_cols > cc:
            nr, nc = max(num_rows, cr), max(num_cols, cc)
            new_matrix = np.empty((nr, nc), dtype=object)
            
            if cr > 0 and cc > 0:
                new_matrix[:cr, :cc] = self.symbol_matrix
            
            self.symbol_matrix = new_matrix

    def placeAndRoute(self, debug=False):
        import traceback
        self.placeInputPorts()
        self.placeInstances()
        self.placeOutputPorts()
        self.replaceAsColRow()

        #self.bruteForceSort()
        self.columnAssignment()
        self.replaceAsColRow()
        #self.moveToRightColumn()
        #self.removeEmptyColumns()
        
        try:
            self.insertMissingConnectionSymbols(debug=debug)
            self.createNets(debug=debug) 
        except Exception as e:
            
            print('WARNING: error in create nets')
            traceback.print_exc()
            
        self.replaceAsColRow()
        try:
            self.passthroughCreation()
        except Exception as e:
            print('WARNING: error in passthrough')
            traceback.print_exc()
        self.replaceAsColRow()
        self.replaceAsColRow()
        self.removeArrowsSpecialCases()
        self.replaceAsColRow(debug=debug)

        #self.rowAssignment()
        

        self.trackAssignment()
        self.replaceAsColRow()
        
        #self.replaceByAdjacencyMatrix()
        
        # self.replaceByDependency()
        
        #self.replaceVerticalCompress()
        # #self.replaceHorizontalCompress()
        

        self.routeNets()
    
        
    def draw(self):
        self.drawAll()
        import matplotlib.pyplot as plt
        return plt.show()
    
    def permuteColumn1(self, col, c1, perm):
        nr, nc = self.symbol_matrix.shape
        # 1. Identify the row indices that are part of the set c1
        rows = [r for r in range(nr) if self.symbol_matrix[r, col + 1] in c1]
        if len(rows) != len(perm):
            raise ValueError(f"Permutation size ({len(perm)}) != rows found ({len(rows)})")
        
        # 2. Apply the permutation to ALL columns from col+1 to the end
        for c in range(col + 1, nc):
            # Extract only the values we are interested in moving
            current_values = [self.symbol_matrix[r, c] for r in rows]
            
            # Reorder those values based on the permutation list
            reordered_values = [current_values[i] for i in perm]
            
            # Write them back and UPDATE SYMBOL ROW REFERENCES
            for i, r in enumerate(rows):
                symbol = reordered_values[i]
                self.symbol_matrix[r, c] = symbol
                if symbol is not None:
                    symbol.r = r  # Update the symbol's row position
    
    
    def permuteColumn0(self, col, c0, perm):
        nr, nc = self.symbol_matrix.shape
        # 1. Identify the row indices that are part of the set c0
        rows = [r for r in range(nr) if self.symbol_matrix[r, col] in c0]
        if len(rows) != len(perm):
            print(f"Permutation size ({len(perm)}) != rows found ({len(rows)})")
            print('permutations:' , perm, [c0[i].name for i in perm])
            print('identified rows', rows, [self.symbol_matrix[i,col].name for i in rows])
        
        # 2. Apply the permutation to ALL columns from col backwards to 0
        for c in range(col, -1, -1):
            # Extract only the values we are interested in moving
            current_values = [self.symbol_matrix[r, c] for r in rows]
            
            # Reorder those values based on the permutation list
            reordered_values = [current_values[i] for i in perm]
            
            # Write them back and UPDATE SYMBOL ROW REFERENCES
            for i, r in enumerate(rows):
                symbol = reordered_values[i]
                self.symbol_matrix[r, c] = symbol
                if symbol is not None:
                    symbol.r = r  # Update the symbol's row position

    def getAdjacencyMatrixOfColumns(self, c, withFeedback=True):
        """
        Creates an adjacency matrix of two consecutive columns.
        The returned matrix contains rows for the column c and columns for the column c+1
        
             c+1[0]  c+1[1] .... c[m-1]
        c[0]   0      1           0
        c[1]   1      0           0
        ...
        c[n-1]  0      0          1
        
        
        Returns
        -------
        adjacency matrix : numpy 2D array with the connections between 
            circuit instances
    
        """
        c0_syms = []
        c1_syms = []
    
        nr, nc = self.symbol_matrix.shape
    
        for r in range(nr):
            sym0 = self.symbol_matrix[r, c]
            sym1 = self.symbol_matrix[r, c+1]
    
            if (sym0 is not None):
                c0_syms.append(sym0)
            if (sym1 is not None):
                c1_syms.append(sym1)
                
                # treat feedback stop points specially. 
                # We create a fake source in the previous columns
                if (withFeedback):
                    if (isinstance(sym1 , FeedbackStopSymbol)):
                        c0_syms.append(sym1.fb_start)
    
        am = np.zeros((len(c0_syms), len(c1_syms)), dtype=int) # adjacency matrix
        nr, nc = am.shape
    
        for sym0_id in range(nr):
            sym0 = c0_syms[sym0_id]
    
            for sym1_id in range(nc):
                sym1 = c1_syms[sym1_id]
    
                if (isinstance(sym0, FeedbackStartSymbol) and isinstance(sym1, FeedbackStopSymbol)):
                    am[sym0_id, sym1_id] = sym1.fb_start == sym0
                else:
                    am[sym0_id, sym1_id] = self.areSourceTarget(sym0, sym1)
    
    
        return c0_syms, c1_syms, am
                    
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
        Track assignment with horizontal overlap awareness.
    
        Key improvement: Assign tracks considering cross-over patterns.
        - Nets going DOWN get lower track indices (left side)
        - Nets going UP get higher track indices (right side)
        - This prevents horizontal overlap of routing segments
    
        Returns
        -------
        None.
        """
        nets = self.getNets()
        nr, nc = self.symbol_matrix.shape
        self.channels = [] 
    
        for c in range(nc):
            # ===== FORWARD TRACKS =====
            track = 0
            netsInCol = [n for n in nets if n.source.c == c]
            channeltracks = {}
    
            # Separate forward and feedback nets
            forward_nets = [n for n in netsInCol]
    
            # Analyze net directions to minimize overlaps
            net_directions = []
            for net in forward_nets:
                src_row = net.source.r
                sink_row = net.sink.r
    
                if src_row is not None and sink_row is not None:
                    if sink_row > src_row:
                        direction = 'down'
                        magnitude = sink_row - src_row
                    elif sink_row < src_row:
                        direction = 'up'
                        magnitude = src_row - sink_row
                    else:
                        direction = 'flat'
                        magnitude = 0
    
                    net_directions.append((direction, magnitude, net))
    
            # Sort by direction (down first, then up) to separate horizontally
            # Nets going DOWN use lower tracks (left side of routing area)
            # Nets going UP use higher tracks (right side of routing area)
            net_directions.sort(key=lambda x: (x[0] == 'up', x[1]))
    
            # Assign tracks respecting direction-based ordering
            for direction, magnitude, net in net_directions:
                if net.wire not in channeltracks:
                    net.track = track
                    track += 1
                    channeltracks[net.wire] = {'num': net.track, 'nets': [net]}
                else:
                    net.track = channeltracks[net.wire]['num']
                    channeltracks[net.wire]['nets'].append(net)
    
            
    
            # Store both forward and feedback track info
            self.channels.append({
                'tracks': track,              # Forward tracks
                'track': channeltracks,       # Forward track details
            })    
        
    def moveToRightColumn(self, debug=False):
        """
        Analyzes all elements of the symbol_matrix. 
        For each element we check their sinks and find the minimum sink with 
        a column bigger that the current element. We move the element to the 
        column -1 
        
        Parameters
        ----------
        debug : bool
            Enable debug output
            
        Returns
        -------
        moves : int
            Number of symbols moved
        """
        nr, nc = self.symbol_matrix.shape
        moves = 0
        
        
        # Iterate through all symbols in the matrix
        for r in range(nr):
            for c in range(nc):
                sym = self.symbol_matrix[r, c]
                
                if sym is None:
                    continue
                
                if isinstance(sym, InPortSymbol):
                    continue
                    
                sinks = self.getAllInstanceSinks(sym)
                
                min_delta = nc
                min_delta_obj = None
                for sink in sinks:
                    sc = sink.c
                    if (sc > c):
                        min_delta = sc - c
                        min_delta_obj = sink
                                                
                if (min_delta > 1) and not(min_delta_obj is None):
                    if (debug):
                        print('min delta for', sym.name, '=', min_delta, 'with obj', min_delta_obj.name)

                    # Find a free row in the target column
                    target_col = c + min_delta-1
                    target_row = self._findFreeRowInColumn(target_col, r)
                    
                    # Move the symbol
                    self.symbol_matrix[r, c] = None
                    self.symbol_matrix[target_row, target_col] = sym
                    
                    moves += 1
                        
                    if debug:
                        sym_name = sym.name if hasattr(sym, 'name') else str(type(sym).__name__)
                        print(f"Moved '{sym_name}' from ({r},{c}) to ({target_row},{target_col})")
        
        if debug:
            print(f"Total symbols moved: {moves}")
        
        return moves
    
    


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
        
        if (isinstance(obj, InPort)):
            # an input port dows not have a source 
            return []

        elif (isinstance(obj, OutPort)):
            # an output port is a single driver
            inports = [obj]

        else:
            if (not(hasattr(obj, 'inPorts'))):
                raise Exception('obj {} from type {} {} has not in ports'.format(obj.getFullPath(), type(obj), isinstance(obj, InPort)))
                
            inports = obj.inPorts
        
        for inp in inports:
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



    def columnAssignment(self):
        """
        Assign columns using DFS-based Longest Path layering and populate symbol_matrix.
        - Column 0: Strictly Inputs.
        - Column 1+: Logic instances (sorted by dependency depth).
        - Final Column: Outputs.
        
        Each symbol is placed in symbol_matrix[row, col] based on column assignment
        and its position within that column.
        """
        self._reset_symbol_matrix()
        
        # 1. Define Groups
        input_objs = self.objs[:self.numInputs]
        instances = self.objs[self.numInputs:self.firstOutput]
        output_objs = self.objs[self.firstOutput:]
    
        # 2. Initialization for level calculation
        # levels: stores the calculated depth. Inputs are fixed at Level 0.
        levels = {obj: 0 for obj in input_objs}
        
        # visiting_state: 0=unvisited, 1=visiting, 2=visited
        visiting_state = {}
    
        def get_level(obj):
            if obj in levels:
                return levels[obj]
            
            # Cycle detection: if currently visiting, break the loop
            if visiting_state.get(obj) == 1:
                return -1 
            
            visiting_state[obj] = 1 # Mark visiting
            
            sources = self.getAllInstanceSources(obj)
            max_src_level = 0
            
            # If an object has no sources (e.g., constant 'one' or 'zero'),
            # max_src_level stays 0.
            # Therefore, level = 0 + 1 = 1. (Placed in Column 1)
            
            for src in sources:
                if src == obj: continue # Ignore self-loops
                
                src_lvl = get_level(src)
                if src_lvl != -1:
                    max_src_level = max(max_src_level, src_lvl)
            
            # Level is always 1 higher than the deepest source
            levels[obj] = max_src_level + 1
            
            visiting_state[obj] = 2 # Mark visited
            return levels[obj]
    
        # 3. Compute levels for all instances
        for obj in instances:
            if obj not in levels:
                get_level(obj)
    
        # 4. Determine max level and build column assignments
        instance_levels = [levels[obj] for obj in instances if obj in levels]
        max_level = max(instance_levels) if instance_levels else 0
        
        # Group symbols by column
        columns_dict = {}
        
        # Column 0: Inputs
        columns_dict[0] = input_objs
        
        # Columns 1..N: Instances grouped by level
        for level in range(1, max_level + 1):
            col = [obj for obj in instances if levels.get(obj) == level]
            if col:
                columns_dict[level] = col
        
        # Final column: Outputs
        columns_dict[max_level + 1] = output_objs
        
        # 5. Populate symbol_matrix
        col_idx = 0
        for col_num in sorted(columns_dict.keys()):
            col = columns_dict[col_num]
            for row_idx, sym in enumerate(col):
                self._expand_symbol_matrix(row_idx + 1, col_idx + 1)
                self.symbol_matrix[row_idx, col_idx] = sym
            col_idx += 1

    
    

    
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
        nr, nc = self.symbol_matrix.shape
        
        self.pt_idx = 0 # reset passthrough instance counter

        for c in range(nc):
            # we are not going to modify nc
            
            r = 0
            
            while r < nr:
                obj = self.symbol_matrix[r,c]

                #print(f'check[{r},{c}] ', end='')
                
                r += 1

                if (obj is None):
                    continue

                #print(obj.name)

                # We list the objects in the column 
                if (isinstance(obj, PassthroughSymbol)):
                    continue
                if (isinstance(obj, FeedbackStartSymbol)):
                    continue
                if (isinstance(obj, FeedbackStopSymbol)):
                    continue
                if (isinstance(obj, MissingConnectionSymbol)):
                    continue
                
                print('object in', r, c, obj.__class__)
                
                sinks = self.getAllInstanceSinks(obj)
                
                for sink in sinks:
                    sinkcol = sink.c
                    
                    if (sinkcol > c +1):
                        #print('WARNING: passthrough required between: [{}]'.format(colidx), type(obj).__name__, '[{}]'.format(sinkcol), type(sink).__name__, )
                        if (debug): print('Inserting passtrought from ', obj.name, 'to', sink.name)
                        self.insertPassthrough(obj, c, sink, sinkcol, debug)
                        
                        
                    if (sinkcol <= c):
                        #print('WARNING: feedback required between: [{}]'.format(colidx), type(obj).__name__, '[{}]'.format(sinkcol), type(sink).__name__)
                        if (debug): print('Inserting feedback from ', obj.name, 'to', sink.name)
                        self.insertFeedback(obj, c, sink, sinkcol, debug)
                        
                        
                nr, nc = self.symbol_matrix.shape


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
        r = source.r
        
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
                raise Exception(f'Wire:{wire.getFullPath()} {source.name} --> {sink.name} not in remove nets')
            
            if (len(removeNets) > 1):
                self.dumpNets()
                raise Exception('Muliple nets between source:{} {} and sink:{} {}'.format( type(source).__name__, source.obj.getFullPath(), type(sink).__name__, sink.obj.getFullPath()))

            netToRemove = removeNets[0]
            self.nets.remove(netToRemove)
        
            lastSymbol = source
            lastSourcePort = netToRemove.sourcePort
            
            # is the path free ?
            if not(np.all(self.symbol_matrix[r, sourcecol+1:sinkcol-1] is None)):
                if (debug): print(f'row {r} not free, creating row below')
                empty_row = np.empty(self.symbol_matrix.shape[1], dtype=object)
                self.symbol_matrix = np.insert(self.symbol_matrix, r + 1, empty_row, axis=0)
                r += 1
                self.replaceAsColRow()

            for col in range(sourcecol+1, sinkcol):
                pts = PassthroughSymbol()

                pts.name = f'pt{self.pt_idx}'
                self.pt_idx += 1
                
                self.objs.append(pts)
                self.symbol_matrix[r, col] = pts

                # raise Exception('TODO get the port of this wire')
                # self.sources.append({'symbol':pts, 'port':wire})
                # self.sinks.append({'symbol':pts, 'port':wire})
                
                # TODO what to do here with the port info ??
                net1 = NetSymbol(wire, lastSourcePort, None, lastSymbol, pts)
                net1.arrow = False
                self.nets.append(net1)
                
                lastSymbol = pts
                lastSourcePort = None
                
                
            if (lastSymbol != None):
                # TODO what to do here with the port info 
                net2 = NetSymbol(wire, None, netToRemove.sinkPort, pts, sink)
                self.nets.append(net2)
                                
    def dumpNets(self):
        for idx, net in enumerate(self.nets):
            print(f'Net {idx} wire:{net.wire.getFullPath()} {net.source.name} --> {net.sink.name}')
            
    def insertFeedback(self, source:LogicSymbol, sourcecol:int, sink:LogicSymbol, sinkcol:int, debug=False):
        """
        Create feedback nets between source and sink.
        
        The FeedbackStopSymbol is placed in sinkcol-1 (column before sink),
        and a PassthroughSymbol is inserted in sinkcol to connect it to the sink.
        This prevents FeedbackStopSymbol from overlapping with instance symbols.
    
        Parameters
        ----------
        source : LogicSymbol
            Source symbol
        sourcecol : int
            Column index of source
        sink : LogicSymbol
            Sink symbol
        sinkcol : int
            Column index of sink
        debug : bool
            Debug flag
    
        Returns
        -------
        None.
        """
        r  = source.r

        if (sourcecol == sinkcol):
            sinkcol -= 1
            
        if (debug):
            print('Create feedback', sourcecol, sinkcol)
    
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
                raise Exception('Wire:{} with source:{} {} and sink:{} {} not in remove nets'.format(
                    wire.getFullPath(), type(source).__name__, source.obj.getFullPath(), 
                    type(sink).__name__, sink.obj.getFullPath()))
    
            if (len(removeNets) > 1):
                self.dumpNets()
                raise Exception('Multiple nets between source:{} {} and sink:{} {}'.format(
                    type(source).__name__, source.obj.getFullPath(), 
                    type(sink).__name__, sink.obj.getFullPath()))
    
            netToRemove = removeNets[0]
            self.nets.remove(netToRemove)
        
            lastSymbol = source
            
            # is the path free ?
            #if True: # not(np.all(self.symbol_matrix[r, sourcecol+1:sinkcol] is None)):
            #    empty_row = np.empty(self.symbol_matrix.shape[1], dtype=object)
            #    self.symbol_matrix = np.insert(self.symbol_matrix, r + 1, empty_row, axis=0)
            #    r += 1
            nr, nc = self.symbol_matrix.shape
            self._expand_symbol_matrix(nr+1, sourcecol+2)
            r = nr
            
            # Insert feedback start in source column
            fb_start = FeedbackStartSymbol()
            fb_start.name = f'fA{self.pt_idx}'
            self.pt_idx += 1

            fb_start.debug = debug
            self.objs.append(fb_start)
            self.symbol_matrix[r,sourcecol+1] = fb_start
            
            net1 = NetSymbol(wire, netToRemove.sourcePort, None, lastSymbol, fb_start)
            net1.arrow = False
            self.nets.append(net1)            
            
            lastSymbol = fb_start
            
            # Insert passthroughs in intermediate columns (sourcecol+1 to sinkcol-2)
            for col in range(sourcecol , sinkcol-1 , -1):
                pts = PassthroughSymbol()
                pts.name = f'pt{self.pt_idx}'
                self.pt_idx += 1

                self.objs.append(pts)
                self.symbol_matrix[r,col] = pts
                
                net1 = NetSymbol(wire, None, None, pts, lastSymbol)
                net1.sourcecol = col - 1
                net1.arrow = False
                self.nets.append(net1)
                
                lastSymbol = pts
            
            # Insert feedback stop in sinkcol-1 (column BEFORE sink)
            fb_end = FeedbackStopSymbol()
            fb_end.name = f'fZ{self.pt_idx}'
            self.pt_idx += 1
            fb_end.fb_start = fb_start

            fb_end.debug = debug
            self.objs.append(fb_end)
            assert(sinkcol > 0)
            self.symbol_matrix[r, sinkcol-1 ] = fb_end
            
            net2 = NetSymbol(wire, None, None, fb_end , lastSymbol  )
            net2.arrow = False
            self.nets.append(net2)
            
            # Insert passthrough in sinkcol to bridge FeedbackStopSymbol to actual sink
            #pts_final = PassthroughSymbol()
            #pts_final.name = f'pt{self.pt_idx}'
            #self.pt_idx += 1

            #self.objs.append(pts_final)
            #self.symbol_matrix[r, sinkcol] = pts_final
            
            net3 = NetSymbol(wire, None, netToRemove.sinkPort, fb_end, sink)
            #net3 = NetSymbol(wire, None, netToRemove.sinkPort, fb_end, sink)
            net3.arrow = True
            self.nets.append(net3)
            
            # Connect passthrough to actual sink
            #net4 = NetSymbol(wire, None, netToRemove.sinkPort, pts_final, sink)
            #net4.sourcecol = sinkcol
            #net4.arrow = True
            #self.nets.append(net4)
        
    def getWiresFromSource(self, source):
        return [x['port'].wire for x in self.sources if x['symbol'] == source]

    def getWiresFromSink(self, sink):
        return [x['port'].wire for x in self.sinks if x['symbol'] == sink]
    
    def replaceByAdjacencyMatrix(self):
        raise Exception('non used')
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
                

    
    
    def _findFreeRowInColumn(self, target_col, preferred_row, debug=False):
        """
        Find a free row in target column.
        
        Strategy:
        1. Try preferred_row first (same row as source)
        2. Try rows nearby (above and below alternately)
        3. Try any empty row
        4. Expand matrix if necessary
        
        Parameters
        ----------
        target_col : int
            Target column
        preferred_row : int
            Preferred row (same as current)
        debug : bool
            Enable debug output
            
        Returns
        -------
        int or None
            Row index if found, None if no suitable row
        """
        nr, nc = self.symbol_matrix.shape
        
        if target_col >= nc:
            return None
        
        # Try preferred row first
        if preferred_row < nr and self.symbol_matrix[preferred_row, target_col] is None:
            return preferred_row
        
        # Try nearby rows (alternating above and below)
        for offset in range(1, nr):
            # Try above
            test_row = preferred_row - offset
            if 0 <= test_row < nr and self.symbol_matrix[test_row, target_col] is None:
                return test_row
            
            # Try below
            test_row = preferred_row + offset
            if test_row < nr and self.symbol_matrix[test_row, target_col] is None:
                return test_row
        
        # Try any empty row
        for row in range(nr):
            if self.symbol_matrix[row, target_col] is None:
                return row
        
        # No free row found
        return None
    
    

    
    def placeInputPorts(self):
        """
        Place the input ports of the module. We just place them using the grid

        Returns
        -------
        None.

        """
        nr, nc = self.symbol_matrix.shape

        self._expand_symbol_matrix(nr, nc+1) # we force a column for inputs
        
        r = 0
        for inp in self.sys.inPorts:
            isym = InPortSymbol(inp, 0, 0)
            self.objs.append(isym)
            self.sources.append({'symbol':isym, 'x':15, 'y':8+5, 'port':inp})
            self._expand_symbol_matrix(r+1, nc+1)
            self.symbol_matrix[r, nc] = isym
            r += 1
        
            
        # g = genGraph(self.sources)
        # g.add_edge(self.sources)
        # print("Executed")
        # g.col_assignment()
        # g.print_graph()
        self.numInputs = r
        
    def getSymbol(self, obj, x, y):
        try:
            cons = Schematic.mapping[type(obj)]
            

            #print('getSymbol -> good', obj)
                
        except:
            #print('getSymbol -> none for object', type(obj))
            return None

        ret = cons(obj, x, y)
        ret.name = obj.name
        return ret
        

    def placeInstance(self, child):
        isym = self.getSymbol(child, 0, 0)
        
        if (isym is None):
            isym = InstanceSymbol(child, 0, 0)
            
        
        self.objs.append(isym)

        i = 0
        for inp in child.inPorts:
            #print('adding inport ', child, inp.name)
            self.sinks.append({'symbol':isym, 'x':0, 'y':0, 'port':inp})
            i = i+1
        i = 0
        for inp in child.outPorts:
            #print('adding outport ', child, inp.name)
            self.sources.append({'symbol':isym, 'x':isym.getWidth(), 'y':8, 'port':inp})
            i = i+1
                
        return isym
    
    def placeInstances(self):
        nr, nc = self.symbol_matrix.shape
        r = 0
        
        for child in self.sys.children.values():
            isym = self.placeInstance(child)
            self._expand_symbol_matrix(r+1, nc+1)
            self.symbol_matrix[r,nc] = isym
            r += 1
            
                        
        
    def placeOutputPorts(self):
        '''
        Place Output Ports and InOutPorts.
        This basically means creating an output port symbol for each port and
        assigning the its y coordinate 

        Returns
        -------
        None.

        '''
        nr, nc = self.symbol_matrix.shape
        
        self._expand_symbol_matrix(nr, nc+1) # we force a column for outputs
        
        r = 0

        
        self.firstOutput = len(self.objs)
        
        for inp in self.sys.outPorts:
            osym = OutPortSymbol(inp, self.x, self.y)
            self.objs.append(osym)
            self.sinks.append({'symbol':osym, 'x':0, 'y':8+5, 'port':inp})
            self._expand_symbol_matrix(r+1, nc+1)
            self.symbol_matrix[r, nc] = osym
            r += 1

        for inp in self.sys.inOutPorts:
            osym = InOutPortSymbol(inp, self.x, self.y)
            self.objs.append(osym)
            self.sinks.append({'symbol':osym, 'x':0, 'y':8+5, 'port':inp})
            self.sources.append({'symbol':osym, 'x':0, 'y':8+5, 'port':inp})
            self._expand_symbol_matrix(r+1, nc+1)
            self.symbol_matrix[r, nc] = osym
            r += 1

        #self.x = self.x + 3

        self.lastOutput = len(self.objs)

    def getSourceSymbols(self, sym):
        return [net.source for net in self.getNets() if net.sink == sym]
    
    def getSinkSymbols(self, sym):
        return [net.sink for net in self.getNets() if net.source == sym]

    def mergeVirtualSymbols(self, debug=False):
        from collections import defaultdict
    
        doRun = True
    
        while (doRun):
            source = defaultdict(list)
            sink = defaultdict(list)
    
            doRun = False
            for net in self.getNets():
                source[net.source].append(net)
    
            if (debug): print('Trying to merge sinks')
                
            for src in list(source.keys()):
                sink_nets = []
                all_nets =  source[src]
    
                # First we check sources with passthrough sinks
                for net in all_nets:
                    if isinstance(net.sink, PassthroughSymbol):
                        sink_nets.append(net)
    
                num = len(sink_nets)
                sink_nets.sort(key=lambda x: x.sink.r)
    
    
                if (num > 1):
                    lastr = -1
                    lastnet = None
                    removed_nets = []
                    for net in sink_nets:
                        mergeable = (lastnet is not None) # (net.sink.r == lastr +1 ) # this element is mergeable if it is in a consecutive row
    
    
                        if (mergeable):
                            if (debug):
                                print('Merging Sink:', lastnet.sink.name, 'with', net.sink.name, 'in ', net.sink.r, net.sink.c)
                                print()
    
                            # source symbol 
                            pt1 = lastnet.sink
                            pt2 = net.sink
    
                            net1 = lastnet
                            net2 = net
    
                            if (net in removed_nets):
                                print('WARNING: this net was already removed!')
                                continue
    
                            pt2_nets = [net for net in self.getNets() if net.source == pt2]
    
                            self.nets.remove(net2) # delete the net sym -> pt2
                            removed_nets.append(net2)
                            self.symbol_matrix[pt2.r , pt2.c] = None # delete the pt2
    
                            for pt2_net in pt2_nets:
                                pt2_net.source = pt1
    
                            lastr = pt2.r
                            lastnet = net1
    
                            doRun = True
                        else:
                            lastr = net.sink.r
                            lastnet = net
    
            if (debug): print('Trying to merge feedback starts')
            for pt1 in list(source.keys()):
                if not(isinstance(pt1, PassthroughSymbol)):
                    # only consider passthrough to feedback start symbols
                    continue
    
                sink_nets = []
                all_nets =  source[pt1]
    
                # Get the feedback start symbol
                for net in all_nets:
                    if isinstance(net.sink, FeedbackStartSymbol):
                        sink_nets.append(net)
    
                num = len(sink_nets)
    
                if (num == 1):
                    pt1_fA1_net = sink_nets[0]
                    fA1_sym = pt1_fA1_net.sink
    
                    if (debug): print('pt1_fA1_net = ', pt1.name, '-->', fA1_sym.name)
    
                    fA1_sources = self.getSourceSymbols(fA1_sym)
                    final_sym = [sym for sym in fA1_sources if not isinstance(sym, VirtualSymbol)][0]
    
                    if (debug): print('A_fA1_net   = ', final_sym.name, '-->', fA1_sym.name)
    
                    # now get the other start symbols from this final symbol
                    fA2_nets = [net for net in self.getNets() if net.source == final_sym and isinstance(net.sink, FeedbackStartSymbol) and net.sink != fA1_sym]
    
                    for fA2_net_from_sym in fA2_nets:
    
                        if (debug): print('A_fA2_net   = ', fA2_net_from_sym.source.name, '-->', fA2_net_from_sym.sink.name)
    
                        # get the net from pt2
                        fA2_sym = fA2_net_from_sym.sink
    
                        fA2_nets = [net for net in self.getNets() if net != fA2_net_from_sym and net.sink == fA2_sym]
    
                        #print('pt2_nets = ', [net.source.name for net in fA2_nets])
                        pt2_net = fA2_nets[0]
                        pt2 = pt2_net.source
    
                        if (debug): print('pt1_fA2_net  = ',  pt2.name, '-->',  fA2_sym.name)
    
                        # now, link pt2 --> fA1 and remove the rest of the elements
                        # we have to remove fA2, pt2_net, and A_fA2 net
                        pt2_net.sink = fA1_sym
                        if (debug):
                            print('Merging Feedback:', pt2.name, '-->', fA1_sym.name)
                            print()
    
                        self.nets.remove(fA2_net_from_sym) 
                        removed_nets.append(fA2_net_from_sym)
                        self.symbol_matrix[fA2_sym.r , fA2_sym.c] = None # delete the fA2
    
            for net in self.getNets():
                sink[net.sink].append(net)
    
            if (debug): print('Trying to merge sources')        
                
            for dst in list(sink.keys()):
                source_nets = []
                all_nets =  sink[dst]
    
                # First we check sinks with passthrough sources
                for net in all_nets:
                    if isinstance(net.source, PassthroughSymbol):
                        source_nets.append(net)
    
                num = len(source_nets)
                source_nets.sort(key=lambda x: x.source.r)
    
                #print('sink', dst.name, 'sources:', [x.source.name for x in source_nets])
    
                if (num > 1):
                    lastr = -1
                    removed_nets = []
                    for net in source_nets:
                        mergeable = (net.source.r == lastr +1 )
    
                        if (mergeable):
                            if (debug): print('Merging Source:', net.source.name, net.source.r, net.source.c, mergeable)
    
                            pt1 = lastnet.source
                            pt2 = net.source
    
                            net1 = lastnet
                            net2 = net
    
                            if (net in removed_nets):
                                continue
    
                            self.nets.remove(net2) # delete the net sym -> pt2
                            removed_nets.append(net2)
                            self.symbol_matrix[pt2.r , pt2.c] = None # delete the pt2
    
                            pt2_nets = [net for net in self.getNets() if net.sink == pt2]
                            for pt2_net in pt2_nets:
                                pt2_net.sink = pt1
    
                            lastr = pt2.r
                            lastnet = net1
    
                            doRun = True
                        else:
                            lastr = net.source.r
                            lastnet = net        
                            
    def findSourceTuple(self, sinkWire:Wire):
        # finds a source symbol that contains the wire
        for source in self.sources:
            if (source['port'].wire == sinkWire):
                return source
            
        sourceNames = [x['port'].wire.getFullPath() for x in self.sources]
        raise Exception('Could not find a source to wire "{}" in the sources collection {}'.format(sinkWire.getFullPath(), sourceNames ) )
            
    def findSinkTuples(self, sourceWire):
        raise Exception('non used')
        ret = []
        for sink in self.sinks:
            if (sink['port'].wire == sourceWire):
                ret.append(sink)
        return ret;

    def insertMissingConnectionSymbols(self, debug=False):
        """
        Pre-pass before createNets: identify every sink whose wire has no
        driving source and insert a MissingConnectionSymbol in the column
        immediately to the left of the sink.
    
        This keeps createNets clean — by the time it runs, every wire
        that was undriven now has a synthetic source registered in
        self.sources.
        """
        from .schematic_symbols import MissingConnectionSymbol  # adjust if needed
    
        for sink in self.sinks:
            wire = sink['port'].wire
            sink_sym = sink['symbol']
            port = sink['port']
    
            # Check 1: port has no wire at all
            if wire is None:
                label = port.name
            else:
                # Check 2: wire exists but has no source in this schematic
                source = next(
                    (s for s in self.sources if s['port'].wire == wire),
                    None
                )
                if source is not None:
                    continue  # wire is properly driven — nothing to do
                label = wire.getFullPath()
    
            print(f'WARNING: no source for sink {sink_sym.name}.{port.name} '
                  f'("{label}") — inserting MissingConnectionSymbol')
    
            ms = MissingConnectionSymbol(label)
            ms.name = f'missing_{label}'
    
            # Place in the column immediately left of the sink
            r, c = sink_sym.r, sink_sym.c
            target_col = max(c - 1, 0)
    
            free_row = self._findFreeRowInColumn(target_col, r)
            if free_row is None:
                nr, _ = self.symbol_matrix.shape
                self._expand_symbol_matrix(nr + 1, self.symbol_matrix.shape[1])
                free_row = nr
    
            self.objs.append(ms)
            self.symbol_matrix[free_row, target_col] = ms
    
            # Register as a source so createNets can find it normally
            self.sources.append({
                'symbol': ms,
                'x': ms.getWidth(),
                'y': ms.getHeight() // 2,
                'port': port,          # same port object — wire identity is shared
            })
            
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
            
            if (debug):
                print('Sink:', sink['symbol'].name, sink['port'].name)
                
            wire = sink['port'].wire
            
            if (wire is None):
                raise Exception('sink {} port {} does not have a connected wire'.format(sink['symbol'].name, sink['port'].name))
                
            source = self.findSourceTuple(wire)
            
            net = NetSymbol(wire, source['port'], sink['port'], source['symbol'], sink['symbol'])
            self.nets.append(net)   
        
                
        self.maxfanoutwires = []


    def createNetsWithMaxFanout(self, maxfanout):
        raise Exception('non used')
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
                print('createNetsWithMaxFanout Exception', err)
                
    def getNets(self):
        return self.nets
    
    def getNonNets(self):
        # we return non nets sorted by column and row in the grid
        
        #oa = np.array(self.objs)
        #ba = np.array([not isinstance(x, NetSymbol) for x in self.objs])
        #return list(oa[ba])
        ret = []
        nr, nc = self.symbol_matrix.shape
        
        for c in range(nc):
            for r in range(nr):
                item = self.symbol_matrix[r,c]
                if (item is not None):
                    ret.append(item)
        
        return ret

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
            if (False): #debug):
                print('draw', type(obj))
            
            obj.draw(self.canvas, debug=debug)
            
            if (self.showValues):
                self.drawValues(obj)

        # Draw Nets
        for obj in self.getNets():
            
            self.canvas.setForecolor(obj.color)  
            self.canvas.setFillcolor(obj.color)
            self.canvas.setLineWidth(1)

            if (False): # debug):
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
        

    


    def areSourceTarget(self, srcobj, trgobj):
        """
        Determine if srcobj is a source to trgobj by checking for shared wires.
        Handles PassthroughSymbol, FeedbackStartSymbol, and FeedbackStopSymbol.
        
        Parameters
        ----------
        srcobj : LogicSymbol
            Source symbol
        trgobj : LogicSymbol
            Target symbol
            
        Returns
        -------
        int
            Number of shared wires between source and target
        """
        if len(self.nets) == 0:
            # No nets and passthough / feedback objects are created
            if isinstance(srcobj, InPortSymbol):
                outwires = [srcobj.obj.wire]
            elif isinstance(srcobj, OutPortSymbol):
                outwires = []
            elif isinstance(srcobj, InOutPortSymbol):
                outwires = [srcobj.obj.wire]
            else:
                # Regular logic symbol
                if srcobj.obj is None:
                    outwires = []
                else:
                    outwires = [outport.wire for outport in srcobj.obj.outPorts]
            
            if isinstance(trgobj, InPortSymbol):
                inwires = []
            elif isinstance(trgobj, OutPortSymbol):
                inwires = [trgobj.obj.wire]
            elif isinstance(trgobj, InOutPortSymbol):
                inwires = [trgobj.obj.wire]
            else:
                # Regular logic symbol
                if trgobj.obj is None:
                    inwires = []
                else:
                    inwires = [inport.wire for inport in trgobj.obj.inPorts]
        
                
            # Find intersection of wires
            inter = Intersection(inwires, outwires)
            
            return len(inter)

        else:
            count = 0
            for net in self.nets:
                if net.source == srcobj and net.sink == trgobj:
                    count += 1
            return count
        
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
            w = obj.x + obj.getWidth() 
            h = obj.y + obj.getHeight() 
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
            w = obj.getWidth() 
            h = obj.getHeight() 
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
                    grid[y[0]-netspacing:y[1]+self.NET_SPACING, x[0]:x[1]] = 2
                    grid[y[1]:y[2], x[1]-self.NET_SPACING:x[2]+self.NET_SPACING] = 2
                    grid[y[2]-netspacing:y[3]+self.NET_SPACING, x[2]:x[3]] = 2
                    grid[y[3]:y[4], x[3]-self.NET_SPACING:x[4]+self.NET_SPACING] = 2
                    grid[y[4]-netspacing:y[5]+self.NET_SPACING, x[4]:x[5]] = 2
                    
                #print('OG:', obj.obj.getFullPath(), x,y, x+w, y+h)
            
        return grid


        
    def routeNetSquare(self, net):
        """
        Route a single net with proper feedback track handling.
        
        Parameters
        ----------
        net : NetSymbol
            The net to route.
    
        Returns
        -------
        None.
        """
        p0 = net.getStartPoint()
        pf = net.getEndPoint()
        
        # Get source column width
        sw = 0
        try:
            sw = self.channels[net.source.c]['sourcewidth'] 
        except:
            print('WARNING: net without source column, assigning track 0 (will cause collisions)')
            net.track = 0
        
        # Ensure track is set
        if not hasattr(net, 'track'):
            print('WARNING: net without track')
            net.track = 0
    
        # FEEDBACK NET ROUTING (going backwards, right to left)
        if isinstance(net.source, FeedbackStopSymbol):
            mp_x = net.source.x + sw + self.NET_SPACING + net.track * self.NET_TRACK_SPACING
            
            #net.setPath([p0[0], mp_x, mp_x, pf[0]], [p0[1], p0[1], pf[1], pf[1]])
            net.setPath([mp_x, mp_x, pf[0]], 
                        [p0[1], pf[1], pf[1]])
            
        
        # FEEDBACK START (receives feedback from the left)
        elif isinstance(net.sink, FeedbackStartSymbol):
            # Normal forward routing to feedback start symbol
            mp_x = net.source.x + sw + self.NET_SPACING + net.track * self.NET_TRACK_SPACING
            #net.setPath([p0[0], mp_x, mp_x, pf[0]], [p0[1], p0[1], pf[1], pf[1]])
            net.setPath([p0[0], mp_x, mp_x ], 
                        [p0[1], p0[1], pf[1]])
        
        # NORMAL FORWARD NET ROUTING
        else:
            # Standard routing to the right
            mp_x = net.source.x + sw + self.NET_SPACING + net.track * self.NET_TRACK_SPACING
            mp_y = (p0[1] + pf[1]) // 2
            net.setPath([p0[0], mp_x, mp_x, pf[0]], [p0[1], p0[1], pf[1], pf[1]])
    
        net.routed = True
    
    

    
    def routeNetDirect(self, net:NetSymbol):
        p0 = net.getStartPoint()
        pf = net.getEndPoint()

        net.setPath([p0[0], pf[0]], [p0[1],pf[1]])
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
    
    def replaceAsColRow(self, debug=False):
        """
        Place objects using row and column information.
        Uses self.rows (row assignments) to determine y-coordinates,
        and self.columns (column assignments) to determine x-coordinates.
        
        Returns
        -------
        None.
        """
        # Compute y-coordinate for each row
        current_y = self.GRID_SIZE * 3
        
        nr , nc = self.symbol_matrix.shape
        
        for r in range(nr):
            
            # Find max height in this row
            max_height = 0 # gridsize * 2  # Minimum row height
            for c in range(nc):
                sym = self.symbol_matrix[r,c]
                
                if not(sym is None):
                    sym.y = current_y
                    sym.r , sym.c = r, c
                    max_height = max(max_height, sym.getHeight())
                    
            if (debug):
                print('y=', current_y, 'Max height in row', r, '=', max_height , '+CELL MARGIN_VERTICAL=', max_height + self.CELL_MARGIN_VERTICAL)
            
            current_y += max_height + self.CELL_MARGIN_VERTICAL
        
        # Compute x-coordinate for each column
        x = 0
        
        for c in range(nc):
            # Add space for feedback tracks BEFORE this column
            if c < len(self.channels):
                feedback_space = self.channels[c].get('feedback_tracks', 0) * self.NET_TRACK_SPACING
                x = x + feedback_space
                if feedback_space > 0:
                    x = x + self.NET_SPACING # Extra margin
            
            # Find max width in this column
            maxw = 0
            for r in range(nr):
                sym = self.symbol_matrix[r,c]
                
                if not(sym is None):
                    sym.x = x
                    maxw = max(maxw, sym.getWidth())
            
            if (debug):
                print('x=', x, 'Max width in column', c, '=', maxw, '+CELL MARGIN_VERTICAL=', max_height + self.CELL_MARGIN_VERTICAL)

            # Move past this column
            x +=  maxw + self.CELL_MARGIN_HORIZONTAL
            
            # Add space for forward tracks AFTER this column
            if c < len(self.channels):
                forward_space = self.channels[c]['tracks'] * self.NET_TRACK_SPACING
                x +=  forward_space
                if forward_space > 0:
                    x +=  self.NET_SPACING  # Extra margin
                
                self.channels[c]['sourcewidth'] = maxw

    def insertEmptyColumn(self, col):
        """
        Inserts an empty column at index col.
        """
        nr, nc = self.symbol_matrix.shape
        new = np.empty((nr, nc + 1), dtype=object)
    
        new[:, :col] = self.symbol_matrix[:, :col]
        new[:, col] = None
        new[:, col + 1:] = self.symbol_matrix[:, col:]
    
        self.symbol_matrix = new
        
    def insertColumnsAfterFeedback(self, debug=False):
        """
        Detect symbols with feedback edges (adjacency entries left of diagonal)
        and insert an empty column before their column.
        """
    
        feedback_syms = self.findFeedbackSourceSymbols()
    
        if debug:
            print('feedback symbols', [sym.name for sym in feedback_syms])
        
        # Collect unique columns to split
        cols_to_insert = set()
    
        for sym in feedback_syms:
            col = sym.c
            if col is not None and col > 0:
                cols_to_insert.add(col+1)
    
        
        # Insert from right to left to preserve indices
        for col in sorted(cols_to_insert, reverse=True):
            self.insertEmptyColumn( col)        
        
    def insertColumnsBeforeFeedback(self, debug=False):
        """
        Detect symbols with feedback edges (adjacency entries left of diagonal)
        and insert an empty column before their column.
        """
    
        feedback_syms = self.findFeedbackSinkSymbols()
    
        if debug:
            print('feedback symbols', [sym.name for sym in feedback_syms])
        
        # Collect unique columns to split
        cols_to_insert = set()
    
        for sym in feedback_syms:
            col = sym.c
            if col is not None and col > 0:
                cols_to_insert.add(col)
    
        
        # Insert from right to left to preserve indices
        for col in sorted(cols_to_insert, reverse=True):
            self.insertEmptyColumn( col)        

    def findFeedbackSinkSymbols(self):
        # feedback sink symbols are net sinks that have columns lower than their source 
        nets = self.getNets()
        ret = []
        
        for net in nets:
            if net.sink.c < net.source.c:
                ret.append(net.sink)
                
        return ret
        
    def findFeedbackSourceSymbols(self):
        # feedback sink symbols are net sinks that have columns lower than their source 
        nets = self.getNets()
        ret = []
        
        for net in nets:
            if net.sink.c < net.source.c:
                ret.append(net.source)
                
        return ret


    def removeEmptyColumns(self, debug=False):
        """
        Remove all empty columns from symbol_matrix.
        But do not remove the first or last column
        
        Parameters
        ----------
        debug : bool
            Enable debug output
            
        Returns
        -------
        removed : int
            Number of columns removed
        """
        nr, nc = self.symbol_matrix.shape
        
        # Find columns that are NOT empty (have at least one non-None element)
        non_empty_cols = []
        for col in range(1, nc-1):
            if not np.all(self.symbol_matrix[:, col] == None):
                non_empty_cols.append(col)
        
        removed = nc - len(non_empty_cols)
        
        if debug:
            print(f"removeEmptyColumns: Removed {removed} columns ({nc} → {len(non_empty_cols)})")
        
        # Keep only non-empty columns
        self.symbol_matrix = self.symbol_matrix[:, non_empty_cols]
        
        return removed
    
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
