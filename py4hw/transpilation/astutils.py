# -*- coding: utf-8 -*-
"""
Created on Tue Apr  4 19:45:20 2023

@author: dcastel1
"""

import ast
import inspect
import textwrap
from types import FunctionType


def getMethodASTInspectingLiveObject(obj, methodname):
    methods = inspect.getmembers(obj, inspect.ismethod)
    method = [x[1] for x in methods if x[0] == methodname ][0]

    source = textwrap.dedent(inspect.getsource(method))
    node = ast.parse(source)
    return node.body[0]

def getASTFromClassMethod(class_ast, mname):
    for item in class_ast.body:
        if isinstance(item, ast.FunctionDef):
            if item.name == mname:
                return item
    return None

class MethodRenamer(ast.NodeTransformer):
    # An AST transformer to rename a method 
    def __init__(self, from_name: str, to_name: str):
        self.from_name = from_name
        self.to_name = to_name
        
    def visit_FunctionDef(self, node):
        # 1. Rename propagate() to build()
        if (node.name == self.from_name):
            node.name = self.to_name
        
        return node
    
    

class ClassRenamer(ast.NodeTransformer):
    def __init__(self, from_name: str, to_name: str):
        self.from_name = from_name
        self.to_name = to_name
    
    def visit_ClassDef(self, node: ast.ClassDef):
        if node.name == self.from_name:
            node.name = self.to_name
        return node

    
class AppendCallInConstructor(ast.NodeTransformer):
    # An AST transformer to inject a call to a method at the end of the constructor
    def __init__(self, fname):
        self.fname = fname
        
    def visit_FunctionDef(self, node):
        # 1. Rename propagate() to build()
        if (node.name == '__init__'):
            method_call = ast.Expr(value=ast.Call(
                        func=ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()),
                            attr=self.fname,
                            ctx=ast.Load()),
                        args=[],
                        keywords=[]
                    )
                )
            node.body.append(method_call)
        
        return node
    

def is_method_defined_in_class(cls, method_name):
    return method_name in cls.__dict__

def get_class_ast(clazz):
    '''
    
    Parameters
    ----------
    clazz : Class object
        Class that we want to obtain the AST from.

    Raises
    ------
    ValueError
        If the provided object is not a class.

    Returns
    -------
    class_node : Ast tree
        Returns the AST tree of the class.

    '''
    
    if not inspect.isclass(clazz):
        raise ValueError("Input must be a class")
        
    # Get the full class source and parse it
    source = textwrap.dedent(inspect.getsource(clazz))
    module_node = ast.parse(source)

    # Find the class definition node
    for node in module_node.body:
        if isinstance(node, ast.ClassDef) and node.name == clazz.__name__:
            return node

    raise ValueError(f"Class {clazz.__name__} AST could not be found")

def get_text_dimensions(text_str, fontsize=12, factor=(1,1)):
    """Estimate text width/height in points (compatible with node_size)."""
    lines = text_str.split('\n')
    max_line_length = max(len(line) for line in lines) if lines else 0
    num_lines = len(lines)
    width = max_line_length * fontsize * factor[0]  # Approx width per character
    height = num_lines * fontsize * factor[1]       # Approx height per line
    return width, height

