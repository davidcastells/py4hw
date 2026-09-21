# -*- coding: utf-8 -*-
"""
Created on Sun Apr  2 13:59:30 2023

@author: dcr
"""

from .. import *
from deprecated import deprecated

import ast
from .astutils import * 
import inspect

def startsWith(line, sub):
    if (line[0:len(sub)] == sub):
        return True
    else:
        return False
    
def strip(line):
    line = line.strip()
    
    while (startsWith(line, '\t')):
        # remove tabs
        line = line[1:]

    return line

class TranspilationException(Exception):
    pass


def safeUnparse(node, maxlen=120):
    try:
        s = ast.unparse(node)
    except Exception:
        s = f'<{type(node).__name__}>'
    return s if len(s) <= maxlen else s[:maxlen] + '...'

def addErrorNote(e, text):
    """Attach context to an exception. Works on Python 3.10+."""
    try:
        if hasattr(e, 'add_note'):                 # Python >= 3.11
            e.add_note(text)
        else:                                      # Python 3.10
            msg = ' '.join(str(a) for a in e.args)
            e.args = (msg + '\n' + text,)
    except Exception:
        pass    # never hide the original error because annotating failed

def tagSource(stmts):
    """Remember the source text/line of every Python statement."""
    for s in stmts:
        for n in ast.walk(s):
            if isinstance(n, ast.stmt):
                first = ast.unparse(n).splitlines()[0]   # 'if x:' for compound statements
                n._py_src = first
                n._py_line = getattr(n, 'lineno', '?')

def warn(msg, node=None):
    where = ''
    if node is not None:
        where = f' [python line {getattr(node, "lineno", "?")}: {safeUnparse(node)}]'
    print('WARNING: ' + msg + where)

class TracedTransformer(ast.NodeTransformer):
    """Base class for all passes: adds the offending Python statement to errors."""
    def visit(self, node):
        try:
            result = super().visit(node)
        except Exception as e:
            src = getattr(node, '_py_src', None)
            if src is not None and not getattr(e, '_py_located', False):
                try:
                    e._py_located = True
                except Exception:
                    pass
                addErrorNote(e, f'  -> in pass {type(self).__name__}, '
                                f'python line {getattr(node, "_py_line", "?")}:\n'
                                f'       {src}')
            raise

        # Verilog* replacement nodes inherit the tag of the node they replace
        src = getattr(node, '_py_src', None)
        if (src is not None and isinstance(result, ast.AST) and result is not node
                and getattr(result, '_py_src', None) is None):
            result._py_src = src
            result._py_line = getattr(node, '_py_line', None)
        return result
    
def createVerilogBody(node, slist=''):
    # the Module node contains a body, that contains a list, containting
    # a function definition with a body
    assert(isinstance(node, list))
    tagSource(node)
    
    # AST visitors can not deal directly with list, we wrap them in 
    # a dummy verilog body object
    var = VerilogDeclarations()
    init = VerilogInitial()
    process = VerilogProcess(node, slist)
    return VerilogBody(var, init, process)
    
