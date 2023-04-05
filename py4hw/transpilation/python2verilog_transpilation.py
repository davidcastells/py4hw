# -*- coding: utf-8 -*-
"""
Created on Sun Apr  2 13:59:30 2023

@author: dcr
"""

from .. import *
from deprecated import deprecated

import ast
from .astutils import * 


def getBody(node):
    # the Module node contains a body, that contains a list, containting
    # a function definition with a body
    
    # AST visitors can not deal directly with list, we wrap them in 
    # a dummy verilog body object
    return VerilogBody(node.body[0].body)
    
class Python2VerilogTranspiler:

    def __init__(self, obj:Logic, methodName:str):
        self.obj = obj
        self.methodName = methodName
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
    
        node = getBody(module)
    
        assert(isinstance(node, ast.AST))
        
        node = ReplaceIf().visit(node)
        node = ReplaceWireGets().visit(node)
        node = ReplaceWirePrepare().visit(node)
        node = ReplaceWirePut().visit(node)
        node = ReplaceExpr().visit(node)
        node = ReplaceBinOp().visit(node)
        node = ReplaceAttribute().visit(node)
        node = ReplaceConstant().visit(node)
        node = ReplaceAssign().visit(node)
 
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

        if (isinstance(node, list)):
            str = ''
            for item in node:
                str += Python2VerilogTranspiler.toVerilog(item)
            return str
        
        toV = getattr(node, 'toVerilog')
        
        if (toV is None):
            print('No toVerilog for', type(node))
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
            str += "reg [7:0] " + sig + " = 0;\n" 
            
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
        str += self.getIndent() + "begin\n"
        self.indent += 1
        str += self.getIndent() + self.transpileUnknown(line.body)
        self.indent -= 1
        str +=  "end\n"
        
        if (not(line.orelse is None)):
            str += self.getIndent() + "else \n"
            str += self.getIndent() + "begin\n"
            self.indent += 1
            str += self.getIndent() + self.transpileUnknown(line.orelse)
            self.indent -= 1
            str +=  "end\n"

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
        

class ReplaceWireGets(ast.NodeTransformer):
        
    def visit_Call(self, node):
        from py4hw.rtl_generation import getAstName

        attr = getAstName(node.func)
        
        #print('checking call', attr)
        if (attr == 'get'):
            #if isinstance(node.func.value, ast.Attribute):
            wirename = getAstName(node.func.value)
            #print('REPLACING GET ', wirename)
            return VerilogWire(wirename)
        
        node = ast.NodeTransformer.generic_visit(self, node)
        
        return node
    
    
class ReplaceWirePrepare(ast.NodeTransformer):
    def visit_Call(self, node):
        from py4hw.rtl_generation import getAstName

        attr = getAstName(node.func)
        
        #print('checking call', attr)
        
        if (attr == 'prepare'):
            #print('REPLACE WIRE PUTS FUNC:', attr , node.func.value.attr, node.args)
            left = VerilogWire(node.func.value.attr)
            return VerilogSynchronousAssignment(left, node.args[0])
        
        node = ast.NodeTransformer.generic_visit(self, node)
        
        return node
    
class ReplaceWirePut(ast.NodeTransformer):
    def visit_Call(self, node):
        attr = getAstName(node.func)
        
        if (attr == 'put'):
            #print('REPLACE WIRE PUTS FUNC:', attr , node.func.value.attr, node.args)
            left = VerilogWire(node.func.value.attr)
            return VerilogAsynchronousAssignment(left, node.args[0])
        
        node = ast.NodeTransformer.generic_visit(self, node)
        
        return node

class ReplaceBinOp(ast.NodeTransformer):
    
    def visit_BinOp(self, node):
        #print('replacing BinOp')
        return VerilogOperator(node.left, node.op, node.right)

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

        
class VerilogAsynchronousAssignment(ast.AST):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def toVerilog(self):
        str = ''
        
        str += Python2VerilogTranspiler.toVerilog(self.left) + '='
        str += Python2VerilogTranspiler.toVerilog(self.right) + '\n'
        return str
        
class VerilogSynchronousAssignment(ast.AST):
    def __init__(self, left, right):
        self.left = left
        self.right = right
        self._fields = tuple(['left', 'right'])

    def toVerilog(self):
        str = ''
        
        str += Python2VerilogTranspiler.toVerilog(self.left) + '<='
        str += Python2VerilogTranspiler.toVerilog(self.right) + ';\n'
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
        elif (isinstance(operator, ast.Eq)):
            return '=='
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
        
class VerilogBody(ast.AST):
    '''
    AST node to wrap body
    '''
    def __init__(self, body:list):
        self.body = body
        self._fields = tuple(['body', 'dummy'])
    
    def toVerilog(self):
        str = ''
        for node in self.body:
            str += Python2VerilogTranspiler.toVerilog(node)
        return str
            
            
class VerilogIf(ast.AST):
    def __init__(self, condition, positive, negative):
        self.condition = condition
        self.positive = positive
        self.negative = negative
        self._fields = tuple(['condition', 'positive', 'negative'])
        
    def toVerilog(self):
        str = 'if (' + Python2VerilogTranspiler.toVerilog(self.condition) + ')\n'
        str += 'begin\n'
        str += Python2VerilogTranspiler.toVerilog(self.positive) + '\n'
        str += 'end\n'
        str += 'else\n'
        str += 'begin\n'
        str += Python2VerilogTranspiler.toVerilog(self.negative) + '\n'
        str += 'end\n'
        return str
    
class VerilogConstant(ast.AST):
    def __init__(self, value):
        self.value = value
        
    def toVerilog(self):
        return '{}'.format(self.value)