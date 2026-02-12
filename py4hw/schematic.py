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
        
        self.placeInputPorts()
        self.placeInstances()
        self.placeOutputPorts()
        self.replaceAsColRow()

        #self.bruteForceSort()
        self.columnAssignment()
        self.replaceAsColRow()
        #self.moveToRightColumn()
        #self.removeEmptyColumns()
        
        self.createNets(debug=debug) 
        self.replaceAsColRow()
        self.passthroughCreation()
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
    
    
    def _findFreeRowInColumn(self, c):
        raise Exception('non used')
        nr, nc = self.symbol_matrix.shape
        
        for r in range(nr):
            if self.symbol_matrix[r,c] is None:
                return r
            
        self._expand_symbol_matrix(nr+1, nc)
        
        return nr
    
    
    def compressLongRoutingPaths(self, max_path_length=2, debug=False):
        raise Exception('non used')
        """
        More aggressive compression: move any low-fanout symbol to be closer
        to its primary sink if it would otherwise require long routing.
        
        Only moves symbols if:
        - Fanout <= max_fanout (e.g., 2)
        - Current distance to sink > max_path_length columns
        - Target position doesn't create conflicts
        
        Parameters
        ----------
        max_path_length : int
            If distance > this, consider moving the symbol
        debug : bool
            Enable debug output
            
        Returns
        -------
        moves : int
            Number of symbols moved
        """
        nr, nc = self.symbol_matrix.shape
        moves = 0
        
        for r in range(nr):
            for c in range(nc):
                sym = self.symbol_matrix[r, c]
                
                if sym is None:
                    continue
                
                # Skip passthrough and feedback symbols
                sym_type = type(sym).__name__
                if sym_type in ['PassthroughSymbol', 'FeedbackStartSymbol', 
                               'FeedbackStopSymbol', 'OutPortSymbol']:
                    continue
                
                sinks = self.getAllInstanceSinks(sym)
                
                if not sinks or len(sinks) > 3:  # Only compress low-fanout
                    continue
                
                # Find distance to closest sink
                min_distance = float('inf')
                closest_sink = None
                
                for sink in sinks:
                    sink_row, sink_col = self.getSymbolLocation(sink)
                    if sink_col is not None:
                        distance = sink_col - c
                        if 0 < distance < min_distance:
                            min_distance = distance
                            closest_sink = sink
                
                # If path is long, try to move closer
                if min_distance > max_path_length and closest_sink is not None:
                    closest_sink_row, closest_sink_col = self.getSymbolLocation(closest_sink)
                    
                    # Target: column just before sink
                    target_col = closest_sink_col - 1
                    
                    if target_col > c:
                        target_row = self._findFreeRowInColumn(target_col, c, nc)
                        
                        # Check if move creates conflicts (simple check: no symbol swap)
                        if target_row < nr and self.symbol_matrix[target_row, target_col] is None:
                            self.symbol_matrix[r, c] = None
                            self.symbol_matrix[target_row, target_col] = sym
                            
                            moves += 1
                            
                            if debug:
                                sym_name = sym.name if hasattr(sym, 'name') else str(sym_type)
                                print(f"Compressed '{sym_name}': ({r},{c}) → ({target_row},{target_col}) "
                                      f"(distance: {min_distance} → {closest_sink_col - target_col})")
        
        if debug:
            print(f"Total symbols compressed: {moves}")
        
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

    def getSymbolColumn(self, sym):
        raise Exception('non used')
        _, c = self.getSymbolLocation(sym)
        return c
    
    def getSymbolLocation(self, sym):
        raise Exception('non used')
        """
        Find the row, column assigned to a symbol

        Parameters
        ----------
        src : TYPE
            DESCRIPTION.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        nr, nc = self.symbol_matrix.shape
        
        for r in range(nr):
            for c in range(nc):
                if self.symbol_matrix[r,c] == sym:
                    return r,c
            
        return None, None
                          
    def columnManualAssignment(self, inlist, inslist, outlist):
        raise Exception('non used')
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

    
    
    def rowAssignment(self, debug=False):
        raise Exception('non used')
        """
        Assign rows by minimizing crossings between adjacent columns.
        
        For each column pair (col_prev, col_curr):
        1. Build adjacency matrix: sources(rows) × sinks(columns)
        2. Find row permutation of col_curr that minimizes crossings
        3. Apply permutation to symbol_matrix
        
        Parameters
        ----------
        debug : bool
            Enable debug output
            
        Returns
        -------
        None
        """
        nr, nc = self.symbol_matrix.shape
        
        if nc <= 1:
            return
        
        
        # Process each column pair (col_prev, col_curr)
        for col_curr in range(1, nc):
            col_prev = col_curr - 1
            
            before = self._countCrossingsInColumnPair(col_prev, col_curr)
            
            if debug:
                print(f"\nProcessing columns {col_prev} → {col_curr}: {before} crossings before")
            
            if (before == 0):
                continue
            
            # Optimize this column pair using adjacency matrix
            self._optimizeColumnPairMatrix(col_prev, col_curr, debug)
            
            if debug:
                after = self._countCrossingsInColumnPair(col_prev, col_curr)
                print(f"  After optimization: {after} crossings")
        
    
    
    def _optimizeColumnPairMatrix(self, col_prev, col_curr, debug=False):
        raise Exception('non used')
        """
        Minimize crossings between adjacent columns using adjacency matrix.
        
        Algorithm:
        1. Get symbols in both columns
        2. Build adjacency matrix: prev_symbols (rows) × curr_symbols (cols)
           Entry [i,j] = number of wires connecting prev[i] to curr[j]
        3. Find row permutation of curr that minimizes crossings
        4. Apply permutation to symbol_matrix
        
        Parameters
        ----------
        col_prev : int
            Previous column
        col_curr : int
            Current column
        debug : bool
            Enable debug output
            
        Returns
        -------
        None
        """
        nr = self.symbol_matrix.shape[0]
        
        # Collect symbols in both columns (preserving row order)
        prev_symbols = []
        prev_rows = []
        curr_symbols = []
        curr_rows = []
        
        for row in range(nr):
            sym_prev = self.symbol_matrix[row, col_prev]
            if sym_prev is not None:
                prev_symbols.append(sym_prev)
                prev_rows.append(row)
            
            sym_curr = self.symbol_matrix[row, col_curr]
            if sym_curr is not None:
                curr_symbols.append(sym_curr)
                curr_rows.append(row)
        
        if len(curr_symbols) <= 1:
            return
        
        # Build adjacency matrix: prev_symbols × curr_symbols
        # adj[i,j] = number of wires from prev_symbols[i] to curr_symbols[j]
        num_prev = len(prev_symbols)
        num_curr = len(curr_symbols)
        
        adj_matrix = np.zeros((num_prev, num_curr), dtype=int)
        
        for i, prev_sym in enumerate(prev_symbols):
            for j, curr_sym in enumerate(curr_symbols):
                # Use areSourceTarget to get number of connections
                num_wires = self.areSourceTarget(prev_sym, curr_sym)
                adj_matrix[i, j] = num_wires
        
        # Find optimal ordering of curr_symbols using the matrix
        if num_curr <= 8:
            # Small set: try permutations
            best_perm = self._findOptimalPermutationMatrix(adj_matrix)
        else:
            # Large set: use greedy
            best_perm = self._findOptimalPermutationGreedy(adj_matrix)
        
        # Apply permutation to symbol_matrix
        reordered_symbols = [curr_symbols[i] for i in best_perm]
        
        for pos, sym in enumerate(reordered_symbols):
            self.symbol_matrix[curr_rows[pos], col_curr] = sym
        
        if debug:
            sym_names = [s.name if hasattr(s, 'name') 
                        else str(type(s).__name__) 
                        for s in reordered_symbols]
            print(f"  Optimal order: {' → '.join(sym_names)}")
    
    
    def _findOptimalPermutationMatrix(self, adj_matrix):
        raise Exception('non used')
        """
        Find optimal column permutation by trying all permutations.
        
        Optimal = permutation that minimizes total edge crossings.
        
        Parameters
        ----------
        adj_matrix : np.ndarray
            Shape (num_sources, num_sinks)
            Entry [i,j] = number of wires from source i to sink j
            
        Returns
        -------
        perm : list
            Optimal column ordering (indices into original column)
        """
        from itertools import permutations
        
        num_curr = adj_matrix.shape[1]
        
        best_crossings = float('inf')
        best_perm = list(range(num_curr))
        
        # Try all permutations of column indices
        for perm in permutations(range(num_curr)):
            # Reorder columns according to this permutation
            reordered = adj_matrix[:, perm]
            
            # Count crossings for this ordering
            crossings = self._countMatrixCrossings(reordered)
            
            if crossings < best_crossings:
                best_crossings = crossings
                best_perm = list(perm)
        
        return best_perm
    
    
    def _findOptimalPermutationGreedy(self, adj_matrix):
        raise Exception('non used')
        """
        Find ordering greedily using barycenter method on the adjacency matrix.
        
        For each column, compute barycenter (weighted average row position of sources).
        Sort columns by their barycenters.
        
        Parameters
        ----------
        adj_matrix : np.ndarray
            Shape (num_sources, num_sinks)
            
        Returns
        -------
        perm : list
            Column ordering by barycenter
        """
        num_sources, num_sinks = adj_matrix.shape
        
        # Compute barycenter for each sink column
        barycenters = []
        
        for j in range(num_sinks):
            col = adj_matrix[:, j]
            total_weight = col.sum()
            
            if total_weight > 0:
                # Weighted average of source row indices
                barycenter = sum(i * col[i] for i in range(num_sources)) / total_weight
            else:
                # No connections, use middle
                barycenter = num_sources / 2.0
            
            barycenters.append((barycenter, j))
        
        # Sort by barycenter
        barycenters.sort(key=lambda x: x[0])
        
        # Return column indices in sorted order
        return [j for _, j in barycenters]
    
    
    def _countMatrixCrossings(self, adj_matrix):
        raise Exception('non used')
        """
        Count edge crossings for a given adjacency matrix column ordering.
        
        Crossing occurs when:
        - Column j1 < column j2 (in the ordering)
        - But adj_matrix[i1, j1] > 0 and adj_matrix[i2, j2] > 0
        - And i1 > i2 (crossed relative positions)
        
        Parameters
        ----------
        adj_matrix : np.ndarray
            Shape (num_sources, num_sinks)
            Columns are in the current ordering
            
        Returns
        -------
        int
            Number of crossing wire pairs
        """
        num_sources, num_sinks = adj_matrix.shape
        
        crossings = 0
        
        # For each pair of columns (ordering is already applied)
        for j1 in range(num_sinks):
            for j2 in range(j1 + 1, num_sinks):
                # For each pair of rows
                for i1 in range(num_sources):
                    for i2 in range(i1 + 1, num_sources):
                        # Check if there's a crossing:
                        # Wires: i1→j1 and i2→j2
                        # Crossing if both exist and rows are reversed
                        
                        wire_i1_j1 = adj_matrix[i1, j1]
                        wire_i2_j2 = adj_matrix[i2, j2]
                        
                        # Also check reverse direction for crossing detection
                        wire_i1_j2 = adj_matrix[i1, j2]
                        wire_i2_j1 = adj_matrix[i2, j1]
                        
                        # Crossing: i1→j1 and i2→j2 cross if rows are in different order
                        # i.e., (i1 < i2 but j1 > j2) - but j is already ordered j1 < j2
                        # So just check: i1 < i2 but we have wires in reversed pattern
                        if wire_i1_j1 > 0 and wire_i2_j2 > 0 and wire_i1_j2 > 0 and wire_i2_j1 > 0:
                            # Both (i1→j1, i2→j2) and (i1→j2, i2→j1) exist = crossing
                            # Count minimum of these wire pairs
                            crossing_count = min(
                                wire_i1_j1 * wire_i2_j2,
                                wire_i1_j2 * wire_i2_j1
                            )
                            crossings += crossing_count
        
        return crossings
    
    
    
    
    def _countCrossingsInColumnPair(self, col_a, col_b):
        raise Exception('non used')
        """
        Count crossing nets between two adjacent columns using areSourceTarget.
        
        Parameters
        ----------
        col_a : int
            Source column
        col_b : int
            Sink column
            
        Returns
        -------
        int
            Number of crossing net pairs
        """
        nr = self.symbol_matrix.shape[0]
        
        # Get all symbols in both columns
        col_a_symbols = []
        col_a_rows = []
        col_b_symbols = []
        col_b_rows = []
        
        for row in range(nr):
            sym_a = self.symbol_matrix[row, col_a]
            if sym_a is not None:
                col_a_symbols.append(sym_a)
                col_a_rows.append(row)
            
            sym_b = self.symbol_matrix[row, col_b]
            if sym_b is not None:
                col_b_symbols.append(sym_b)
                col_b_rows.append(row)
        
        # Build adjacency matrix
        num_a = len(col_a_symbols)
        num_b = len(col_b_symbols)
        
        if num_a == 0 or num_b == 0:
            return 0
        
        adj = np.zeros((num_a, num_b), dtype=int)
        
        for i, sym_a in enumerate(col_a_symbols):
            for j, sym_b in enumerate(col_b_symbols):
                adj[i, j] = self.areSourceTarget(sym_a, sym_b)
        
        # Count crossings in this matrix
        crossings = 0
        
        for i1 in range(num_a):
            for i2 in range(i1 + 1, num_a):
                for j1 in range(num_b):
                    for j2 in range(j1 + 1, num_b):
                        # Crossing: i1→j1 and i2→j2 cross with i1→j2 and i2→j1
                        w_i1_j1 = adj[i1, j1]
                        w_i2_j2 = adj[i2, j2]
                        w_i1_j2 = adj[i1, j2]
                        w_i2_j1 = adj[i2, j1]
                        
                        if w_i1_j1 > 0 and w_i2_j2 > 0 and w_i1_j2 > 0 and w_i2_j1 > 0:
                            crossings += min(w_i1_j1 * w_i2_j2, w_i1_j2 * w_i2_j1)
        
        return crossings
    

    def replaceAsColRow(self):
        raise Exception('non used')
        """
        Place objects using symbol_matrix positions.
        Converts matrix (row, col) positions to actual (x, y) coordinates.
        
        For each row: computes a consistent y-coordinate across all columns
        For each column: computes a consistent x-coordinate and places all symbols
        
        Returns
        -------
        None.
        """
        num_rows, num_cols = self.symbol_matrix.shape
        
        # Compute y-coordinate for each row
        row_y_positions = {}
        current_y = gridsize * 3
        
        for row_idx in range(num_rows):
            row_y_positions[row_idx] = current_y
            
            # Find max height in this row
            max_height = gridsize * 2  # Minimum row height
            for col_idx in range(num_cols):
                sym = self.symbol_matrix[row_idx, col_idx]
                
                if sym is not None:
                    max_height = max(max_height, sym.getHeight())
            
            current_y += max_height + self.CELL_MARGIN_VERTICAL
        
        # Compute x-coordinate for each column and place symbols
        x = 0
        
        for col_idx in range(num_cols):
            # Add space for feedback tracks BEFORE this column
            if col_idx < len(self.channels):
                feedback_space = self.channels[col_idx].get('feedback_tracks', 0) * self.NET_TRACK_SPACING
                x = x + feedback_space
                if feedback_space > 0:
                    x = x + self.NET_TRACK_SPACING
            
            # Find max width in this column
            maxw = 0
            for row_idx in range(num_rows):
                sym = self.symbol_matrix[row_idx, col_idx]
                if sym is not None:
                    maxw = max(maxw, sym.getWidth())
            
            # Place all symbols in this column
            for row_idx in range(num_rows):
                sym = self.symbol_matrix[row_idx, col_idx]
                if sym is not None:
                    sym.x = x
                    sym.y = row_y_positions[row_idx]
            
            # Move past this column
            x = x + maxw + self.CELL_MARGIN_HORIZONTAL
            
            # Add space for forward tracks AFTER this column
            if col_idx < len(self.channels):
                forward_space = self.channels[col_idx]['tracks'] * self.NET_TRACK_SPACING
                x = x + forward_space
                if forward_space > 0:
                    x = x + netspacing
                
                self.channels[col_idx]['sourcewidth'] = maxw
    
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
            self._expand_symbol_matrix(nr+1, nc)
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
                
    def horizontalCompression(self, debug=False):
        raise Exception('non used')
        """
        Move symbols closer to their sinks by utilizing empty cells.
        
        Algorithm:
        1. For each column (left to right)
        2. For each symbol in the column
        3. Find the closest sink column
        4. If distance > 0 (sink is not in same column)
        5. Check for empty cells in columns between symbol and sink
        6. If empty cells exist, move symbol towards sink
        
        This reduces the span of long-distance connections and minimizes
        passthrough chains.
        
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
        
        if debug:
            print("horizontalCompression:")
        
        # Process each column from left to right
        for c in range(nc-1):
            col_moves = 0
            
            
            for r in range(nr):
                sym = self.symbol_matrix[r, c]
                
                if sym is None:
                    continue


                # find the mean row of the dependents
                deps = []
                for r2 in range(nr):
                    sym2 = self.symbol_matrix[r2, c+1]
                    if not(sym2 is None):
                        if self.areSourceTarget(sym, sym2):
                            deps.append(r2)
                if len(deps) > 0:
                    rm = int(np.mean(deps))

                    # check that we can move 
                    if (rm != r):
                        step = np.sign(r-rm) # increment
                        cr = r 
                        while (cr != rm) and (self.symbol_matrix[cr, c] is None):
                            cr += step
                            
                        # this will stop when we find an occupied cell
                        if (cr != r):
                            self.symbol_matrix[r, c] = None
                            self.symbol_matrix[cr, c] = sym
                            col_moves += 1
                    
            
            if debug and col_moves > 0:
                print(f"  Column {col}: {col_moves} symbols moved")
        
        if debug:
            print(f"Total symbols moved: {moves}")
        
        return moves
    
    
    def _moveSymbolCloserToSinks(self, sym, current_col, current_row, debug=False):
        raise Exception('non used')
        """
        Move a single symbol closer to its sinks if possible.
        
        Parameters
        ----------
        sym : LogicSymbol
            Symbol to potentially move
        current_col : int
            Current column of the symbol
        current_row : int
            Current row of the symbol
        debug : bool
            Enable debug output
            
        Returns
        -------
        bool
            True if symbol was moved
        """
        # Find all sinks of this symbol
        sinks = self.getAllInstanceSinks(sym)
        
        if not sinks:
            return False
        
        # Find the column of each sink
        sink_cols = []
        for sink in sinks:
            sink_row, sink_col = self.getSymbolLocation(sink)
            if sink_col is not None and sink_col > current_col:
                sink_cols.append(sink_col)
        
        if not sink_cols:
            # All sinks are in same column or to the left
            return False
        
        # Find the closest sink column
        closest_sink_col = min(sink_cols)
        distance = closest_sink_col - current_col
        
        if distance <= 0:
            return False
        
        # Try to move the symbol one column closer
        target_col = current_col + 1
        
        # Find a free row in the target column
        free_row = self._findFreeRowInColumn(target_col, current_row, debug)
        
        if free_row is None:
            return False
        
        # Move the symbol
        self.symbol_matrix[current_row, current_col] = None
        self.symbol_matrix[free_row, target_col] = sym
        
        if debug:
            sym_name = sym.name if hasattr(sym, 'name') else str(type(sym).__name__)
            print(f"    Moved '{sym_name}' from ({current_row},{current_col}) to ({free_row},{target_col}) "
                  f"(distance to sink: {distance-1})")
        
        return True
    
    
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
    
    
    # ============================================================================
    # ADVANCED VERSION: Multi-column look-ahead
    # ============================================================================
    
    def horizontalCompressionAggressive(self, max_distance=3, debug=False):
        raise Exception('non used')
        """
        More aggressive horizontal compression.
        
        Move symbols further than one column if:
        - Empty cells exist in the path
        - Target column is closer to sinks
        - Multiple columns of empty space available
        
        Parameters
        ----------
        max_distance : int
            Maximum number of columns to move a symbol
        debug : bool
            Enable debug output
            
        Returns
        -------
        moves : int
            Number of symbols moved
        """
        nr, nc = self.symbol_matrix.shape
        moves = 0
        
        if debug:
            print("horizontalCompressionAggressive:")
        
        # Process each column from left to right
        for col in range(nc):
            col_moves = 0
            
            # Collect symbols in this column
            symbols_in_col = []
            for row in range(nr):
                sym = self.symbol_matrix[row, col]
                if sym is not None:
                    symbols_in_col.append((row, sym))
            
            # Try to move each symbol closer to its sinks
            for row, sym in symbols_in_col:
                moved = self._moveSymbolAggressiveCloser(sym, col, row, max_distance, debug)
                if moved:
                    col_moves += 1
                    moves += 1
            
            if debug and col_moves > 0:
                print(f"  Column {col}: {col_moves} symbols moved")
        
        if debug:
            print(f"Total symbols moved: {moves}")
        
        return moves
    
    
    def _moveSymbolAggressiveCloser(self, sym, current_col, current_row, max_distance, debug=False):
        raise Exception('non used')
        """
        Move symbol as far as possible towards its sinks (within max_distance).
        
        Parameters
        ----------
        sym : LogicSymbol
            Symbol to move
        current_col : int
            Current column
        current_row : int
            Current row
        max_distance : int
            Maximum columns to move
        debug : bool
            Enable debug output
            
        Returns
        -------
        bool
            True if moved
        """
        # Find all sinks
        sinks = self.getAllInstanceSinks(sym)
        
        if not sinks:
            return False
        
        # Find closest sink column
        sink_cols = []
        for sink in sinks:
            sink_row, sink_col = self.getSymbolLocation(sink)
            if sink_col is not None and sink_col > current_col:
                sink_cols.append(sink_col)
        
        if not sink_cols:
            return False
        
        closest_sink_col = min(sink_cols)
        distance = closest_sink_col - current_col
        
        if distance <= 0:
            return False
        
        # Try to move towards the closest sink, up to max_distance
        target_col = min(current_col + min(distance - 1, max_distance), closest_sink_col - 1)
        
        if target_col <= current_col:
            return False
        
        # Find free row in target column
        free_row = self._findFreeRowInColumn(target_col, current_row, debug)
        
        if free_row is None:
            return False
        
        # Move the symbol
        self.symbol_matrix[current_row, current_col] = None
        self.symbol_matrix[free_row, target_col] = sym
        
        if debug:
            sym_name = sym.name if hasattr(sym, 'name') else str(type(sym).__name__)
            print(f"    Moved '{sym_name}' from ({current_row},{current_col}) to ({free_row},{target_col}) "
                  f"(distance to sink: {closest_sink_col - target_col})")
        
        return True
         
        
    def replaceVerticalCompress(self):
        raise Exception('non used')
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
        raise Exception('non used')
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
        raise Exception('non used')
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
        raise Exception('non used')
        raise Exception('This counts wires, not ports')

        wiresFromSource = [source['port'].wire for source in self.sources if source['symbol'] == sourceSym]
        wiresToSink = [sink['port'].wire for sink in self.sinks if sink['symbol'] == sinkSym]
        common = [wire for wire in wiresFromSource if wire in wiresToSink ]
        return len(common)

    def rowWiseReordering(self, max_iterations=5, debug=False):
        raise Exception('non used')
        """
        Reorder entire rows within the symbol_matrix to minimize edge crossings
        and reduce net overlaps. Works at row granularity to preserve passthrough
        entity placement.
        
        When nets cross (A: row1->row2, B: row2->row1), swapping rows can separate
        them, allowing different track assignments.
        
        Parameters
        ----------
        max_iterations : int
            Maximum iterations for convergence
        debug : bool
            Enable debug output
            
        Returns
        -------
        None
        """
        nr, nc = self.symbol_matrix.shape
        
        if nr <= 1:
            return
        
        total_crossings_before = self._countRowCrossings()
        
        if debug:
            print(f'Initial row crossings: {total_crossings_before}')
        
        for iteration in range(max_iterations):
            changed = False
            best_swap = None
            best_improvement = 0
            
            # Try swapping adjacent rows
            for r1 in range(nr - 1):
                r2 = r1 + 1
                
                # Swap rows in matrix
                self.symbol_matrix[[r1, r2]] = self.symbol_matrix[[r2, r1]]
                
                # Count crossings with this configuration
                crossings = self._countRowCrossings()
                improvement = total_crossings_before - crossings
                
                if improvement > best_improvement:
                    best_improvement = improvement
                    best_swap = (r1, r2)
                    total_crossings_before = crossings
                
                # Swap back
                self.symbol_matrix[[r1, r2]] = self.symbol_matrix[[r2, r1]]
            
            # Apply best swap if found
            if best_swap is not None:
                r1, r2 = best_swap
                self.symbol_matrix[[r1, r2]] = self.symbol_matrix[[r2, r1]]
                changed = True
                
                if debug:
                    print(f'Iteration {iteration + 1}: Swapped rows {r1}↔{r2}, '
                          f'crossings now: {total_crossings_before}')
            
            if not changed:
                if debug:
                    print(f'Converged after {iteration + 1} iterations')
                break
        
        total_crossings_after = self._countRowCrossings()
        if debug:
            print(f'Final row crossings: {total_crossings_after}')

    def _countRowCrossings(self):
        raise Exception('non used')
        """
        Count edge crossings between columns based on row positions.
        
        An edge crossing occurs when:
        - Net A goes from row_src_a to row_sink_a
        - Net B goes from row_src_b to row_sink_b
        - Same column range but crossing pattern: (src_a < src_b and sink_a > sink_b)
        
        Returns
        -------
        int
            Total number of crossing pairs
        """
        nr, nc = self.symbol_matrix.shape
        total_crossings = 0
        
        # For each column pair, count crossings
        for col_start in range(nc):
            for col_end in range(col_start + 1, nc):
                col_range = (col_start, col_end)
                crossings = self._countCrossingsInColumnRange(col_range, nr)
                total_crossings += crossings
        
        return total_crossings
    
    def _countCrossingsInColumnRange(self, col_range, nr):
        raise Exception('non used')
        """
        Count crossings between two columns.
        
        Parameters
        ----------
        col_range : tuple
            (col_start, col_end)
        nr : int
            Number of rows
            
        Returns
        -------
        int
            Number of crossing net pairs
        """
        col_start, col_end = col_range
        crossings = 0
        
        # Find all nets that span this column range
        nets_in_range = []
        for net in self.getNets():
            if hasattr(net, 'sourcecol') and hasattr(net, 'sinkcol'):
                net_col_start = min(net.sourcecol, net.sinkcol)
                net_col_end = max(net.sourcecol, net.sinkcol)
                
                if net_col_start == col_start and net_col_end == col_end:
                    src_row, _ = self.getSymbolLocation(net.source)
                    sink_row, _ = self.getSymbolLocation(net.sink)
                    
                    if src_row is not None and sink_row is not None:
                        nets_in_range.append({
                            'net': net,
                            'src_row': src_row,
                            'sink_row': sink_row
                        })
        
        # Count crossing pairs
        for i, net_a_info in enumerate(nets_in_range):
            for net_b_info in nets_in_range[i+1:]:
                src_a = net_a_info['src_row']
                sink_a = net_a_info['sink_row']
                src_b = net_b_info['src_row']
                sink_b = net_b_info['sink_row']
                
                # Check for crossing: one goes down, other goes up
                if (src_a < sink_a and src_b > sink_b) or \
                   (src_a > sink_a and src_b < sink_b):
                    # Only count if same source or sink side
                    if src_a == src_b or sink_a == sink_b:
                        crossings += 1
        
        return crossings
    
    
    def _calculateBarycenter(self, obj, col_idx):
        raise Exception('non used')
        """
        Calculate barycentric position of an object based on its connections
        to previous and next columns.
        
        Parameters
        ----------
        obj : LogicSymbol
            The object to calculate barycenter for
        col_idx : int
            Column index of the object
            
        Returns
        -------
        float
            Weighted barycenter position (average of connected node positions)
        """
        
        positions = []
        
        # Get connections from previous column (sources)
        if col_idx > 0:
            prev_col = self.columns[col_idx - 1]
            sources = self._getSourcesInColumn(obj, prev_col)
            for src in sources:
                if src in prev_col:
                    positions.append(prev_col.index(src))
        
        # Get connections to next column (sinks)
        if col_idx < len(self.columns) - 1:
            next_col = self.columns[col_idx + 1]
            sinks = self._getSinksInColumn(obj, next_col)
            for sink in sinks:
                if sink in next_col:
                    positions.append(next_col.index(sink))
        
        # Calculate barycenter
        if positions:
            return sum(positions) / len(positions)
        else:
            # No connections, maintain current position
            return self.columns[col_idx].index(obj) if obj in self.columns[col_idx] else 0
    
    def _getSourcesInColumn(self, obj, source_col):
        raise Exception('non used')
        """
        Get all objects in source_col that drive obj through nets.
        
        Parameters
        ----------
        obj : LogicSymbol
            Target object
        source_col : list
            List of symbols in source column
            
        Returns
        -------
        list
            Symbols in source_col that are sources to obj
        """
        sources = []
        
        for net in self.nets:
            if net.sink == obj and net.source in source_col:
                if net.source not in sources:
                    sources.append(net.source)
        
        return sources
    
    def _getSinksInColumn(self, obj, sink_col):
        raise Exception('non used')
        """
        Get all objects in sink_col that obj drives through nets.
        
        Parameters
        ----------
        obj : LogicSymbol
            Source object
        sink_col : list
            List of symbols in sink column
            
        Returns
        -------
        list
            Symbols in sink_col that are sinks to obj
        """
        sinks = []
        
        for net in self.nets:
            if net.source == obj and net.sink in sink_col:
                if net.sink not in sinks:
                    sinks.append(net.sink)
        
        return sinks
    
    def _countCrossingsInColumn(self, col_idx):
        raise Exception('non used')
        """
        Count edge crossings for nets passing through a column boundary.
        
        Parameters
        ----------
        col_idx : int
            Column index
            
        Returns
        -------
        int
            Number of crossing pairs
        """
        if col_idx >= len(self.columns) - 1:
            return 0
        
        current_col = self.columns[col_idx]
        next_col = self.columns[col_idx + 1]
        
        # Get all nets from current to next column
        nets_between = [n for n in self.nets 
                        if n.source in current_col and n.sink in next_col]
        
        crossings = 0
        
        # Count crossings: net A crosses net B if:
        # A.source < B.source AND A.sink > B.sink (or vice versa)
        for i, net_a in enumerate(nets_between):
            for net_b in nets_between[i+1:]:
                src_a_pos = current_col.index(net_a.source)
                src_b_pos = current_col.index(net_b.source)
                sink_a_pos = next_col.index(net_a.sink)
                sink_b_pos = next_col.index(net_b.sink)
                
                # Check if they cross
                if (src_a_pos < src_b_pos and sink_a_pos > sink_b_pos) or \
                   (src_a_pos > src_b_pos and sink_a_pos < sink_b_pos):
                    crossings += 1
        
        return crossings
    
    def _countColumnCrossings(self):
        raise Exception('non used')
        """
        Count total edge crossings across all column boundaries.
        
        Returns
        -------
        int
            Total number of crossings
        """
        total = 0
        for col_idx in range(len(self.columns) - 1):
            total += self._countCrossingsInColumn(col_idx)
        return total
    
    def _rebuildObjsFromColumns(self):
        raise Exception('non used')
        """
        Rebuild the self.objs list from self.columns to reflect reordering.
        
        This maintains the structure of self.objs while updating the order
        based on column assignments.
        
        Returns
        -------
        None
        """
        new_objs = []
        for col in self.columns:
            new_objs.extend(col)
        
        self.objs = new_objs
        
        # Update indices for numInputs and firstOutput
        # These should remain pointing to the same logical positions
        self.numInputs = len(self.columns[0]) if self.columns else 0
        
        # Find where output columns start
        output_col_start = len(self.columns) - 1
        self.firstOutput = sum(len(self.columns[i]) for i in range(output_col_start))
    
    def placeInputPorts(self):
        """
        Place the input ports of the module. We just place them using the grid

        Returns
        -------
        None.

        """
        nr, nc = self.symbol_matrix.shape

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
        # finds a source symbol that contains thw wire
        for source in self.sources:
            if (source['port'].wire == sinkWire):
                return source
            
        sourceNames = [x['wire'].getFullPath() for x in self.sources]
        raise Exception('Could not find a source to wire "{}" in the sources collection {}'.format(sinkWire.getFullPath(), sourceNames ) )
            
    def findSinkTuples(self, sourceWire):
        raise Exception('non used')
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
        #oa = np.array(self.objs)
        #ba = np.array([isinstance(x, NetSymbol) for x in self.objs])
        #return list(oa[ba])
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
        raise Exception('non used')
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
        
    def computeAdjacencyMatrixCost(self):
        raise Exception('non used')
        am = self.getAdjacencyMatrix()
        cost = 0
        for y in range(am.shape[0]):
            for x in range(y):
                cost = cost + am[y, x]

        return cost
    
    def swap(self, a, b):
        raise Exception('non used')
        self.objs[a], self.objs[b] = self.objs[b], self.objs[a] 


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

    def isFreeRectangle(self, og, x0, y0, x1, y1):
        raise Exception('non used')
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
    
        
    def alignPassthroughSymbols(self):
        raise Exception('non used')
        """
        Align passthrough and feedback symbols that belong to the same net to the same row.
        
        For each net with multiple passthrough/feedback symbols:
        1. Find all related passthrough/feedback symbols across columns
        2. Move them all to the same row
        3. Move other symbols in affected rows to avoid collisions
        
        Returns
        -------
        None.
        """
        nets = self.getNets()
        
        # Group nets by wire to find chains of passthroughs
        wire_nets = {}
        for net in nets:
            if net.wire not in wire_nets:
                wire_nets[net.wire] = []
            wire_nets[net.wire].append(net)
        
        # For each wire, align all related passthrough/feedback symbols
        for wire, net_list in wire_nets.items():
            passthrough_symbols = []
            feedback_symbols = []
            all_special = []
            
            for net in net_list:
                if isinstance(net.source, PassthroughSymbol):
                    passthrough_symbols.append(net.source)
                if isinstance(net.sink, PassthroughSymbol):
                    passthrough_symbols.append(net.sink)
                if isinstance(net.source, FeedbackStartSymbol):
                    feedback_symbols.append(net.source)
                if isinstance(net.sink, FeedbackStartSymbol):
                    feedback_symbols.append(net.sink)
                if isinstance(net.source, FeedbackStopSymbol):
                    feedback_symbols.append(net.source)
                if isinstance(net.sink, FeedbackStopSymbol):
                    feedback_symbols.append(net.sink)
            
            # Remove duplicates
            passthrough_symbols = list(set(passthrough_symbols))
            feedback_symbols = list(set(feedback_symbols))
            all_special = passthrough_symbols + feedback_symbols
            
            # Skip if only one or none
            if len(all_special) <= 1:
                continue
            
            # Find reference row from non-special symbols connected to this wire
            reference_row = None
            
            for net in net_list:
                if not isinstance(net.source, (PassthroughSymbol, FeedbackStartSymbol, FeedbackStopSymbol)):
                    if net.source in self.symbol_to_row:
                        reference_row = self.symbol_to_row[net.source]
                        break
                if not isinstance(net.sink, (PassthroughSymbol, FeedbackStartSymbol, FeedbackStopSymbol)):
                    if net.sink in self.symbol_to_row:
                        reference_row = self.symbol_to_row[net.sink]
                        break
            
            # If no reference row, use the first symbol's current row
            if reference_row is None:
                reference_row = self.symbol_to_row.get(all_special[0], 0)
            
            # Find a suitable target row for all special symbols
            target_row = self._findFreeRow(reference_row, all_special)
            
            # Move all special symbols to target row
            self._moveSymbolsToRow(all_special, target_row)
    
    
    def _findFreeRow(self, reference_row, symbols_to_place):
        raise Exception('non used')
        """
        Find a row where all given symbols can be placed without colliding with instances.
        
        Parameters
        ----------
        reference_row : int
            Preferred row based on connected symbols
        symbols_to_place : list
            Symbols to be placed in the row
            
        Returns
        -------
        int
            Row index suitable for placement
        """
        # Get the columns these symbols will occupy
        cols_to_use = set(sym.col_idx for sym in symbols_to_place if hasattr(sym, 'col_idx'))
        
        # Check if reference_row is free in all required columns
        if self._isRowFreeInColumns(reference_row, cols_to_use, symbols_to_place):
            return reference_row
        
        # Search for alternative rows
        for offset in range(1, len(self.rows) + 10):
            # Try above reference
            test_row = reference_row - offset
            if test_row >= 0 and self._isRowFreeInColumns(test_row, cols_to_use, symbols_to_place):
                return test_row
            
            # Try below reference
            test_row = reference_row + offset
            if self._isRowFreeInColumns(test_row, cols_to_use, symbols_to_place):
                return test_row
        
        # If no free row found, return reference
        return reference_row
    
    
    def _isRowFreeInColumns(self, row_idx, column_indices, symbols_to_place):
        raise Exception('non used')
        """
        Check if a row is free from instance collisions in specified columns.
        
        Parameters
        ----------
        row_idx : int
            Row to check
        column_indices : set
            Column indices to check
        symbols_to_place : list
            Symbols being placed (don't count these as collisions)
            
        Returns
        -------
        bool
            True if row is free for placement
        """
        if row_idx >= len(self.rows):
            return True
        
        symbols_in_row = self.rows[row_idx]
        
        for sym in symbols_in_row:
            # Skip symbols being placed or special symbols
            if sym in symbols_to_place:
                continue
            if isinstance(sym, (PassthroughSymbol, FeedbackStartSymbol, FeedbackStopSymbol)):
                continue
            
            # Check if this instance is in one of the columns we care about
            if hasattr(sym, 'col_idx') and sym.col_idx in column_indices:
                # Instance blocks this row
                return False
        
        return True
    
    
    def _moveSymbolsToRow(self, symbols, target_row):
        raise Exception('non used')
        """
        Move symbols to a target row, removing them from their current rows.
        
        Parameters
        ----------
        symbols : list
            Symbols to move
        target_row : int
            Target row index
            
        Returns
        -------
        None
        """
        # Remove symbols from their current rows
        for sym in symbols:
            current_row = self.symbol_to_row.get(sym)
            if current_row is not None and current_row < len(self.rows):
                if sym in self.rows[current_row]:
                    self.rows[current_row].remove(sym)
        
        # Ensure target row exists
        while len(self.rows) <= target_row:
            self.rows.append([])
        
        # Add symbols to target row
        for sym in symbols:
            if sym not in self.rows[target_row]:
                self.rows[target_row].append(sym)
            sym.row_idx = target_row
            self.symbol_to_row[sym] = target_row
    
    
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
