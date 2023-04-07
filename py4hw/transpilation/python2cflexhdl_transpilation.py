# -*- coding: utf-8 -*-
"""
Created on Sun Apr  2 13:59:30 2023


Copyright (C) 2023 dcr
Copyright (C) 2023 Victor Suarez Rovere <suarezvictor@gmail.com>
"""

from .. import *
from deprecated import deprecated

import ast
from .astutils import * 


def getBody(node, slist):
    # the Module node contains a body, that contains a list, containting
    # a function definition with a body
    
    # AST visitors can not deal directly with list, we wrap them in 
    # a dummy verilog body object
    var = VerilogWireDeclarations()
    process = VerilogProcess(node.body[0].body, slist)
    return VerilogBody(var, process)
    
class Python2VerilogTranspiler:

    def __init__(self, obj:Logic, methodName:str, slist:str):
        self.obj = obj
        self.methodName = methodName
        self.slist = slist
        self.signals = {}
        self.indent = 0

    def getIndent(self):
        return ' ' * (self.indent * 4)


    def transpileRTL(self):
        '''
        Transpile RTL style behavioural descriptions

        Returns
        -------
        str
            the equivalent RTL

        '''
        module = getMethod(self.obj, self.methodName)
    
        node = getBody(module, self.slist)
    
        assert(isinstance(node, ast.AST))
        
        node = ReplaceIf().visit(node)
        node = ReplaceWireCalls().visit(node)
        node = ReplaceExpr().visit(node)
        node = ReplaceBinOp().visit(node)
        node = ReplaceAttribute().visit(node)
        node = ReplaceConstant().visit(node)
        node = ReplaceAssign().visit(node)
 
        node = FlattenOperators().visit(node)

        return Python2VerilogTranspiler.toVerilog(node)
        #return self.transpileUnknown(node)
        
    @staticmethod
    def toVerilog(node):
        '''
        Tranlates to Verilog a node by calling its toVerilog method
        For lists, in invokes the same method to the elements of the list

        Parameters
        ----------
        node : TYPE
            DESCRIPTION.

        Returns
        -------
        toV : TYPE
            DESCRIPTION.

        '''
        # print('transpiling', type(node))
        if (isinstance(node, ast.Name)): #FIXME: move code
            return node.id

        if (isinstance(node, ast.IfExp)): #FIXME: move code
            test = Python2VerilogTranspiler.toVerilog(node.test)
            body = Python2VerilogTranspiler.toVerilog(node.body)
            orelse = Python2VerilogTranspiler.toVerilog(node.orelse)
            return test + " ? " + body + " : " + orelse;

        if (isinstance(node, list)):
            str = ''
            for item in node:
                str += Python2VerilogTranspiler.toVerilog(item)
            return str
        
        toV = getattr(node, 'toVerilog', None)
        
        if (toV is None):
            return '/*No toVerilog for {}*/'.format(type(node))
        else:
            return toV()
    
    def getExtraDeclarations(self):
        from py4hw.rtl_generation import getValidVerilogName

        str = ""
        
        portNames = []
        
        
        for inp in self.obj.inPorts:
            portNames.append(getValidVerilogName(inp.name))

        for outp in self.obj.outPorts:
            portNames.append(getValidVerilogName(outp.name))        
        
        #print('SIGNALS:', self.signals)
        #print('PORT NAMES:', portNames)

        extra = [x for x in self.signals if x not in portNames]
        
        # @todo we should analyze the number of possible values of 
        # extra signals to decide their width. By now we consider a worst
        # case scenario with extra signals all requiring a maximum of 8 bits
        # this will be simplyfied during synthesis if less bits are required
        # but it will cause a BUG if the required bits are higher
        for sig in extra:
            str += "uint8_t " + sig + " = 0;\n" 
            
        return str
    
    def transpileUnknown(self, line):
        # @deprecated use toVerilog
        if (type(line) == ast.If):
            return self.transpileIf(line);
        if (type(line) == ast.Compare):
            return self.transpileCompare(line)
        if (type(line) == ast.Assign):
            return self.transpileAssign(line)
        if (type(line) == ast.BinOp):
            return self.transpileBinOp(line)
        if (type(line) == ast.Attribute):
            return self.transpileAttribute(line)
        if (isinstance(line, ast.Name)):
            return self.transpileName(line)
        if (type(line) == ast.Eq):
            return "==";
        if (type(line) == ast.Constant):
            return "{}".format(getAstValue(line))
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
        
    # @deprecated
    def transpileAttribute(self, line:ast.Attribute):
        return line.attr
            
    # @deprecated
    def transpileExpr(self, line:ast.Expr):
        return self.transpileUnknown(line.value)
        
    # @deprecated
    def transpileBinOp(self, line:ast.BinOp):
        return "(" + self.transpileUnknown(line.left) + self.transpileOp(line.op) + self.transpileUnknown(line.right) + ")";

    # @deprecated
    def transpileOp(self, op):
        if (isinstance(op, ast.BitAnd)):
            return '&'
        elif (isinstance(op, ast.BitOr)):
            return '|'
        elif (isinstance(op, ast.BitXor)):
            return '^'
        else:
            raise Exception('Op not supported: {}'.format(op))
        
    # @deprecated
    def transpileAssign(self, line:ast.Assign):
        raise Exception('deprecated')
        # targets = line.targets 
        # if (len(targets) > 1):
        #     return ast.dump(line)
        
        # var = getAstName(targets[0])
        
        # self.signals[var] = var
        
        # return var + " <= " + self.transpileUnknown(line.value) + ";\n" + self.getIndent()  ;
    
    # @deprecated
    def transpileIf(self, line:ast.If):
        str = "if " + self.transpileUnknown(line.test) + "\n"
        str += self.getIndent() + "{\n"
        self.indent += 1
        str += self.getIndent() + self.transpileUnknown(line.body)
        self.indent -= 1
        str +=  "}\n"
        
        if (not(line.orelse is None)):
            str += self.getIndent() + "else \n"
            str += self.getIndent() + "{\n"
            self.indent += 1
            str += self.getIndent() + self.transpileUnknown(line.orelse)
            self.indent -= 1
            str +=  "}\n"

        return str
    
    # @deprecated
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
    
    
    
