import ast
import textwrap
import inspect
import copy
from typing import Dict, Any

class YieldFromInliner(ast.NodeTransformer):
    def __init__(self, cls_node):
        self.cls_node = cls_node
        self.inlinable_methods = {}
        self.calls_to_inline = []
        self.methods_to_remove = set()
        self._phase1_collect_info()
        self.current_function_stack = []

    def _phase1_collect_info(self):
        for node in self.cls_node.body:
            if isinstance(node, ast.FunctionDef):
                self.inlinable_methods[node.name] = node
        call_collector = CallSiteCollector(self.inlinable_methods.keys())
        call_collector.visit(self.cls_node)
        self.calls_to_inline = call_collector.collected_calls

    def _phase2_apply_inlining(self):
        transformed_cls_node = self.visit(self.cls_node)
        new_class_body = []
        removed_count = 0
        for node in transformed_cls_node.body:
            if isinstance(node, ast.FunctionDef) and node.name in self.methods_to_remove:
                removed_count += 1
            else:
                new_class_body.append(node)
        transformed_cls_node.body = new_class_body
        return transformed_cls_node

    def visit_FunctionDef(self, node):
        self.current_function_stack.append(node.name)
        new_body = []
        for stmt in node.body:
            transformed_stmt = self.visit(stmt)
            if isinstance(transformed_stmt, list):
                new_body.extend(transformed_stmt)
            else:
                if transformed_stmt is not None:
                    new_body.append(transformed_stmt)
        node.body = new_body
        self.current_function_stack.pop()
        return node

    def visit_Expr(self, node):
        node = self.generic_visit(node)
        if isinstance(node.value, ast.YieldFrom):
            call = node.value.value
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name) and (call.func.value.id == 'self'):
                method_name = call.func.attr
                if method_name in self.inlinable_methods:
                    if self.current_function_stack and method_name == self.current_function_stack[(-1)]:
                        raise RecursionError(f'Refusing to inline recursive call to {method_name}')
                    else:
                        method_node = self.inlinable_methods[method_name]
                        transformed_inlined_body = []
                        for stmt in method_node.body:
                            visited_stmt = self.visit(copy.deepcopy(stmt))
                            if isinstance(visited_stmt, list):
                                transformed_inlined_body.extend(visited_stmt)
                            else:
                                if visited_stmt is not None:
                                    transformed_inlined_body.append(visited_stmt)
                        self.methods_to_remove.add(method_name)
                        return transformed_inlined_body
        return node

    def visit_Return(self, node):
        return self.generic_visit(node)

class YieldStateTransformer(ast.NodeTransformer):
    def __init__(self):
        self.yield_counter = 1

    def visit_ClassDef(self, node):
        self.generic_visit(node)
        init_found = False
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef) and stmt.name == '__init__':
                    init_found = True
                    assign_stmt = ast.parse('self.state = 0').body[0]
                    stmt.body.insert(0, assign_stmt)
                    break
        if not init_found:
            init_func = ast.FunctionDef(name='__init__', args=ast.arguments(posonlyargs=[], args=[ast.arg(arg='self')], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]), body=[ast.parse('self.state = 0').body[0]], decorator_list=[])
            node.body.insert(0, init_func)
        return node

    def visit_FunctionDef(self, node):
        if node.name == 'run':
            self.generic_visit(node)
        return node

    def visit_Yield(self, node):
        state_assign = ast.Assign(targets=[ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr='state', ctx=ast.Store())], value=ast.Constant(value=self.yield_counter))
        self.yield_counter += 1
        return state_assign

class CallSiteCollector(ast.NodeVisitor):
    def __init__(self, inlinable_method_names):
        self.inlinable_method_names = inlinable_method_names
        self.collected_calls = []
        self.current_function_stack = []

    def visit_FunctionDef(self, node):
        self.current_function_stack.append(node.name)
        self.generic_visit(node)
        self.current_function_stack.pop()

    def visit_YieldFrom(self, node):
        call = node.value
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name) and (call.func.value.id == 'self'):
                        method_name = call.func.attr
                        if method_name in self.inlinable_method_names and self.current_function_stack:
                                calling_function = self.current_function_stack[(-1)]
                                self.collected_calls.append((calling_function, method_name, call))
        self.generic_visit(node)