class Python2VerilogTranspiler:

    def __init__(self, obj:Logic, ast_tree:ast.AST):
        self.obj = obj
        self.ast_tree = ast_tree
        self.signals = {}
        self.indent = 0

    def getIndent(self):
        return ' ' * (self.indent * 4)


    _last_src = None     # last python statement seen while generating verilog

    def transpileCombinational(self):
        return self._guarded(self._transpileCombinational)

    def transpileSequential(self):
        return self._guarded(self._transpileSequential)

    def _guarded(self, fn):
        Python2VerilogTranspiler._last_src = None
        try:
            return fn()
        except Exception as e:
            cls = type(self.obj)
            try:
                fname = inspect.getsourcefile(cls)
            except Exception:
                fname = '?'
            addErrorNote(e, f'  -> while transpiling {self.obj.getFullPath()} '
                            f'(class {cls.__name__}, file {fname})')
            raise
            
    def _transpileCombinational(self):
        '''
        Transpile RTL style behavioural descriptions

        Returns
        -------
        str
            the equivalent RTL

        '''
        
        module = self.getMethodAST('__init__')
        node = createVerilogBody(module.body)
        
        initExtracter = ExtractInitializers(self.obj)
        init = initExtracter.visit(node)
        
        module = self.getMethodAST('propagate')
        node = createVerilogBody(module.body, '*')
        
        #initExtracter = ExtractInitializers(self.obj)
        #init = initExtracter.visit(node)

    
        assert(isinstance(node, ast.AST))
        
        node = RemovePrints().visit(node)
        node = RemoveAssert().visit(node)
        node = InlineWireAliases(self.obj).visit(node)  
        node = ReplaceWidthCalls(self.obj).visit(node)            
        
        node = ReplaceIf().visit(node)
        node = ReplaceParameterCalls().visit(node)
        node = ReplaceWireCalls().visit(node)
        node = ReplaceExpr().visit(node)
        node = ReplaceOperators().visit(node)
        node = ReplaceOperators().visit(node) # repeat to handle Compare

        #node = ReplaceAttribute().visit(node)
        wiresAndVars = ReplaceWiresAndVariables(initExtracter.ports, initExtracter.variables, initExtracter.arguments)
        node = wiresAndVars.visit(node)
        node = ReplaceConstant().visit(node)
        node = ReplaceAssign().visit(node)
 
        node.wires.variables = wiresAndVars.variables.values();
        # node = FlattenOperators().visit(node)

        return node
        #return Python2VerilogTranspiler.toVerilog(node)
        #return self.transpileUnknown(node)

    def getMethodAST(self, method_name):
        if (self.ast_tree is None):
            tree = getMethodASTInspectingLiveObject(self.obj, method_name)
        else:
            tree= next(node for node in self.ast_tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == method_name)
            tree = tree.body
        
        return tree
        
    def _transpileSequential(self):
        '''
        Transpile RTL style behavioural descriptions

        Returns
        -------
        str
            the equivalent RTL

        '''
        # start analyzing the constructor to get wires and variables
        
        module = self.getMethodAST('__init__')
        assert(isinstance(module, ast.FunctionDef))
        node = createVerilogBody(module.body)
        
        initExtracter = ExtractInitializers(self.obj)
        
        init = initExtracter.visit(node)
        
        if hasattr(self.obj, 'initial'):
            # Add the initialization done at the initial method
            module = self.getMethodAST('initial')
            node = getBody(module)
        
            node = ReplaceParameterCalls().visit(node)
            node = ReplaceWireCalls().visit(node)
            node = ReplaceExpr().visit(node)
            node = ReplaceOperators().visit(node)
            node = ReplaceConstant().visit(node)
            
            #print('Constructor Initial=', init.init.body)
            #print('initial method=', node.process.body)
            init.init.body.extend(node.process.body)
        
        module = self.getMethodAST('clock')
        
        clkname = getObjectClockDriver(self.obj).name

        node = createVerilogBody(module.body, 'posedge {}'.format(clkname))
        node.init.body = init.init.body
    
        assert(isinstance(node, ast.AST))
        
        
        node = RemovePrints().visit(node)
        node = RemoveAssert().visit(node)
        node = InlineWireAliases(self.obj).visit(node)  # NEW, before ReplaceWireCalls
        node = ReplaceWidthCalls(self.obj).visit(node)                    
        # node = IfTreeToCaseTransformer().visit(node)
        
        node = ReplaceMatch().visit(node)
        node = ReplaceIf().visit(node)
        node = ReplaceParameterCalls().visit(node)
        node = ReplaceWireCalls().visit(node)
        
        node = PropagateConstants().process(node)
        
        node = ReplaceExpr().visit(node)
        node = ReplaceOperators().visit(node)
        node = ReplaceOperators().visit(node) # repeat to handle Compare
        node = ReplaceOperators().visit(node) # repeat to handle Compare
        
        wiresAndVars = ReplaceWiresAndVariables(initExtracter.ports, initExtracter.variables, initExtracter.arguments)
        node = wiresAndVars.visit(node)
        node = ReplaceConstant().visit(node)
        node = ReplaceAssign().visit(node)
        node = ReplaceIfExp().visit(node)
        node = ReplaceDocStrings().visit(node)
        
        
        
        node.wires.variables = wiresAndVars.variables.values();
        #node = FlattenOperators().visit(node)

        # print('variables', node.wires.variables)
        
        return node;
        # return Python2VerilogTranspiler.toVerilog(node)
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
        #print('transpiling', type(node))

        if (isinstance(node, list)):
            str = ''
            for item in node:
                str += Python2VerilogTranspiler.toVerilog(item)
            return str
        
        if not(hasattr(node, 'toVerilog')):
            raise Exception('No toVerilog for', type(node), node)
        else:
            toV = getattr(node, 'toVerilog')
            return toV()

    def format(self, str):
        lines = str.split('\n')
        indent = 0
        ret = ''
        
        for line in lines:
            line = strip(line)
            
            if (startsWith(line, 'end')):
                indent -= 1
                #print('end->indent: ', indent)
                
            sindent = ''
            if (indent > 0):
                sindent = ' ' * (indent * 4)
                #print('len indent:', len(sindent))
                #ret += '{:02}-'.format(indent)  + sindent
                
            if (startsWith(line, 'begin')):
                indent += 1
                #print('begin->indent: ', indent)
                
            if (len(line) > 0):
                ret += sindent  + line + '\n'
        
        return ret
    
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
    
    
    