class ASTDrawer:
    
    def draw_ast(self, tree):
        self.fontsize = 10
        x, y = 0, 0
        self.xs = 0.5
        self.ys = 0.5
        self.margin = 0.1
        self.xmax, self.ymax = 0,0
        
        self._draw_ast(None, x, y, tree, False)

        import math
        import matplotlib.pyplot as plt


        szx = int(math.ceil(self.xmax + self.margin*2))
        szy = int(math.ceil(abs(self.ymax) + 2*self.ys + self.margin*2))
        figsize=(szx, szy)
        fig, self.ax = plt.subplots(figsize=figsize)

        #print('result of dry test', szx, szy)

        self._draw_ast(None, self.margin, szy - self.ys - self.margin, tree, True)

        self.ax.set_xlim(0, szx)
        self.ax.set_ylim(0, szy)
        plt.show()

    def _draw_ast(self, p, x, y, node, draw=True):
        from matplotlib.patches import Rectangle
        from matplotlib.text import Text
        from matplotlib.lines import Line2D

        node_name = str(type(node).__name__) + ':'

        if (isinstance(node, ast.ClassDef)): node_name += node.name
        if (isinstance(node, ast.FunctionDef)): node_name += node.name
        if (isinstance(node, ast.Name)): node_name += node.id
        if (isinstance(node, ast.Constant)): node_name += str(node.value)
        if (isinstance(node, ast.arg)): node_name += str(node.arg)

        w,h = get_text_dimensions(node_name, fontsize=10, factor=(0.01, 0.02))
        w += self.margin * 2 
        h += self.margin * 2 

        #print(f'drawing {node_name} at {x},{y} dim {w} x {h}')

        if (draw):
            rect = Rectangle((x , y) , w, h, facecolor="lightblue", edgecolor="black", lw=1 )
            self.ax.add_patch(rect)
            self.ax.text(x+self.margin, y+h-self.margin, node_name, ha='left', va='top', fontsize=self.fontsize)

        self.xmax = max(x+w, self.xmax)
        self.ymax = min(y+h, self.ymax)

        if not(p is None):
            if (draw):
                line = Line2D([p[0], x], [p[1], y+h/2],  linestyle='-', color='blue')
                self.ax.add_line(line)

        np = (x+w, y+h/2)

        yini = y
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        y = self._draw_ast(np, x + w+self.xs, y, item, draw)
            elif isinstance(value, ast.AST):
                y = self._draw_ast(np, x + w+self.xs, y, value, draw)

        if (y == yini):
            y -= self.ys

        return y
    
def invert(node):
    """
    Invert the operation in an ast node object (get its negation).

    Args:
        node: An ast node object.

    Returns:
        An ast node object containing the inverse (negation) of the input node.
    """
    inverse = {ast.Eq: ast.NotEq,
               ast.NotEq: ast.Eq,
               ast.Lt: ast.GtE,
               ast.LtE: ast.Gt,
               ast.Gt: ast.LtE,
               ast.GtE: ast.Lt,
               ast.Is: ast.IsNot,
               ast.IsNot: ast.Is,
               ast.In: ast.NotIn,
               ast.NotIn: ast.In}

    if type(node) == ast.Compare:
        op = type(node.ops[0])
        inverse_node = ast.Compare(left=node.left, ops=[inverse[op]()],
                                   comparators=node.comparators)
    elif isinstance(node, ast.BinOp) and type(node.op) in inverse:
        op = type(node.op)
        inverse_node = ast.BinOp(node.left, inverse[op](), node.right)
    elif isinstance(node, ast.Constant):
        inverse_node = ast.Constant(value=not node.value)
    elif isinstance(node, ast.NameConstant):
        inverse_node = ast.NameConstant(value=not node.value)
    else:
        inverse_node = ast.UnaryOp(op=ast.Not(), operand=node)

    return inverse_node


def condition_to_assignment(condition_ast, var_name):
    """
    Transforms an AST condition (e.g., `x > 0`) into an assignment AST
    (e.g., `condition_var = x > 0`).

    Args:
        condition_ast (ast.AST): The AST of the condition (e.g., from `ast.parse("x > 0")`).
        var_name (str): The name of the variable to assign to (e.g., "condition_var").

    Returns:
        ast.Assign: The AST of the assignment.
    """
    # Create a Name node for the variable (left-hand side of assignment)
    target = ast.Name(id=var_name, ctx=ast.Store())

    # The condition_ast is the value (right-hand side of assignment)
    value = condition_ast

    # Build the assignment node
    assignment = ast.Assign(targets=[target], value=value)
    assignment.lineno = -1

    return assignment

class Block:
    '''
    A basic block is a block of statements that can be considered a single 
    control flow unit.
    
    They store statments in st list.
    
    Entries to a Block are the list of nodes that can lead to this node.
    
    Exits are the destination of one block to another. 
    
    '''
    def __init__(self, id):
        self.id = id
        self.st = []
        self.exits = []
        self.entries = []
        self.mergeofid = -1
        
    def addExit(self, target, cond):
        # Exits can have a conidition
        link = Link(self, target, cond)
        self.exits.append(link)
        target.entries.append(link)
        
    def toString(self):
        ret = f'BB{self.id}'
        if (self.mergeofid != -1):
            ret += f' merge of BB{self.mergeofid}'
        ret += '\n'
        for st in self.st:
            ret += ast.unparse(st) + '\n'
            
        return ret
        