class KeepInitAndClockTransformer(ast.NodeTransformer):
    def visit_ClassDef(self, node):
        node.body = [item for item in node.body if not isinstance(item, ast.FunctionDef) or item.name in ['__init__', 'clock']]
        self.generic_visit(node)
        return node

class IOWireDirectoryDetector(ast.NodeVisitor):
    def __init__(self):
        self.input_dir = None
        self.output_dir = None
    def visit_FunctionDef(self, node):
        if node.name!= '__init__':
            return None
        else:
            for stmt in node.body:
                if isinstance(stmt, ast.For):
                    self._process_for_loop(stmt)

    def _process_for_loop(self, node):
        # irreducible cflow, using cdg fallback
        # ***<module>.IOWireDirectoryDetector._process_for_loop: Failure: Compilation Error
        if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Attribute) and (node.iter.func.attr == 'keys') and isinstance(node.iter.func.value, ast.Name):
                        dict_var = node.iter.func.value.id
                        for inner_stmt in node.body:
                            pass
            if isinstance(inner_stmt, ast.Expr):
                call = inner_stmt.value
                if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name) and (call.func.value.id == 'self'):
                    method = call.func.attr
                    if method == 'addIn' and self.input_dir is None:
                        self.input_dir = dict_var
                        if method == 'addOut' and self.output_dir is None:
                                self.output_dir = dict_var

class ReplacePrintByPass(ast.NodeTransformer):
    def visit_Call(self, node):
        from py4hw.rtl_generation import getAstName
        attr = getAstName(node.func)
        if attr == 'print':
            return ast.Pass()
        else:
            node = ast.NodeTransformer.generic_visit(self, node)
            return node

import ast
from typing import Any, Dict, Tuple

def dotted_name_from_attribute(node: ast.Attribute) -> str | None:
    """Return dotted name like \'ALU.OP_INC\' or \'pkg.mod.Class.CONST\'."""
    parts = []
    cur = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
        return '.'.join(reversed(parts))

class ClassConstantCollector(ast.NodeVisitor):
    def __init__(self, namespace):
        self.constants = {}
        self.current_class = None
        self.namespace = namespace

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Collect class-level constants (case 1)"""
        self.current_class = node.name
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        try:
                            value = ast.literal_eval(item.value)
                            self.constants[f'self.{target.id}'] = value
                        except (ValueError, SyntaxError):
                            pass
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Collect external class constants (case 2)"""
        if isinstance(node.value, ast.Name):
            print('Attribute', f'{node.value.id}.{node.attr}')
            try:
                value = eval(f'{node.value.id}.{node.attr}', self.namespace)
                self.constants[f'{node.value.id}.{node.attr}'] = value
            except:
                print('error')
        else:
            if isinstance(node.value, ast.Attribute) and isinstance(node.value.value, ast.Name) and (node.value.value.id == 'self'):
                pass
        self.generic_visit(node)

class StaticAttributeInliner(ast.NodeTransformer):
    def __init__(self, ast_constants: Dict[str, Any], runtime_namespace: Dict[str, Any], allowed_types: Tuple[type, ...]=(int, float, str, bool, tuple)):
        self.constants = dict(ast_constants)
        self.runtime_namespace = runtime_namespace
        self.allowed_types = allowed_types
        self._current_class = None
        self._in_bases = False

    def visit_ClassDef(self, node: ast.ClassDef):
        prev_class = self._current_class
        self._current_class = node.name
        self._in_bases = True
        for i, base in enumerate(node.bases):
            node.bases[i] = self.visit(base)
        self._in_bases = False
        node.body = [self.visit(stmt) for stmt in node.body]
        self._current_class = prev_class
        return node

    def visit_Attribute(self, node: ast.Attribute):
        # irreducible cflow, using cdg fallback
        # ***<module>.StaticAttributeInliner.visit_Attribute: Failure: Compilation Error
        if self._in_bases:
            return self.generic_visit(node)
        self.generic_visit(node)
        if isinstance(node.value, ast.Name) and node.value.id == 'self' and self._current_class:
            key = f'{self._current_class}.{node.attr}'
            if key in self.constants:
                return ast.copy_location(ast.Constant(value=self.constants[key]), node)
        dotted = dotted_name_from_attribute(node)
        if dotted:
            if dotted in self.constants:
                return ast.copy_location(ast.Constant(value=self.constants[dotted]), node)
            else:
                parts = dotted.split('.')
                if len(parts) >= 2:
                    last_two = '.'.join(parts[(-2):])
                    if last_two in self.constants:
                        return ast.copy_location(ast.Constant(value=self.constants[last_two]), node)
            val = eval(dotted, self.runtime_namespace)
            if isinstance(val, self.allowed_types):
                self.constants[dotted] = val
                if len(parts) >= 2:
                    self.constants[last_two] = val
                return ast.copy_location(ast.Constant(value=val), node)
                except Exception:
                        pass
                        return node

