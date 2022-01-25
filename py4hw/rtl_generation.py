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

def getVerilogModuleName(obj:Logic):
    sid = hex(id(obj))
    str = type(obj).__name__ + "_" + sid[2:] 
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
    for child in obj.children:
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
        ret.append(inp.wire)

    for outp in obj.outPorts:
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
    
    for child in obj.children:
        
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

def InlineZeroExtend(obj:Logic):
    return "assign {} = {};\n".format(getParentWireName(obj, obj.r), getParentWireName(obj, obj.a))
    
def InlineAnd2(obj:Logic):
    return "assign {} = {} & {};\n".format(getParentWireName(obj, obj.r), getParentWireName(obj, obj.a) , getParentWireName(obj, obj.b))

def InlineNand2(obj:Logic):
    return "assign {} = ~({} & {});\n".format(getParentWireName(obj, obj.r), getParentWireName(obj, obj.a) , getParentWireName(obj, obj.b))

def InlineOr2(obj:Logic):
    return "assign {} = {} | {};\n".format(getParentWireName(obj, obj.r), getParentWireName(obj, obj.a) , getParentWireName(obj, obj.b))

def InlineXor2(obj:Logic):
    return "assign {} = {} ^ {};\n".format(getParentWireName(obj, obj.r), getParentWireName(obj, obj.a) , getParentWireName(obj, obj.b))

def InlineMux2(obj:Logic):
    return "assign {} = ({})? {} : {};\n".format(getParentWireName(obj, obj.r), getParentWireName(obj, obj.sel), getParentWireName(obj, obj.sel1) , getParentWireName(obj, obj.sel0))

def InlineAdd(obj:Logic):
    return "assign {} = {} + {};\n".format(getParentWireName(obj, obj.r), getParentWireName(obj, obj.a) , getParentWireName(obj, obj.b))

def InlineSub(obj:Logic):
    return "assign {} = {} - {};\n".format(getParentWireName(obj, obj.r), getParentWireName(obj, obj.a) , getParentWireName(obj, obj.b))

def InlineEqualConstant(obj:Logic):
    return "assign {} = ({} == {})? 1 : 0;\n".format(getParentWireName(obj, obj.r), getParentWireName(obj, obj.a), obj.v )

def InlineBits(obj:Logic):
    str = ""
    for i in range(len(obj.bits)):
        str += "assign {} = {}[{}];\n".format(getParentWireName(obj, obj.bits[i]), getParentWireName(obj, obj.a), i)
        
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

def BodyReg(obj:Logic):
    str = "reg "+getWidthInfo(obj.q) + " rq = 0;\n"
    str += "always @(posedge clk)\n"
    str +=  "if (e == 1)\n"
    str += "begin\n"
    str += "   rq <= d;\n"
    str += "end\n"
    str += "assign q = rq;\n"
    return str

class VerilogGenerator:
    
    
    def __init__(self, obj:Logic):
        #print('Testing Verilog Generation')
        self.obj = obj
        
        self.inlinablePrimitives = {}
        
        self.inlinablePrimitives[Add] = InlineAdd
        self.inlinablePrimitives[And2] = InlineAnd2
        self.inlinablePrimitives[And] = InlineAnd
        self.inlinablePrimitives[Buf] = InlineBuf
        self.inlinablePrimitives[ZeroExtend] = InlineZeroExtend
        self.inlinablePrimitives[Constant] = InlineConstant
        self.inlinablePrimitives[Equal] = InlineEqual
        self.inlinablePrimitives[EqualConstant] = InlineEqualConstant
        self.inlinablePrimitives[Not] = InlineNot
        self.inlinablePrimitives[Nor] = InlineNor
        self.inlinablePrimitives[Nand2] = InlineNand2
        self.inlinablePrimitives[Or2] = InlineOr2
        self.inlinablePrimitives[Or] = InlineOr
        self.inlinablePrimitives[Mux2] = InlineMux2
        self.inlinablePrimitives[Sub] = InlineSub
        self.inlinablePrimitives[Bits] = InlineBits
        self.inlinablePrimitives[Xor2] = InlineXor2
        
        self.providingBody = {}
        
        self.providingBody[Reg] = BodyReg 
        
    def getVerilogForHierarchy(self, obj=None):
        """
        Generates Verilog for all entities of the object hierarchy

        Returns
        -------
        None.

        """
        if (obj is None):
            obj = self.obj
            
        str = self.getVerilog(obj)
        
        for child in obj.children:
            if (not(self.isInlinable(child))):
                # skip inlinable modules from verilog generation
                str += "\n"
                str += self.getVerilogForHierarchy(child)

        return str        
        
    def getVerilog(self, obj=None):
        str = "// This file was automatically created by py4hw RTL generator\n"
        
        if (obj is None):
            obj = self.obj
            
            
        str += self.createModuleHeader(obj)
        
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
            pass
        elif (obj.isClockable()):
            #generate code from clock function
            if (self.isProvidingBody(obj)):
                str += self.provideBody(obj);
            else:
                str += self.generateCodeFromClock(obj)
            pass
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
        
        for child in obj.children:
            if (self.anyClockableDescendant(child)):
                return True
            
        return False
        
    def createModuleHeader(self, obj:Logic):
        str = "module " + getVerilogModuleName(obj) + " (\n\t"
        
        reg = ""
        if (obj.isClockable() and not(self.isProvidingBody(obj))):
            reg = " reg "
        
        link = ""
        
        if (self.anyClockableDescendant(obj)):
            str += "input clk"
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
        
        for child in obj.children:
            
            if (self.isInlinable(child)):
                str += self.inlinePrimitive(child)
            else:
                str += self.instantiateStructural(child)

        return str;

    def instantiateStructural(self, child:Logic):
        str = getVerilogModuleName(child) + " " +  getInstanceName(child)
        str += "("
        link = ""
        
        # Clock is an implicit parameter
        if (self.anyClockableDescendant(child)):
            str += link + ".clk(clk)"
            link = ","
        
        # get the wire names from the instantiator
        wireName = getWireNames(child.parent)
        
        for inp in child.inPorts:
            
            str += link +  "." + getPortName(inp) + "("+wireName[inp.wire]+")"
            link = ","

        for outp in child.outPorts:
            str += link + "." + getPortName(outp) + "("+wireName[outp.wire]+")"
 
            link = ","
        
        str += ");\n"

        return str                
    
    
    def generateCodeFromClock(self, obj:Logic):
        str = "// Code generated from clock method\n"
        
        tr = Python2VerilogTranspiler(obj, 'clock')
        
        transpiled = tr.transpile() ;
        
        str += "// local declarations\n"
        str += tr.getExtraDeclarations() + "\n";
        str += "// sequential process\n"
        str += "always @(posedge clk)\n"
        str += "begin\n"
        str += transpiled + "\n"
        str += "end\n"
        
        str += "\n"
        
        return str

