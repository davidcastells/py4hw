
        
class Logic:
    """
    Base class for all logic circuits
    """
    
    def __init__(self, parent, instanceName:str):
        self.parent = parent
        self.name = instanceName
        
        if (not(parent is None)):
            if not(isinstance(parent, Logic)):
                raise Exception('parent object must be a Logic object not a {}'.format(type(parent)))
                
            # Add this object as a parent's child
            if (instanceName in parent.children.keys()):
                raise Exception('there is already a child named {} in {}'.format(instanceName, parent.getFullPath() ))

            parent.children[instanceName] = self

        self.inPorts = []   # in ports are a sorted list
        self.outPorts = []  # out ports are a sorted list
        self.inOutPorts = [] # in/out ports
        self.sources = []   # list of InterfaceSource objects
        self.sinks = []     # List of InterfaceSink objects
    
        self.children = {}          # children are keyed by name
        self.clockDriver = None     # every circuit has a clock driver, if None it is inherited from parent
                                    # the clock driver in place for an object can be obtained by the function
                                    # getObjectClockDriver(obj)
        
        self._wires = {}        # dictionary of wires created by the object
        
    def addIn(self, name , wire):
        port = InPort(self, name, wire)
        self.inPorts.append(port)
        return wire;
    
    def getInPortByName(self, name):
        for port in self.inPorts:
            if (port.name == name):
                return port
        return None

    def getOutPortByName(self, name):
        for port in self.outPorts:
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
    
    def addInOut(self, name, wire):
        port = InOutPort(self, name, wire)
        self.inOutPorts.append(port)
        return wire;

    def addParameter(self, name, value):
        if not(hasattr(self, 'parameters')):
            self.parameters = {}
            
        self.parameters[name] = value
        
    def getParameterValue(self, name):
        value = self.parameters[name]
        
        if (isinstance(value, Parameter)):
            value = value.obj.parameters[value.name]
        return value
    
    def getParameterInstantiationValue(self, name):
        # returns the final name associated with this parameter, used in rtl
        # generation.
        # If the parent instantiates the parameter with a value, we return it
        # If the parent instantiates the parameter with a parent parameter, we return it
        value = self.parameters[name]

        if (isinstance(value, Parameter)):
            return value.name
        else:
            return value            
    
    def getParameter(self, name):
        return Parameter(self, name)        
    
    def getParameterNames(self):
        if not(hasattr(self, 'parameters')):
            return None
        
        return self.parameters.keys()
    
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
        if (len(name) > 0):
            name = name + '_'
            
        for obj in interface.sourceToSink:
            wire = obj[1]
            portname = name + obj[0]
            port = OutPort(self, portname, wire)
            self.outPorts.append(port)
            ports.append(port)
        
        for obj in interface.sinkToSource:
            wire = obj[1]
            portname = name + obj[0]
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
        if (len(name) > 0):
            name = name + '_'
            
        for obj in interface.sourceToSink:
            wire = obj[1]
            portname = name + obj[0]
            port = InPort(self, portname, wire)
            self.inPorts.append(port)
            ports.append(port)
        for obj in interface.sinkToSource:
            wire = obj[1]
            portname = name + obj[0]
            port = OutPort(self, portname, wire)
            self.outPorts.append(port)
            ports.append(port)
            
        self.sinks.append(InterfaceSink(name, ports))
        
        return interface;
        
    def appendWire(self, wire):
        #print('checking if ', wire.name, 'is already in', [x for x in self._wires.keys()])
        if (wire.name in self._wires.keys()):
            raise Exception('a wire named {} already exist'.format(wire.name))
            
        self._wires[wire.name] = wire
        
    def bidir_wire(self, name, width=1):
        return BidirWire(self, name, width)
    
    def wire(self, name, width=1):
        return Wire(self, name, width);
    
    def wires(self, name:str, num:int, width:int) -> list:
        """
        Creates a number of wires

        Parameters
        ----------
        name : str
            prefix of the wire names, it will be suffixed by _0, _1, etc.
        num : int
            numer of wires to create.
        width : int
            width of the wires to create.

        Returns
        -------
        list
            a list with the created wires.

        """
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
        
class Parameter:
    def __init__(self, obj, name):
        self.obj = obj
        self.name = name
        