class PropagateConstants(TracedTransformer):
    # Propagate constants.
    # Meaning that operations between constants are collapsed, and calls to functions
    # with constant arguments are evaluated
    def process(self, node):
        
        self.anyChange = True
        
        while (self.anyChange):
            self.anyChange = False
            node = self.visit(node)
            
        return node
    
    def has_constant_args(self, call_node):
        """Checks if an ast.Call node has all constant arguments."""

        # Determine supported constant node types based on Python version
        if hasattr(ast, "Constant"):
            constant_nodes = (ast.Constant,)
        else:
            constant_nodes = (ast.Num, ast.Str, ast.Bytes, ast.NameConstant)
        
        for arg in call_node.args:
            if not isinstance(arg, constant_nodes):
                return False
            
        for keyword in call_node.keywords:
            if not isinstance(keyword.value, constant_nodes):
                return False
                
        return True

    def visit_Call(self, node):
        from py4hw.rtl_generation import getAstName

        attr = getAstName(node.func)
        
        if (self.has_constant_args(node)):
            import astunparse
            #print(astunparse.unparse(node), eval(astunparse.unparse(node)))
            return VerilogConstant(eval(astunparse.unparse(node)))
        
        #print('checking call', attr)
        #if (attr == 'print'):
        #    # remove prints
        #    return VerilogComment('print removed')
        #
        #node = ast.NodeTransformer.generic_visit(self, node)
        
        return node 
    
class ReplaceIf(TracedTransformer):
    # Transforms Python If into Verilog If
    
    def __init__(self):
        super().__init__()
        self.inCall = False
        
    def visit_If(self, node):
        condition = self.visit(node.test)
        
        positive = [self.visit(stmt) for stmt in node.body]
        negative = [self.visit(stmt) for stmt in node.orelse]
        
        node2 = VerilogIf(condition, positive, negative)

        #node2 = ast.NodeTransformer.generic_visit(self, node2)
        return node2
        
    def visit_Call(self, node):
        self.inCall = True
        transformed_node = self.generic_visit(node)
        self.inCall = False
        return transformed_node
    
    def visit_IfExp(self, node):
        if (self.inCall):
            raise TranspilationException('Ternary "if" inside a call not supported')
            
        """Transforms Python ternary if-expressions into VerilogIf"""
        condition = self.visit(node.test)
        positive = [self.visit(node.body)]  # Wrap in list to match VerilogIf structure
        negative = [self.visit(node.orelse)]
        return VerilogIf(condition, positive, negative)