def replaceConstants(tree: ast.AST, clazz):
    module = inspect.getmodule(clazz)
    src = inspect.getsource(module)
    namespace = {}
    print(src[0:1000])
    exec(src, namespace)
    collector = ClassConstantCollector(namespace)
    collector.visit(tree)
    print('Collected constants', collector.constants)
    transformer = StaticAttributeInliner(collector.constants, globals())
    new_tree = transformer.visit(tree)
    return new_tree

class ScopedSelfAliasRewriter(ast.NodeTransformer):
    def __init__(self):
        self.current_aliases = {}

    def visit_FunctionDef(self, node):
        saved_aliases = self.current_aliases
        self.current_aliases = {}
        node = self.generic_visit(node)
        new_body = []
        for stmt in node.body:
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name) and self._is_self_expr(stmt.value):
                            continue
            new_body.append(stmt)
        self.current_aliases = saved_aliases
        node.body = new_body
        return node

    def visit_Assign(self, node):
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and self._is_self_expr(node.value):
            alias_name = node.targets[0].id
            self.current_aliases[alias_name] = copy.deepcopy(node.value)
            return None
        else:
            return self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load) and node.id in self.current_aliases:
            return copy.deepcopy(self.current_aliases[node.id])
        else:
            return node

    def _is_self_expr(self, expr):
        """\n        Returns True if expr starts from `self`, e.g., self.foo.bar()[\'x\'].baz\n        """
        while isinstance(expr, (ast.Attribute, ast.Subscript, ast.Call)):
            if isinstance(expr, ast.Call):
                expr = expr.func
            else:
                if isinstance(expr, ast.Subscript):
                    expr = expr.value
                else:
                    expr = expr.value
        return isinstance(expr, ast.Name) and expr.id == 'self'

class IODictKeyCollector(ast.NodeVisitor):
    def __init__(self, input_dir_name, output_dir_name, method_name):
        self.input_dir_name = input_dir_name
        self.output_dir_name = output_dir_name
        self.method_name = method_name
        self.input_keys = set()
        self.output_keys = set()

    def visit_FunctionDef(self, node):
        print('checking function ', node.name, self.method_name)
        if node.name!= self.method_name:
            return None
        else:
            self.generic_visit(node)

    def visit_Subscript(self, node):
        import astunparse
        target = node.value
        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and (target.value.id == 'self'):
                    dict_name = target.attr
                    if isinstance(node.slice, ast.Constant):
                        key = node.slice.value
                    else:
                        if isinstance(node.slice, ast.Index) and isinstance(node.slice.value, ast.Constant):
                            key = node.slice.value.value
                        else:
                            key = None
                    if isinstance(key, str):
                        if dict_name == self.input_dir_name:
                            self.input_keys.add(key)
                        else:
                            if dict_name == self.output_dir_name:
                                self.output_keys.add(key)
        self.generic_visit(node)

import itertools

class SSARewriter(ast.NodeTransformer):
    def __init__(self):
        self.counter = itertools.count()
        self.versions = {}
        self.rename_map = {}

    def visit_Assign(self, node):
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            orig_name = node.targets[0].id
            node.value = self.visit(node.value)
            new_name = f'{orig_name}_{next(self.counter)}'
            self.versions[orig_name] = new_name
            self.rename_map[orig_name] = new_name
            node.targets[0].id = new_name
            return node
        else:
            return self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load) and node.id in self.rename_map:
                node.id = self.rename_map[node.id]
        return node

