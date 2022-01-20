# -*- coding: utf-8 -*-
from .base import HWSystem
from .base import Wire
from .base import Logic
from .base import Interface

def printHierarchy(sys:HWSystem):
    
    global indent 
    
    indent = 0;
    
    printElement(sys)
    
    
def printElement(obj:Logic):
    
    global indent
    
    indStr = ' ' * indent
    
    print( indStr + type(obj).__name__)
    
    if (len(obj.children) > 0):
        oldindent = indent;
        
        
        for child in obj.children:
            indent = oldindent + 1
            printElement(child)
        
        
        #for child in obj.children:
        #    printElement(child)
    
        indent = oldindent 


def printHierarchyWithValues(sys:HWSystem, include=None):
    
    global indent 
    
    indent = 0;
    
    printElementWithValues(sys, include=include)
    
    
def printElementWithValues(obj:Logic, include=None):
    
    global indent
    
    indStr = ' ' * indent

    doPrint = True    
    
    if (not(include is None)):
        # something to filter
        if (not(type(obj).__name__ in include)):
            doPrint = False

    if (doPrint):
        # no filter
        print( indStr + type(obj).__name__ , obj.name, getPortValues(obj))
    
    if (len(obj.children) > 0):
        oldindent = indent;
        
        for child in obj.children:
            indent = oldindent + 1
            printElementWithValues(child, include=include)
            
        indent = oldindent
    
def getPortValues(obj:Logic):
    ret = '('
    link = ''
    for ip in obj.inPorts:
        ret = ret + link + ip.name + '=' + str(ip.wire.get()) 
        link = ','
        
    ret = ret + ') -> ('
    
    link = ''
    for ip in obj.outPorts:
        ret = ret + link + ip.name + '=' + str(ip.wire.get()) 
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
            
    for child in obj.children:
        checkIntegrity(child)