class Link:
    def __init__(self, source, target, cond):
        self.source = source
        self.target = target
        self.cond = cond


class CFGBuilder(ast.NodeVisitor):
    '''
    Control Data-Flow Graph Builder
    '''
    
    def __init__(self, entry_id=0):
        self.current_id = entry_id
        self.current_block = Block(self.current_id)
        self.blocks = []
        self.entry = self.current_block
        self.open_blocks = [self.current_block]
                
    def newBlock(self):
        # When we create a new block we automatically append it to open blocks
        self.blocks.append(self.current_block)
        self.current_id += 1
        self.current_block = Block(self.current_id)
        self.open_blocks.append(self.current_block)
        return self.current_block

    def closeBlock(self, block):
        # we clock some open block
        self.open_blocks.remove(block)
        
    def closeOpenBlocks(self, fromid, nextblock):
        ast_none = ast.Constant(value=None)
        toremove = []
        
        for i in range(len(self.open_blocks)):
            block = self.open_blocks[i]
            if (block != nextblock and block.id > fromid):
                block.addExit(nextblock, ast_none)
                toremove.append(block)

        for item in toremove:
            self.open_blocks.remove(item)
            
        nextblock.mergeofid = fromid
            
    def build(self, tree):
        self.generic_visit(tree)
        self.blocks.append(self.current_block)
        
    def visit_Expr(self, node):
        self.generic_visit(node)
        if not isinstance(node.value, ast.Yield):
            self.current_block.st.append(node)
        
    #def visit_Call(self, node):
    #    self.current_block.st.append(node)
        
    def visit_Assign(self, node):
        self.current_block.st.append(node)
        
    def visit_AnnAssign(self, node):
        self.current_block.st.append(node)
        
    def visit_AugAssign(self, node):
        self.current_block.st.append(node)

    def visit_Raise(self, node):
        print('Warning: Raise not supported')
        return ast.Pass()
        #raise Exception('raise Not supported')
        
    def visit_Assert(self, node):
        raise Exception('assert Not supported')

    def visit_Yield(self, node):
        ast_none = ast.Constant(value=None)
        
        last = self.current_block
        last.st.append(node)
        
        nextblock = self.newBlock()
        last.addExit(nextblock, ast_none)
        self.closeBlock(last)
        
        print('yield')
        
    def visit_If(self, node):
        cond = condition_to_assignment(node.test, f'BB{self.current_id}_cond')
        self.current_block.st.append(cond)
        last = self.current_block
        
        # We add the condition to last block
        # and link last -> pos
        pos = self.newBlock()
        
        last.addExit(pos, node.test)
        self.closeBlock(last)
        
        for st in node.body:
            # visit all the positive blocks, open exits will have to be resolved later
            # to the following block
            self.visit(st)
            
        neg = None
        if len(node.orelse) != 0:
            neg = self.newBlock()
            # link last -> neg
            last.addExit(neg, invert(node.test))
            #self.closeBlock(last)
            
            # visit all the negative blocks, open exits will have to be resolved later
            # to the following block
            for child in node.orelse:
                self.visit(child)
        else:
            # if without else also create an empty basic block 
            neg = self.newBlock()
            # link last -> neg
            last.addExit(neg, invert(node.test))
            
        nextblock = self.newBlock()
        self.closeOpenBlocks(last.id, nextblock)
        print(f'closing open blocks in BB{last.id} to next BB{nextblock.id}')
        
    def visit_While(self, node):
        ast_none = ast.Constant(value=None)
        
        last = self.current_block
        whilenode = self.newBlock()
        
        cond = condition_to_assignment(node.test, f'BB{self.current_id}_cond')
        whilenode.st.append(cond)
        
        last.addExit(whilenode, ast_none)
        self.closeBlock(last)
        
        #cond = condition_to_assignment(node.iter, f'BB{self.current_id}_cond')
        #self.current_block.st.append(cond)
        #last = self.current_block
        
        body = self.newBlock()
        whilenode.addExit(body, cond)
        self.closeBlock(whilenode)
        
        for child in node.body:
            self.visit(child)

        self.closeOpenBlocks(whilenode.id, whilenode)

        next = self.newBlock()
        whilenode.addExit(next, invert(cond))
        
    def visit_For(self, node):
        
                
        ast_none = ast.Constant(value=None)
        
        last = self.current_block
        fornode = self.newBlock()
        
        cond = condition_to_assignment(node.iter, f'BB{self.current_id}_cond')
        fornode.st.append(cond)
        
        last.addExit(fornode, ast_none)
        self.closeBlock(last)
        
        #cond = condition_to_assignment(node.iter, f'BB{self.current_id}_cond')
        #self.current_block.st.append(cond)
        #last = self.current_block
        
        body = self.newBlock()
        fornode.addExit(body, cond)
        self.closeBlock(fornode)
        
        for child in node.body:
            self.visit(child)

        self.closeOpenBlocks(fornode.id, fornode)

        next = self.newBlock()
        fornode.addExit(next, invert(cond))
        
    def visit_Pass(self, node):
        self.current_block.st.append(node)
        
        
    def draw(self):
        #for item in self.blocks:
        #    print(f'[BB{item.id}]')
        #    for st in item.st:
        #        print(ast.unparse(st))
                
        root = self.entry
        self.draw_visited = {}
        
        self.fontsize = 10
        x, y = 0, 0
        self.xs = 0.5
        self.ys = 0.5
        self.margin = 0.1
        self.xmax, self.ymax = 0,0
        
        self._draw_graph(None, x, y, root, False)

        import math
        import matplotlib.pyplot as plt


        szx = int(math.ceil(self.xmax + self.margin*2))
        szy = int(math.ceil(abs(self.ymax) + 3*self.ys + self.margin*2))
        figsize=(szx, szy)
        fig, self.ax = plt.subplots(figsize=figsize)

        #print('result of dry test', szx, szy)

        self.draw_visited = {}

        self._draw_graph(None, self.margin, szy - 3*self.ys - self.margin, root, True)

        self.ax.set_xlim(0, szx)
        self.ax.set_ylim(0, szy)
        plt.show()

    def _draw_graph(self, p, x, y, node, draw):
        from matplotlib.patches import Rectangle
        from matplotlib.text import Text
        from matplotlib.lines import Line2D

        if (node in self.draw_visited.keys()):
            # draw missing exit line
            np = self.draw_visited[node]
            if not(p is None):
                if (draw):
                    line = Line2D([p[0], np[0]+np[2]/2], [p[1], np[1]+np[3]],  linestyle='-', color='blue')
                    self.ax.add_line(line)
                    
            return y, x, 0
        
        node_name = node.toString()

        w,h = get_text_dimensions(node_name, fontsize=10, factor=(0.01, 0.02))
        w += self.margin * 2 
        h += self.margin * 2 
        
        self.draw_visited[node] = (x,y,w,h)

        # print(f'drawing block at {x},{y} dim {w} x {h}')

        if (draw):
            rect = Rectangle((x , y) , w, h, facecolor="lightblue", edgecolor="black", lw=1 )
            self.ax.add_patch(rect)
            self.ax.text(x+self.margin, y+h-self.margin, node_name, ha='left', va='top', fontsize=self.fontsize)

        self.xmax = max(x+w, self.xmax)
        self.ymax = min(y+h, self.ymax)

        if not(p is None):
            if (draw):
                line = Line2D([p[0], x+w/2], [p[1], y+h],  linestyle='-', color='blue')
                self.ax.add_line(line)

        np = (x+w/2, y)

        y -= self.ys + h
        
            
        yini = y
        xini = x
        
        for exit in node.exits:
            yr, xr, wr = self._draw_graph(np, x, yini, exit.target, draw)
            y = min(y, yr)
            x = max(xini + wr, xr)
            
            #print('yr:', yr, 'xr:', xr)
        

        if (x == xini):
            # if the value of x has not changed
            x += self.xs + w 

        return y, x, w + self.xs


    def generate_tkiz(self):
        ret = ''
        
        node = self.entry
        self.draw_visited = {}
        
        ret = '\\begin{figure}\n'
        ret += '\\centering\n'
        ret += '\\begin{tikzpicture}[node distance=0.8cm, % Distance between nodes\n'
        ret += 'every node/.style={draw, rectangle, rounded corners, minimum size=0.8cm, align=center}, \n'
        ret += "edge/.style={->'}]\n"

        rn, re = self._generate_tkiz(None, '', node)
        ret += rn
        ret += re
        ret += '\\end{tikzpicture}\n'
        ret += '\\caption{}\n'
        ret += '\\label{}\n'
        ret += '\\end{figure}\n'
    
        return ret
        
    def _generate_tkiz(self, p, rel, node):
        ret_nodes = ''
        ret_edges = ''
        
        if (node in self.draw_visited.keys()):
            # draw missing exit line with a node it was already visited
            # this will happen in feedbacks
            ret_edges += f'\draw[edge] (BB{p.id}) to[out=45, in=-0] (BB{node.id});\n'
                    
            return ret_nodes, ret_edges
        
        node_name = node.toString().strip()
        
        node_name = node_name.replace('_', '\_')
        node_name = node_name.replace('\n', ' \\\\ ')

        
        self.draw_visited[node] = node

        # print(f'drawing block at {x},{y} dim {w} x {h}')

        # ret += f'\\node (BB{node.id}) {{{node_name}}};\n'
        ret_nodes += f'\\node (BB{node.id})  {rel} {{{node_name}}};\n'
        #ret += f'\\node (BB{node.id})  [below=of BB{node.id-1}] {{BB{node.id}}};\n'


        if not(p is None):
            ret_edges += f'\\draw[edge] (BB{p.id}) -- (BB{node.id});\n'
        
            
        last = None
        for exit in node.exits:
            if (last is None):
                rel = f'[below=of BB{node.id}]'
            else:
                rel = f'[right=of BB{last.id}]'
            ns, es = self._generate_tkiz(node, rel, exit.target)
            ret_nodes += ns
            ret_edges += es
            last = exit.target

        return ret_nodes, ret_edges
    
