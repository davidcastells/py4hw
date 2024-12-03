# -*- coding: utf-8 -*-
"""
Created on Thu Jan 20 18:42:23 2022

@author: dcr
"""

from .base import *
from .logic import *
from .logic.bitwise import *
from .logic.storage import *
from .schematic_symbols import *
from .transpilation.python2verilog_transpilation import *

def getVerilogModuleName(obj:Logic, noInstanceNumber=False):
    '''
    Returns the module name of an object.
    Logic classes can provide their module name by implementing the method structureName,
    if it is not provided the structure is unique for every instance, hence the number
    of structures is significantly increase (which is generally bad for reading)

    Parameters
    ----------
    obj : Logic
        DESCRIPTION.
    noInstanceNumber : TYPE, optional
        DESCRIPTION. The default is False.

    Returns
    -------
    str : TYPE
        DESCRIPTION.

    '''
    if (has_method(obj, 'structureName')):
        return obj.structureName()
    
    str = type(obj).__name__  
    if (not(noInstanceNumber)):
        sid = hex(id(obj))
        str += "_" +sid[2:] 
        
    return str

def getWidthInfo(w:Wire):
    ww = w.getWidth()
    if (ww > 1):
        return "[{}:0]".format(ww-1)
    else:
        return ""
    
def getInstanceName(ins:Logic):
    return "i_" + ins.name

def isReservedVerilogKeyword(str):
    # info from https://www.intel.com/content/www/us/en/programmable/quartushelp/13.0/mergedProjects/hdl/vlog/vlog_file_reserved_words.htm
    reserved95 = ['always','and','assign',
                'begin','buf','bufif0','bufif1',
                'case','casex','casez','cmos',
                'deassign','default','defparam','disable',
                'edge','else','end','endcase','endfunction','endmodule','endprimitive','endspecify','endtable','endtask','event',
                'for','force','forever','fork','function',
                'highz0','highz1',
                'if','ifnone', 'initial','inout','input','integer',
                'join',
                'large',
                'macromodule','medium','module',
                'nand','negedge','nmos','nor','not','notif0','notif1',
                'or','output',
                'parameter','pmos','posedge','primitive','pull0','pull1','pulldown','pullup',
                'rcmos','real','realtime','reg','release','repeat','rnmos','rpmos','rtran','rtranif0','rtranif1',
                'scalared','small','specify','specparam','strong0','strong1','supply0','supply1',
                'table','task','time','tran','tranif0','tranif1','tri','tri0','tri1', 'triand','trireg','trior',
                'vectored',
                'wait','wand','weak0','weak1','while','wire','wor',
                'xor','xnor']

    reserved2001 = ['automatic',
                    'cell','config',
                    'endconfig','endgenerate',
                    'generate','genvar',
                    'incdir','include','instance',
                    'liblist','library','localparam',
                    'noshowcancelled',
                    'pulsestyle_ondetect','pulsestyle_onevent',
                    'showcancelled','signed',
                    'unsigned','use' ]


    reservedSV = ['accept_on','alias','always_comb','always_ff','always_latch','assert','assume',
                  'before','bind','bins','binsof','bit','break','byte',
                  'chandle','checker','class','clocking','const','constraint','context','continue','cover','covergroup','coverpoint','cross',
                  'dist','do',
                  'endclass','endchecker','endclocking','endgroup','endinterface','endpackage','endprogram','endproperty','endsequence','enum','eventually','expect','export','extends','extern',
                  'final','first_match','foreach','forkjoin',
                  'global',
                  'iff','inside','int','illegal_bins','ignore_bins','implies','import','interface','intersect',
                  'join_any','join_none',
                  'let','local','logic','longint',
                  'matches','modport',
                  'new','nexttime','null',
                  'package','packed','priority','program','property','protected','pure',
                  'rand','randc','randcase','randsequence','ref','reject_on','restrict','return',
                  's_always','s_eventually','s_nexttime','s_until','s_until_with','shortint','shortreal','sequence','solve','static','string','strong','struct','super','sync_accept_on','sync_reject_on',
                  'tagged','this','throughout','timeprecision','timeunit','type','typedef',
                  'union','unique','unique0','until','until_with','untypted',
                  'var','virtual','void','wait_order','weak','wildcard','with','within']

    if (str in reserved95):
        return True
    if (str in reserved2001):
        return True
    if (str in reservedSV):
        return True
    return False

