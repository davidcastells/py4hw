
        
class Logic:
    """
    Base class for all logic circuits
    """
    
    def __init__(self, parent, instanceName:str):
        self.parent = parent
        self.name = instanceName
        
        if (not(parent is None)):
            # Add this object as a parent's child
            if (instanceName in parent.children.keys()):
                raise Exception('there is already a child named {} in {}'.format(instanceName, parent.getFullPath() ))

            parent.children[instanceName] = self

        self.inPorts = []   # in ports are a sorted list
        self.outPorts = []  # out ports are a sorted list
        self.sources = []   # list of InterfaceSource objects
        self.sinks = []     # List of InterfaceSink objects
    
        self.children = {}          # children are keyed by name
        self.clockDriver = None     # every circuit has a clock driver, if None it is inherited from parent
        
    def addIn(self, name , wire):
        port = InPort(self, name, wire)
        self.inPorts.append(port)
        return wire;
    
    def getInPortByName(self, name):
        for port in self.inPorts:
            if (port.name == name):
                return port
        return None
        
    def reconnectIn(self, name, wire):
        # there is already a port with this name, but we just one to change the wire assigned
        port = self.getInPortByName(name)
        port.wire = wire
        
        
    def addOut(self, name, wire):
        port = OutPort(self, name, wire)
        self.outPorts.append(port)
        return wire;

    def addInterfaceSource(self, name:str, interface):
        """
        Adds the source ports of the interface to the 

        Parameters
        ----------
        Interface : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        ports = []
        for obj in interface.sourceToSink:
            wire = obj[1]
            portname = name + "_" +obj[0]
            port = OutPort(self, portname, wire)
            self.outPorts.append(port)
            ports.append(port)
        
        for obj in interface.sinkToSource:
            wire = obj[1]
            portname = name + "_" +obj[0]
            port = InPort(self, portname, wire)
            self.inPorts.append(port)
            ports.append(port)

        self.sources.append(InterfaceSource(name, ports))
            
        return interface;
            
    def addInterfaceSink(self, name:str, interface):
        """
        Adds the source ports of the interface to the 

        Parameters
        ----------
        Interface : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        ports = []
        for obj in interface.sourceToSink:
            wire = obj[1]
            portname = name + "_" +obj[0]
            port = InPort(self, portname, wire)
            self.inPorts.append(port)
            ports.append(port)
        for obj in interface.sinkToSource:
            wire = obj[1]
            portname = name + "_" +obj[0]
            port = OutPort(self, portname, wire)
            self.outPorts.append(port)
            ports.append(port)
            
        self.sinks.append(InterfaceSink(name, ports))
        
        return interface;
        
    def wire(self, name, width=1):
        return Wire(self, name, width);
    
    def wires(self, name:str, num:int, width:int):
        ret = []
        for i in range(num):
            ret.append(self.wire('{}_{}'.format(name,i), width))
        return ret;
    
    def allLeaves(self):
        acum = []
        if (len(self.children) > 0):
            for obj in self.children.values():
                acum = acum + obj.allLeaves()
        else:
            acum = acum + [self];
            
        return acum
    
    def isPropagatable(self):
        return has_method(self, "propagate")
        
    def isClockable(self):
        return has_method(self, "clock")
    
    
    # def getHierarchy(self):
    #     str = ''
        
    #     if (self.parent != None):
    #         str = self.parent.getHierarchy()

    #     str = str + '/' + type(self).__name__  
        
    #     return str;
    
    def isPrimitive(self):
        return self.isClockable() or self.isPropagatable();
    
    def isStructural(self):
        # structural circuits have children
        return (len(self.children.values()) > 0)
        
    def getFullPath(self, withselfnames=True)->str:
        """
        Gets the full of a hierarchy element

        Returns
        -------
        str
            DESCRIPTION.

        """
        str = ''
        
        if (self.parent != None):
            str = self.parent.getFullPath(withselfnames=withselfnames)
            
        str = str + '/' + type(self).__name__ 
        if (withselfnames):
            str += '[' + self.name + ']' 
        
        return str

    
    def getFromFullPath(self, path:str):
        """
        Gets a Logic from the full path

        Parameters
        ----------
        path : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        pos0 = path.find('/', 0)
        pos1 = path.find('/', pos0+1)
        
        if (pos1 >=0):
            currentname = path[pos0+1:pos1]
        else:
            currentname = path[pos0+1:]
            
            
        pos2 = path.find('/', pos1+1)
        
        if (pos2 >=0):
            childname = path[pos1+1:pos2]
        else:
            childname = path[pos1+1:]
            
        parts = childname.split('[')
        childType = parts[0]
        parts2 = parts[1].split(']')
        childInstance = parts2[0]
        
        for child in self.children:
            if  ( type(child).__name__ == childType and child.name == childInstance):
                objFound = child
        
        if (pos2 >= 0):
            return objFound.getFromFullPath( path[pos1:])
        else:
            return objFound;
        
class Wire:
    """
    Wires in py4hw connect one source with one (or more) sinks
    """
    
    # this is the list of prepared wires, 
    prepared = []
    
    def __init__(self, parent, name : str, width: int = 1 ):
        self.parent = parent
        self.name = name
        self.width = width
        self.value = 0 # should be None      # reset state
        self.sinks = []
        self.source = None
        
    def getFullPath(self)->str:
        return self.parent.getFullPath() + '[{}]'.format(self.name)
    
    def getWidth(self) -> int:
        return self.width
    
    def put(self, val:int):
        mask = (1<<self.width) -1
        self.value = val & mask

    def prepare(self, val:int):
        mask = (1<<self.width) -1
        self.next = val & mask
        Wire.prepared.append(self)
        
    def settle(self):
        self.value = self.next
        
    def get(self) -> int:
        return self.value
    
    def setSource(self, source):
        if (self.source != None):
            raise Exception('Source already connected to ' + self.source.parent.getFullPath())

        self.source = source
        
        
    def getSource(self):
        """
        Returns the OutPort that drives this wire

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        return self.source
    
    def addSink(self, sink):
        """
        Adds a sink to the wire

        Parameters
        ----------
        sink : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        self.sinks.append(sink)
        
    def getSinks(self):
        """
        Gets all the sinks from a wire

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        return self.sinks;
    

    def settleAll():
        """
        Settles all pending wires that were changed by clock methods

        Returns
        -------
        None.

        """
        for w in Wire.prepared:
            w.settle()
            
        # empty list
        Wire.prepared = []
    
    

