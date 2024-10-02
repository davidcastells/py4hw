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
        
        # wires contain all the elements of the input list, there might be repeatitions
        self.wires = wires if isinstance(wires, list) else [wires]
        self.format = []
        self.data = {}  # this is a dictionary of obj (wire or port) -> data, list of wire values 

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
            else:
                raise Exception('Unsupported object class to watch: {}'.format(type(x)))
                

            if isinstance(x, FieldInspector):
               self.format.append(x.getFormat()) 
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
        
        
    def clock(self):
        # Data is indexed by wire (or field inspector) to avoid repeats
        # For ports, the value used for x will be its wire
        for x in self.uniqueWires:
            if isinstance(x, FieldInspector):
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
        
        signals = [{"name": "clk", 'wave': 'P'}]
        
        for idx, obj in enumerate(self.wires):
            if (isinstance(obj, FieldInspector)):
                w = obj
                ww = -1
            else:
                w = Waveform.getwire(obj)
                ww = w.getWidth()
                
            fmt = self.format[idx]
            wavedata = 'x'
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
                    
            wavedata += 'x'
            
            if (shortNames):
                name = obj.name
            else:
                name = obj.getFullPath()
                
            signals.append({'name': name, 'wave':wavedata, 'data':wavedatadata})

        wavedata = 'P'
        for i in range(numclks):
            wavedata += '.'
        wavedata += 'x'

        signals[0]['wave'] = wavedata
        
        ret = {
            "signal": signals,
            "head": {
                "text": self.name,
                "tock": 0,
            }
        }
        
        return ret
    
    def gui(self, root=None, shortNames=False):
        
        window = WaveformWindow(root, self, shortNames)

