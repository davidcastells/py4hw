# -*- coding: utf-8 -*-
"""
Created on Tue Apr  4 19:45:20 2023

@author: dcastel1
"""

import ast
import inspect
import textwrap
from types import FunctionType


def getMethod(obj, methodname):
    methods = inspect.getmembers(obj, inspect.ismethod)
    method = [x[1] for x in methods if x[0] == methodname ][0]

    source = textwrap.dedent(inspect.getsource(method))
    node = ast.parse(source)
    return node

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
        
    class_node = ast.ClassDef(
        name=clazz.__name__,
        bases=[ast.Name(id=base.__name__, ctx=ast.Load()) 
               for base in clazz.__bases__],
        keywords=[],
        body=[],
        decorator_list=[]
    )
    
    for name, member in inspect.getmembers(clazz):
        if inspect.isfunction(member) or inspect.ismethod(member):
            
            if (is_method_defined_in_class(clazz,name)):
                source = textwrap.dedent(inspect.getsource(member))
                method_node = ast.parse(source).body[0]
                class_node.body.append(method_node)
    
    return class_node

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
    def __init__(self, id):
        self.id = id
        self.st = []
        self.exits = []
        self.entries = []
        self.mergeofid = -1
        
    def addExit(self, target, cond):
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
        self.blocks.append(self.current_block)
        self.current_id += 1
        self.current_block = Block(self.current_id)
        self.open_blocks.append(self.current_block)
        return self.current_block

    def closeBlock(self, block):
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
        #print('expr')
        self.current_block.st.append(node)
        
    def visit_Call(self, node):
        self.current_block.st.append(node)
        
    def visit_Assign(self, node):
        self.current_block.st.append(node)
        
    def visit_AnnAssign(self, node):
        self.current_block.st.append(node)
        
    def visit_AugAssign(self, node):
        self.current_block.st.append(node)

    def visit_Raise(self, node):
        raise Exception('raise Not supported')
        
    def visit_Assert(self, node):
        raise Exception('assert Not supported')

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

        nextblock = self.newBlock()
        self.closeOpenBlocks(last.id, nextblock)
        print(f'closing open blocks in BB{last.id} to next BB{nextblock.id}')
        
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