class InPort:
    """
    An Input port
    """
    
    def __init__(self, parent:Logic, name, wire:Wire):
        """
        Creates an in port to the cell.
        The cell will be registered as sink to the wire only if it is
        a leaf (a primitive) in the hierarchy

        Parameters
        ----------
        parent : Logic
            DESCRIPTION.
        name : TYPE
            DESCRIPTION.
        wire : Wire
            DESCRIPTION.

        Returns
        -------
        None.

        """
        #print('in port')
        self.name = name
        self.parent = parent
        self.wire = wire

        if (parent.isPrimitive()):
            wire.addSink(self)
            
    def getFullPath(self):
        return self.parent.getFullPath() + '[{}]'.format(self.name)
    
class OutPort:
    """
    An output port
    """
    def __init__(self, parent:Logic, name:str, wire:Wire):
        """
        Creates an out port to the cell.
        The cell will be registered as source of the wire only if it
        is a leaf (a primitive) in the hierarchy 

        Parameters
        ----------
        parent : Logic
            Parent Cell of the port
        name : str
            name of the port.
        wire : Wire
            Wire associated with the port

        Returns
        -------
        None.

        """
        #print('out port')
        self.name = name
        self.parent = parent
        self.wire = wire
        
        if (parent.isPrimitive()):
            wire.setSource(self)

    def getFullPath(self):
        return self.parent.getFullPath() + '[{}]'.format(self.name)

class InterfaceSource:
    def __init__(self, name:str, ports):
        self.name = name
        self.ports = ports
    
    
    
