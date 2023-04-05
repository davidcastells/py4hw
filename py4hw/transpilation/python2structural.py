# -*- coding: utf-8 -*-
"""
Created on Tue Apr  4 16:22:33 2023

@author: dcastel1
"""

import py4hw
from py4hw.base import *
from .astutils import * 

class Python2Structural:

    def __init__(self, obj:Logic, methodName:str):
        self.obj = obj
        self.methodName = methodName
        self.signals = {}
        self.indent = 0

    def generateStructural(self, instanceName):
        '''
        Transpile RTL style behavioural descriptions

        Returns
        -------
        str
            the equivalent RTL

        '''
        module = getMethod(self.obj, self.methodName)
    
        
        node = ReplaceBasic1().visit(module)        
        node = ReplaceBasic2().visit(node)        
        
        return HLSCircuit(self.obj.parent, instanceName, self.obj, node)
    
class HLSCircuit(py4hw.Logic):
    def __init__(self, parent, name, obj, node):
        super().__init__(parent, name)

        wires = {}
        wc = 0
        ic = 0
        
        # copy the reference circuit interface
        for inPort in obj.inPorts:
            ip = self.addIn(inPort.name, inPort.wire)
            wires[inPort.name] = ip
            
        for outPort in obj.outPorts:
            # @todo in the future we should disconnect behavioural and reuse
            # the wire, instead of creating a new wire
            
            ow = parent.wire('hls_'.format(outPort.name), outPort.wire.getWidth())
            op = self.addOut(outPort.name, ow)
            wires[outPort.name] = op
            
        for st in node.body:
            if (isinstance(st, RTLSynchronousAssignment)):
                left_reg = wires[st.left.name]
                right_reg = self.wire('w{}'.format(wc), left_reg.getWidth())
                wc += 1
                
                py4hw.Reg(self, 'i{}'.format(ic), d=right_reg, q=left_reg)
                ic += 1
                
                if (isinstance(st.right, RTLOperator)):
                    if (st.right.op == '+'):
                        left_add = wires[st.right.left.name]
                        right_add = wires[st.right.right.name]
                          
                        py4hw.Add(self, 'i{}'.format(ic), left_add, right_add, right_reg)
                        ic += 1
                    else:
                        raise Exception('operator {} not supported'.format(st.right.op))
                else:
                    raise Exception('right part type {} not supported'.format(st.right))
            else:
                raise Exception('statement {} not supported'.format(st))

class ReplaceBasic1(ast.NodeTransformer):
    
    def visit_Module(self, node):
        body = node.body[0].body
        body = RTLBody(body)
        node = ast.NodeTransformer.generic_visit(self, body)
        return node 
    
    
    def visit_Call(self, node):
        from py4hw.rtl_generation import getAstName

        attr = getAstName(node.func)
        
        print('checking call', attr)
        if (attr == 'get'):
            #if isinstance(node.func.value, ast.Attribute):
            wirename = getAstName(node.func.value)
            #print('REPLACING GET ', wirename)
            ret =  RTLWire(wirename)
        elif (attr == 'prepare'):
            left = RTLWire(node.func.value.attr)
            ret = RTLSynchronousAssignment(left, node.args[0])        
        else:
            raise Exception('Function {} not supported'.format(attr))
            
        ret = ast.NodeTransformer.generic_visit(self, ret)
        
        return ret

class ReplaceBasic2(ast.NodeTransformer):
    
    
    def visit_BinOp(self, node):
        #print('replacing BinOp')
        node =  RTLOperator(node.left, node.op, node.right)
        node = ast.NodeTransformer.generic_visit(self, node)
        return node

    def visit_Attribute(self, node):
        return RTLWire(node.attr)

    def visit_Expr(self, node):        
        ret = node.value
        ret = ast.NodeTransformer.generic_visit(self, ret)
        return ret
    


class RTLSynchronousAssignment(ast.AST):
    def __init__(self, left, right):
        self.left = left
        self.right = right
        self._fields = tuple(['left', 'right'])

class RTLBody(ast.AST):
    '''
    AST node to wrap body
    '''
    def __init__(self, body:list):
        self.body = body
        self._fields = tuple(['body', 'dummy'])

class RTLWire(ast.AST):
    '''
    AST node for Verilog Wires
    '''
    def __init__(self, name:str):
        self.name = name
        self._fields = tuple(['name', 'dummy'])

    def toVerilog(self):
        return self.name


class RTLOperator(ast.AST):
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
