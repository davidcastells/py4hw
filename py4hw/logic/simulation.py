# -*- coding: utf-8 -*-
"""
Created on Wed Jan 19 12:49:00 2022

@author: dcr
"""

from .. import *
from deprecated import deprecated


import numpy as np
import tkinter
import tkinter.font
from tkinter import *
from tkinter import ttk
import threading
    
class FieldInspector:
    def __init__(self, obj, field):
        self.obj = obj
        self.name = field
        
    def getFormat(self):
        return '{}'
    
    def get(self):
        return getattr(self.obj, self.name)
    
    def getFullPath(self):
        return self.obj.getFullPath() + '/' + self.name
    
# This is a class to provide custom visualization of values
class ValueFormatter:
    def __init__(self, x, fmt):
        self.x = x
        self.fmt = fmt

    def getFullPath(self):
        return self.x.getFullPath()
        
    def get(self):
        x = self.x.get()
        result = eval(f"f'{self.fmt}'")
        return result
        
class Waveform(Logic):
    def __init__(self, parent, name, wires):
        """
        Collects the progress of signals along the time.
        We try to reduce data by avoiding data duplication.

        Parameters
        ----------
        parent : TYPE
            DESCRIPTION.
        name : TYPE
            DESCRIPTION.
        wires : TYPE
            Can be a list of wires or a list of ports.

        Returns
        -------
        None.

        """
        super().__init__(parent, name)
        
        assert(len(wires) > 0)
            
        # wires contain all the elements of the input list, there might be repeatitions
        self.wires = wires if isinstance(wires, list) else [wires]
        self.format = []
        
        
        
        self.data = {}  
        # this is a dictionary of obj (wire or port) -> data, list of wire values 
        # so, repetitions in wires will be discarded

        self.uniqueWires = []
        
        for x in self.wires:

            if isinstance(x, Wire):
                w = x
                if not(x in self.uniqueWires):
                    self.addIn(x.name, x)
                    self.uniqueWires.append(x)
                    self.data[x] = []            
            elif isinstance(x, InPort) or isinstance(x, OutPort):
                w = x.wire
                if (w is None):
                    raise Exception('Wire is null for port', x.getFullPath())
                if not (w in self.uniqueWires):
                    self.addIn(w.name, w)
                    self.uniqueWires.append(w)
                    self.data[w] = []     
            elif isinstance(x, FieldInspector):
                w = None
                if not(x in self.uniqueWires):
                    self.uniqueWires.append(x)
                    self.data[x] = []
            elif isinstance(x, ValueFormatter):
                w = None
                if not(x in self.uniqueWires):
                    self.uniqueWires.append(x)
                    self.data[x] = []
            else:
                raise Exception('Unsupported object class to watch: {}'.format(type(x)))
                

            if isinstance(x, FieldInspector):
                self.format.append(x.getFormat()) 
            elif isinstance(x, ValueFormatter):
                self.format.append('{}')
            elif (w.getWidth() == 1):
                self.format.append('')
            else:
                self.format.append('{:X}')

    @staticmethod
    def getwire(x):
        if isinstance(x, Wire):
            w = x
        elif isinstance(x, InPort) or isinstance(x, OutPort):
            w = x.wire
        else:
            raise Exception('Object is not wire {}'.format(x))
            
        return w
    
    def clear(self):
        for key in self.data.keys():
            self.data[key] = []
        
        
    def monitor(self):
        # Data is indexed by wire (or field inspector) to avoid repeats
        # For ports, the value used for x will be its wire
        for x in self.uniqueWires:
            if isinstance(x, FieldInspector):
                self.data[x].append(x.get())
            elif isinstance(x, ValueFormatter):
                self.data[x].append(x.get())
            else:
                w = Waveform.getwire(x)
                
                if not(w in self.data):
                    raise Exception('Wire {}/{} not in data list {}'.format(x, w, self.data.keys()))
                    
                self.data[w].append(w.get())
            
    def getDict(self):
        return self.data

    def draw(self):
        import matplotlib.pyplot as plt
        fig, axs = plt.subplots(len(self.wires)+1, sharex=True)
        
        obj = self.wires[0]
        if (isinstance(obj, FieldInspector)):
            w = obj
            ww = -1
        else:
            w = Waveform.getwire(obj)
            ww = w.getWidth()
        
        
        numclocks = len(self.data[w])
        clock = 1 - np.arange(numclocks*2) % 2
        tclock = 0.5 * np.arange(numclocks*2)
        t =  np.arange(numclocks)
        
        axs[0].step(tclock, clock, 'r', linewidth = 2, where='post')
        axs[0].set_ylabel('clock', rotation=0)
        
        for idx, obj in enumerate(self.wires):
            w = Waveform.getwire(obj)

            axs[idx+1].step(t, self.data[w], linewidth=2, where='post')
            axs[idx+1].set_ylabel(w.name, rotation=0)
        
        return fig, axs
    

    
    def draw_wavedrom(self, shortNames=False):
        """
        

        Parameters
        ----------
        shortNames : bool, optional
            Indicates that the names of the wires should be short (instead of the full
            path). The default is False.

        Returns
        -------
        TYPE
            a widget.

        """
        import nbwavedrom as wave
        return wave.draw(self.get_wavedrom(shortNames))
    
    
    
    def get_wavedrom(self, shortNames=False):
        """
        

        Parameters
        ----------
        shortNames : TYPE, optional
            DESCRIPTION. The default is False.

        Returns
        -------
        ret : TYPE
            DESCRIPTION.

        """
        numclks = 0
        
        signals = [{"name": "clk", 'wave': 'P'}]
        
        for idx, obj in enumerate(self.wires):
            if (isinstance(obj, FieldInspector)):
                w = obj
                ww = -1
            elif (isinstance(obj, ValueFormatter)):
                w = obj
                ww = -1
            else:
                w = Waveform.getwire(obj)
                ww = w.getWidth()
                
            fmt = self.format[idx]
            wavedata = ''
            wavedatadata = []
            
            data = self.data[w]
            last = 'x'
            numclks = len(data)
            for i in range(numclks):
                v = data[i]
                if (v != last):
                    if (ww == 1):
                        wavedata += '{}'.format(v)
                    else:
                        wavedata += '{}'.format(2)
                        wavedatadata.append(fmt.format(v))
                else:
                    wavedata += '.'
                last = v
                    
            if (shortNames):
                name = obj.name
            else:
                name = obj.getFullPath()
                
            signals.append({'name': name, 'wave':wavedata, 'data':wavedatadata})

        wavedata = '0P'
        for i in range(numclks-2):
            wavedata += '.'
        

        signals[0]['wave'] = wavedata
        
        ret = {
            "signal": signals,
            "head": {
                "text": self.name,
                "tock": 0,
            }
        }
        
        return ret
    
    def gui(self, root=None, shortNames=False, detached=False):
        
        window = WaveformWindow(root, self, shortNames, blocking=not(detached))