wire_names_cache_obj = None
wire_names_cache = None

def getWireNames(obj:Logic):
    """
    Collects the wires of the obj and their names in 
    its scope. Since this does not change and it could be called multiple 
    times during the RTL generation process, we maintain a cached copy. 

    Parameters
    ----------
    obj : Logic
        The logic circuit that we collect the wires from.

    Returns
    -------
        A dictionary keyed by wire objects returning their name
        in the obj scope
    """
    global wire_names_cache_obj
    global wire_names_cache

    if (obj == wire_names_cache_obj):
        return wire_names_cache

    ret = {}
    
    # process all the wires connected to child instances
    for child in obj.children.values():
        for wire in collectPortWires(child):
            if (isinstance(wire, Wire)):
                # avoid reporting fake wires
                ret[wire]= "w_" + wire.name
            else:
                ret[wire] = wire.name
 
    # overwrite the wires that are part of the interface
    for inp in obj.inPorts:
        ret[inp.wire]= getPortName(inp) 
        link = ","

    for outp in obj.outPorts:
        ret[outp.wire] = getPortName(outp) 
        
    for outp in obj.inOutPorts:
        ret[outp.wire] = getPortName(outp) 
 
    wire_names_cache_obj = obj
    wire_names_cache = ret
       
    return ret
    
def collectPortWires( obj:Logic):
    """
    Return the wires of the object interface.
    @todo where is this used ?

    Parameters
    ----------
    obj : Logic
        DESCRIPTION.

    Returns
    -------
        a list of the wires from the object interface

    """
    ret = []
    
    for inp in obj.inPorts:
        wire = inp.wire 
        if (not(wire is None)):
            ret.append(inp.wire)

    for outp in obj.outPorts:
        wire = outp.wire 
        if (not(wire is None)):
            ret.append(outp.wire)
            
    for outp in obj.inOutPorts:
        wire = outp.wire
        if (not(wire is None)):
            ret.append(outp.wire)

    return ret

def collectLocalWires(obj:Logic):
    """
    Collects local wires

    Parameters
    ----------
    obj : Logic
        DESCRIPTION.

    Returns
    -------
    ret : TYPE
        A list of local wires

    """
    ret = []
    
    portWires = collectPortWires(obj)
    
    for child in obj.children.values():
        
        childLocalWires = [x for x in collectPortWires(child) if x not in portWires]
        ret.extend(childLocalWires)

    # remove duplicates
    ret = list(set(ret))
    return ret

def getValidVerilogName(name):
    if (isReservedVerilogKeyword(name)):
        name = "reserved_" + name;        
    return name
    
def getPortName(p):
    return getValidVerilogName(p.name)

def getWireName(scope:Logic, w:Wire):
    wNames = getWireNames(scope)
    
    if not(w in wNames.keys()):
        print('ERROR: wire ', w.getFullPath(), 'not in the wires of ', scope.getFullPath()) 
        for w2 in wNames.keys():
            print(wNames[w2], w2 )
        raise Exception('Wire wire {} not in the wires of {}'.format( w.getFullPath(), scope.getFullPath())) 
        
    return wNames[w]

def getParentWireName(child:Logic, w:Wire):
    if  (isinstance(w, FakeWire)):
        # return name for fake wires
        return w.name
    
    wNames = getWireNames(child.parent)
    return wNames[w]
    
def InlineConstant(obj:Logic):
    return "assign {} = {};\n".format(getParentWireName(obj, obj.r) + getWidthInfo(obj.r), obj.value)

def InlineNot(obj:Logic):
    return "assign {} = ~{};\n".format(getParentWireName(obj, obj.r), getParentWireName(obj, obj.a))

def InlineBidirBuf(obj:Logic):
    str =  "assign {} = {};\n".format(getParentWireName(obj, obj.pin), getParentWireName(obj, obj.bidir))
    str += "assign {} = ({}) ? {} : {}'bZ;\n".format(getParentWireName(obj, obj.bidir), getParentWireName(obj, obj.poe), getParentWireName(obj, obj.pout), obj.bidir.getWidth())
    return str

def InlineBuf(obj:Logic):
    return "assign {} = {};\n".format(getParentWireName(obj, obj.r), getParentWireName(obj, obj.a))

