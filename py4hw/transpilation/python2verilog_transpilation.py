# -*- coding: utf-8 -*-
"""
Created on Sun Apr  2 13:59:30 2023

@author: dcr
"""

from .. import *
from deprecated import deprecated

def getMethod(obj, methodname):
    methods = inspect.getmembers(obj, inspect.ismethod)
    method = [x[1] for x in methods if x[0] == methodname ][0]

    source = textwrap.dedent(inspect.getsource(method))
    node = ast.parse(source)
    return node

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


    def transpile(self):
        module = getMethod(self.obj, self.methodName)
    
        node = getBody(module)
    
        node = ReplaceWireGets().visit(node)
        node= ReplaceWirePrepare().visit(node)
        node= ReplaceWirePut().visit(node)
         
        return self.toVerilog(node)
        #return self.transpileUnknown(node)
        
    def toVerilog(self, node):
        print('transpiling', type(node))
        
        str = ''
        if (isinstance(node, VerilogBody)):
            for obj in node.body:
                str += self.toVerilog(obj) + '\n'
        elif (isinstance(node, ast.Expr)):
            str += self.toVerilog(node.value) + '\n'             
        else:
            return 'unknown {}'.format(type(node))
        
        return str;
    
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
        
    def transpileAttribute(self, line:ast.Attribute):
        return line.attr
            
    def transpileExpr(self, line:ast.Expr):
        return self.transpileUnknown(line.value)
        
    def transpileBinOp(self, line:ast.BinOp):
        return "(" + self.transpileUnknown(line.left) + self.transpileOp(line.op) + self.transpileUnknown(line.right) + ")";

    def transpileOp(self, op):
        if (isinstance(op, ast.BitAnd)):
            return '&'
        elif (isinstance(op, ast.BitOr)):
            return '|'
        elif (isinstance(op, ast.BitXor)):
            return '^'
        else:
            raise Exception('Op not supported: {}'.format(op))
        
    def transpileAssign(self, line:ast.Assign):
        targets = line.targets 
        if (len(targets) > 1):
            return ast.dump(line)
        
        var = getAstName(targets[0])
        
        self.signals[var] = var
        
        return var + " <= " + self.transpileUnknown(line.value) + ";\n" + self.getIndent()  ;
    
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
        attr = getAstName(node.func)
        
        print('checking call', attr)
        if (attr == 'get'):
            #if isinstance(node.func.value, ast.Attribute):
            wirename = getAstName(node.func.value)
            #print('REPLACING GET ', wirename)
            return VerilogWire(wirename)
        
        node = ast.NodeTransformer.generic_visit(self, node)
        
        return node
    
    
class ReplaceWirePrepare(ast.NodeTransformer):
    def visit_Call(self, node):
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
    

class VerilogAsynchronousAssignment(ast.AST):
    def __init__(self, left, right):
        self.left = left
        self.right = right

class VerilogSynchronousAssignment(ast.AST):
    def __init__(self, left, right):
        self.left = left
        self.right = right
        
class VerilogWire(ast.AST):
    '''
    AST node for Verilog Wires
    '''
    def __init__(self, name:str):
        self.name = name
        
class VerilogBody(ast.AST):
    '''
    AST node to wrap body
    '''
    def __init__(self, body:list):
        self.body = body
        self._fields = ('body')
        
class VerilogComment(Logic):
    def __init__(self, parent, name: str, comment:str):
        super().__init__(parent, name)
        self.comment = comment