from py4hw.gui import GuiManager                  


class WaveformWindow:

    def __init__(self, root, wvf, shortNames, blocking=False, manager=None):
        """
        root     : None (default) -> the window is created in the py4hw GUI thread through
                   the GuiManager, so all windows share one Tk root and one thread.
                   A Tk/Toplevel   -> used directly as the window; the caller must be on
                   the thread that runs its mainloop.
        blocking : only with root=None. True -> return when the window is closed
                   (other windows keep working).
        manager  : GuiManager to use; defaults to GuiManager.default().
        """
        self.waveform = wvf
        self.shortNames = shortNames
        self.foreground = 'black'

        # geometry shared by the tree (left) and the canvas (right)
        self.vspace = 21          # row height in pixels (must match Treeview rowheight)
        self.off = 18             # baseline of the clock row inside its 21 px row
        self.hclock = 20

        self.pollMs = 100          # how often the Tk thread checks for new simulation data
        self.followLatest = True   # keep the view at the right edge if it was already there
        self._dirty = False        # set by the simulator thread, consumed by the Tk thread
        self._closed = False
        self._closed_event = threading.Event()

        self.toplevel = None
        self.root = None

        # Register from the calling (simulation) thread, not from the GUI thread, so the
        # simulator's listener list is never modified from another thread while it may
        # be iterating it. The callback only sets a flag, so it is thread safe.
        self.waveform.getTop().getSimulator().addListener(self)

        try:
            if root is not None:
                self._create(root)
            else:
                mgr = manager if manager is not None else GuiManager.default()
                mgr.open_window(lambda r, m: self._create(tkinter.Toplevel(r)),
                                blocking=blocking)
        except BaseException:
            self._closed = True   # stop reacting to the simulator
            raise

    def _create(self, win):
        """Build the window contents into `win`. Must run in the GUI thread."""
        self.toplevel = win
        self.root = win
        self._build()
        return self               # exposes .toplevel, which GuiManager tracks

    def wait(self):
        """Block until the window is closed (useful at the end of a script)."""
        while not self._closed_event.wait(0.2):
            pass

    def _build(self):
        from py4hw.gui import getResourceIcon

        self.root.title('Waveform viewer ' + self.waveform.name)
        
        self.icon_win = getResourceIcon('waveform.png')
        if self.icon_win is not None:
            self.root.iconphoto(True, self.icon_win)

        self.treeFont = tkinter.font.Font(size=9)

        style = ttk.Style()
        style.configure("Treeview", fg="light yellow")
        style.configure("Treeview", rowheight=self.vspace)
        style.configure("Prolepsis.Treeview", font=self.treeFont)

        self.topPane = PanedWindow(self.root, orient=VERTICAL)

        # --- toolbar ---------------------------------------------------
        self.toolbar = Frame(self.topPane, bd=1, relief=RAISED)

        # keep references, otherwise Tk images get garbage collected
        self.icon_zo = getResourceIcon('zoomout24.png')
        self.icon_zi = getResourceIcon('zoomin24.png')

        zoomInButton = ttk.Button(self.toolbar, image=self.icon_zi, text="Zoom in", command=self.zoomIn)
        zoomOutButton = ttk.Button(self.toolbar, image=self.icon_zo, text="Zoom out", command=self.zoomOut)
        zoomInButton.pack(side=tkinter.LEFT)
        zoomOutButton.pack(side=tkinter.LEFT)

        self.topPane.add(self.toolbar)

        # --- main pane -------------------------------------------------
        self.mainPane = PanedWindow(self.topPane, orient=HORIZONTAL)
        self.topPane.add(self.mainPane)

        # left: names
        self.hierarchyFrame = Frame(self.mainPane)
        self.buildHierarchyTree()
        self.mainPane.add(self.hierarchyFrame, minsize=80)

        # right: waveforms
        self.linesFrame = Frame(self.mainPane)
        self.mainPane.add(self.linesFrame, stretch='always')

        self.canvas = Canvas(self.linesFrame, bg='white', width=400, height=100)
        self.canvas.configure(yscrollincrement=str(self.vspace))   # scroll in whole rows

        self.h_scroll = ttk.Scrollbar(self.linesFrame, orient=HORIZONTAL, command=self.canvas.xview)
        # the vertical scrollbar drives the tree; the tree then drives the canvas
        self.v_scroll = ttk.Scrollbar(self.linesFrame, orient=VERTICAL, command=self.tree.yview)
        self.canvas.configure(xscrollcommand=self.h_scroll.set)

        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.v_scroll.grid(row=0, column=1, sticky='ns')
        self.h_scroll.grid(row=1, column=0, sticky='ew')
        self.linesFrame.rowconfigure(0, weight=1)
        self.linesFrame.columnconfigure(0, weight=1)

        # mouse wheel on the canvas
        self.canvas.bind('<MouseWheel>', self._on_canvas_wheel)   # Windows / macOS
        self.canvas.bind('<Button-4>', self._on_canvas_wheel)     # Linux
        self.canvas.bind('<Button-5>', self._on_canvas_wheel)

        self._updateScrollRegion()
        self.drawWaveforms()

        self.topPane.pack(fill=BOTH, expand=True)

        # --- live updates ----------------------------------------------
        self.topPane.bind('<Destroy>', self._on_destroy)
        self.root.after(self.pollMs, self._poll)

    # ------------------------------------------------------------------
    # simulator listener
    # ------------------------------------------------------------------
    def simulatorUpdated(self, *args, **kwargs):
        """
        Called by the simulator, i.e. from the simulation thread.
        It must NOT touch any Tk object (Tk is not thread safe), so it only
        raises a flag; the Tk thread picks it up in _poll().
        """
        self._dirty = True

    __call__ = simulatorUpdated   # in case the simulator invokes listeners as callables

    def _poll(self):
        # runs in the Tk thread
        if self._closed:
            return
        if self._dirty:
            self._dirty = False
            self.refresh()
        self.root.after(self.pollMs, self._poll)

    def _on_destroy(self, event):
        if event.widget is self.topPane:
            self._closed = True
            self._closed_event.set()

    def refresh(self):
        """Redraw with the latest data, keeping the scroll position."""
        _, last = self.canvas.xview()
        atEnd = last >= 0.999
        self.redraw()
        if self.followLatest and atEnd:
            self.canvas.xview_moveto(1.0)

    def buildHierarchyTree(self):
        f = self.hierarchyFrame

        self.tree = ttk.Treeview(f, show='tree', selectmode=tkinter.BROWSE,
                                 yscrollcommand=self._on_tree_yscroll)
        tv = self.tree
        tv["style"] = "Prolepsis.Treeview"

        self.tree_hscroll = ttk.Scrollbar(f, orient=HORIZONTAL, command=tv.xview)
        tv.configure(xscrollcommand=self.tree_hscroll.set)

        tv.grid(row=0, column=0, sticky='nsew')
        self.tree_hscroll.grid(row=1, column=0, sticky='ew')
        f.rowconfigure(0, weight=1)
        f.columnconfigure(0, weight=1)

        # First row: the clock
        # @todo we should take the clock name from the clock driver of self.waveform
        names = ["clk"]
        for wav in self.waveform.wires:
            names.append(wav.name if self.shortNames else wav.getFullPath())

        for name in names:
            tv.insert("", tkinter.END, text=name, open=True)

        # The #0 column must not stretch, and must be as wide as the longest name,
        # otherwise the horizontal scrollbar has nothing to scroll.
        needed = max(self.treeFont.measure(n) for n in names) + 40   # indent + margins
        tv.column("#0", width=max(needed, 150), minwidth=needed, stretch=False)

    # ------------------------------------------------------------------
    # scrolling: the tree is the master, the canvas follows it
    # ------------------------------------------------------------------
    def _on_tree_yscroll(self, first, last):
        # called by the tree for ANY vertical scroll (wheel, keyboard, scrollbar...)
        self.v_scroll.set(first, last)
        self.canvas.yview_moveto(first)

    def _on_canvas_wheel(self, event):
        step = -3 if (event.num == 4 or event.delta > 0) else 3
        if event.state & 0x1:                       # shift -> horizontal
            self.canvas.xview_scroll(step, 'units')
        else:
            self.tree.yview_scroll(step, 'units')   # tree callback syncs the canvas
        return 'break'

    def _updateScrollRegion(self):
        # height == exactly the height of all tree rows, so both panes share the same scale
        numrows = len(self.waveform.wires) + 1
        self.hw = self.hclock * self.getNumClocks()
        self.canvas.config(scrollregion=(0, 0, self.hw, numrows * self.vspace))

    # ------------------------------------------------------------------
    # zoom / redraw
    # ------------------------------------------------------------------
    def zoomIn(self):
        self.hclock *= 1.1
        self.redraw()

    def zoomOut(self):
        self.hclock /= 1.1
        self.redraw()

    def redraw(self):
        self._updateScrollRegion()
        self.canvas.delete('all')
        self.drawWaveforms()
        self.canvas.update_idletasks()

    def getNumClocks(self):
        wd = self.waveform.getDict()
        return len(list(wd.values())[0])

    # ------------------------------------------------------------------
    # drawing
    # ------------------------------------------------------------------
    def drawWaveforms(self):
        off = self.off
        vspace = self.vspace
        wd = self.waveform.getDict()

        hclock = self.hclock  # width of a clock cycle in pixels
        vsig = 15
        vtext = 7
        htrans = 3

        numclocks = self.getNumClocks()
        numrows = len(self.waveform.wires) + 1  # +1 for the clock row

        # --- Background: thin vertical tick lines at each clock edge ---
        y_top = 0
        y_bottom = numrows * vspace

        self.setColor('#cccccc')
        for clk in range(numclocks + 1):
            x = clk * hclock
            self.canvas.create_line(x, y_top, x, y_bottom, fill=self.foreground, dash=(2, 2))

        self.setColor('blue')

        # Draw clock signal
        y_high = off - vsig
        y_low = off

        # first line shows rest state (no clock)
        self.drawLine(0, y_low, hclock, y_low)

        for clk in range(1, numclocks):
            x0 = clk * hclock
            xmid = clk * hclock + hclock / 2
            x1 = (clk + 1) * hclock

            # rising edge at the start of the cycle
            self.drawLine(x0, y_low, x0, y_high)
            self.drawArrow(x0, y_high)
            # high half (positive pulse)
            self.drawLine(x0, y_high, xmid, y_high)
            # falling edge at mid-cycle
            self.drawLine(xmid, y_high, xmid, y_low)
            # low half
            self.drawLine(xmid, y_low, x1, y_low)

        self.setColor('blue')

        for idx, obj in enumerate(self.waveform.wires):
            row = idx + 1

            if (isinstance(obj, FieldInspector)):
                w = obj
                ww = -1
            else:
                w = Waveform.getwire(obj)
                ww = w.getWidth()

            data = wd[w]
            fmt = self.waveform.format[idx]

            if (ww == 1):
                lastval = None
            else:
                lastval = '?'  # arbitrary value

            for clk in range(len(data)):
                val = data[clk]
                if (ww == 1):
                    # binary wires
                    self.drawLine(clk*hclock, off + row*vspace - val*vsig,
                                  (clk+1)*hclock, off + row*vspace - val*vsig)
                    if not(lastval is None):
                        # draw the transition at the beginning
                        self.drawLine(clk*hclock, off + row*vspace - lastval*vsig,
                                      clk*hclock, off + row*vspace - val*vsig)
                    lastval = val
                else:
                    # non binary wires
                    if not(lastval is None) and (lastval != val):
                        # draw the transition at the beginning
                        self.drawLine(clk*hclock - htrans, off + row*vspace - vsig,
                                      clk*hclock + htrans, off + row*vspace)
                        self.drawLine(clk*hclock - htrans, off + row*vspace,
                                      clk*hclock + htrans, off + row*vspace - vsig)
                        self.drawLine(clk*hclock + htrans, off + row*vspace - vsig,
                                      (clk+1)*hclock - htrans, off + row*vspace - vsig)
                        self.drawLine(clk*hclock + htrans, off + row*vspace,
                                      (clk+1)*hclock - htrans, off + row*vspace)

                        self.drawText(clk*hclock + htrans, off + row*vspace - vtext, fmt.format(val), 'w')
                    else:
                        self.drawLine(clk*hclock - htrans, off + row*vspace - vsig,
                                      (clk+1)*hclock - htrans, off + row*vspace - vsig)
                        self.drawLine(clk*hclock - htrans, off + row*vspace,
                                      (clk+1)*hclock - htrans, off + row*vspace)
                    lastval = val

    def setColor(self, color):
        self.foreground = color

    def drawLine(self, x0, y0, x1, y1):
        self.canvas.create_line(x0, y0, x1, y1, fill=self.foreground)

    def drawArrow(self, x, y, size=3):
        """
        Draws a small downward-pointing triangle whose tip sits at (x, y).
        Used to mark positive (rising) clock edges.
        """
        self.canvas.create_polygon(
            x - size, y + size * 1.5,
            x + size, y + size * 1.5,
            x, y,
            fill=self.foreground, outline=self.foreground)

    def drawText(self, x, y, text, anchor):
        self.canvas.create_text(x, y, anchor=anchor, text=text)