def InlineSignExtend(obj:Logic):
    return "assign {} = {{ {{ {} {{ {}[{}] }} }}, {} }};\n".format(getParentWireName(obj, obj.r), obj.r.getWidth() - obj.a.getWidth(),  getParentWireName(obj, obj.a), obj.a.getWidth()-1, getParentWireName(obj, obj.a))

def InlineZeroExtend(obj:Logic):
    return "assign {} = {};\n".format(getParentWireName(obj, obj.r), getParentWireName(obj, obj.a))
    
def InlineAnd2(obj:Logic):
    return "assign {} = {} & {};\n".format(getParentWireName(obj, obj.r), getParentWireName(obj, obj.a) , getParentWireName(obj, obj.b))

def InlineNand2(obj:Logic):
    return "assign {} = ~({} & {});\n".format(getParentWireName(obj, obj.r), getParentWireName(obj, obj.a) , getParentWireName(obj, obj.b))

def InlineOr2(obj:Logic):
    return "assign {} = {} | {};\n".format(getParentWireName(obj, obj.r), getParentWireName(obj, obj.a) , getParentWireName(obj, obj.b))

def InlineNor2(obj:Logic):
    return "assign {} = ~({} | {});\n".format(getParentWireName(obj, obj.r), getParentWireName(obj, obj.a) , getParentWireName(obj, obj.b))

def InlineXor2(obj:Logic):
    return "assign {} = {} ^ {};\n".format(getParentWireName(obj, obj.r), getParentWireName(obj, obj.a) , getParentWireName(obj, obj.b))

def InlineMux2(obj:Logic):
    return "assign {} = ({})? {} : {};\n".format(getParentWireName(obj, obj.r), getParentWireName(obj, obj.sel), getParentWireName(obj, obj.sel1) , getParentWireName(obj, obj.sel0))

def InlineAdd(obj:Logic):
    return "assign {} = {} + {};\n".format(getParentWireName(obj, obj.r), getParentWireName(obj, obj.a) , getParentWireName(obj, obj.b))

def InlineMul(obj:Logic):
    return "assign {} = {} * {};\n".format(getParentWireName(obj, obj.r), getParentWireName(obj, obj.a) , getParentWireName(obj, obj.b))

def InlineDiv(obj:Logic):
    return "assign {} = {} / {};\n".format(getParentWireName(obj, obj.r), getParentWireName(obj, obj.a) , getParentWireName(obj, obj.b))

def InlineMod(obj:Logic):
    return "assign {} = {} % {};\n".format(getParentWireName(obj, obj.r), getParentWireName(obj, obj.a) , getParentWireName(obj, obj.b))

def InlineSub(obj:Logic):
    return "assign {} = {} - {};\n".format(getParentWireName(obj, obj.r), getParentWireName(obj, obj.a) , getParentWireName(obj, obj.b))

def InlineEqualConstant(obj:Logic):
    return "assign {} = ({} == {})? 1 : 0;\n".format(getParentWireName(obj, obj.r), getParentWireName(obj, obj.a), obj.v )

def InlineRange(obj:Logic):
    return "assign {} = {}[{}:{}];\n".format(getParentWireName(obj, obj.r), getParentWireName(obj, obj.a) , obj.high, obj.low)

def InlineBit(obj:Logic):
    return "assign {} = {}[{}];\n".format(getParentWireName(obj, obj.r), getParentWireName(obj, obj.a) , obj.bit)

def InlineBitsLSBF(obj:Logic):
    str = ""
    w = len(obj.bits)
    if (w == 1):
        return "assign {} = {};\n".format(getParentWireName(obj, obj.bits[0]), getParentWireName(obj, obj.a))

    for i in range(w):
        str += "assign {} = {}[{}];\n".format(getParentWireName(obj, obj.bits[i]), getParentWireName(obj, obj.a), i)
        
    return str

def InlineBitsMSBF(obj:Logic):
    str = ""
    w = len(obj.bits)
    if (w == 1):
        return "assign {} = {};\n".format(getParentWireName(obj, obj.bits[0]), getParentWireName(obj, obj.a))

    for i in range(w):
        str += "assign {} = {}[{}];\n".format(getParentWireName(obj, obj.bits[i]), getParentWireName(obj, obj.a), i)
        
    return str