class RemoveUnusedAssignments(ast.NodeTransformer):
    def __init__(self):
        self.changed = False

    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        assigned_vars = set()
        used_vars = set()
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    for t in ast.walk(target):
                        if isinstance(t, ast.Name) and isinstance(t.ctx, ast.Store):
                                assigned_vars.add(t.id)
            else:
                if isinstance(stmt, ast.AnnAssign):
                    target = stmt.target
                    if isinstance(target, ast.Name) and isinstance(target.ctx, ast.Store):
                            assigned_vars.add(target.id)
                else:
                    if isinstance(stmt, ast.Name) and isinstance(stmt.ctx, ast.Load):
                            used_vars.add(stmt.id)
        unused_vars = assigned_vars - used_vars
        if len(unused_vars) > 0:
            self.changed = True
            print('ununsed', unused_vars)
        def is_unused_assignment(stmt):
            def extract_names(target):
                if isinstance(target, ast.Name):
                    return [target.id]
                else:
                    if isinstance(target, ast.Tuple):
                        return [id for elt in target.elts for id in extract_names(elt)]
                    else:
                        return []
            if isinstance(stmt, ast.Assign):
                all_names = []
                for t in stmt.targets:
                    all_names.extend(extract_names(t))
                return all_names and all((name in unused_vars for name in all_names))
            else:
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    return stmt.target.id in unused_vars
                else:
                    return False

        class AssignmentCleaner(ast.NodeTransformer):
            def visit_Assign(self, stmt):
                return ast.Pass() if is_unused_assignment(stmt) else stmt
            def visit_AnnAssign(self, stmt):
                return ast.Pass() if is_unused_assignment(stmt) else stmt
        node.body = [AssignmentCleaner().visit(stmt) for stmt in node.body]
        return node

class RemoveIrrelevantConditions(ast.NodeTransformer):
    def visit_If(self, node):
        self.generic_visit(node)
        ret = False
        if len(node.body) == 0:
            ret = True
        else:
            if len(node.body) == 1:
                if isinstance(node.body[0], ast.Pass):
                    ret = True
                else:
                    if isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Pass):
                            ret = True
        if len(node.orelse)!= 0:
            ret = False
        if ret:
            return None
        else:
            return node

class ExpandInitLoopTransformer(ast.NodeTransformer):
    def __init__(self, input_dir, output_dir, input_keys, output_keys):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.input_keys = input_keys
        self.output_keys = output_keys
        self.all_keys = input_keys.union(output_keys)
    def visit_FunctionDef(self, node):
        if node.name == '__init__':
            new_body = []
            for stmt in node.body:
                if self._is_status_loop(stmt):
                    new_body.extend(self._generate_input_assignments())
                else:
                    if self._is_control_loop(stmt):
                        new_body.extend(self._generate_output_assignments())
                    else:
                        new_body.append(stmt)
            node.body = new_body
        else:
            self.generic_visit(node)
        return node

    def visit_Subscript(self, node):
        if isinstance(node.value, ast.Attribute) and isinstance(node.value.value, ast.Name) and (node.value.value.id == 'self') and (node.value.attr in {self.input_dir, self.output_dir}):
            key = None
            if isinstance(node.slice, ast.Constant):
                key = node.slice.value
            else:
                if isinstance(node.slice, ast.Index) and isinstance(node.slice.value, ast.Constant):
                        key = node.slice.value.value
            if isinstance(key, str) and key in self.all_keys:
                return ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr=key, ctx=node.ctx)
        return self.generic_visit(node)

    def _is_status_loop(self, node):
        return isinstance(node, ast.For) and isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Attribute) and (node.iter.func.attr == 'keys') and isinstance(node.iter.func.value, ast.Name) and (node.iter.func.value.id == self.input_dir)

    def _is_control_loop(self, node):
        return isinstance(node, ast.For) and isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Attribute) and (node.iter.func.attr == 'keys') and isinstance(node.iter.func.value, ast.Name) and (node.iter.func.value.id == self.output_dir)

    def _generate_input_assignments(self):
        return [ast.Assign(targets=[ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr=key, ctx=ast.Store())], value=ast.Call(func=ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr='addIn', ctx=ast.Load()), args=[ast.Subscript(value=ast.Name(id=self.input_dir, ctx=ast.Load()), slice=ast.Constant(value=key), ctx=ast.Load())], keywords=[])) for key in sorted(self.input_keys)]

    def _generate_output_assignments(self):
        return [ast.Assign(targets=[ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr=key, ctx=ast.Store())], value=ast.Call(func=ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr='addOut', ctx=ast.Load()), args=[ast.Subscript(value=ast.Name(id=self.output_dir, ctx=ast.Load()), slice=ast.Constant(value=key), ctx=ast.Load())], keywords=[])) for key in sorted(self.output_keys)]