class ReplaceMatch(TracedTransformer):
    """Transforms Python match/case into VerilogCase."""

    def visit_Match(self, node):
        # Visit the subject expression
        subject = self.visit(node.subject)

        cases = []
        default_body = None

        for c in node.cases:
            # Visit the body first
            body = [self.visit(stmt) for stmt in c.body]

            # Handle default: match _
            if isinstance(c.pattern, ast.MatchAs) and c.pattern.name is None:
                default_body = body
                continue

            # Handle constant value matches
            if isinstance(c.pattern, ast.MatchValue):
                value = self.visit(c.pattern.value)
                # Optional guard
                if c.guard:
                    # In Verilog, this could be an 'if' inside the case body or ignored
                    # depending on your semantics
                    guard_expr = self.visit(c.guard)
                    body = [VerilogIf(guard_expr, body, [])]
                cases.append(VerilogCaseItem(value, body))
            else:
                # Unsupported pattern type — could raise or skip
                raise NotImplementedError(f"Unsupported match pattern: {ast.dump(c.pattern)}")

        return VerilogCase(subject, cases, default_body)


class _SubstituteAliases(TracedTransformer):
    def __init__(self, aliases):
        self.aliases = aliases

    def visit_Name(self, node):
        import copy
        if isinstance(node.ctx, ast.Load) and node.id in self.aliases:
            return copy.deepcopy(self.aliases[node.id])
        return node


class InlineWireAliases(TracedTransformer):
    """
    Removes temporaries such as
        a = self.a.get()
        n = self.n
        w = self.a.getWidth()
    and substitutes their value where they are used. Only names assigned
    exactly once are inlined.
    """
    def __init__(self, obj):
        self.obj = obj


    def visit_VerilogProcess(self, node):
        node.body = self.process(node.body)
        return node

    def process(self, stmts):
        stored_names = {}
        self.stored_attrs = set()

        for s in stmts:
            for n in ast.walk(s):
                if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
                    stored_names[n.id] = stored_names.get(n.id, 0) + 1
                elif isinstance(n, ast.Attribute) and isinstance(n.ctx, ast.Store):
                    self.stored_attrs.add(n.attr)

        aliases = {}
        out = []
        for s in stmts:
            s = _SubstituteAliases(aliases).visit(s)

            if (isinstance(s, ast.Assign)
                    and len(s.targets) == 1
                    and isinstance(s.targets[0], ast.Name)
                    and stored_names[s.targets[0].id] == 1
                    and self.isAlias(s.value)):
                aliases[s.targets[0].id] = s.value
                continue  # drop the assignment

            out.append(s)
        return out

    def isAlias(self, v):
        if isinstance(v, ast.Constant):
            return True
        # self.x.get() / self.x.getWidth()
        if (isinstance(v, ast.Call) and not v.args and not v.keywords
                and isinstance(v.func, ast.Attribute)):
            return v.func.attr in ('get', 'getWidth')
        # self.n where n is a constructor constant that is never modified
        if (isinstance(v, ast.Attribute) and isinstance(v.value, ast.Name)
                and v.value.id == 'self'):
            return (v.attr not in self.stored_attrs
                    and isinstance(getattr(self.obj, v.attr, None), (int, bool)))
        return False
    
