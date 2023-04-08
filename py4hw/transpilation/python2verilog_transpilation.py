# -*- coding: utf-8 -*-
"""
Created on Sun Apr  2 13:59:30 2023

@author: dcr
"""

from .. import *
from deprecated import deprecated

import ast
from .astutils import * 


def getBody(node, slist=''):
    # the Module node contains a body, that contains a list, containting
    # a function definition with a body
    
    # AST visitors can not deal directly with list, we wrap them in 
    # a dummy verilog body object
    var = VerilogDeclarations()
    init = VerilogInitial()
    process = VerilogProcess(node.body[0].body, slist)
    return VerilogBody(var, init, process)
    
class Python2VerilogTranspiler:

    def __init__(self, obj:Logic):
        self.obj = obj
        self.signals = {}
        self.indent = 0

    def getIndent(self):
        return ' ' * (self.indent * 4)


    def transpileCombinational(self):
        '''
        Transpile RTL style behavioural descriptions

        Returns
        -------
        str
            the equivalent RTL

        '''
        module = getMethod(self.obj, 'propagate')
    
        node = getBody(module, '*')
    
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

    def transpileSequential(self):
        '''
        Transpile RTL style behavioural descriptions

        Returns
        -------
        str
            the equivalent RTL

        '''
        # start analyzing the constructor to get wires and variables
        module = getMethod(self.obj, '__init__')
        node = getBody(module)
        
        initExtracter = ExtractInitializers()
        init = initExtracter.visit(node)
        
        module = getMethod(self.obj, 'clock')
        clkname = getObjectClockDriver(self.obj).name

        node = getBody(module, 'posedge {}'.format(clkname))
        node.init.body = init.init.body
    
        assert(isinstance(node, ast.AST))
        
        node = ReplaceIf().visit(node)
        node = ReplaceWireCalls().visit(node)
        node = ReplaceExpr().visit(node)
        node = ReplaceBinOp().visit(node)
        
        wiresAndVars = ReplaceWiresAndVariables(initExtracter.ports, initExtracter.variables)
        node = wiresAndVars.visit(node)
        node = ReplaceConstant().visit(node)
        node = ReplaceAssign().visit(node)
        node = ReplaceIfExp().visit(node)
        
        node.wires.variables = wiresAndVars.variables.values();
        #node = FlattenOperators().visit(node)

        print('variables', node.wires.variables)
        
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
    
    @deprecated
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

class ReplaceIfExp(ast.NodeTransformer):
    def visit_IfExp(self, node):
        cond = ast.NodeTransformer.generic_visit(self, node.test)
        positive = ast.NodeTransformer.generic_visit(self, node.body)
        negative = ast.NodeTransformer.generic_visit(self, node.orelse)
        return VerilogTernaryConditionalOperator(cond, positive, negative)
        

class ReplaceWiresAndVariables(ast.NodeTransformer):
    def __init__(self, ports, variables):
        self.ports = ports
        self.variables = variables
        
    def visit_Name(self, node):
        name = node.id
        if (name in self.ports.keys()):
            return VerilogWire(name)

        if (name in self.variables.keys()):
            return VerilogVariable(name, self.variables[name].type)

        # create new variable
        self.variables[name] = VerilogVariableDeclaration(name, 'integer')
        return VerilogVariable(name, 'integer')

    def visit_Attribute(self, node):
        name = node.attr
        if (name in self.ports.keys()):
            return VerilogWire(name)

        if (name in self.variables.keys()):
            return VerilogVariable(name, self.variables[name].type)

        # create new variable
        self.variables[name] = VerilogVariableDeclaration(name, 'integer')
        return VerilogVariable(name, 'integer')
    
class ReplaceConstant(ast.NodeTransformer):
    def visit_Constant(self, node):
        return VerilogConstant(node.value)
    
    def visit_Num(self, node):
        return VerilogConstant(node.n)
    