class InterfaceSink:
    def __init__(self, name:str, ports):
        self.name = name
        self.ports = ports
    
class HWSystem(Logic):
    """
    A Hardware system is the top level entity of all designs 
    """
    def __init__(self, clock_driver=None):
        super().__init__(None, "HWSystem")
        self.simulator = None
        if (clock_driver is None):
            clock_driver = ClockDriver('clk50', 50E6, 0) # we create a 50MHz clock driver by default
        self.clockDriver = clock_driver
        
    def getSimulator(self):
        """
        Returns the singleton simulator instance

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        from .simulation import Simulator

        if (self.simulator == None):
            self.simulator = Simulator(self)
        else: 
            self.simulator.topologicalSort() # Updates existing simulator
            
        return self.simulator
        
    
class ClockDriver():
    """
    A clock driver
    """
    
    def __init__(self, name:str, freq=50E6, phaseOffset=0, base=None, enable=None):
        """
        Creates a clock driver

        Parameters
        ----------
        name : str
            Name of the clock driver.
        freq : number, optional
            frequency (in Hz) of the clock .
        phaseOffset : number, optional
            phase offset (in %) of the positive edge of the clock
        base : ClockDriver, optional
            ClockDriver that this clock driver is based on. This is useful for gated clocks.
        enable : Wire, optional
            Wire controling the gating of the clock. When enable is 0, the clock
            will be gated

        Returns
        -------
        None.

        """
        self.name = name
        self.base = base
        
        if (base is None):
            self.freq = freq
            self.phaseOffset = phaseOffset
        else:
            self.freq = base.freq;
            self.phaseOffset = base.phaseOffset
            
        self.enable = enable
        

def has_method(o, name):
    return callable(getattr(o, name, None))


class Interface:
    """
    An interface is a collection of wires that connect
    a source to a sink
    """
    def __init__(self, parent:Logic, name:str):
        self.name = name
        self.parent = parent
        self.sourceToSink = []
        self.sinkToSource = []
    
    def addSourceToSink(self, name:str, width:int):
        """
        Adds a source wire to the definition of the interface

        Parameters
        ----------
        name : str
            DESCRIPTION.
        width : int
            DESCRIPTION.

        Returns
        -------
        None.

        """
        w = self.parent.wire(self.name + "_" + name, width)
        self.sourceToSink.append([name, w])
        return w;
        
    def addSinkToSource(self, name:str, width:int):
        """
        Adds a source wire to the definition of the interface

        Parameters
        ----------
        name : str
            DESCRIPTION.
        width : int
            DESCRIPTION.

        Returns
        -------
        None.

        """
        w = self.parent.wire(self.name + "_" + name, width)
        self.sinkToSource.append([name, w])
        return w;
        

def disconnectWireFromLogicObject(w:Wire, obj:Logic):
    """
    Disconnects a wire from a logic object

    Parameters
    ----------
    w : Wire
        The wire to disconnect from the object.
    obj : Logic
        The object to disconnect from the wire.

    Returns
    -------
    None.

    """
    if (w.source in obj.outPorts):
        # wire is connected to an output port of the obj
        port = w.source
        w.source = None
        port.wire = None
        return 

    for sink in w.sinks:
        if (sink in obj.inPorts):
            # wire is connected to an input port of the obj
            w.sinks.remove(sink)
            sink.wire = None
            return
        
    raise Exception('wire and object are not connected')
    
def getObjectClockDriver(obj:Logic) -> ClockDriver:
    """
    Returns the clock driver of an object.
    @todo consider multiple clock drivers scenario

    Parameters
    ----------
    obj : Logic
        Object of interest.

    Raises
    ------
    Exception
        DESCRIPTION.

    Returns
    -------
    ClockDriver
        The ClockDriver of the object.

    """
    
    if (obj.clockDriver != None):
        return obj.clockDriver
    if (obj.parent == None):
        raise Exception('No clock driver at top level')
    else:
        return getObjectClockDriver(obj.parent)