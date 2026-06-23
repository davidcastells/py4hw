from __future__ import print_function, unicode_literals
import six
import sys
import ast
import os
import tokenize
from six import StringIO

INFSTR = '1e' + repr(sys.float_info.max_10_exp + 1)

def interleave(inter, f, seq):
    """Call f on each item in seq, calling inter() in between.\n    """
    seq = iter(seq)
    try:
        f(next(seq))
    except StopIteration:
        return None
    else:
        for x in seq:
            inter()
            f(x)

class Py4hwUnparser:
    """Methods in this class recursively traverse an AST and\n    output source code for the abstract syntax; original formatting\n    is disregarded. """
    def __init__(self, tree, file=sys.stdout):
        """Unparser(tree, file=sys.stdout) -> None.\n         Print the source for tree to file."""
        self.f = file
        self.future_imports = []
        self._indent = 0
        self.dispatch(tree)
        print('', file=self.f)
        self.f.flush()
    def fill(self, text=''):
        """Indent a piece of text, according to the current indentation level"""
        self.f.write('\n' + '    ' * self._indent + text)
    def write(self, text):
        """Append a piece of text to the current line."""
        self.f.write(six.text_type(text))
    def enter(self):
        """Print \':\', and increase the indentation."""
        self.write(':')
        self._indent += 1
    def leave(self):
        """Decrease the indentation level."""
        self._indent -= 1
    def dispatch(self, tree):
        """Dispatcher function, dispatching tree type T to method _T."""
        if isinstance(tree, list):
            for t in tree:
                self.dispatch(t)
        else:
            meth = getattr(self, '_' + tree.__class__.__name__)
            meth(tree)
    def _Module(self, tree):
        for stmt in tree.body:
            self.dispatch(stmt)
    def _Interactive(self, tree):
        for stmt in tree.body:
            self.dispatch(stmt)
    def _Expression(self, tree):
        self.dispatch(tree.body)
    def _Expr(self, tree):
        if not hasattr(tree, 'value'):
            return None
        else:
            self.fill()
            self.dispatch(tree.value)
    def _NamedExpr(self, tree):
        self.write('(')
        self.dispatch(tree.target)
        self.write(' := ')
        self.dispatch(tree.value)
        self.write(')')
    def _Import(self, t):
        self.fill('import ')
        interleave(lambda: self.write(', '), self.dispatch, t.names)
    def _ImportFrom(self, t):
        if t.module and t.module == '__future__':
                self.future_imports.extend((n.name for n in t.names))
        self.fill('from ')
        self.write('.' * t.level)
        if t.module:
            self.write(t.module)
        self.write(' import ')
        interleave(lambda: self.write(', '), self.dispatch, t.names)
    def _Assign(self, t):
        self.fill()
        for target in t.targets:
            self.dispatch(target)
            self.write(' = ')
        self.dispatch(t.value)
    def _Match(self, t):
        self.fill('match ')
        self.dispatch(t.subject)
        self.enter()
        for case in t.cases:
            self.fill('case ')
            self.dispatch(case.pattern)
            self.enter()
            self.dispatch(case.body)
            self.leave()
        self.leave()
    def _MatchValue(self, t):
        if t.value is None:
            self.write('_')
            return None
        else:
            self.dispatch(t.value)
    def _MatchAs(self, t):
        if t.pattern is None:
            self.write('_')
            return None
        else:
            self.dispatch(t.pattern)
            self.write(' as ')
            self.dispatch(t.name)
    def _NoneType(self, t):
        self.write('None')
    def _VerilogBody(self, t):
        self.fill()
        self.dispatch(t.wires)
        self.fill()
        self.dispatch(t.init)
        self.fill()
        self.dispatch(t.process)
    def _VerilogInitial(self, t):
        self.fill()
        self.dispatch(t.body)
    def _VerilogProcess(self, t):
        self.fill()
        self.write('always @({})\n'.format(t.sensitivity_list))
        self.write('begin')
        self.fill()
        self.dispatch(t.body)
        self.fill()
        self.write('end')
    def _VerilogDeclarations(self, t):
        self.fill()
        self.dispatch(t.wires)
        self.fill()
        self.dispatch(t.variables)
    def _VerilogSynchronousAssignment(self, t):
        self.fill()
        self.dispatch(t.left)
        self.write(' v_= ')
        self.dispatch(t.right)
    def _VerilogVariableAssignment(self, t):
        self.fill()
        self.dispatch(t.left)
        self.write(' v_= ')
        self.dispatch(t.right)
    def _VerilogWire(self, t):
        self.write(t.name)
    def _VerilogVariable(self, t):
        self.write(t.name)
    def _VerilogConstant(self, t):
        self.write(t.value)
    def _AugAssign(self, t):
        self.fill()
        self.dispatch(t.target)
        self.write(' ' + self.binop[t.op.__class__.__name__] + '= ')
        self.dispatch(t.value)
    def _AnnAssign(self, t):
        self.fill()
        if not t.simple and isinstance(t.target, ast.Name):
                self.write('(')
        self.dispatch(t.target)
        if not t.simple and isinstance(t.target, ast.Name):
                self.write(')')
        self.write(': ')
        self.dispatch(t.annotation)
        if t.value:
            self.write(' = ')
            self.dispatch(t.value)
    def _Return(self, t):
        self.fill('return')
        if t.value:
            self.write(' ')
            self.dispatch(t.value)
    def _Pass(self, t):
        self.fill('pass')
    def _Break(self, t):
        self.fill('break')
    def _Continue(self, t):
        self.fill('continue')
    def _Delete(self, t):
        self.fill('del ')
        interleave(lambda: self.write(', '), self.dispatch, t.targets)
    def _Assert(self, t):
        self.fill('assert ')
        self.dispatch(t.test)
        if t.msg:
            self.write(', ')
            self.dispatch(t.msg)
    def _Exec(self, t):
        self.fill('exec ')
        self.dispatch(t.body)
        if t.globals:
            self.write(' in ')
            self.dispatch(t.globals)
        if t.locals:
            self.write(', ')
            self.dispatch(t.locals)
    def _Print(self, t):
        self.fill('print ')
        do_comma = False
        if t.dest:
            self.write('>>')
            self.dispatch(t.dest)
            do_comma = True
        for e in t.values:
            if do_comma:
                self.write(', ')
            else:
                do_comma = True
            self.dispatch(e)
        if not t.nl:
            self.write(',')
    def _Global(self, t):
        self.fill('global ')
        interleave(lambda: self.write(', '), self.write, t.names)
    def _Nonlocal(self, t):
        self.fill('nonlocal ')
        interleave(lambda: self.write(', '), self.write, t.names)
    def _Await(self, t):
        self.write('(')
        self.write('await')
        if t.value:
            self.write(' ')
            self.dispatch(t.value)
        self.write(')')
    def _Yield(self, t):
        self.write('(')
        self.write('yield')
        if t.value:
            self.write(' ')
            self.dispatch(t.value)
        self.write(')')
    def _YieldFrom(self, t):
        self.write('(')
        self.write('yield from')
        if t.value:
            self.write(' ')
            self.dispatch(t.value)
        self.write(')')
    def _Raise(self, t):
        self.fill('raise')
        if six.PY3:
            if not t.exc:
                assert not t.cause
            else:
                self.write(' ')
                self.dispatch(t.exc)
                if t.cause:
                    self.write(' from ')
                    self.dispatch(t.cause)
        else:
            self.write(' ')
            if t.type:
                self.dispatch(t.type)
            if t.inst:
                self.write(', ')
                self.dispatch(t.inst)
            if t.tback:
                self.write(', ')
                self.dispatch(t.tback)
    def _Try(self, t):
        self.fill('try')
        self.enter()
        self.dispatch(t.body)
        self.leave()
        for ex in t.handlers:
            self.dispatch(ex)
        if t.orelse:
            self.fill('else')
            self.enter()
            self.dispatch(t.orelse)
            self.leave()
        if t.finalbody:
            self.fill('finally')
            self.enter()
            self.dispatch(t.finalbody)
            self.leave()
    def _TryExcept(self, t):
        self.fill('try')
        self.enter()
        self.dispatch(t.body)
        self.leave()
        for ex in t.handlers:
            self.dispatch(ex)
        if t.orelse:
            self.fill('else')
            self.enter()
            self.dispatch(t.orelse)
            self.leave()
    def _TryFinally(self, t):
        if len(t.body) == 1 and isinstance(t.body[0], ast.TryExcept):
            self.dispatch(t.body)
        else:
            self.fill('try')
            self.enter()
            self.dispatch(t.body)
            self.leave()
        self.fill('finally')
        self.enter()
        self.dispatch(t.finalbody)
        self.leave()
    def _ExceptHandler(self, t):
        self.fill('except')
        if t.type:
            self.write(' ')
            self.dispatch(t.type)
        if t.name:
            self.write(' as ')
            if six.PY3:
                self.write(t.name)
            else:
                self.dispatch(t.name)
        self.enter()
        self.dispatch(t.body)
        self.leave()
    def _ClassDef(self, t):
        self.write('\n')
        for deco in t.decorator_list:
            self.fill('@')
            self.dispatch(deco)
        self.fill('class ' + t.name)
        if six.PY3:
            self.write('(')
            comma = False
            for e in t.bases:
                if comma:
                    self.write(', ')
                else:
                    comma = True
                self.dispatch(e)
            for e in t.keywords:
                if comma:
                    self.write(', ')
                else:
                    comma = True
                self.dispatch(e)
            if sys.version_info[:2] < (3, 5):
                if t.starargs:
                    if comma:
                        self.write(', ')
                    else:
                        comma = True
                    self.write('*')
                    self.dispatch(t.starargs)
                if t.kwargs:
                    if comma:
                        self.write(', ')
                    else:
                        comma = True
                    self.write('**')
                    self.dispatch(t.kwargs)
            self.write(')')
        else:
            if t.bases:
                self.write('(')
                for a in t.bases:
                    self.dispatch(a)
                    self.write(', ')
                self.write(')')
        self.enter()
        self.dispatch(t.body)
        self.leave()
    def _FunctionDef(self, t):
        self.__FunctionDef_helper(t, 'def')
    def _AsyncFunctionDef(self, t):
        self.__FunctionDef_helper(t, 'async def')
    def __FunctionDef_helper(self, t, fill_suffix):
        self.write('\n')
        for deco in t.decorator_list:
            self.fill('@')
            self.dispatch(deco)
        def_str = fill_suffix + ' ' + t.name + '('
        self.fill(def_str)
        self.dispatch(t.args)
        self.write(')')
        if getattr(t, 'returns', False):
            self.write(' -> ')
            self.dispatch(t.returns)
        self.enter()
        self.dispatch(t.body)
        self.leave()
    def _For(self, t):
        self.__For_helper('for ', t)
    def _AsyncFor(self, t):
        self.__For_helper('async for ', t)
    def __For_helper(self, fill, t):
        self.fill(fill)
        self.dispatch(t.target)
        self.write(' in ')
        self.dispatch(t.iter)
        self.enter()
        self.dispatch(t.body)
        self.leave()
        if t.orelse:
            self.fill('else')
            self.enter()
            self.dispatch(t.orelse)
            self.leave()
    def _If(self, t):
        # ***<module>.Py4hwUnparser._If: Failure: Different control flow
        self.fill('if ')
        self.dispatch(t.test)
        self.enter()
        self.dispatch(t.body)
        self.leave()
        while t.orelse and len(t.orelse) == 1 and isinstance(t.orelse[0], ast.If):
            if t.orelse:
                self.fill('else')
                self.enter()
                self.dispatch(t.orelse)
                self.leave()
        else:
            t = t.orelse[0]
            self.fill('elif ')
            self.dispatch(t.test)
            self.enter()
            self.dispatch(t.body)
            self.leave()
    def _VerilogIf(self, t):
        self.fill('v_if ')
        self.dispatch(t.condition)
        self.enter()
        self.dispatch(t.positive)
        self.leave()
        if t.negative:
            self.fill('else')
            self.enter()
            self.dispatch(t.negative)
            self.leave()
    def _While(self, t):
        self.fill('while ')
        self.dispatch(t.test)
        self.enter()
        self.dispatch(t.body)
        self.leave()
        if t.orelse:
            self.fill('else')
            self.enter()
            self.dispatch(t.orelse)
            self.leave()
    def _generic_With(self, t, async_=False):
        self.fill('async with ' if async_ else 'with ')
        if hasattr(t, 'items'):
            interleave(lambda: self.write(', '), self.dispatch, t.items)
        else:
            self.dispatch(t.context_expr)
            if t.optional_vars:
                self.write(' as ')
                self.dispatch(t.optional_vars)
        self.enter()
        self.dispatch(t.body)
        self.leave()
    def _With(self, t):
        self._generic_With(t)
    def _AsyncWith(self, t):
        self._generic_With(t, async_=True)
    def _Bytes(self, t):
        self.write(repr(t.s))
    def _Str(self, tree):
        if six.PY3:
            self.write(repr(tree.s))
        else:
            if 'unicode_literals' not in self.future_imports:
                self.write(repr(tree.s))
            else:
                if isinstance(tree.s, str):
                    self.write('b' + repr(tree.s))
                else:
                    if isinstance(tree.s, unicode):
                        self.write(repr(tree.s).lstrip('u'))
                    else:
                        assert False, 'shouldn\'t get here'
    def _JoinedStr(self, t):
        self.write('f')
        string = StringIO()
        self._fstring_JoinedStr(t, string.write)
        v = string.getvalue()
        if '\n' in v or '\r' in v:
            quote_types = ['\'\'\'', '\"\"\"']
        else:
            quote_types = ['\'', '\"', '\"\"\"', '\'\'\'']
        for quote_type in quote_types:
            if quote_type not in v:
                v = '{quote_type}{v}{quote_type}'.format(quote_type=quote_type, v=v)
                break
        else:
            v = repr(v)
        self.write(v)
    def _FormattedValue(self, t):
        self.write('f')
        string = StringIO()
        self._fstring_JoinedStr(t, string.write)
        self.write(repr(string.getvalue()))
    def _fstring_JoinedStr(self, t, write):
        for value in t.values:
            meth = getattr(self, '_fstring_' + type(value).__name__)
            meth(value, write)
    def _fstring_Str(self, t, write):
        value = t.s.replace('{', '{{').replace('}', '}}')
        write(value)
    def _fstring_Constant(self, t, write):
        assert isinstance(t.value, str)
        value = t.value.replace('{', '{{').replace('}', '}}')
        write(value)
    def _fstring_FormattedValue(self, t, write):
        write('{')
        expr = StringIO()
        Py4hwUnparser(t.value, expr)
        expr = expr.getvalue().rstrip('\n')
        if expr.startswith('{'):
            write(' ')
        write(expr)
        if t.conversion!= (-1):
            conversion = chr(t.conversion)
            assert conversion in 'sra'
            write('!{conversion}'.format(conversion=conversion))
        if t.format_spec:
            write(':')
            meth = getattr(self, '_fstring_' + type(t.format_spec).__name__)
            meth(t.format_spec, write)
        write('}')
    def _Name(self, t):
        self.write(t.id)
    def _NameConstant(self, t):
        self.write(repr(t.value))
    def _Repr(self, t):
        self.write('`')
        self.dispatch(t.value)
        self.write('`')
    def _write_constant(self, value):
        if isinstance(value, (float, complex)):
            self.write(repr(value).replace('inf', INFSTR))
        else:
            self.write(repr(value))
    def _Constant(self, t):
        value = t.value
        if isinstance(value, tuple):
            self.write('(')
            if len(value) == 1:
                self._write_constant(value[0])
                self.write(',')
            else:
                interleave(lambda: self.write(', '), self._write_constant, value)
            self.write(')')
        else:
            if value is Ellipsis:
                self.write('...')
            else:
                if t.kind == 'u':
                    self.write('u')
                self._write_constant(t.value)
    def _Num(self, t):
        repr_n = repr(t.n)
        if six.PY3:
            self.write(repr_n.replace('inf', INFSTR))
            return None
        else:
            if repr_n.startswith('-'):
                self.write('(')
            if 'inf' in repr_n and repr_n.endswith('*j'):
                    repr_n = repr_n.replace('*j', 'j')
            self.write(repr_n.replace('inf', INFSTR))
            if repr_n.startswith('-'):
                self.write(')')
    def _List(self, t):
        self.write('[')
        interleave(lambda: self.write(', '), self.dispatch, t.elts)
        self.write(']')
    def _ListComp(self, t):
        self.write('[')
        self.dispatch(t.elt)
        for gen in t.generators:
            self.dispatch(gen)
        self.write(']')
    def _GeneratorExp(self, t):
        self.write('(')
        self.dispatch(t.elt)
        for gen in t.generators:
            self.dispatch(gen)
        self.write(')')
    def _SetComp(self, t):
        self.write('{')
        self.dispatch(t.elt)
        for gen in t.generators:
            self.dispatch(gen)
        self.write('}')
    def _DictComp(self, t):
        self.write('{')
        self.dispatch(t.key)
        self.write(': ')
        self.dispatch(t.value)
        for gen in t.generators:
            self.dispatch(gen)
        self.write('}')
    def _comprehension(self, t):
        if getattr(t, 'is_async', False):
            self.write(' async for ')
        else:
            self.write(' for ')
        self.dispatch(t.target)
        self.write(' in ')
        self.dispatch(t.iter)
        for if_clause in t.ifs:
            self.write(' if ')
            self.dispatch(if_clause)
    def _IfExp(self, t):
        self.write('(')
        self.dispatch(t.body)
        self.write(' if ')
        self.dispatch(t.test)
        self.write(' else ')
        self.dispatch(t.orelse)
        self.write(')')
    def _VerilogCase(self, t):
        self.fill('case (')
        self.dispatch(t.var)
        self.write(')\n')
        self.enter()
        for key in t.cases.keys():
            st = t.cases[key]
            self.fill('')
            self.dispatch(key)
            self.write(' : ')
            if len(st) > 1:
                self.fill('begin')
                self.enter()
                self.dispatch(st)
                self.leave()
                self.fill('end')
            else:
                self.dispatch(st)
        self.fill('default: ')
        self.dispatch(t.default)
        self.leave()
        self.fill('endcase')
    def _Set(self, t):
        assert t.elts
        self.write('{')
        interleave(lambda: self.write(', '), self.dispatch, t.elts)
        self.write('}')
    def _Dict(self, t):
        self.write('{')
        def write_key_value_pair(k, v):
            self.dispatch(k)
            self.write(': ')
            self.dispatch(v)
        def write_item(item):
            k, v = item
            if k is None:
                self.write('**')
                self.dispatch(v)
            else:
                write_key_value_pair(k, v)
        interleave(lambda: self.write(', '), write_item, zip(t.keys, t.values))
        self.write('}')
    def _Tuple(self, t):
        self.write('(')
        if len(t.elts) == 1:
            elt = t.elts[0]
            self.dispatch(elt)
            self.write(',')
        else:
            interleave(lambda: self.write(', '), self.dispatch, t.elts)
        self.write(')')
    unop = {'Invert': '~', 'Not': 'not', 'UAdd': '+', 'USub': '-'}
    def _UnaryOp(self, t):
        self.write('(')
        self.write(self.unop[t.op.__class__.__name__])
        self.write(' ')
        if six.PY2 and isinstance(t.op, ast.USub) and isinstance(t.operand, ast.Num):
            self.write('(')
            self.dispatch(t.operand)
            self.write(')')
        else:
            self.dispatch(t.operand)
        self.write(')')
    binop = {'Add': '+', 'Sub': '-', 'Mult': '*', 'MatMult': '@', 'Div': '/', 'Mod': '%', 'LShift': '<<', 'RShift': '>>', 'BitOr': '|', 'BitXor': '^', 'BitAnd': '&', 'FloorDiv': '//', 'Pow': '**'}
    def _BinOp(self, t):
        self.write('(')
        self.dispatch(t.left)
        self.write(' ' + self.binop[t.op.__class__.__name__] + ' ')
        self.dispatch(t.right)
        self.write(')')
    def _VerilogOperator(self, t):
        self.write('(')
        self.dispatch(t.left)
        self.write(' ' + t.op + ' ')
        self.dispatch(t.right)
        self.write(')')
    cmpops = {'Eq': '==', 'NotEq': '!=', 'Lt': '<', 'LtE': '<=', 'Gt': '>', 'GtE': '>=', 'Is': 'is', 'IsNot': 'is not', 'In': 'in', 'NotIn': 'not in'}
    def _Compare(self, t):
        self.write('(')
        self.dispatch(t.left)
        for o, e in zip(t.ops, t.comparators):
            self.write(' ' + self.cmpops[o.__class__.__name__] + ' ')
            self.dispatch(e)
        self.write(')')
    boolops = {ast.And: 'and', ast.Or: 'or'}
    def _BoolOp(self, t):
        self.write('(')
        s = ' %s ' % self.boolops[t.op.__class__]
        interleave(lambda: self.write(s), self.dispatch, t.values)
        self.write(')')
    def _Attribute(self, t):
        self.dispatch(t.value)
        if isinstance(t.value, getattr(ast, 'Constant', getattr(ast, 'Num', None))) and isinstance(t.value.n, int):
                self.write(' ')
        self.write('.')
        self.write(t.attr)
    def _Call(self, t):
        self.dispatch(t.func)
        self.write('(')
        comma = False
        for e in t.args:
            if comma:
                self.write(', ')
            else:
                comma = True
            self.dispatch(e)
        for e in t.keywords:
            if comma:
                self.write(', ')
            else:
                comma = True
            self.dispatch(e)
        if sys.version_info[:2] < (3, 5):
            if t.starargs:
                if comma:
                    self.write(', ')
                else:
                    comma = True
                self.write('*')
                self.dispatch(t.starargs)
            if t.kwargs:
                if comma:
                    self.write(', ')
                else:
                    comma = True
                self.write('**')