def InlineRepeat(obj:Logic):
    str = ""
    w = obj.r.getWidth()
    if (w == 1):
        return "assign {} = {};\n".format(getParentWireName(obj, obj.r), getParentWireName(obj, obj.i))

    str = 'assign {} ='.format(getParentWireName(obj, obj.r))
    
    link = '{'
    for i in range(w):
        str += link + "{}".format(getParentWireName(obj, obj.i))
        link = ','
    str += '};\n'
    
    return str

def InlineConcatenateMSBF(obj:Logic):
    str = '' # "# MSBF \n"
    w = len(obj.ins)
    if (w == 1):
        return "assign {} = {};\n".format(getParentWireName(obj, obj.r), getParentWireName(obj, obj.ins[0]))

    str += 'assign {} ='.format(getParentWireName(obj, obj.r))
    
    link = '{'
    for i in range(w):
        str += link + "{}".format(getParentWireName(obj, obj.ins[i]))
        link = ','
    str += '};\n'
    
    return str

def InlineConcatenateLSBF(obj:Logic):
    str = '' # "# LSBF \n"
    w = len(obj.ins)
    if (w == 1):
        return "assign {} = {};\n".format(getParentWireName(obj, obj.r), getParentWireName(obj, obj.ins[0]))

    str += 'assign {} ='.format(getParentWireName(obj, obj.r))
    
    link = '{'
    for i in range(w):
        str += link + "{}".format(getParentWireName(obj, obj.ins[i]))
        link = ','
    str += '};\n'
    
    return str

def InlineAnd(obj:Logic):
    str = "assign {} =".format(getParentWireName(obj, obj.r))
    link = ""
    for iw in obj.ins:
        str += link + " {} ".format(getParentWireName(obj, iw)) 
        link = "&";
    str += ";\n"
    return str

def InlineOr(obj:Logic):
    str = "assign {} =".format(getParentWireName(obj, obj.r))
    link = ""
    for iw in obj.ins:
        str += link + " {} ".format(getParentWireName(obj, iw)) 
        link = "|";
    str += ";\n"
    return str

def InlineNor(obj:Logic):
    str = "assign {} = ~(".format(getParentWireName(obj, obj.r))
    link = ""
    for iw in obj.ins:
        str += link + " {} ".format(getParentWireName(obj, iw)) 
        link = "|";
    str += ");\n"
    return str

def InlineEqual(obj:Logic):
    return "assign {} = ({} == {})? 1:0;\n".format(getParentWireName(obj, obj.r), getParentWireName(obj, obj.a), getParentWireName(obj, obj.b))

def InlineVerilogCommnent(obj:Logic):
    return '// {}\n'.format(obj.comment)
    
def BodyReg(obj:Logic):
    clkname = getObjectClockDriver(obj).name
    str = "reg "+getWidthInfo(obj.q) + " rq = {};\n".format(obj.reset_value)
    str += "always @(posedge {})\n".format(clkname)
    close = ""
    if not(obj.r is None):
        str += "if (r == 1)\n"
        str += "begin\n"
        str += "   rq <= {};\n".format(obj.reset_value)
        str += "end\n";
        str += "else\n";
        str += "begin\n";
        close = "end\n";
        
    if not(obj.e is None):
        str += "if (e == 1)\n"
        str += "begin\n"
        close = "end\n" + close
        
    str += "   rq <= d;\n"
    
    str += close
    str += "assign q = rq;\n"
    return str

def BodyGatedClock(obj:Logic):
    str = "reg eq = 0;\n"
    str += "always @(negedge clk_in)\n"
    str += "begin\n"
    str += "   eq <= enin;\n"
    str += "end\n"
    str += "assign enout = eq;\n"
    str += "assign clk_out = enout & clk_in;\n"
    return str

