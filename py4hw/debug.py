# -*- coding: utf-8 -*-
from .base import HWSystem
from .base import Wire
from .base import Logic
from .base import Interface

def printHierarchy(sys:Logic):
    """
    Prints the hierarchy of the object

    Parameters
    ----------
    sys : HWSystem
        DESCRIPTION.

    Returns
    -------
    None.

    """
    global indent 
    
    indent = 0;
    
    _printElement(sys)
    
    
def _printElement(obj:Logic):
    
    global indent
    
    indStr = ' ' * indent
    
    print( indStr + type(obj).__name__)
    
    if (len(obj.children) > 0):
        oldindent = indent;
        
        
        for child in obj.children.values():
            indent = oldindent + 1
            _printElement(child)
        
        
        #for child in obj.children:
        #    printElement(child)
    
        indent = oldindent 


def printHierarchyWithValues(sys:Logic, include=None, format=None):
    
    global indent 
    
    indent = 0;
    
    if (format is None):
        format = '{}'
        
    _printElementWithValues(sys, include=include, format=format)
    
    
def _printElementWithValues(obj:Logic, include, format):
    
    global indent
    
    indStr = ' ' * indent

    doPrint = True    
    
    if (not(include is None)):
        # something to filter
        if (not(type(obj).__name__ in include)):
            doPrint = False

    if (doPrint):
        # no filter
        print( indStr + type(obj).__name__ , obj.name, _getPortValues(obj, sfmt=format))
    
    if (len(obj.children) > 0):
        oldindent = indent;
        
        for child in obj.children.values():
            indent = oldindent + 1
            _printElementWithValues(child, include=include, format=format)
            
        indent = oldindent
    
def getPorts(obj):
    # For a logic block, it returns its ports 
    # For an interface, it resturns the ports of its source 
    ret = []
    if (isinstance(obj, Logic)):
        for ip in obj.inPorts:
            ret.append(ip)
    
        for ip in obj.outPorts:
            ret.append(ip)
    elif (isinstance(obj, Interface)):

        for sourceInfo in obj.sourceToSink:
            name = sourceInfo[0]
            wire = sourceInfo[1]
            sourcePort = wire.getSource()
            
            if not(sourcePort is None):
                ret.append(sourcePort)
            
        for sinkInfo in obj.sinkToSource:
            name = sinkInfo[0]
            wire = sinkInfo[1]
            
            sourcePort = wire.getSource()
            if not(sourcePort is None):
                ret.append(sourcePort)

    return ret

def getPortWires(obj:Logic):
    ret = []
    for ip in obj.inPorts:
        ret.append(ip.wire)

    for ip in obj.outPorts:
        ret.append(ip.wire)

    return ret

def _getPortValues(obj:Logic, sfmt:str):
    ret = '('
    link = ''
    for ip in obj.inPorts:
        ret = ret + link + ip.name + '=' + sfmt.format(ip.wire.get()) 
        link = ','
        
    ret = ret + ') -> ('
    
    link = ''
    for ip in obj.outPorts:
        ret = ret + link + ip.name + '=' + sfmt.format(ip.wire.get()) 
        link = ','
        
    ret = ret + ') '
    
    return ret

def dumpInterfaceSources(interface:Interface):
    print('Interface name:', interface.name)
    for sourceInfo in interface.sourceToSink:
        name = sourceInfo[0]
        wire = sourceInfo[1]
        print(' Wire: ->' , name)
        
        sourcePort = wire.getSource()
        portParent = sourcePort.parent
        portName = sourcePort.name
        print('  Source Port Parent:', portParent.getFullPath())
        print('  Source Port Name:', portName)
        
    for sinkInfo in interface.sinkToSource:
        name = sinkInfo[0]
        wire = sinkInfo[1]
        print(' Wire: <-' , name)
        
        sourcePort = wire.getSource()
        portParent = sourcePort.parent
        portName = sourcePort.name
        print('  Source Port Parent:', portParent.getFullPath())
        print('  Source Port Name:', portName)
        
        
    
def checkPortParent(port, obj:Logic):
    if (port.parent != obj):
        print('ERROR', obj.name + '['+ port.name+']', ' parent is ',  port.parent.getFullPath(), 'expecting', obj.getFullPath())

def checkPort(port):
    parent = port.parent # parent logic
    
    if (not(port in parent.inPorts or port in parent.outPorts)):
        raise Exception('ERROR: {} not port of parent {}'.format(port.name, parent.getFullPath()) )
    
def checkIntegrity(obj:Logic):
    """
    Checks that the circuit has integrity.
    All wires are correctly connected

    Parameters
    ----------
    obj : Logic
        DESCRIPTION.

    Returns
    -------
    None.

    """
    
    # check that the parents of ports are referering to the same entity
    for inP in obj.inPorts:
        checkPortParent(inP, obj)

    for outP in obj.inPorts:
        checkPortParent(outP, obj)
            
    # check that wires of ports are connected
    for inP in obj.inPorts:
        wire = inP.wire
        sinks = wire.getSinks()
        source = wire.getSource() # gets the source port
        
        if (len(sinks) == 0):
            print('WARNING', obj.getFullPath(), wire.name, 'with no sinks')
        if (source == None):
            raise Exception('ERROR: {} {} with no source'.format(obj.getFullPath(), wire.name))
            
        checkPort(source)
            
    for outP in obj.outPorts:
        wire = outP.wire
        sinks = wire.getSinks()
        source = wire.getSource()
        
        if (len(sinks) == 0):
            print('WARNING', obj.getFullPath(), wire.name, 'with no sinks')
        if (source == None):
            raise Exception('ERROR: {} {} with no source'.format(obj.getFullPath(), wire.name))
            
    for child in obj.children.values():
        checkIntegrity(child)