class ReplaceWidthCalls(TracedTransformer):
    """
    Replaces <wire>.getWidth() with the integer width of the wire,
    resolved against the live object (e.g. self.a.getWidth() -> 8)
    """
    def __init__(self, obj):
        super().__init__()
        self.obj = obj

    def resolve(self, node):
        if isinstance(node, ast.Name) and node.id == 'self':
            return self.obj
        if isinstance(node, ast.Attribute):
            return getattr(self.resolve(node.value), node.attr)
        raise TranspilationException(
            f'Cannot resolve "{ast.unparse(node)}" to compute its width')

    def visit_Call(self, node):
        node = self.generic_visit(node)

        if (isinstance(node.func, ast.Attribute)
                and node.func.attr == 'getWidth'
                and not node.args and not node.keywords):
            try:
                wire = self.resolve(node.func.value)
                return ast.Constant(value=int(wire.getWidth()))
            except AttributeError as e:
                raise TranspilationException(
                    f'Cannot compute width of "{ast.unparse(node.func.value)}": {e}')

        return node
    
class RemovePrints(TracedTransformer):
        
    def visit_Call(self, node):
        from py4hw.rtl_generation import getAstName

        attr = getAstName(node.func)
        
        #print('checking call', attr)
        if (attr == 'print'):
            # remove prints
            return VerilogComment('print removed')
        
        node = ast.NodeTransformer.generic_visit(self, node)
        
        return node

class RemoveAssert(TracedTransformer):
        
    def visit_Assert(self, node):
        from py4hw.rtl_generation import getAstName

        # remove asserts
        return VerilogComment('assert removed')
        
class ReplaceDocStrings(TracedTransformer):
    
    def visit_VerilogProcess(self, node):
        newbody = []
        
        for obj in node.body:
            if (isinstance(obj, VerilogConstant)):
                obj = VerilogComment(obj.value)
            newbody.append(obj)
        return VerilogProcess(newbody, node.sensitivity_list)
    
class ReplaceParameterCalls(TracedTransformer):
        
    def visit_Call(self, node):
        from py4hw.rtl_generation import getAstName

        attr = getAstName(node.func)
        
        #print('checking call', attr)
        if (attr == 'getParameterValue'):
            import astunparse
            #if isinstance(node.func.value, ast.Attribute):
            paramname = getAstName(node.args[0])
            #print('REPLACING getParameterValue ',  astunparse.unparse(node.args[0]), node.args[0])
            return VerilogParameter(paramname)
        elif (attr == 'getParameter'):
            paramname = getAstName(node.args[0])
            return VerilogParameter(paramname)
            
        else:
            #print('WARNING: unhandled call {}'.format(attr))
            pass
                 
        node = ast.NodeTransformer.generic_visit(self, node)
        
        return node

def isSelfAttribute(node):
    """True only for the exact form `self.<name>`."""
    return (isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == 'self')
    
class ReplaceWireCalls(TracedTransformer):
        
    WIRE_METHODS = ('get', 'put', 'prepare')
    
    def visit_Call(self, node):
        from py4hw.rtl_generation import getAstName

        #print('Replacing Wire Call in', ast.unparse(node))
        attr = getAstName(node.func)
        
        # Wire accesses must be of the form self.<wire name>.<method>(...)
        if attr in self.WIRE_METHODS and isinstance(node.func, ast.Attribute):
            if not isSelfAttribute(node.func.value):
                raise TranspilationException(
                    "Cannot transpile '{}': '{}()' is only supported on a wire "
                    "of the form self.<wire name>, but found '{}'".format(
                        ast.unparse(node), attr, ast.unparse(node.func.value)))
                
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
    
    