class VerilogGenerator:
    
    
    def __init__(self, obj:Logic):
        #print('Testing Verilog Generation')
        self.obj = obj
        
        self.inlinablePrimitives = {}
        
        self.inlinablePrimitives[Add] = InlineAdd
        
        self.inlinablePrimitives[And2] = InlineAnd2
        self.inlinablePrimitives[And] = InlineAnd
        self.inlinablePrimitives[BidirBuf] = InlineBidirBuf
        self.inlinablePrimitives[Bit] = InlineBit
        self.inlinablePrimitives[BitsLSBF] = InlineBitsLSBF
        self.inlinablePrimitives[BitsMSBF] = InlineBitsMSBF
        self.inlinablePrimitives[Buf] = InlineBuf
        self.inlinablePrimitives[ConcatenateMSBF] = InlineConcatenateMSBF
        self.inlinablePrimitives[ConcatenateLSBF] = InlineConcatenateLSBF
        self.inlinablePrimitives[Constant] = InlineConstant
        self.inlinablePrimitives[Div] = InlineDiv
        self.inlinablePrimitives[Equal] = InlineEqual
        self.inlinablePrimitives[EqualConstant] = InlineEqualConstant
        self.inlinablePrimitives[Mod] = InlineMod
        self.inlinablePrimitives[Mul] = InlineMul
        self.inlinablePrimitives[Mux2] = InlineMux2
        self.inlinablePrimitives[Nand2] = InlineNand2
        self.inlinablePrimitives[Not] = InlineNot
        self.inlinablePrimitives[Nor] = InlineNor
        self.inlinablePrimitives[Nor2] = InlineNor2
        self.inlinablePrimitives[Or] = InlineOr
        self.inlinablePrimitives[Or2] = InlineOr2
        self.inlinablePrimitives[Sub] = InlineSub
        self.inlinablePrimitives[Range] = InlineRange
        self.inlinablePrimitives[Repeat] = InlineRepeat
        self.inlinablePrimitives[SignExtend] = InlineSignExtend
        self.inlinablePrimitives[ZeroExtend] = InlineZeroExtend
        self.inlinablePrimitives[VerilogComment] = InlineVerilogCommnent
        self.inlinablePrimitives[Xor2] = InlineXor2
        
        self.providingBody = {}
        
        self.providingBody[Reg] = BodyReg 
        self.providingBody[GatedClock] = BodyGatedClock
        
    def getVerilogForHierarchy(self, obj=None, noInstanceNumberInTopEntity=True, 
                               forceName=None, createdStructures=[]):
        """
        Generates Verilog for all entities of the object hierarchy

        Returns
        -------
        An string with the Verilog for the Hierarchy.

        """
        
        self.created_structures = createdStructures
        return self._getVerilogForHierarchy(obj, noInstanceNumberInTopEntity, forceName)
    
    def _getVerilogForHierarchy(self, obj=None, noInstanceNumberInTopEntity=True, forceName=None):
        
        
        if (obj is None):
            obj = self.obj
        
        #print('generating {}'.format(obj.getFullPath()))
            
        str = self._getVerilog(obj, noInstanceNumber = noInstanceNumberInTopEntity, forceName=forceName)
        
        for child in obj.children.values():
            if (self.isInlinable(child)):
                #print('inlining {}'.format(child.name))
                pass
            else:
                # skip inlinable modules from verilog generation
                part = self._getVerilogForHierarchy(child, noInstanceNumberInTopEntity=False)
                
                if len(part) > 0:
                    str += "\n"
                    str += part

        return str        
        
    def getVerilog(self, obj=None, noInstanceNumber=False, forceName=None):
        '''
        Create Verilog for a module

        Parameters
        ----------
        obj : TYPE, optional
            DESCRIPTION. The default is None.
        noInstanceNumber : TYPE, optional
            DESCRIPTION. The default is False.

        Returns
        -------
        str : TYPE
            DESCRIPTION.

        '''
        self.created_structures = []
        return self._getVerilog(obj, noInstanceNumber, forceName)
    
    def _getVerilog(self, obj=None, noInstanceNumber=False, forceName=None):
        
        str = "// This file was automatically created by py4hw RTL generator\n"
        
        if (obj is None):
            obj = self.obj
            
        # check if structure was already generated
        
        if not(forceName is None):
            structure_name = forceName
        else:
            structure_name = getVerilogModuleName(obj, noInstanceNumber=noInstanceNumber)
        
        if (structure_name in self.created_structures):
            return ''
            
        str += self.createModuleHeader(obj, structure_name)
        
        localWires = collectLocalWires(obj)
        wireNames = getWireNames(obj)
        
        for wire in localWires:
            if (isinstance(wire, FakeWire)):
                continue
            
            name = wireNames[wire]
            ww = wire.getWidth()
            if (ww > 1):
                str += "wire [{}:0] {};\n".format(ww-1, name)
            else:
                str += "wire {};\n".format(name)
                
        if (obj.isPropagatable()):
            # generate code from propagate function
            if (self.isProvidingBody(obj)):
                str += self.provideBody(obj);
            else:
                print('transpiling', obj.getFullPath())
                str += self.generateCodeFromPropagate(obj)

        elif (obj.isClockable()):
            #generate code from clock function
            if (self.isProvidingBody(obj)):
                str += self.provideBody(obj);
            else:
                str += self.generateCodeFromClock(obj)

        else:
            # structural circuit
            str += self.createModuleInstances(obj)
        
        str += "endmodule\n"
        
        self.created_structures.append(structure_name)
        
        return str
        
    def anyClockableDescendant(self, obj:Logic):
        """
        Checks it any of the descendants of obj is clockable

        Parameters
        ----------
        obj : Logic
            Logic circuit to test.

        Returns
        -------
        True if there is a descendant that is clockable

        """
        if (obj.isPrimitive()):
            return obj.isClockable()
        
        for child in obj.children.values():
            if (self.anyClockableDescendant(child)):
                return True
            
        return False
        
    def createModuleHeader(self, obj:Logic, structureName):
        # Created the Module Header containing inputs, ouputs and parameters
        
        str = "module " + structureName 
        
        # Add parameters
        paramNames = obj.getParameterNames()
        if not(paramNames is None):
            str += " #( \n\t"
            link = ""
            
            for paramName in paramNames:
                str += link + 'parameter ' +  paramName
                link = ',\n\t'
                
            str += ')\n'
                
            
        str += " (\n\t"

        link = ""
        
        if (isinstance(obj, GatedClock)):
            drv = obj.drv
            str += link + "input clk_in".format(drv.base.name)
            link = ",\n\t"
            str += link + "output clk_out".format(drv.name)
            
        reg = ""
        if ((obj.isClockable() or obj.isPropagatable()) and not(self.isProvidingBody(obj))):
            reg = " reg "
        
        if (self.anyClockableDescendant(obj)):
            clkname = getObjectClockDriver(obj).name
            str += "input {}".format(clkname)
            link = ",\n\t"
        
        for inp in obj.inPorts:
            str += link +  "input " + getWidthInfo(inp.wire) + " " + getPortName(inp)+ ""
            link = ",\n\t"

        for outp in obj.outPorts:
            str += link + "output " + reg + getWidthInfo(outp.wire) + " " + getPortName(outp)+ ""
            link = ",\n\t"

        for outp in obj.inOutPorts:
            str += link + "inout " + reg + getWidthInfo(outp.wire) + " " + getPortName(outp)+ ""
            link = ",\n\t"
            
        str += ");\n"
        
        return str
    

    
        
    def isInlinable(self, obj:Logic):
        # if (not(obj.isPrimitive())):
        #     return False
        
        try:
            ret = self.inlinablePrimitives[type(obj)]
        except:
            return False
        
        return True
    
    def isProvidingBody(self, obj:Logic):
        # if (not(obj.isPrimitive())):
        #     return False

        if (has_method(obj, 'verilogBody')):
            return True
        
        try:
            ret = self.providingBody[type(obj)]
        except:
            return False
        
        return True

    def inlinePrimitive(self, obj:Logic):
        ret = self.inlinablePrimitives[type(obj)]
        return ret(obj)

    def provideBody(self, obj:Logic):

        if (has_method(obj, 'verilogBody')):
            return obj.verilogBody()

        ret = self.providingBody[type(obj)]
        return ret(obj)
        
    def createModuleInstances(self, obj:Logic):
        '''
        Instantiate the child instances of the module

        Parameters
        ----------
        obj : Logic
            DESCRIPTION.

        Returns
        -------
        str
            The Verilog of sub-circuit instantiation.

        '''
        str = "\n"
        
        for child in obj.children.values():
            if (self.isInlinable(child)):
                #print('create inlinable instance {}'.format(child.name))
                #print('>>', self.inlinePrimitive(child))

                str += self.inlinePrimitive(child)
            else:
                str += self.instantiateStructural(child)

        return str;

    def instantiateStructural(self, child:Logic):
        parent = child.parent
        str = getVerilogModuleName(child) + " " 
        
        paramNames = child.getParameterNames()
        if not(paramNames is None):
            str += '#('
            link = ''
            
            for paramName in paramNames:
                paramValue = child.getParameterInstantiationValue(paramName)
                
                if isinstance(paramValue, Parameter):
                    paramValue = paramValue.name
                    
                str += link + f'.{paramName}({paramValue})'
                link = ','
            str += ') '
            
        str += getInstanceName(child)
        str += "("
        link = ""
        
        if (isinstance(child, GatedClock)):
            # ClockGate elements are special
            drv:ClockDriver = child.drv
            str += link + ".clk_in({})".format(drv.base.name)
            link = ","
            str += link + ".clk_out({})".format(drv.name)
            
        elif (self.anyClockableDescendant(child)):
            # Clock is an implicit parameter
            drv:ClockDriver = getObjectClockDriver(child)
            clkname = drv.name
            if (drv.wire is None):
                raise Exception('None clk driver wire for', clkname, child.getFullPath())
                
            parentDrv:ClockDriver = getObjectClockDriver(child.parent)
            
            if (drv.wire == parentDrv.wire):
                wirename = clkname
            else:
                wirename = getWireName(parent, drv.wire)
                
            str += link + ".{}({})".format(clkname, wirename)
            link = ","
        

        # get the wire names from the instantiator
        wireName = getWireNames(child.parent)
        
        for inp in child.inPorts:
            if (inp.wire is None):
                raise Exception('Input port {} from {} not connected to any wire'.format(inp.name, child.getFullPath()));
                
            if (not(inp.wire in wireName)):
                raise Exception('Input port wire {} not part of the wires of the parent {}'.format(inp.wire.getFullPath(), child.parent.getFullPath()))
                
            str += link +  "." + getPortName(inp) + "("+wireName[inp.wire]+")"
            link = ","

        for outp in child.outPorts:
            if (outp.wire is None):
                raise Exception('Output port {} from {} not connected to any wire'.format(outp.name, child.getFullPath()));

            if (not(outp.wire in wireName)):
                raise Exception('Output port wire {} not part of the wires of the parent {}'.format(outp.wire.getFullPath(), child.parent.getFullPath()))

            str += link + "." + getPortName(outp) + "("+wireName[outp.wire]+")"
 
            link = ","
        
        for outp in child.inOutPorts:
            if (outp.wire is None):
                raise Exception('Input/Output port {} from {} not connected to any wire'.format(outp.name, child.getFullPath()));

            if (not(outp.wire in wireName)):
                raise Exception('Input/Output port wire {} {} not part of the wires of the parent {}'.format(outp.wire.getFullPath(), outp.wire, child.parent.getFullPath()))

            str += link + "." + getPortName(outp) + "("+wireName[outp.wire]+")"
 
            link = ","
            
        str += ");\n"

        return str                
    
    
    def generateCodeFromClock(self, obj:Logic):
        str = "// Code generated from clock method\n"
        
        tr = Python2VerilogTranspiler(obj)
        
        node = tr.transpileSequential()
        str += tr.toVerilog(node)
        
        str = tr.format(str)
        
        return str

    def generateCodeFromPropagate(self, obj:Logic):
        str = "// Code generated from propagate method\n"
        
        tr = Python2VerilogTranspiler(obj)
        
        node = tr.transpileCombinational()
        str += tr.toVerilog(node)
        
        str = tr.format(str)
        
        return str
import inspect
import ast
import textwrap
    

def getAstValue(obj):
    if (isinstance(obj, ast.Constant)):
        return getAstValue(obj.value)
    elif (isinstance(obj, str)):
        return obj
    elif (isinstance(obj, int)):
        return obj
    if (isinstance(obj, ast.Name)):
        return obj.id
    else:
        print('DECODING VALUE:', type(obj))
        return obj
    
def getAstName(obj):
    if (isinstance(obj, ast.Name)):
        return obj.id
    elif (isinstance(obj, ast.Attribute)):
        return getAstName(obj.attr)
    elif (isinstance(obj, ast.Constant)):
        return obj.value
    elif (isinstance(obj, str)):
        return obj
    elif (isinstance(obj, list)):
        if (len(obj)>1):
            raise Exception('multiple names in {}'.format(obj))
        
        return getAstName(obj[0])
    else:
        raise Exception('unknown type {}'.format(type(obj)))

class VerilogComment(Logic):
    def __init__(self, parent, name: str, comment:str):
        super().__init__(parent, name)
        self.comment = comment