class CFGVisitor:
    def visit(self, cfg):
        # First phase, collect the empty nodes
        to_visit = [cfg.entry]
        visited = []
        empty = []
        
        while len(to_visit) > 0:
            # take first element in to_visit
            el = to_visit.pop()
            
            visited.append(el)
            
            self.visitNode(el)
            
            for exit in el.exits:
                next_el = exit.target
                if not(next_el in visited):
                    to_visit.append(next_el)
        
    def visitNode(node):
        pass
        
def selectEmptyNodes(build):
    '''
    Selects empty nodes, i.e. nodes with no statemetns

    Parameters
    ----------
    build : CFGBuilder 

    Returns
    -------
    empty : list of Block objects

    '''
    class emptyNodeVisitor(CFGVisitor):
        def __init__(self):
            self.empty = []
            
        def visitNode(self, el):
            if (len(el.st) == 0) and (len(el.exits) == 1):
                self.empty.append(el)
            
    visitor = emptyNodeVisitor()
    visitor.visit(build)
    
    return visitor.empty

def selectIrrelevantConditionNodes(cfg):
    class irrelevantNodeVisitor(CFGVisitor):
        def __init__(self):
            self.nodes = []
            
        def visitNode(self, el):
            if (len(el.exits) == 2) and (el.exits[0].target == el.exits[1].target):
                #print('Irrelevant', el.id)
                self.nodes.append(el)
                
    visitor = irrelevantNodeVisitor()
    visitor.visit(cfg)
    
    return visitor.nodes
    