class ReplaceAssign(ast.NodeTransformer):
            
    def visit_Assign(self, node):
        if (len(node.targets) > 1):
            raise Exception('{} targets! only 1 is supported'.format(len(node.targets)))
            
        left = ast.NodeTransformer.generic_visit(self, node.targets[0])
        right = ast.NodeTransformer.generic_visit(self, node.value)
            
        if (isinstance(left, VerilogVariable)):
            node = VerilogVariableAssignment(left, right)
        else:
            node =  VerilogSynchronousAssignment(left, right)
        
        return node
    
    def visit_AugAssign(self, node):
        left = node.target
        right = node.value
        
        newvalue = VerilogOperator(left, node.op, right)
        if (isinstance(left, VerilogVariable)):
            node = VerilogVariableAssignment(left, newvalue)
        else:
            node = VerilogSynchronousAssignment(left, newvalue)
        
        return node

class ExtractInitializers(ast.NodeTransformer):
    ports = {}
    variables = {}
    
    # Extracts initializers from class constructor
    def visit_Constant(self, node):
        return VerilogConstant(node.value)
    
    def visit_Num(self, node):
        return VerilogConstant(node.n)

    def visit_VerilogBody(self, node):
        self.top = node
        return ast.NodeTransformer.generic_visit(self, node)
    
    def visit_Assign(self, node):
        from py4hw.rtl_generation import getAstName

        if (isinstance(node.value, ast.Call)):
            fname = getAstName(node.value.func)
            pname = ''
            
            if (fname == 'addIn'):
                pname = node.targets[0].attr
                print('in port', pname)
            elif (fname == 'addOut'):
                node.targets[0].attr
                print('out port', node.targets[0].attr)
            else:
                print('not expected', fname)

            w = VerilogWire(pname)
            self.ports[pname] = w        
            self.top.wires.wires.append(w)
            return None
        
        elif (isinstance(node.value, ast.Num)):
            vname = node.targets[0].attr
            var = VerilogVariable(vname, type(node.value.n))
            self.top.wires.variables.append(var)
            node = VerilogVariableAssignment(var, node.value)
            node = ast.NodeTransformer.generic_visit(self, node)
            self.top.init.body.append(node)

            # save variable
            self.variables[vname] = VerilogVariableDeclaration(vname, 'integer')
            return None
        
        else:
            raise Exception('not handled')
        
        return node
                
    def visit_Call(self, node):
        from py4hw.rtl_generation import getAstName

        attr = getAstName(node.func)
        
        print('checking call', attr)
        if (attr == '__init__'):
            return None
        
        return node

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


class VerilogVariableAssignment(ast.AST):
    def __init__(self, left, right):
        self.left = left
        self.right = right
        self._fields = tuple(['left', 'right'])

    def toVerilog(self):
        str = ''
        
        str += Python2VerilogTranspiler.toVerilog(self.left) + '='
        str += Python2VerilogTranspiler.toVerilog(self.right) + ';\n'
        return str
        
class VerilogAsynchronousAssignment(ast.AST):
    def __init__(self, left, right):
        self.left = left
        self.right = right
        self._fields = tuple(['left', 'right'])

    def toVerilog(self):
        str = ''
        
        str += Python2VerilogTranspiler.toVerilog(self.left) + '<='
        str += Python2VerilogTranspiler.toVerilog(self.right) + ';\n'
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
        # ARITHMETIC
        if (isinstance(operator, ast.Add)):
            return '+'
        elif (isinstance(operator, ast.Mult)):
            return '*'
        elif (isinstance(operator, ast.FloorDiv)):
            return '/'
        # BITWISE
        elif (isinstance(operator, ast.BitAnd)):
            return '&'
        elif (isinstance(operator, ast.BitOr)):
            return '|'
        elif (isinstance(operator, ast.BitXor)):
            return '^'
        elif (isinstance(operator, ast.RShift)):
            return '>>'
        # RELATIONAL
        elif (isinstance(operator, ast.Eq)):
            return '=='
        elif (isinstance(operator, ast.Lt)):
            return '<'        
        elif (isinstance(operator, ast.GtE)):
            return '>='        
        else:
            raise Exception('operator {} not supported'.format(type(operator)))
            
    def toVerilog(self):
        str = ''
        
        if (isinstance(self.left, VerilogOperator)):
            str += '(' + Python2VerilogTranspiler.toVerilog(self.left)  + ')'
        else:
            str += Python2VerilogTranspiler.toVerilog(self.left) 
            
        str += self.op

        if (isinstance(self.right, VerilogOperator)):
            str += '(' + Python2VerilogTranspiler.toVerilog(self.right) + ')'
        else:
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