class Scope(Logic):

    def __init__(self, parent: Logic, name: str, wires):
        """
        Parameters
        ----------
        parent : Logic
            Parent circuit.
        name : str
            Name of the instance.
        wires
            Wire or list of wire to monitor.

        Returns
        -------
        None.
        """

        super().__init__(parent, name)
        self.wires = wires if isinstance(wires, list) else [wires]
        for x in self.wires:
            self.addIn(x.name, x)

        # Get simulator
        sim = parent
        while sim.parent != None:
            sim = sim.parent

        sim.getSimulator().addListener(self)

    def simulatorUpdated(self):
        head = f"Scope [{self.name}]:"
        print(head)

        for x in self.wires:
            print(f"{x.name}={x.get()}")

        print("-" * len(head))




class Sequence(Logic):
    def __init__(self, parent: Logic, name: str, values: list(), r: Wire, once=False):
        '''
        Creates a sequence object. It outputs a list of values after every clock cycle.

        Parameters
        ----------
        parent : Logic
            DESCRIPTION.
        name : str
            DESCRIPTION.
        values : list
            DESCRIPTION.
        r : Wire
            DESCRIPTION.
        once : TYPE, optional
            DESCRIPTION. The default is False.

        Returns
        -------
        None
        '''
        super().__init__(parent, name)
        self.r = self.addOut("r", r)

        self.values = values
        self.n = len(values)
        self.i = 0
        self.once = once
        
    def clock(self):
        self.r.prepare(self.values[self.i])
        
        if (self.once):
            if (self.i < (self.n - 1)):
                self.i += 1
        else:
            self.i = ( self.i +1 ) % self.n