import inspect
import ast
import textwrap
    
class Python2VerilogTranspiler:

    def __init__(self, obj:Logic, methodName:str):
        self.obj = obj
        self.methodName = methodName
        self.signals = {}
        
    def transpile(self):
        
        methods = inspect.getmembers(self.obj, inspect.ismethod)
        method = [x[1] for x in methods if x[0] == self.methodName ][0]

        source = textwrap.dedent(inspect.getsource(method))
        module = ast.parse(source)

        
        module = ReplaceWireGets().visit(module)
        module = ReplaceWirePrepare().visit(module)
        
        func = module.body[0].body
        
        return self.transpileUnknown(func)
        
    def getExtraDeclarations(self):
        str = ""
        
        portNames = []
        
        
        for inp in self.obj.inPorts:
            portNames.append(getValidVerilogName(inp.name))

        for outp in self.obj.outPorts:
            portNames.append(getValidVerilogName(outp.name))        
        
        #print('SIGNALS:', self.signals)
        #print('PORT NAMES:', portNames)

        extra = [x for x in self.signals if x not in portNames]
        
        for sig in extra:
            str += "reg " + sig + " = 0;" 
            
        return str
    
    def transpileUnknown(self, line):
        
        if (type(line) == ast.If):
            return self.transpileIf(line);
        if (type(line) == ast.Compare):
            return self.transpileCompare(line)
        if (type(line) == ast.Assign):
            return self.transpileAssign(line)
        if (type(line) == ast.Attribute):
            return self.transpileAttribute(line)
        if (isinstance(line, ast.Name)):
            return self.transpileName(line)
        if (type(line) == ast.Eq):
            return "==";
        if (type(line) == ast.Num):
            return "{}".format(int(line.n))
        
        if (type(line) == list):
            str = ""
            for item in line:
                str += self.transpileUnknown(item) 
            return str

        if (type(line) == ast.Expr):
            return self.transpileExpr(line)
        
        else:
            str= "type = {}\n".format(type(line))
            
            str += ast.dump(line) + "\n"
            
            return str
        
    def transpileAttribute(self, line:ast.Attribute):
        return line.attr
            
    def transpileExpr(self, line:ast.Expr):
        return self.transpileUnknown(line.value)
        
    def transpileAssign(self, line:ast.Assign):
        targets = line.targets 
        if (len(targets) > 1):
            return ast.dump(line)
        
        target:ast.Attribute = targets[0]
        
        var = target.attr
        
        self.signals[var] = var
        
        return var + " <= " + self.transpileUnknown(line.value) + ";\n";
    
    def transpileIf(self, line:ast.If):
        str = "if " + self.transpileUnknown(line.test) + "\n"
        str += "begin\n"
        str += self.transpileUnknown(line.body)
        str += "end\n"
        
        if (not(line.orelse is None)):
            str += "else \n"
            str += "begin\n"
            str += self.transpileUnknown(line.orelse)
            str += "end\n"
        return str
    
    def transpileCompare(self, line:ast.Compare):
        str = "("
        str += self.transpileUnknown(line.left)
        str += self.transpileUnknown(line.ops)
        str += self.transpileUnknown(line.comparators)
        str += ")"
        return str;
    
    def transpileName(self, line:ast.Name):
        str =  getValidVerilogName(line.id)
        self.signals[str] = str
        return str
    
    
    
class ReplaceWireGets(ast.NodeTransformer):
    def visit_Call(self, node):
        attr = node.func.attr
        
        if (attr == 'get'):
            if isinstance(node.func.value, ast.Attribute):
                wirename = node.func.value.attr
                #print('REPLACING GET ', wirename)
                return ast.Name(wirename, ast.Load)
        
        return node
    
class ReplaceWirePrepare(ast.NodeTransformer):
    def visit_Call(self, node):
        attr = node.func.attr
        
        if (attr == 'prepare'):
            #print('REPLACE WIRE PUTS FUNC:', attr , node.func.value.attr, node.args)
            return ast.Assign([node.func.value], node.args[0])
        
        
        return node