def selectYieldingNodes(build):
    '''
    Selects nodes that contain (actualy they should end up with) 
    a yield instruction

    Parameters
    ----------
    build : TYPE
        DESCRIPTION.

    Returns
    -------
    yields : TYPE
        DESCRIPTION.

    '''
    to_visit = [build.entry]
    visited = []
    yields = []
    
    while len(to_visit) > 0:
        # take first element in to_visit
        el = to_visit.pop()
    
        #print('Visiting ', el.id, el.st)
        visited.append(el)
    
        # Condition to be considered empty is that it has no statments
        # and a single exit
        if (True in [isinstance(x, ast.Yield) for x in el.st]):
            yields.append(el)
    
        for exit in el.exits:
            next_el = exit.target
            if not(next_el in visited):
                to_visit.append(next_el)
    return yields


def selectConstantControlFlowNodes(build):
    to_visit = [build.entry]
    visited = []
    constant = []
        
    while len(to_visit) > 0:
        # take first element in to_visit
        el = to_visit.pop()
    
        
        print('Visiting ', el.id)
        visited.append(el)
    
        if len(el.exits) > 1:
            assign = el.st[0]
            var = assign.targets[0].id
            val = assign.value
            if (isinstance(val, ast.Constant)):
                constant.append(el)
                val = val.value
                print('Condition:', var, val)
        
        for exit in el.exits:
            next_el = exit.target
            if not(next_el in visited):
                to_visit.append(next_el)

    return constant