class ReplaceIf(ast.NodeTransformer):
        
    def visit_If(self, node):
        #print('transpiling if')
        condition = node.test
        
        positive = node.body
        negative = node.orelse
        
        node2 = VerilogIf(condition, positive, negative)

        node2 = ast.NodeTransformer.generic_visit(self, node2)
        return node2
        

class ReplaceWireCalls(ast.NodeTransformer):
        
    def visit_Call(self, node):
        from py4hw.rtl_generation import getAstName

        attr = getAstName(node.func)
        
        #print('checking call', attr)
        if (attr == 'get'):
            #if isinstance(node.func.value, ast.Attribute):
            wirename = getAstName(node.func.value)
            #print('REPLACING GET ', wirename)
            return VerilogWire(wirename)
        
        elif (attr == 'prepare'):
            #print('REPLACE WIRE PUTS FUNC:', attr , node.func.value.attr, node.args)
            left = VerilogWire(node.func.value.attr)
            node = VerilogSynchronousAssignment(left, node.args[0])
        
        elif (attr == 'put'):
            #print('REPLACE WIRE PUTS FUNC:', attr , node.func.value.attr, node.args)
            left = VerilogWire(node.func.value.attr)
            right = ast.NodeTransformer.generic_visit(self, node.args[0])
            node = VerilogAsynchronousAssignment(left, right)
        else:
            print('WARNING: unhandled call {}'.format(attr))
                 
        node = ast.NodeTransformer.generic_visit(self, node)
        
        return node
    
    