class ReplaceOperators(TracedTransformer):
    
    def visit_BinOp(self, node):
        #print('replacing BinOp')
        left = ast.NodeTransformer.generic_visit(self, node.left)
        right = ast.NodeTransformer.generic_visit(self, node.right)
        node =  VerilogOperator(left, node.op, right)
        #node = ast.NodeTransformer.generic_visit(self, node)
        return node

    def logarithmicIteration(op, in_list):
        out_list = []

        for i in range(0, len(in_list), 2):
            if (i < (len(in_list)-1)):
                out_list.append( VerilogOperator(in_list[i], op, in_list[i+1]))
            else:
                out_list.append(in_list[i])
                
        return out_list
        
    def visit_BoolOp(self, node):
        if (len(node.values) == 2):
            left = ast.NodeTransformer.generic_visit(self, node.values[0])
            right = ast.NodeTransformer.generic_visit(self, node.values[1])
            node = VerilogOperator(left, node.op, right)
            return node
        else:
            # create a hierarchy
            in_list = node.values
            
            while (len(in_list) > 1):
                in_list = ReplaceOperators.logarithmicIteration(node.op, in_list)
                
            return in_list[0]
            
                        
                
    
    def visit_Compare(self, node):
        # print('visiting compare')
        left = ast.NodeTransformer.generic_visit(self, node.left)
        right = node.comparators # ast.NodeTransformer.generic_visit(self, node.comparators)
        node = VerilogOperator(left, node.ops, right)            
        return node
    
    def visit_UnaryOp(self, node):
        operand = ast.NodeTransformer.generic_visit(self, node.operand)
        node = VerilogOperator(None, node.op, operand)
        return node

    
class ReplaceExpr(TracedTransformer):
    def visit_Expr(self, node):
        
        return node.value

class ReplaceIfExp(TracedTransformer):
    def visit_IfExp(self, node):
        cond = ast.NodeTransformer.generic_visit(self, node.test)
        positive = ast.NodeTransformer.generic_visit(self, node.body)
        negative = ast.NodeTransformer.generic_visit(self, node.orelse)
        return VerilogTernaryConditionalOperator(cond, positive, negative)
        

class ReplaceWiresAndVariables(TracedTransformer):
    # We replace names by verilog wires or variables that were identified in the constructor
    
    def __init__(self, ports, variables, arguments):
        self.ports = ports
        self.variables = variables
        self.arguments = arguments
        
    def visit_Name(self, node):
        
        name = node.id
        if (name in self.ports.keys()):
            return VerilogWire(name)

        if (name in self.variables.keys()):
            return VerilogVariable(name, self.variables[name].type)
        
        if (name in self.arguments.keys()):
            return self.arguments[name]

        # create new variable
        self.variables[name] = VerilogVariableDeclaration(name, 'integer')
        return VerilogVariable(name, 'integer')

    def visit_Attribute(self, node):
        
        name = node.attr
        if (name in self.ports.keys()):
            return VerilogWire(name)

        if (name in self.variables.keys()):
            return VerilogVariable(name, self.variables[name].type)
        
        if (name in self.arguments.keys()):
            return self.arguments[name]

        # create new variable
        self.variables[name] = VerilogVariableDeclaration(name, 'integer')
        return VerilogVariable(name, 'integer')
    

class ReplaceConstant(TracedTransformer):
    def __init__(self):
        super().__init__()

    def visit_Constant(self, node):
        if isinstance(node.value, bool):
            #raise TranspilationException("Boolean constants not supported! Use integers.")
            return VerilogConstant(int(node.value))
        
        return VerilogConstant(node.value)
    
    def visit_Num(self, node):
        return VerilogConstant(node.n)
    
    
class ReplaceAssign(TracedTransformer):
            
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

