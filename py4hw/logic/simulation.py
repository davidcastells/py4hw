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
    
class Waveform(Logic):
    def __init__(self, parent, name, wires):
        """
        

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
        self.wires = wires if isinstance(wires, list) else [wires]
        self.data = {}  # this is a dictionary of obj (wire or port) -> data, list of wire values 

        for x in self.wires:
            if isinstance(x, Wire):
                self.addIn(x.name, x)
            elif isinstance(x, InPort) or isinstance(x, OutPort):
                w = x.wire
                if (w is None):
                    raise Exception('Wire is null for port', x.getFullPath())
                self.addIn(w.name, w)
            else:
                raise Exception('Unsupported object class to watch ' + type(x))
                
            self.data[x] = []            

    @staticmethod
    def getwire(x):
        if isinstance(x, Wire):
            w = x
        elif isinstance(x, InPort) or isinstance(x, OutPort):
            w = x.wire
        else:
            raise Exception('Object is not wire {}'.format(x))
            
        return w
    
    def clock(self):
        for x in self.wires:
            w = Waveform.getwire(x)
                
            self.data[x].append(w.get())
            
    def getDict(self):
        return self.data

    def draw(self):
        import matplotlib.pyplot as plt
        fig, axs = plt.subplots(len(self.data.keys())+1, sharex=True)
        
        
        numclocks = len(self.data[self.wires[0]])
        clock = 1 - np.arange(numclocks*2) % 2
        tclock = 0.5 * np.arange(numclocks*2)
        t =  np.arange(numclocks)
        
        axs[0].step(tclock, clock, 'r', linewidth = 2, where='post')
        axs[0].set_ylabel('clock', rotation=0)
        
        for idx, x in enumerate(self.wires):
           axs[idx+1].step(t, self.data[x], linewidth=2, where='post')
           axs[idx+1].set_ylabel(x.name, rotation=0)
        
        return fig, axs
    
    def draw_wavedrom(self):
        import nbwavedrom as wave
        return wave.draw(self.get_wavedrom())
    
    def get_wavedrom(self):
        signals = [{"name": "clk", 'wave': 'P'}]
        
        for obj in self.wires:
            w = Waveform.getwire(obj)
            wavedata = 'x'
            
            data = self.data[obj]
            last = 'x'
            numclks = len(data)
            for i in range(numclks):
                v = data[i]
                if (v != last):
                    wavedata += '{}'.format(v)
                else:
                    wavedata += '.'
                last = v
                    
            wavedata += 'x'
            signals.append({'name': obj.getFullPath(), 'wave':wavedata})

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
    
    def gui(self, root=None):
        
        window = WaveformWindow(root, self)

class WaveformWindow:
    
    def __init__(self, root, wvf):
        if (root is None):
            self.root = tkinter.Tk()
        else:
            self.root = root

        self.waveform = wvf
            
        self.root.title('Waveform viewer ' + wvf.name)
        
        ttk.Style().configure("Treeview", fg="light yellow")
        font = tkinter.font.Font(size=8)
        ttk.Style().configure("Prolepsis.Treeview", font=font)

        self.topPane = PanedWindow(self.root, orient=VERTICAL)

        self.toolbar= Frame(self.topPane, bd=1, relief=RAISED)
        
        zoomInButton = Button(self.toolbar, text='zoomIn', relief=FLAT,  command=self.zoomIn)
        zoomInButton.pack(side=LEFT, padx=2, pady=2)
        zoomOutButton = Button(self.toolbar, text='zoomOut', relief=FLAT,  command=self.zoomOut)
        zoomOutButton.pack(side=LEFT, padx=2, pady=2)

        self.topPane.add(self.toolbar)

        self.mainPane = PanedWindow(self.topPane, orient=HORIZONTAL)
        self.topPane.add(self.mainPane)
        
        self.hierarchyFrame = Frame(self.mainPane) # PanedWindow(self.mainPane, relief = SUNKEN, width=50, height=100)
        #self.hierarchyPane.pack()
        

        self.hierarchyTree()

        self.mainPane.add(self.hierarchyFrame)

        self.linesPane = PanedWindow(self.mainPane, relief = SUNKEN, width=100, height=100)
        self.mainPane.add(self.linesPane)
        
        self.canvas = Canvas(self.linesPane, bg='white', scrollregion=(0,0,1000,1000))
        #self.canvas.configure(yscrollcommand=self.scroll.set)
        self.canvas.configure(yscrollincrement='20')
        
        self.linesPane.add(self.canvas)

        self.hclock = 20
        self.drawWaveforms()

        self.topPane.pack(fill=BOTH, expand=True)

        self.root.mainloop()
        
        self.foreground = 'black'
        

    def zoomIn(self):
        self.hclock *= 1.1
        self.redraw()
    
    def zoomOut(self):
        self.hclock /= 1.1
        self.redraw()
    
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
            dc_iid = tv.insert("", tkinter.END, text=wav.getFullPath(), open=True)
        
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

        
    def drawWaveforms(self):
        off = 45
        vspace = 20
        wd = self.waveform.getDict()

        self.setColor('blue')
        
        hclock = self.hclock
        vsig = 15
        vtext = 7
        htrans = 3
        
        for idx, wav in enumerate(wd.keys()):
            if isinstance(wav, py4hw.Wire):
                w = wav.getWidth()
            else:
                w = wav.wire.getWidth()
                
            data = wd[wav]
            
            if (w == 1):
                lastval = None
            else:
                lastval = '?' # arbitrary value 
            
            for clk in range(len(data)):
                val = data[clk]
                if (w == 1):
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
                        self.drawText(clk*hclock + htrans, off + idx*vspace - vtext, hex(val), 'w')
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