class ReplaceBinOp(ast.NodeTransformer):
    
    def visit_BinOp(self, node):
        #print('replacing BinOp')
        node =  VerilogOperator(node.left, node.op, node.right)
        node = ast.NodeTransformer.generic_visit(self, node)
        return node

    def visit_Compare(self, node):
        return VerilogOperator(node.left, node.ops, node.comparators)    
    
class ReplaceExpr(ast.NodeTransformer):
    def visit_Expr(self, node):
        
        return node.value

class ReplaceAttribute(ast.NodeTransformer):
    def visit_Attribute(self, node):
        return VerilogWire(node.attr)
    
class ReplaceConstant(ast.NodeTransformer):
    def visit_Constant(self, node):
        return VerilogConstant(node.value)
    
class ReplaceAssign(ast.NodeTransformer):
    def visit_Assign(self, node):
        if (len(node.targets) > 1):
            raise Exception('{} targets! only 1 is supported'.format(len(node.targets)))
            
        left = node.targets[0]
        right = node.value
        
        return VerilogSynchronousAssignment(left, right)
    
    def visit_AugAssign(self, node):
        left = node.target
        right = node.value
        
        newvalue = VerilogOperator(left, node.op, right)
        return VerilogSynchronousAssignment(left, newvalue)

class FlattenOperators(ast.NodeTransformer):
    # If recursive operators are found they are extracted, new wires
    # are created and the structure is flattened
    ic = -1

    def loop_visit(self, node):
        self.anyChange = True
        
        while (self.anyChange):
            self.anyChange = False
            node = self.visit(node)
            
        return node
            
    def visit_VerilogBody(self, node):
        self.top = node
        return ast.NodeTransformer.generic_visit(self, node)
    
    def newName(self):
        self.ic += 1
        return 'i{}'.format(self.ic)
    
    def visit_VerilogAsynchronousAssignment(self, node):
        self.sync = False
        return ast.NodeTransformer.generic_visit(self, node)

    def visit_VerilogSynchronousAssignment(self, node):
        self.sync = True
        return ast.NodeTransformer.generic_visit(self, node)
        
    def visit_VerilogOperator(self, node):
        if (isinstance(node.left, VerilogOperator)):
            #print('we should extract left operator')
            wn = self.newName()
            vwd = VerilogWireDeclaration(wn)
            vw = VerilogWire(wn)
            self.top.wires.wires.append(vwd)
            
            if (self.sync):
                assign = VerilogSynchronousAssignment(vw, node.left)
            else:
                assign = VerilogAsynchronousAssignment(vw, node.left)
                
            self.top.process.body.append(assign)
            node.left = vw
            self.anyChange = True 
            
        if (isinstance(node.right, VerilogOperator)):
            #print('we should extract right operator')
            wn = self.newName()
            vwd = VerilogWireDeclaration(wn)
            vw = VerilogWire(wn)
            self.top.wires.wires.append(vwd)
            
            if (self.sync):
                assign = VerilogSynchronousAssignment(vw, node.right)
            else:
                assign = VerilogAsynchronousAssignment(vw, node.right)
                
            self.top.process.body.append(assign)
            node.right = vw
            self.anyChange = True
            
        return node

        
class VerilogAsynchronousAssignment(ast.AST):
    def __init__(self, left, right):
        self.left = left
        self.right = right
        self._fields = tuple(['left', 'right'])

    def toVerilog(self):
        str = ''
        
        str += Python2VerilogTranspiler.toVerilog(self.left) + ' = '
        str += Python2VerilogTranspiler.toVerilog(self.right) + '; // async\n'
        return str
        
class VerilogSynchronousAssignment(ast.AST):
    def __init__(self, left, right):
        self.left = left
        self.right = right
        self._fields = tuple(['left', 'right'])

    def toVerilog(self):
        str = ''
        
        str += Python2VerilogTranspiler.toVerilog(self.left) + ' = '
        str += Python2VerilogTranspiler.toVerilog(self.right) + '; // sync\n'
        return str