def getClassTree(cls: type) -> ast.AST:
    """\n    Transforms a generator-based class\'s \'run\' method into a state machine \'clock\' method.\n\n    Args:\n        cls: The class object to transform.\n\n    Returns:\n        The AST of the class\n    """
    if not isinstance(cls, type):
        raise TypeError('Expected a class object')
    else:
        try:
            source = inspect.getsource(cls)
        except Exception as e:
            raise ValueError(f'Could not retrieve source for {cls.__name__}: {e}')
        source = textwrap.dedent(source)
        tree = ast.parse(source)
        class_node = next((n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == cls.__name__), None)
        if class_node is None:
            raise ValueError(f'Class {cls.__name__} not found in AST.')
        else:
            return class_node

def transform_generator_to_fsm(class_node: ast.AST) -> ast.AST:
    transformer = GeneratorToFSMTransformer()
    tree = transformer.visit(class_node)
    ast.fix_missing_locations(tree)
    return tree

def removeUnusedAssignments(tree: ast.AST) -> ast.AST:
    tr = RemoveUnusedAssignments()
    doRun = True
    while doRun:
        tr.changed = False
        tree = tr.visit(tree)
        doRun = tr.changed
    return tree

def inline_yield_from(class_node: ast.AST) -> ast.AST:
    transformer = YieldFromInliner(class_node)
    tree = transformer._phase2_apply_inlining()
    ast.fix_missing_locations(tree)
    return tree

def yield_to_state(class_node: ast.AST) -> ast.AST:
    tr = YieldStateTransformer()
    tree = tr.visit(class_node)
    ast.fix_missing_locations(tree)
    return tree

class ReplaceIfElseTreeByMatchCase(ast.NodeTransformer):
    """Transforms if/elif chains on the same variable into a match/case AST."""
    def visit_If(self, node):
        match_node = self.try_match_if_chain(node)
        if match_node:
            return match_node
        else:
            return self.generic_visit(node)

    def try_match_if_chain(self, node):
        # ***<module>.ReplaceIfElseTreeByMatchCase.try_match_if_chain: Failure: Different control flow
        var_expr = None
        case_list = []
        default_body = None
        cur = node
        while True:
            if not isinstance(cur.test, ast.Compare):
                return None
            cmp = cur.test
            if len(cmp.ops)!= 1 or not isinstance(cmp.ops[0], ast.Eq):
                return None
            if len(cmp.comparators)!= 1:
                return None
            lhs = cmp.left
            rhs = cmp.comparators[0]
            if var_expr is None:
                var_expr = lhs
            else:
                if ast.dump(var_expr)!= ast.dump(lhs):
                    return None
            pattern = ast.MatchValue(value=rhs)
            case_list.append(ast.match_case(pattern=pattern, guard=None, body=cur.body))
            if len(cur.orelse) == 1 and isinstance(cur.orelse[0], ast.If):
                cur = cur.orelse[0]
            else:
                if cur.orelse:
                    default_body = cur.orelse
                break
                if len(case_list) >= 2:
                    if default_body:
                        case_list.append(ast.match_case(pattern=ast.MatchAs(name=None), guard=None, body=default_body))
                    return ast.Match(subject=var_expr, cases=case_list)