class ExtractInitializers(TracedTransformer):
    # We get port descriptions from addIn, addOut calls
    # @todo Why do we do it like this instead of analyzing the port information of the object ??
    
    # @todo handle interface functions
    # we save ports as a dictionary with associated with a VerilogWire object
    
    # we get variables from  simple assignments like self.state = 0 in the constructor
    
    # we get arguments from simple assignments like self.n = n
    '''
    The goal of this class is to collect information from the constructor of the class.
    We want to know variable declarations and initializations.
    
    things like 
    - self.state = 0
    - self.add = add (where add is a parameter of the constructor)
    
    What we will collect are
    - existing variables
    - existing class arguments
    '''
    
    
    
    def __init__(self, obj):
        self.obj = obj
        self.ports = {}
        self.variables = {}
        self.arguments = {}
        
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
            # We record wires that are used in addIn, addOut calls...
            fname = getAstName(node.value.func)
            pname = ''
            
            if (fname == 'addIn'):
                pname = node.targets[0].attr
                # print('in port', pname)
            elif (fname == 'addOut'):
                pname = node.targets[0].attr
                # print('out port', node.targets[0].attr)
            elif (fname == 'addInterfaceSink'):
                # @todo review what to do here
                pass
            else:
                print('# name not expected', fname)

            w = VerilogWire(pname)
            self.ports[pname] = w        
            self.top.wires.wires.append(w)
            return None
        
        # Change ast.Num to ast.Constant and check if the value is an int or float
        elif isinstance(node.value, ast.Constant):
            vname = node.targets[0].attr
            vvalue = node.value.value
            nvalue = node.value
            
            
            if (isinstance(vvalue, bool)):
                # Convert boolean values to integers
                vvalue = int(vvalue)
                nvalue = VerilogConstant(vvalue)
                
            if not(isinstance(vvalue, int)):
                raise TranspilationException(f'Value should be integer {ast.unparse(node)}')
            
            # Change node.value.n to node.value.value
            var = VerilogVariable(vname, type(vvalue))
            self.top.wires.variables.append(var)
            node = VerilogVariableAssignment(var, nvalue)
            node = ast.NodeTransformer.generic_visit(self, node)
            self.top.init.body.append(node)
        
            # save variable
            self.variables[vname] = VerilogVariableDeclaration(vname, 'integer')
            return None

        # ast.Num was deprecated after Python 3.8
        # elif (isinstance(node.value, ast.Num)):
        #     vname = node.targets[0].attr
        #     var = VerilogVariable(vname, type(node.value.n))
        #     self.top.wires.variables.append(var)
        #     node = VerilogVariableAssignment(var, node.value)
        #     node = ast.NodeTransformer.generic_visit(self, node)
        #     self.top.init.body.append(node)

        #     # save variable
        #     self.variables[vname] = VerilogVariableDeclaration(vname, 'integer')
        #     return None
        
        elif (isinstance(node.value, ast.Name)):
            #return VerilogConstant(getattr(self.obj, node.value.id))
            vname = node.targets[0].attr
            print('Assign ', vname , '=', node.value)
            self.arguments[vname] = VerilogConstant(getattr(self.obj, node.value.id))
            return None
        
        else:
            raise Exception(f'Assign not handled: {ast.unparse(node)} type:', type(node.value) )
        
        return node
                
    def visit_Call(self, node):
        from py4hw.rtl_generation import getAstName

        attr = getAstName(node.func)
        
        #print('checking call', attr)
        if (attr == '__init__'):
            return None
        
        return node

class FlattenOperators(TracedTransformer):
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
        elif (isinstance(operator, ast.Sub)):
            return '-'
        elif (isinstance(operator, ast.USub)):
            return '-'
        elif (isinstance(operator, ast.Mult)):
            return '*'
        elif (isinstance(operator, ast.FloorDiv)):
            return '/'
        # BITWISE
        elif (isinstance(operator, ast.Invert)):
            return '~'
        elif (isinstance(operator, ast.BitAnd)):
            return '&'
        elif (isinstance(operator, ast.BitOr)):
            return '|'
        elif (isinstance(operator, ast.BitXor)):
            return '^'
        elif (isinstance(operator, ast.LShift)):
            return '<<'
        elif (isinstance(operator, ast.RShift)):
            return '>>'
        elif (isinstance(operator, ast.Not)):
            return '!'
        # RELATIONAL
        elif (isinstance(operator, ast.And)):
            return '&&'
        elif (isinstance(operator, ast.Or)):
            return '||'
        elif (isinstance(operator, ast.Eq)):
            return '=='
        elif (isinstance(operator, ast.NotEq)):
            return '!='
        elif (isinstance(operator, ast.Lt)):
            return '<'        
        elif (isinstance(operator, ast.LtE)):
            return '<='
        elif (isinstance(operator, ast.Gt)):
            return '>'
        elif (isinstance(operator, ast.GtE)):
            return '>='        
        elif (isinstance(operator, ast.Mod)):
            return '%'
        else:
            raise Exception('operator {} not supported'.format(type(operator)))
            
    def toVerilog(self):
        str = ''
        
        if not(self.left is None):
            # skip for unary operators
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
    