class VerilogOperator(ast.AST):
    def __init__(self, left, op, right):
        if (isinstance(op, list)):
            # we only support single operators
            assert(len(op) == 1)
            op = op[0]
            
        self.left = left
        self.op = self.getOp(op)
        self.right = right
        self._fields = tuple(['left', 'op', 'right'])

    def getOp(self, operator):
        # translated an AST operator into verilog syntax
        if (isinstance(operator, ast.Add)):
            return '+'
        elif (isinstance(operator, ast.BitAnd)):
            return '&'
        elif (isinstance(operator, ast.BitOr)):
            return '|'
        elif (isinstance(operator, ast.BitXor)):
            return '^'
        elif (isinstance(operator, ast.Eq)):
            return '=='
        elif (isinstance(operator, ast.FloorDiv)):
            return '/'
        elif (isinstance(operator, ast.Mult)):
            return '*'
        elif (isinstance(operator, ast.RShift)):
            return '>>'
        elif (isinstance(operator, ast.Lt)):
            return '<'
        elif (isinstance(operator, ast.GtE)):
            return '>='
        else:
            raise Exception('operator {} not supported'.format(type(operator)))
            
    def toVerilog(self):
        str = ''
        
        str += Python2VerilogTranspiler.toVerilog(self.left) 
        str += self.op
        str += Python2VerilogTranspiler.toVerilog(self.right)
        return str


class VerilogWire(ast.AST):
    '''
    AST node for Verilog Wires
    '''
    def __init__(self, name:str):
        self.name = name
        self._fields = tuple(['name', 'dummy'])

    def toVerilog(self):
        return self.name

class VerilogWireDeclaration(ast.AST):
    '''
    AST node for Verilog Wires
    '''
    def __init__(self, name:str):
        self.name = name
        self._fields = tuple(['name', 'dummy'])

    def toVerilog(self):
        return 'int ' + self.name + ';\n'


class VerilogWireDeclarations(ast.AST):
    # wire declaration section at the beginning of the module
    def __init__(self):
        self.wires = []
        self._fields = tuple(['wires', 'dummy'])
        
    def toVerilog(self):
        str = ''
        
        for w in self.wires:
            str += Python2VerilogTranspiler.toVerilog(w)
            
        return str    

class VerilogProcess(ast.AST):
    def __init__(self, body, sensitivity):
        self.body = body
        self.sensitivity_list = sensitivity
        self._fields = tuple(['body', 'sensitivity_list'])
        
    def toVerilog(self):
        str = 'while(always())\n'.format(self.sensitivity_list)
        str += '{\n'
        
        for st in self.body:
            str += Python2VerilogTranspiler.toVerilog(st) 

        str += '}\n'            
        return str            
    
class VerilogBody(ast.AST):
    '''
    AST node to wrap body
    '''
    def __init__(self, wires, process):
        self.wires = wires
        self.process = process
        self._fields = tuple(['wires', 'process'])
    
    def toVerilog(self):
        str = ''
        
        str += '// variable declaration \n'
        str += Python2VerilogTranspiler.toVerilog(self.wires)

        str += '// process \n'
        str += Python2VerilogTranspiler.toVerilog(self.process)
        return str
            
            
class VerilogIf(ast.AST):
    def __init__(self, condition, positive, negative):
        self.condition = condition
        self.positive = positive
        self.negative = negative
        self._fields = tuple(['condition', 'positive', 'negative'])
        
    def toVerilog(self):
        str = 'if (' + Python2VerilogTranspiler.toVerilog(self.condition) + ')\n'
        str += '{\n'
        str += Python2VerilogTranspiler.toVerilog(self.positive) + '\n'
        if self.negative:
            str += '} else {\n'
            str += Python2VerilogTranspiler.toVerilog(self.negative) + '\n'
        str += '}\n'
        return str
    
class VerilogConstant(ast.AST):
    def __init__(self, value):
        self.value = value
        
    def toVerilog(self):
        return '{}'.format(self.value)