def removeNodesFromCFG(build, empty):
    # Second phase substite the empty nodes
    to_visit = []
    visited = []
    
    # Skip cfg entry if it is already empty
    while (build.entry in empty):
        assert(len(build.entry.exits) == 1)
        build.entry = build.entry.exits[0].target
    
    to_visit.append(build.entry)
    
    while len(to_visit) > 0:
        # take first element in to_visit
        el = to_visit.pop()
        
        print('Visiting ', el.id)
        visited.append(el)
        
        
        for exit in el.exits:
            next_el = exit.target
            
            while (next_el in empty):
                # skip this empty node by modifying link
                print('Skipping', next_el.id)
                next_el = next_el.exits[0].target
                exit.target = next_el
                
            if not(next_el in visited):
                to_visit.append(next_el)

def removeTopExpressionsFromCFG(build):
    class removeTopExpressionVisitor(CFGVisitor):
        def visitNode(self, node):
            node.st = [x.value for x in node.st if isinstance(x, ast.Expr)]
            
    removeTopExpressionVisitor().visit(build)

                
def removePassFromCFG(build):
    class removePassVisitor(CFGVisitor):
        def visitNode(self, node):
            newst = []
            
            for x in node.st:
                if isinstance(x, ast.Pass):
                    pass # ignore it
                elif isinstance(x, ast.Expr):
                    if isinstance(x.value, ast.Pass):
                        pass # ignore it
                    else:
                        newst.append(x)
                else:
                    newst.append(x)

            node.st = newst
            
    removePassVisitor().visit(build)
    
    
def removeEmptyNodesFromCFG(build):
    empty = selectEmptyNodes(build)    
    removeNodesFromCFG(build, empty)

def removeIrrelevantConditionsFromCFG(build):
    nodes = selectIrrelevantConditionNodes(build)
    
    # remove one of the exits
    for node in nodes:
        del node.exits[1]
        
        # remove the irrelevant condition
        del node.st[-1]
    
    empty = [x for x in nodes if len(x.st) == 0]
    
    removeNodesFromCFG(build, empty)
    
def removeUntakenBranches(constants):
    # Some conditions have a constant value, this make some fork nodes
    # unnecessary. This function removes the untaken exit from the 
    # conditional node, so that the removeNodesFromCFG can remove the
    # conditional node easily and know that path to take
    for constant in constants:
        if (constant.st[0].value.value):
            # Constant is True, then the first exit is valid, delete the second
            del constant.exits[1]
        else:
            del constant.exits[0]
        
def removeConstantControlFlowFromCFG(build):
    constant = selectConstantControlFlowNodes(build)
    removeUntakenBranches(constant)
    removeNodesFromCFG(build, constant)
    
def getUsedTargetsInCFG(cfg):
    class usedTargetsVisitor(CFGVisitor):
        def __init__(self):
            self.nodes = []
            
        def visitNode(self, node):
            statements = node.st
            
            if (len(node.exits) > 1):
                # it is a conditional node, avoid last variable
                statements = statements[:-1]
                
            for x in statements:
                if (isinstance(x, ast.Assign)):
                    self.nodes.extend(x.targets)
        
    visitor = usedTargetsVisitor()            
    visitor.visit(cfg)
    
    targets = list(set(visitor.nodes))
    
    return targets