class WaveformWindow:
    
    def __init__(self, root, wvf, shortNames):
        from py4hw.gui import getResourceIcon 
        if (root is None):
            self.root = tkinter.Tk()
        else:
            self.root = root

        self.waveform = wvf
        self.shortNames = shortNames
            
        self.root.title('Waveform viewer ' + wvf.name)
        
        font = tkinter.font.Font(size=9)
        
        style = ttk.Style()
        style.configure("Treeview", fg="light yellow")
        style.configure("Treeview", rowheight=23) 
        style.configure("Prolepsis.Treeview", font=font)
        
        self.topPane = PanedWindow(self.root, orient=VERTICAL)

        self.toolbar= Frame(self.topPane, bd=1, relief=RAISED)
        
        icon_zo = getResourceIcon('zoomout24.png')
        icon_zi = getResourceIcon('zoomin24.png')
        
        zoomInButton = ttk.Button(self.toolbar,  image=icon_zi, text="Zoom in", command=self.zoomIn)
        zoomOutButton = ttk.Button(self.toolbar, image=icon_zo, text="Zoom out", command=self.zoomOut)

        zoomInButton.pack(side=tkinter.LEFT)
        zoomOutButton.pack(side=tkinter.LEFT)

        self.topPane.add(self.toolbar)

        self.mainPane = PanedWindow(self.topPane, orient=HORIZONTAL)
        self.topPane.add(self.mainPane)
        
        self.hierarchyFrame = Frame(self.mainPane) # PanedWindow(self.mainPane, relief = SUNKEN, width=50, height=100)
        #self.hierarchyPane.pack()
        

        self.hierarchyTree()

        self.mainPane.add(self.hierarchyFrame)

        self.linesPane = PanedWindow(self.mainPane, relief = SUNKEN, width=100, height=100)
        self.mainPane.add(self.linesPane)

        self.hclock = 20
        self.hw = self.hclock * self.getNumClocks()
        
        self.canvas = Canvas(self.linesPane, bg='white', scrollregion=(0,0, self.hw,1000))
        #self.canvas.configure(yscrollcommand=self.scroll.set)
        self.canvas.configure(yscrollincrement='20')
        
        self.h_scroll = ttk.Scrollbar(self.linesPane, orient=HORIZONTAL, command=self.canvas.xview)
        self.v_scroll = ttk.Scrollbar(self.linesPane, orient=VERTICAL, command=self.sync_scrolls)
        self.canvas.configure(xscrollcommand=self.h_scroll.set, yscrollcommand=self.v_scroll.set)

        
        self.linesPane.add(self.canvas)
        self.h_scroll.pack(side=tkinter.BOTTOM, fill=X)
        self.v_scroll.pack(side=tkinter.RIGHT, fill=Y)

        self.drawWaveforms()

        self.topPane.pack(fill=BOTH, expand=True)

        self.root.mainloop()
        
        self.foreground = 'black'
        

    def zoomIn(self):
        self.hclock *= 1.1
        self.hw = self.hclock * self.getNumClocks()

        self.canvas.config(scrollregion=(0, 0, self.hw, 1000))
        self.redraw()
    
    def zoomOut(self):
        self.hclock /= 1.1
        self.hw = self.hclock * self.getNumClocks()

        self.canvas.config(scrollregion=(0, 0, self.hw, 1000))
        self.redraw()
    
    def sync_scrolls(self, *args):
        self.hierarchyTree.yview(*args)
        self.v_scroll.set(*args)
        self.canvas.yview_moveto(args[0])
    
    def yview(self, *args):
        print(*args)
        self.hierarchyTree.yview(*args)
        self.canvas.yview(*args)
        
    def hierarchyTree(self):
    
        tree_scroll = Scrollbar(self.hierarchyFrame)
        tree_scroll.pack(side=RIGHT, fill=Y)

        self.scroll = tree_scroll 
        
        self.hierarchyTree = ttk.Treeview(self.hierarchyFrame, yscrollcommand=tree_scroll.set)
        tv = self.hierarchyTree  
        
        tree_scroll.config(command=self.yview)
        
        self.map_id_obj = {}
    
        #tv.bind('<<TreeviewSelect>>', self.callback)
        
        #self.hierarchyPane.add(tv)        
        #self.hierarchyPane.pack(fill=BOTH, expand=YES)
        tv.pack(side=LEFT, fill=BOTH, expand=YES)
        
        wd = self.waveform.getDict()
        
        for wav in wd.keys():
            if (self.shortNames):
                name = wav.name
            else:
                name = wav.getFullPath()

            dc_iid = tv.insert("", tkinter.END, text=name, open=True)
        
        # self.map_id_obj[dc_iid] = self.sys
    
        # self.populateTree(tv, dc_iid, self.sys)
        
        # print(tv.cget("displaycolumns"))
        #tv.config(columns=[ 'instance', 'type'])
        #tv.config(displaycolumns=[ 0, 1])
        #tv.heading('instance', text='Instance name')
        #tv.heading("type", text="Type")
        tv.heading("#0", text="Name")
        tv.config(selectmode=tkinter.BROWSE)
        tv.tag_configure("ally", background="green")
        #tv.tag_bind("char", "<Double-Button-1>", event)
        
        #tv.config(style="Prolepsis.Treeview")
        tv["style"] = "Prolepsis.Treeview"
        #tv.config(bg="light yellow")
        print(ttk.Style().lookup("Prolepsis.Treeview", "background"))

    def redraw(self):
        self.canvas.delete('all')
        self.drawWaveforms()
        self.canvas.update()

    def getNumClocks(self):
        wd = self.waveform.getDict()
        return len(list(wd.values())[0])
    
    def drawWaveforms(self):
        off = 43
        vspace = 21
        wd = self.waveform.getDict()

        self.setColor('blue')
        
        hclock = self.hclock # this is the width of the clock (in pixels ?)
        vsig = 15
        vtext = 7
        htrans = 3
        
        for idx, obj in enumerate(self.waveform.wires):
            
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
                lastval = '?' # arbitrary value 
            
            for clk in range(len(data)):
                val = data[clk]
                if (ww == 1):
                    # binary wires
                    self.drawLine(clk*hclock, off + idx*vspace - val*vsig, 
                                  (clk+1)*hclock, off + idx*vspace - val*vsig)     
                    if not(lastval is None):
                        # draw the transition at the beginning
                        self.drawLine(clk*hclock, off + idx*vspace - lastval*vsig, 
                                  clk*hclock, off + idx*vspace - val*vsig)     
                    lastval = val 
                else:
                    # non binary wires

                    if not(lastval is None) and (lastval != val):
                        # draw the transition at the beginning
                        self.drawLine(clk*hclock - htrans, off + idx*vspace - vsig, 
                                  clk*hclock + htrans, off + idx*vspace )     
                        self.drawLine(clk*hclock - htrans, off + idx*vspace , 
                                  clk*hclock + htrans, off + idx*vspace - vsig)     
                        self.drawLine(clk*hclock + htrans, off + idx*vspace - vsig, 
                                  (clk+1)*hclock - htrans, off + idx*vspace - vsig)     
                        self.drawLine(clk*hclock + htrans, off + idx*vspace , 
                                  (clk+1)*hclock - htrans, off + idx*vspace )     

                        self.drawText(clk*hclock + htrans, off + idx*vspace - vtext, fmt.format(val), 'w')
                    else:
                        self.drawLine(clk*hclock - htrans, off + idx*vspace - vsig, 
                                  (clk+1)*hclock - htrans, off + idx*vspace - vsig)     
                        self.drawLine(clk*hclock - htrans, off + idx*vspace , 
                                  (clk+1)*hclock - htrans, off + idx*vspace )
                    lastval = val 
        
    def setColor(self, color):
        self.foreground = color
        
    def drawLine(self, x0, y0, x1, y1):
        self.canvas.create_line(x0, y0, x1, y1, fill=self.foreground)

    def drawText(self, x, y, text, anchor):
        if (anchor == 'w'):
            ha = 'left'
        elif (anchor == 'e'):
            ha = 'right'
        elif (anchor == 'c'):
            ha = 'center'
            
        self.canvas.create_text(x,y, anchor=anchor, text=text)
        