class Wire:
    """
    Wires in py4hw connect one source with one (or more) sinks.
    For many-to-many connections use BidirWire
    """
    
    # this is the list of prepared wires, 
    prepared = []
    
    def __init__(self, parent, name : str, width: int = 1 ):
        # the following should not be necessary if python checks types
        assert(isinstance(name, str))
        assert(isinstance(width, int))
        
        self.parent = parent
        self.name = name
        self.width = width
        self.value = 0 # should be None      # reset state
        self.sinks = []
        self.source = None
        parent.appendWire(self)
        
    def getFullPath(self)->str:
        return self.parent.getFullPath() + '[{}]'.format(self.name)
    
    def getWidth(self) -> int:
        return self.width
    
    def put(self, val:int):
        mask = (1<<self.width) -1
        self.value = val & mask

    def prepare(self, val:int):
        if (self in Wire.prepared):
            print('WARNING! wire {} already prepared'.format(self.getFullPath()))
            
        mask = (1<<self.width) -1
        self.next = val & mask
        Wire.prepared.append(self)
        
    def settle(self):
        self.value = self.next
        
    def get(self) -> int:
        return self.value
    
    def setSource(self, source):
        if (self.source != None):
            raise Exception('Source of wire {} already connected to {}'.format(self.getFullPath(), self.source.parent.getFullPath()))

        self.source = source
        
    def addSource(self, source):
        self.setSource(source)
        
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
    
    def rename(self, newname):
        del self.parent._wires[self.name]
        self.name = newname
        self.parent.appendWire(self)
        
    def reparent(self, newparent):
        del self.parent._wires[self.name]
        self.parent = newparent
        newparent.appendWire(self)

    def reparentAndRename(self, newparent, newname):
        del self.parent._wires[self.name]
        self.name = newname
        self.parent = newparent
        newparent.appendWire(self)

class BidirWire(Wire):
    """
    Wires in py4hw connect one source with one (or more) sinks.
    For many-to-many connections use BidirWire
    """
    
    # this is the list of prepared wires, 
    # @todo what for ??
    prepared = []
    
    def __init__(self, parent, name : str, width: int = 1 ):
        # the following should not be necessary if python checks types
        assert(isinstance(name, str))
        assert(isinstance(width, int))
        
        self.parent = parent
        self.name = name
        self.width = width
        self.value = 0 # should be None      # reset state
        self.sinks = []
        self.sources = []
        parent.appendWire(self)
        
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
    
    def addSource(self, source):        
        self.sources.append(source)
        
        
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
    
    def rename(self, newname):
        del self.parent._wires[self.name]
        self.name = newname
        self.parent.appendWire(self)
        
    def reparent(self, newparent):
        del self.parent._wires[self.name]
        self.parent = newparent
        newparent.appendWire(self)

    def reparentAndRename(self, newparent, newname):
        del self.parent._wires[self.name]
        self.name = newname
        self.parent = newparent
        newparent.appendWire(self)
        
class FakeWire():
    # By now we use FakeWire to refer to a specific subwire of a bidirectional
    # port.
    def __init__(self, name, w=1):
        self.name = name
        self.w = w

    def addSource(self, source):
        pass
    
    def addSink(self, sink):
        pass
    
    def getWidth(self):
        return self.w
    
    def getFullPath(self):
        return self.name

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
    def __init__(self, parent:Logic, name:str, wire):
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
            wire.addSource(self)

    def getFullPath(self):
        return self.parent.getFullPath() + '[{}]'.format(self.name)

class InOutPort:
    """
    An input/output port
    """
    def __init__(self, parent:Logic, name:str, wire:Wire):
        """
        Creates an in/out port to the cell.
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
            wire.addSource(self)
            wire.addSink(self)


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
    def __init__(self, clock_driver=None, name=None):
        super().__init__(None, "HWSystem")
        self.simulator = None
        if (clock_driver is None):
            clock_driver = ClockDriver('clk', 50E6, 0, wire=self.wire('clk')) # we create a 50MHz clock driver by default
        if not(name is None):
            self.name = name
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
    
    def __init__(self, name:str, freq=50E6, phaseOffset=0, base=None, enable=None, wire=None):
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
        wire : Wire, optional
            Wire that contains the clock

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
        self.wire = wire

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
        assert(isinstance(width, int))
        w = self.parent.wire(self.name + "_" + name, width)
        self.sourceToSink.append([name, w])
        return w;
    
    def getSourceToSink(self, name):
        if len(self.sourceToSink) == 0:
            raise Exception('No source-to-sink elements in this interface')
            
        for p in self.sourceToSink:
            if (p[0] == name):
                return p[1]
            
        raise Exception('SourceToSink {} not found'.format(name))
    
    def getSinkToSource(self, name):
        # returns a wire with that name
        if len(self.sinkToSource) == 0:
            raise Exception('No sink-to-source elements in this interface')
            
        for p in self.sinkToSource:
            if (p[0] == name):
                return p[1]
                
        raise Exception('SinkToSource {} not found'.format(name))
        
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
    
    def addSourceToSinkRef(self, ref, name:str):
        # Adds a reference to another interface, this is used in subinterfaces
        w = ref.getSourceToSink(name)
        self.sourceToSink.append([name, w])
        return w
        
    def addSinkToSourceRef(self, ref, name:str):
        # Adds a reference to another interface, this is used in subinterfaces
        w = ref.getSinkToSource(name)
        self.sinkToSource.append([name, w])
        return w
        

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
    
    
def AbstractLogicInit(self, parent:Logic, name:str):
    super(self.__class__, self).__init__(parent, name)
    
def AbstractLogic(class_name):
    return type(class_name, # class name
                (Logic,), # base classes
                {'__init__': AbstractLogicInit} # methods
                )