def getUsedSourcesInCFG(cfg):
    class usedSourcesVisitor(CFGVisitor):
        def __init__(self):
            self.nodes = []

        def visitNode(self, node):
                
            for stmt in node.st:
                for sub in ast.walk(stmt):
                    # local variable use
                    if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load):
                        self.nodes.append(sub)
                        
                    # member variable use: self.x
                    elif isinstance(sub, ast.Attribute) and isinstance(sub.ctx, ast.Load):
                        if (isinstance(sub.value, ast.Name) and sub.value.id == "self"):
                            self.nodes.append(sub)
                        
    visitor = usedSourcesVisitor()            
    visitor.visit(cfg)
    
    sources = visitor.nodes    
    
    return sources

def removeUnusedTargetsInCFG(cfg):
    
    class removeUnusedTargetVisitor(CFGVisitor):
        def __init__(self, targets, sources):
            self.unused = []
            
            for target in targets:
                if isinstance(target, ast.Name):
                    # check if it is used
                    uses = [x for x in sources if isinstance(x, ast.Name) and x.id == target.id]
                    if (len(uses) == 0):
                        print('Unused variable', target.id)
                        self.unused.append(target)
        
        def targetsInUnused(self, targets):
            tnames = [x.id for x in targets if isinstance(x, ast.Name)]
            unames = [x.id for x in self.unused if isinstance(x, ast.Name)]
            
            for t in tnames:
                if t in unames:
                    return True
                
            return False
            
        def visitNode(self, node):
            ret = []
            for st in node.st:
                if isinstance(st, ast.Assign):
                    
                    if self.targetsInUnused(st.targets):
                        # if unused variable is a target of an assignment
                        # remove this node from the statement
                        pass
                    else:
                        ret.append(st)
                else:
                    ret.append(st)
            
            node.st = ret
            
    targets = getUsedTargetsInCFG(cfg)
    sources = getUsedSourcesInCFG(cfg)            
    visitor = removeUnusedTargetVisitor(targets, sources)
    visitor.visit(cfg)

def extractStates(build, yields):
    state = {}
    state[0] = build.entry
    build.entry.state = 0
    n = 1
    for y in yields:
        dst = y.exits[0].target
        if not(dst in state.values()):
            # If destination is not already there...
            state[n] = dst
            dst.state = n
    
            n += 1
        
    #for i in range(len(state.keys())):
    #    print(f'State {i} = BB{state[i].id}')
        
    return state


def traverseUntilYield(bb, yields):
    '''
    

    Parameters
    ----------
    bb : TYPE
        DESCRIPTION.
    yields : TYPE
        DESCRIPTION.

    Returns
    -------
    ret : TYPE
        DESCRIPTION.

    '''
    if (bb in yields):
        #ret = bb.st
        ret = []
        for st in bb.st:
            if isinstance(st, ast.Yield):
                #print('jumping to ', bb.exits[0].target.id )
                dst = ast.Constant(value=bb.exits[0].target.state)
                selfnode = ast.Name(id='self', ctx=ast.Load())
                store = ast.Attribute(value=selfnode, attr='state', ctx=ast.Store())
                asg = ast.Assign(targets=[store], value=dst)
                ret.append(asg)
            else:
                ret.append(st)
        return ret
    
    if (len(bb.exits) == 2):
    
    
        ret = []
        
        #ret.append(bb.st[0])
        assert(isinstance(bb.st[0], ast.Assign))
        
        test = bb.st[0].value
        body = traverseUntilYield(bb.exits[0].target, yields)
        orelse = traverseUntilYield(bb.exits[1].target, yields)
        cond = ast.If(test, body, orelse)
        
        ret.append(cond)
        return ret
    elif (len(bb.exits) == 1):
        # this node does not contain a yield, but jumps to another one that
        # could have it, continue with it
        ret = []
        ret.extend(bb.st)
        ret.extend(traverseUntilYield(bb.exits[0].target, yields))
        return ret
    else:
        import astunparse
        print('Basic Block')
        print(astunparse.unparse(bb.st))
        raise Exception('Too few exits for a basic block without yields')
    