class VerilogVariable(ast.AST):
    '''
    AST node for Verilog Wires
    '''
    def __init__(self, name:str, type:str):
        self.name = name
        self.type = type
        self._fields = tuple(['name', 'type'])

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
        return 'reg ' + self.name + ';\n'


class VerilogVariableDeclaration(ast.AST):
    '''
    AST node for Verilog Wires
    '''
    def __init__(self, name:str, vartype:str):
        self.name = name
        self.type = vartype
        self._fields = tuple(['name', 'type'])

    def toVerilog(self):
        return '{} {};\n'.format(self.type, self.name )


class VerilogDeclarations(ast.AST):
    # wire declaration section at the beginning of the module
    def __init__(self):
        self.wires = []
        self.variables = []
        self._fields = tuple(['wires', 'variables'])
        
    def toVerilog(self):
        str = ''
        
        for w in self.wires:
            str += Python2VerilogTranspiler.toVerilog(w)

        for v in self.variables:
            str += Python2VerilogTranspiler.toVerilog(v)
            
        return str    

class VerilogInitial(ast.AST):
    def __init__(self):
        self.body = []
        self._fields = tuple(['body', 'dummy'])
        
    def toVerilog(self):
        str = 'initial\n'
        str += 'begin\n'
        
        for st in self.body:
            str += Python2VerilogTranspiler.toVerilog(st) 

        str += 'end\n'            
        return str            

class VerilogProcess(ast.AST):
    def __init__(self, body, sensitivity):
        self.body = body
        self.sensitivity_list = sensitivity
        self._fields = tuple(['body', 'sensitivity_list'])
        
    def toVerilog(self):
        str = 'always @({})\n'.format(self.sensitivity_list)
        str += 'begin\n'
        
        for st in self.body:
            str += Python2VerilogTranspiler.toVerilog(st) 

        str += 'end\n'            
        return str            
    
class VerilogBody(ast.AST):
    '''
    AST node to wrap body
    '''
    def __init__(self, wires, initial, process):
        self.wires = wires
        self.init = initial
        self.process = process
        self._fields = tuple(['wires', 'init','process'])
    
    def toVerilog(self):
        str = ''
        
        str += '// wire/variable declaration \n'
        str += Python2VerilogTranspiler.toVerilog(self.wires)

        str += '// initial \n'
        str += Python2VerilogTranspiler.toVerilog(self.init)

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
        str += 'begin\n'
        str += Python2VerilogTranspiler.toVerilog(self.positive) + '\n'
        str += 'end\n'
        
        if (len(self.negative) > 0):
            str += 'else\n'
            str += 'begin\n'
            str += Python2VerilogTranspiler.toVerilog(self.negative) + '\n'
            str += 'end\n'
        return str
    
class VerilogConstant(ast.AST):
    def __init__(self, value):
        self.value = value
        self._fields = tuple(['condition', 'positive', 'negative'])
        
    def toVerilog(self):
        return '{}'.format(self.value)
    
class VerilogTernaryConditionalOperator(ast.AST):
    def __init__(self, cond, positive, negative):
        self.condition = cond
        self.positive = positive
        self.negative = negative
        self._fields = tuple(['condition', 'positive', 'negative'])

    def toVerilog(self):
        return '({}) ? {} : {}'.format(Python2VerilogTranspiler.toVerilog(self.condition),
            Python2VerilogTranspiler.toVerilog(self.positive),
            Python2VerilogTranspiler.toVerilog(self.negative))