class VerilogParameter(ast.AST):
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
        assert(isinstance(body, list))
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
    
class VerilogComment(ast.AST):
    def __init__(self, value):
        self.value = value
        self._fields = tuple(['value', 'dummy'])
    
    def toVerilog(self):
        return '/* {} */\n'.format(self.value)
    
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

class VerilogCaseItem(ast.AST):
    

    def __init__(self, value, body):
        self.value = value          # AST node
        self.body = body or []  
        self._fields = ("value", "body")
        
class VerilogCase(ast.AST):
    
    def __init__(self, var, cases, default):
        self.var = var
        self.cases = cases # list of VerilogCaseItems
        self.default = default or []
        self._fields = tuple(['var', 'cases', 'default'])
        
    def toVerilog(self):
        str = 'case ({})\n'.format(Python2VerilogTranspiler.toVerilog(self.var))
        for item in self.cases:
            case = Python2VerilogTranspiler.toVerilog(item.value)
            sts = item.body
            
            str += f'{case}: '
            
            if len(sts) > 1:
                str += 'begin\n'

            for st in sts:
                str += '{}\n'.format(Python2VerilogTranspiler.toVerilog(st))

            if len(sts) > 1:
                str += 'end\n'
                
        str += 'default:'
        sts = self.default
        if len(sts) > 1:
            str += 'begin\n'

        for st in sts:
            str += '{}\n'.format(Python2VerilogTranspiler.toVerilog(st))

        if len(sts) > 1:
            str += 'end\n'

        str += 'endcase\n'            
        
        return str
    
class IfTreeToCaseTransformer(ast.NodeTransformer):

    def visit_If(self, node):
        match = self.try_match_if_chain(node)
        if match:
            return match
        else:
            # No match, visit children normally
            return self.generic_visit(node)

    def try_match_if_chain(self, node):
        """Check if an If/elif/else chain is all 'var == value' tests on the same var."""
        var_expr = None
        cases = [] # it must be a list
        default_body = None

        cur = node
        while True:
            if not isinstance(cur.test, ast.Compare):
                return None
            cmp = cur.test

            # Must be: single op ==, one comparator
            if len(cmp.ops) != 1 or not isinstance(cmp.ops[0], ast.Eq):
                return None
            if len(cmp.comparators) != 1:
                return None

            lhs = cmp.left
            rhs = cmp.comparators[0]

            # Allow Name or Attribute for the var
            if not isinstance(lhs, (ast.Name, ast.Attribute)):
                return None

            if var_expr is None:
                var_expr = lhs
            elif not self.same_var(var_expr, lhs):
                return None

            cases.append(VerilogCaseItem(rhs, cur.body))

            # Follow to elif
            if len(cur.orelse) == 1 and isinstance(cur.orelse[0], ast.If):
                cur = cur.orelse[0]
            else:
                if cur.orelse:
                    default_body = cur.orelse
                break

        # Only convert if we have at least 2 cases
        if len(cases) >= 2:
            return VerilogCase(
                var=var_expr,
                cases=cases,
                default=default_body
            )

        return None

    def same_var(self, a, b):
        """Check if two Name/Attribute ASTs refer to the same variable textually."""
        return ast.dump(a) == ast.dump(b)