@deprecated # use Waveform, just maintened for reference
class OldWaveform(Logic):

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
        self.waves = {}  # A dictionary keyed by fullname , wavem and data
        self.prevs = {}
        self.ck = {"name": "CK", "wave": "P"}

        self.wires = wires # if isinstance(wires, list) else [wires]
        for x in self.wires:
            if (isinstance(x, Wire)):
                self.addIn(x.name, x)
                self.waves[x] = {"name": x.getFullPath(), "wave": "x", "data": []}
                self.prevs[x] = None
            else:
                raise Exception('We only support wires by now')
                
        # Get simulator
        self.sim = parent
        while self.sim.parent != None:
            self.sim = self.sim.parent

        self.sim.getSimulator().addListener(self)

    def simulatorUpdated(self):
        for x in self.wires:
            if self.prevs[x] == x.get():
                self.waves[x]["wave"] += "."
            elif x.getWidth() == 1:
                self.waves[x]["wave"] += str(x.get())
            else:
                self.waves[x]["wave"] += "2"
                self.waves[x]["data"].append(hex(x.get()))

            self.prevs[x] = x.get()

        self.ck["wave"] += "."

    def get_waveform(self, with_ck=True):
        signals = list(self.waves.values())
        for x in signals:
            x["wave"] += "x"

        if with_ck:
            ck = self.ck.copy()
            ck["wave"] += "x"
            signals.insert(0, ck)

        waveform = {
            "signal": signals,
            "head": {
                "text": self.name,
                "tock": 0,
            }
        }

        return waveform
    
    def draw(self):
        import nbwavedrom as wave
        return wave.draw(self.get_waveform())
    

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
    """
    A sequence of value
    """

    def __init__(self, parent: Logic, name: str, values: list(), r: Wire):
        super().__init__(parent, name)
        self.r = self.addOut("r", r)

        self.values = values
        self.n = len(values)
        self.i = 0
        
    def clock(self):
        self.r.prepare(self.values[self.i])
        self.i = ( self.i +1 ) % self.n


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