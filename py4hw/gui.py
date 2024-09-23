import tkinter 
import tkinter.font
from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
import os
from .base import Logic
from .schematic import Schematic
    
import sys
import importlib

        
def get_package_path(package_name):
    if sys.version_info >= (3, 9):
        import importlib.resources as resources
        return resources.files(package_name)
    else:
        import importlib_resources as resources
        return resources.path(package_name, '')

def get_resource_path(package_name, resource_name):
    if sys.version_info >= (3, 9):
        import importlib.resources as resources
        package_path = resources.files(package_name)
        return package_path / resource_name
    else:
        import importlib.resources as resources
        with resources.path(package_name, resource_name) as resource_path:
            return resource_path
    
def getIcon(path):
    #script_directory = os.path.dirname(os.path.abspath(__file__))
    #icon_path = os.path.join(script_directory, path)
    
    icon = Image.open(path)
    icon = ImageTk.PhotoImage(icon)
    return icon

def getResourceIcon(name):
    path = get_resource_path('py4hw' , name)

    return getIcon(path)


class Workbench():
    
    
        
    def __init__(self, sys:Logic):
    
        self.sys = sys
        self.detailObj = None
        
        root = tkinter.Tk()
        root.title('py4hw Interactive Workbench')
        
        self.root = root
        
        ttk.Style().configure("Treeview", fg="light yellow")
        font = tkinter.font.Font(size=8)
        ttk.Style().configure("Prolepsis.Treeview", font=font)
        
        self.topPane = PanedWindow(root, orient=HORIZONTAL)
        
        self.hierarchyPane = Frame(self.topPane) # PanedWindow(self.topPane, relief = SUNKEN, width=50, height=100)
        self.topPane.add(self.hierarchyPane)
        
        self.buttonPane = Frame(self.hierarchyPane) #, relief = SUNKEN, width=100, height=100)
        
        self.txtClocks = tkinter.StringVar(value='1')
        #print(ttk.Style().lookup("Prolepsis.Treeview", "font"))
        txtClocks = ttk.Entry(self.buttonPane, width=10, textvariable=self.txtClocks)
        #txtClocks.grid(row=0, column=0)
        txtClocks.pack(side=tkinter.LEFT, padx=10, pady=(10,5))
        
        btnClock = ttk.Button(self.buttonPane, text="Clock", command=self.guiClk)
        btnClock.pack(side=tkinter.RIGHT, padx=(10,0), pady=(10,5))
        #btnClock.grid(row=0, column=1)
        
        #self.hierarchyPane.add(self.buttonPane)
        
        self.buttonPane.pack(side=tkinter.TOP)
        
        self.createHierarchyTree()
        
        self.rightPane = PanedWindow(self.topPane, orient=VERTICAL, relief = SUNKEN, width=100, height=100)
        self.topPane.add(self.rightPane)
        
        self.interfacePane = PanedWindow(self.rightPane, relief = SUNKEN, width=100, height=100)
        
        self.schematicAreaPane = PanedWindow(self.rightPane,  orient=VERTICAL, relief = SUNKEN, width=100, heigh=20)
        self.schematicToolbarPane = Frame(self.schematicAreaPane) #,  orient=HORIZONTAL, relief = SUNKEN, width=100, heigh=20)
                
        self.rightPane.add(self.interfacePane)
        self.rightPane.add(self.schematicAreaPane)
        self.schematicAreaPane.add(self.schematicToolbarPane) 
        
        
        # Construct the full path to the image file
        
        icon_zo = getResourceIcon('zoomout24.png')
        icon_zi = getResourceIcon('zoomin24.png')
        
        btnZoomIn = ttk.Button(self.schematicToolbarPane,  image=icon_zi, text="Zoom in", command=self.guiZoomIn)
        btnZoomOut = ttk.Button(self.schematicToolbarPane, image=icon_zo, text="Zoom out", command=self.guiZoomOut)
        
        btnZoomIn.pack(side=tkinter.LEFT)
        btnZoomOut.pack(side=tkinter.LEFT)
        
        self.schematicPane = PanedWindow(self.schematicAreaPane, relief = SUNKEN, width=100, height=100)
        self.schematicAreaPane.add(self.schematicPane)
        
        #pane2.pack(fill=BOTH, expand=YES, side=RIGHT)
        
        self.circuitDetail(None)
        
        self.topPane.pack(fill=BOTH, expand=True)
        
        # explicitelly update
        # sys.getSimulator().addListener(self)
        
        
        root.mainloop()
        
    def guiClk(self):
        clks = int(self.txtClocks.get())
        sim = self.sys.getSimulator()
        sim.clk(clks)
        #explicitelly update
        self.simulatorUpdated()

    def guiZoomOut(self):
        self.schematicDiagram.scale("all", 0, 0, 0.9, 0.9)

    def guiZoomIn(self):
        self.schematicDiagram.scale("all", 0, 0, 1.1, 1.1)

    
    def simulatorUpdated(self):
        """
        TODO: We do the dirty trick to recreate all the table to just
        update the circuit status. We will try to do better in the future

        Returns
        -------
        None.

        """
        if (self.detailObj != None):
            self.setCircuitDetail(self.detailObj)
        
    def circuitDetail(self, obj:Logic):

        # this is called just once now (?)        
        print('Circuit detail on ', obj)
        
        # Create the Circuit Interface pane
        # @todo we are creating this every time we focus on a circuit, could we
        # just create it once and clear the tree view and populate it as necessary ?
        self.detail_tv = ttk.Treeview(self.interfacePane)
        
        detail_tv = self.detail_tv
        self.interfacePane.add(detail_tv)
        
        detail_tv.pack(fill=BOTH, expand=YES)
        
        detail_tv.config(columns=[ 'direction', 'width', 'value'])
        detail_tv.config(displaycolumns=[ 0, 1,2])

        detail_tv.heading('#0', text='Name')
        detail_tv.heading('direction', text='Direction')
        detail_tv.heading('width', text='Width')
        detail_tv.heading("value", text="Value")
        
        detail_tv.column("#0",minwidth=0,width=100)
        detail_tv.column("#0",minwidth=0,width=100)
        detail_tv.column('direction', minwidth=0,width=100)
        detail_tv.column('width', minwidth=0,width=100)
        detail_tv.column("value", minwidth=0,width=100)
        
        detail_tv.config(selectmode=tkinter.NONE)
        detail_tv.tag_configure("ally", background="green")
        #detail_tv.tag_bind("char", "<Double-Button-1>", event)
        #tv.config(style="Prolepsis.Treeview")
        detail_tv["style"] = "Prolepsis.Treeview"

        #self.debugTkinterHierarchy(self.root, 0)
        
        if (obj == None):
            return
        
        self.setCircuitDetail(obj)
        
        
    def debugTkinterHierarchy(self, obj, ii):
        indent = '|' * ii + '+'
        print('[INFO] {} tkinter obj {} {}'.format(indent, type(obj), obj._name if (hasattr(obj, '_name')) else ''));
        
        try:
            for child in obj.children.values():
                self.debugTkinterHierarchy(child, ii+1)
        except:
            pass
                
    def setCircuitDetail(self, obj:Logic):
        
        if (obj != None):
            for pane in self.schematicPane.panes():
                self.schematicPane.forget(pane)
                
            if (obj.isStructural()):
                # ignore non structural circuits
                sch = Schematic(obj, render='tkinter', parent=self.schematicPane, showValues=True)
    
                sch.drawAll()
                self.schematicDiagram = sch.canvas.canvas
                self.schematicPane.add(self.schematicDiagram)
                #self.schematicPane.pack()
            elif (hasattr(obj, 'tkinter_gui')):
                sch = obj.tkinter_gui(self.schematicPane)
                self.schematicPane.add(sch)
            
        self.detailObj = obj
        self.detail_tv.delete(*self.detail_tv.get_children())
        
        detail_tv = self.detail_tv
        
        visitedPorts = []
        for source in obj.sources:
            sWidth = ''
            sValue = ''
            in_id = detail_tv.insert("", tkinter.END, text=source.name, values=[sWidth, sValue], open=True)
            
            for inp in source.ports:
                sWidth = inp.wire.getWidth()
                sValue = hex(inp.wire.get())
                port_id = detail_tv.insert(in_id, tkinter.END, text=inp.name, values=['in', sWidth, sValue], open=True)
                visitedPorts.append(inp)
        
        for sink in obj.sinks:
            sWidth = ''
            sValue = ''
            in_id = detail_tv.insert("", tkinter.END, text=sink.name, values=[sWidth, sValue], open=True)
        
            for inp in sink.ports:
                sWidth = inp.wire.getWidth()
                sValue = hex(inp.wire.get())
                port_id = detail_tv.insert(in_id, tkinter.END, text=inp.name, values=['out', sWidth, sValue], open=True)
                visitedPorts.append(inp)
            
        for inp in obj.inPorts:
            if (inp not in visitedPorts):
                sWidth = inp.wire.getWidth()
                sValue = hex(inp.wire.get())
                in_id = detail_tv.insert("", tkinter.END, text=inp.name, values=['in', sWidth, sValue], open=True)
        
        for outp in obj.outPorts:
            if (outp not in visitedPorts):
                sWidth = outp.wire.getWidth()
                sValue = hex(outp.wire.get())
                in_id = detail_tv.insert("", tkinter.END, text=outp.name, values=['out', sWidth, sValue], open=True)
           
        
        #tv.config(bg="light yellow")
        
    def callback(self, event):
        tvid = self.hierarchyTree.focus()
        obj = self.map_id_obj[tvid]
        # values = tv.item(tvid)['values']
        # objid =
        # obj = sys.getFromFullPath(values[2])
        #sys.getFromFullPath()
        self.setCircuitDetail(obj)
         
    
    def populateTree(self, tv, tvid, obj:Logic):
        for child in obj.children.values():
            instanceName = child.name
            circuitType = 'Structural'
            if (child.isClockable()):
                circuitType = 'Clockable'
            elif (child.isPropagatable()):
                circuitType = 'Propagatable'
            childid = tv.insert(tvid, tkinter.END, text=type(child).__name__, values=[instanceName, circuitType, child.getFullPath()], tags=["ally","char"])
            self.map_id_obj[childid] = child
            self.populateTree(tv, childid, child)

    def createHierarchyTree(self):
        self.hierarchyTree = ttk.Treeview(self.hierarchyPane)
    
        tv = self.hierarchyTree  
        self.map_id_obj = {}
    
        
        tv.bind('<<TreeviewSelect>>', self.callback)
        #self.hierarchyPane.add(tv)
        tv.pack(fill=BOTH, expand=YES)
        #tv.grid(row=1, column=0, columnspan=2, sticky='nsew')
        
        
        
        dc_iid = tv.insert("", tkinter.END, text="HWSystem", values=['Top', 'Top level'], open=True)
        
        self.map_id_obj[dc_iid] = self.sys
    
        self.populateTree(tv, dc_iid, self.sys)
        
        print(tv.cget("displaycolumns"))
        tv.config(columns=[ 'instance', 'type'])
        tv.config(displaycolumns=[ 0, 1])
        tv.heading('instance', text='Instance name')
        tv.heading("type", text="Type")
        tv.heading("#0", text="Name")
        tv.config(selectmode=tkinter.BROWSE)
        #tv.tag_configure("ally", background="green")
        #tv.tag_bind("char", "<Double-Button-1>", event)
        
        #tv.config(style="Prolepsis.Treeview")
        tv["style"] = "Prolepsis.Treeview"
        #tv.config(bg="light yellow")
        print(ttk.Style().lookup("Prolepsis.Treeview", "background"))
        