class StreamCapture(Logic):
    def __init__(self, parent, name, x):
        super().__init__(parent, name)
        self.x = self.addIn('x', x)
        
        self.data = []
        
    def clock(self):
        self.data.append(self.x.get())

    def clear(self):
        self.data = []

class StreamCaptureSigned(Logic):
    def __init__(self, parent, name, x):
        super().__init__(parent, name)
        self.x = self.addIn('x', x)
        
        self.data = []
        
    def clock(self):
        import py4hw
        self.data.append(py4hw.IntegerHelper.c2_to_signed(self.x.get(), self.x.getWidth()))

    def clear(self):
        self.data = []   

class RandomUniform(Logic):
    def __init__(self, parent, name, r):
        super().__init__(parent, name)
        
        self.r = self.addOut('r', r)
                
        
    def clock(self):
        import random
        # low is inclusive, high is inclusive (+1 for randint/uniform range)
        # Automatically determine range based on bit-width

        v = int(random.randint(0, 1 << self.r.getWidth()))
        self.r.prepare(v)
        
        
class RandomValue(Logic):
    def __init__(self, parent, name, r, mean, stddev):
        super().__init__(parent, name)
        
        self.r = self.addOut('r', r)
        
        self.mean = mean
        self.stddev = stddev
        self.state = '{} <- {}+-{}'.format(self.r.get(), self.mean, self.stddev)
        
    def clock(self):
        import numpy as np
        v = int(np.random.normal(self.mean, self.stddev))
        self.r.prepare(v)
        self.state = '{} <- {}+-{}'.format(v, self.mean, self.stddev)
        
    def update_mean(self, v):
        self.mean = float(v)
        self.label1.config(text="Mean: {}".format(self.mean))
        
    def update_stddev(self, v):
        self.stddev = float(v)
        self.label2.config(text="Stddev: {}".format(self.stddev))
        
    def tkinter_gui(self, parent):
        from tkinter import ttk
        import tkinter as tk
        frame = ttk.Frame(parent, padding="10")
        frame.grid(column=2, row=2, sticky=(tk.W, tk.E, tk.N, tk.S))

        maxv = (2 ** self.r.getWidth()) -1
        
        print('maxv : ', maxv)
        
        # Create sliders and labels
        
        self.label1 = ttk.Label(frame, text="Mean: {}".format(self.mean))
        self.label2 = ttk.Label(frame, text="Stddev: {}".format(self.stddev))

        slider1 = ttk.Scale(frame, from_=0, to=maxv, orient="horizontal", command=self.update_mean)
        slider1.set(self.mean)
        slider2 = ttk.Scale(frame, from_=0, to=maxv, orient="horizontal", command=self.update_stddev)
        slider2.set(self.stddev)
        
        

        # Grid layout for sliders and labels
        slider1.grid(column=0, row=0,  pady=10)
        slider2.grid(column=0, row=1,  pady=10)
        self.label1.grid(column=1, row=0, padx=5)
        self.label2.grid(column=1, row=1, padx=5)
        
        # Configure column weights to make the sliders and labels expandable
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        
        return frame