def createStateSelectionIfElseTree(state, yields):
    '''
    Create a if/elif/else structure for the FSM

    Parameters
    ----------
    state : TYPE
        DESCRIPTION.
    yields : TYPE
        DESCRIPTION.

    Yields
    ------
    lastif : TYPE
        DESCRIPTION.

    '''
    tests = []
    bodies = []
    
    for i in range(len(state.keys())):
        s = state[i]
        
        stvar = ast.Attribute(value=ast.Name(id='self', ctx = ast.Load()), attr='state', ctx=ast.Load())
        stval = ast.Constant(value=i)
        
        # Create the statement "if (state == i):"
        test = ast.Compare(left=stvar, ops=[ast.Eq()], comparators=[stval])
        
        #print(test)
        tests.append(test)
        
        # Get all the AST starting from the basic block s and will finish
        # by one or several yield statements, that we change by a
        # self.state = x
        body = traverseUntilYield(s, yields)
        bodies.append(body)
        
    lastif = None
    
    for k in range(len(tests)):
        i = len(tests) -1 - k
        
        if (k == 0):
            store = ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr='state', ctx=ast.Store())
            orelse = ast.Assign(targets=[store], value=ast.Constant(value=0))
        else:
            orelse = lastif
            
        #print('body', i, bodies[i])
        lastif = ast.If(tests[i], bodies[i], [orelse])
        
    return lastif

def createStateSelectionMatchCase(state, yields):
    """
    Create a match/case structure for the FSM

    Parameters
    ----------
    state : dict
        Dictionary mapping integer state index to CFG node.
    yields : TYPE
        DESCRIPTION.

    Returns
    -------
    match_stmt : ast.Match
        AST node representing:
        
            match self.state:
                case 0:
                    ...
                case 1:
                    ...
                case _:
                    self.state = 0
    """
    cases = []
    
    for i in range(len(state.keys())):
        s = state[i]

        # pattern: case i:
        pattern = ast.MatchValue(ast.Constant(value=i))

        # body for this case
        body = traverseUntilYield(s, yields)

        cases.append(ast.match_case(pattern=pattern, guard=None, body=body))

    # Default case: case _:
    store = ast.Attribute(
        value=ast.Name(id='self', ctx=ast.Load()),
        attr='state',
        ctx=ast.Store()
    )
    default_body = [ast.Assign(targets=[store], value=ast.Constant(value=0))]
    cases.append(ast.match_case(pattern=ast.MatchAs(name=None), guard=None, body=default_body))

    # match self.state:
    match_stmt = ast.Match(
        subject=ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr='state', ctx=ast.Load()),
        cases=cases
    )

    return match_stmt

class ClockMethodReplacer(ast.NodeTransformer):
    def __init__(self, new_if_statement):
        self.new_if = new_if_statement
    
    
    def visit_Assign(self, node):
        if not self.in_init:
            return node  # Skip if not in __init__

        #print('Assign in INIT')
        
        # Check if this is `self.co = self.run()`
        if (
            isinstance(node.targets[0], ast.Attribute)  # self.co
            and isinstance(node.targets[0].value, ast.Name)
            and node.targets[0].value.id == "self"
            and node.targets[0].attr == "co"
            and isinstance(node.value, ast.Call)  # self.run()
            and isinstance(node.value.func, ast.Attribute)
            and isinstance(node.value.func.value, ast.Name)
            and node.value.func.value.id == "self"
            and node.value.func.attr == "run"
        ):
            # Replace with `self.state = 0`
            new_assign = ast.Assign(
                targets=[ast.Attribute(
                    value=ast.Name(id="self", ctx=ast.Load()),
                    attr="state",
                    ctx=ast.Store()
                )],
                value=ast.Constant(value=0)
            )
            return new_assign
        return node
    
    def visit_ClassDef(self, node):
        # Only process the class we're interested in (optional)
        # if node.name != "YourClassName":
        #     return node
        
        # Find the clock method
        new_body = []
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == "clock":
                # Replace the entire body with our if statement
                item.body = [self.new_if]
                new_body.append(item)
            elif isinstance(item, ast.FunctionDef) and item.name == "run":
                continue
            elif isinstance(item, ast.FunctionDef) and item.name == "__init__":
                self.in_init = True  # Mark that we're inside __init__
                item = self.generic_visit(item)  # Process its body
                self.in_init = False  # Reset after processing
                new_body.append(item)
            else:
                new_body.append(item)
                
        node.body = new_body
        return node