[O                self.dispatch(t.kwargs)
        self.write(')')
    def _Subscript(self, t):
        self.dispatch(t.value)
        self.write('[')
        self.dispatch(t.slice)
        self.write(']')
    def _Starred(self, t):
        self.write('*')
        self.dispatch(t.value)
    def _Ellipsis(self, t):
        self.write('...')
    def _Index(self, t):
        self.dispatch(t.value)
    def _Slice(self, t):
        if t.lower:
            self.dispatch(t.lower)
        self.write(':')
        if t.upper:
            self.dispatch(t.upper)
        if t.step:
            self.write(':')
            self.dispatch(t.step)
    def _ExtSlice(self, t):
        interleave(lambda: self.write(', '), self.dispatch, t.dims)
    def _arg(self, t):
        self.write(t.arg)
        if t.annotation:
            self.write(': ')
            self.dispatch(t.annotation)
    def _arguments(self, t):
        first = True
        all_args = getattr(t, 'posonlyargs', []) + t.args
        defaults = [None] * (len(all_args) - len(t.defaults)) + t.defaults
        for index, elements in enumerate(zip(all_args, defaults), 1):
            a, d = elements
            if first:
                first = False
            else:
                self.write(', ')
            self.dispatch(a)
            if d:
                self.write('=')
                self.dispatch(d)
            if index == len(getattr(t, 'posonlyargs', ())):
                self.write(', /')
        if t.vararg or getattr(t, 'kwonlyargs', False):
            if first:
                first = False
            else:
                self.write(', ')
            self.write('*')
            if t.vararg:
                if hasattr(t.vararg, 'arg'):
                    self.write(t.vararg.arg)
                    if t.vararg.annotation:
                        self.write(': ')
                        self.dispatch(t.vararg.annotation)
                else:
                    self.write(t.vararg)
                    if getattr(t, 'varargannotation', None):
                        self.write(': ')
                        self.dispatch(t.varargannotation)
        if getattr(t, 'kwonlyargs', False):
            for a, d in zip(t.kwonlyargs, t.kw_defaults):
                if first:
                    first = False
                else:
                    self.write(', ')
                (self.dispatch(a),)
                if d:
                    self.write('=')
                    self.dispatch(d)
        if t.kwarg:
            if first:
                first = False
            else:
                self.write(', ')
            if hasattr(t.kwarg, 'arg'):
                self.write('**' + t.kwarg.arg)
                if t.kwarg.annotation:
                    self.write(': ')
                    self.dispatch(t.kwarg.annotation)
            else:
                self.write('**' + t.kwarg)
                if getattr(t, 'kwargannotation', None):
                    self.write(': ')
                    self.dispatch(t.kwargannotation)
    def _keyword(self, t):
        if t.arg is None:
            self.write('**')
        else:
            self.write(t.arg)
            self.write('=')
        self.dispatch(t.value)
    def _Lambda(self, t):
        self.write('(')
        self.write('lambda ')
        self.dispatch(t.args)
        self.write(': ')
        self.dispatch(t.body)
        self.write(')')
    def _alias(self, t):
        self.write(t.name)
        if t.asname:
            self.write(' as ' + t.asname)
    def _withitem(self, t):
        self.dispatch(t.context_expr)
        if t.optional_vars:
            self.write(' as ')
            self.dispatch(t.optional_vars)
def roundtrip(filename, output=sys.stdout):
    if six.PY3:
        with open(filename, 'rb') as pyfile:
            encoding = tokenize.detect_encoding(pyfile.readline)[0]
        with open(filename, 'r', encoding=encoding) as pyfile:
            source = pyfile.read()
    else:
        with open(filename, 'r') as pyfile:
            source = pyfile.read()
    tree = compile(source, filename, 'exec', ast.PyCF_ONLY_AST, dont_inherit=True)
    Unparser(tree, output)
def testdir(a):
    # ***<module>.testdir: Failure: Different control flow
    try:
        names = [n for n in os.listdir(a) if n.endswith('.py')]
    except OSError:
        print('Directory not readable: %s' % a, file=sys.stderr)
    else:
        for n in names:
            pass
        fullname = os.path.join(a, n)
        if os.path.isfile(fullname):
            output = StringIO()
            print('Testing %s' % fullname)
            try:
                roundtrip(fullname, output)
            except Exception as e:
                print('  Failed to compile, exception is %s' % repr(e))
        else:
            if os.path.isdir(fullname):
                testdir(fullname)
def main(args):
    if args[0] == '--testdir':
        for a in args[1:]:
            testdir(a)
    else:
        for a in args:
            roundtrip(a)
if __name__ == '__main__':
    main(sys.argv[1:])
