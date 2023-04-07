# -*- coding: utf-8 -*-
"""
Created on Thu Jan 20 18:42:23 2022

Copyright (C) 2023 Victor Suarez Rovere <suarezvictor@gmail.com>
Copyright (C) 2023 dcr

"""

from .base import *
from .logic import *
from .logic.bitwise import *
from .logic.storage import *
from .schematic_symbols import *
from .transpilation.python2cflexhdl_transpilation import *

def getVerilogModuleName(obj:Logic, noInstanceNumber=False):
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

def getCWidthInfo(w:Wire):
    ww = w.getWidth()
    if (ww > 1):
        return "uint{}".format(ww)
    else:
        return "bool"
    
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

def getWireNames(obj:Logic):
    """
    Collects the wires of the obj and their names in the
    its scope 

    Parameters
    ----------
    obj : Logic
        The logic circuit that we collect the wires from.

    Returns
    -------
        A dictionary keyed by wire objects returning their name
        in the obj scope
    """
    ret = {}
    
    # process all the wires connected to child instances
    for child in obj.children.values():
        for wire in collectPortWires(child):
            ret[wire]= "w_" + wire.name
 
    # overwrite the wires that are part of the interface
    for inp in obj.inPorts:
        ret[inp.wire]= getPortName(inp) 
        link = ","

    for outp in obj.outPorts:
        ret[outp.wire] = getPortName(outp) 
        
    return ret
    
def collectPortWires( obj:Logic):
    """
    Return the wires of the object interface

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
        if (not(inp.wire is None)):
            ret.append(inp.wire)

    for outp in obj.outPorts:
        if (not(outp.wire is None)):
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
    return wNames[w]

def getParentWireName(child:Logic, w:Wire):
    wNames = getWireNames(child.parent)
    return wNames[w]
    
def InlineConstant(obj:Logic):
    return "assign {} = {};\n".format(getParentWireName(obj, obj.r) + getWidthInfo(obj.r), obj.value)

def InlineNot(obj:Logic):
    return "assign {} = ~{};\n".format(getParentWireName(obj, obj.r), getParentWireName(obj, obj.a))

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
    str = "reg "+getWidthInfo(obj.q) + " rq = 0;\n"
    str += "always @(posedge {})\n".format(clkname)
    close = ""
    if not(obj.r is None):
        str += "if (r == 1)\n"
        str += "begin\n"
        str += "   rq <= 0;\n"
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
        self.inlinablePrimitives[Mul] = InlineMul
        self.inlinablePrimitives[And2] = InlineAnd2
        self.inlinablePrimitives[And] = InlineAnd
        self.inlinablePrimitives[Buf] = InlineBuf
        self.inlinablePrimitives[Bit] = InlineBit
        self.inlinablePrimitives[BitsLSBF] = InlineBitsLSBF
        self.inlinablePrimitives[BitsMSBF] = InlineBitsMSBF
        self.inlinablePrimitives[ConcatenateMSBF] = InlineConcatenateMSBF
        self.inlinablePrimitives[ConcatenateLSBF] = InlineConcatenateLSBF
        self.inlinablePrimitives[Constant] = InlineConstant
        self.inlinablePrimitives[Div] = InlineDiv
        self.inlinablePrimitives[Equal] = InlineEqual
        self.inlinablePrimitives[EqualConstant] = InlineEqualConstant
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
        
    def getVerilogForHierarchy(self, obj=None, noInstanceNumberInTopEntity=True):
        """
        Generates Verilog for all entities of the object hierarchy

        Returns
        -------
        None.

        """
        
        if (obj is None):
            obj = self.obj
        
        #print('generating {}'.format(obj.getFullPath()))
            
        str = self.getVerilog(obj, noInstanceNumber = noInstanceNumberInTopEntity)
        
        for child in obj.children.values():
            if (self.isInlinable(child)):
                #print('inlining {}'.format(child.name))
                pass
            else:
                # skip inlinable modules from verilog generation
                str += "\n"
                str += self.getVerilogForHierarchy(child, noInstanceNumberInTopEntity=False)

        return str        
        
    def getVerilog(self, obj=None, noInstanceNumber=False):
        str = "// This file was automatically created by py4hw RTL generator\n"
        
        if (obj is None):
            obj = self.obj
            
            
        str += self.createModuleHeader(obj, noInstanceNumber=noInstanceNumber)
        
        localWires = collectLocalWires(obj)
        wireNames = getWireNames(obj)
        
        for wire in localWires:
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
        
    def createModuleHeader(self, obj:Logic, noInstanceNumber=None):
        str = "module " + getVerilogModuleName(obj, noInstanceNumber=noInstanceNumber) + " (\n\t"

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
        
        try:
            ret = self.providingBody[type(obj)]
        except:
            return False
        
        return True

    def inlinePrimitive(self, obj:Logic):
        ret = self.inlinablePrimitives[type(obj)]
        return ret(obj)

    def provideBody(self, obj:Logic):
        ret = self.providingBody[type(obj)]
        return ret(obj)
        
    def createModuleInstances(self, obj:Logic):
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
        str = getVerilogModuleName(child) + " " +  getInstanceName(child)
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
            clkname = getObjectClockDriver(child).name
            str += link + ".{}({})".format(clkname, clkname)
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
        
        str += ");\n"

        return str                
    
    
    def generateCodeFromClock(self, obj:Logic):
        str = "// Code generated from clock method\n"
        clkname = getObjectClockDriver(obj).name
        
        tr = Python2VerilogTranspiler(obj, 'clock', 'posedge {}'.format(clkname))
        
        str += tr.transpileRTL() ;
        
        
        return str

    def generateCodeFromPropagate(self, obj:Logic):
        str = "// Code generated from propagate method\n"
        
        tr = Python2CflexHDLTranspiler(obj, 'propagate', '*')
        
        str += tr.transpileRTL()
        
        return str

class CflexHDLGenerator(VerilogGenerator):
    def __init__(self, obj:Logic):
        super().__init__(obj)

    def createModuleHeader(self, obj:Logic, noInstanceNumber=None):
        str = "MODULE " + getVerilogModuleName(obj, noInstanceNumber=noInstanceNumber) + " (\n\t"

        link = ""
        
        if (isinstance(obj, GatedClock)):
          pass
            
        reg = ""
        if ((obj.isClockable() or obj.isPropagatable()) and not(self.isProvidingBody(obj))):
            #reg = " reg "
            pass
        
        if (self.anyClockableDescendant(obj)):
            #clkname = getObjectClockDriver(obj).name
            #str += "const {}".format(clkname)
            #link = ",\n\t"
            pass
        
        for inp in obj.inPorts:
            str += link +  "const " + getCWidthInfo(inp.wire) + "& " + getPortName(inp)+ ""
            link = ",\n\t"

        for outp in obj.outPorts:
            str += link + reg + getCWidthInfo(outp.wire) + "& " + getPortName(outp)+ ""
            link = ",\n\t"
            
        str += ") {\n"
        
        return str

    def getVerilog(self, obj=None, noInstanceNumber=False):
        str = "// This CflexHDL file was automatically created by py4hw RTL generator\n"
        
        if (obj is None):
            obj = self.obj
            
            
        str += self.createModuleHeader(obj, noInstanceNumber=noInstanceNumber)
        
        localWires = collectLocalWires(obj)
        wireNames = getWireNames(obj)
        
        for wire in localWires:
            name = wireNames[wire]
            ww = wire.getWidth()
            if (ww > 1):
                str += "uint{} {};\n".format(ww-1, name)
            else:
                str += "bool {};\n".format(name)
                
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
        
        str += "}\n"
        
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