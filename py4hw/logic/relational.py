# -*- coding: utf-8 -*-
"""
Created on Wed Jan 19 12:53:34 2022

@author: dcr
"""
from .. import *

from deprecated import deprecated

class AnyEqual(Logic):
    """
    Checks whether there are any equal values in the inputs
    """
    
    def __init__(self, parent, name, ins, r:Wire):
        super().__init__(parent, name)
        
        from .bitwise import Or
        from .bitwise import Not
        
        r = self.addOut('r',r)
        lins = []
        for idx, inv in enumerate(ins):
            lins.append(self.addIn('in{}'.format(idx), inv))
            
        num = len(ins)
        checks = []
        for i in range(num):
            for j in range(num):
                if (i != j):
                    rp = self.wire('eq_{}_{}'.format(i,j), 1)
                    Equal(self, 'eq_{}_{}'.format(i,j), lins[i], lins[j], rp)
                    checks.append(rp)

        Or(self, 'anyEqual', checks, r)

class NotEqualConstant(Logic):
    """
    An Equal comparator circuit
    """

    def __init__(self, parent, name: str, a: Wire, v: int, r: Wire):
        super().__init__(parent, name)

        from .bitwise import Not

        self.addIn("a", a)
        self.addOut("r", r)
        
        eq = self.wire('eq')
        EqualConstant(self, 'eq', a, v, eq)
        Not(self, 'r', eq, r)
                
class EqualConstant(Logic):
    """
    An Equal comparator circuit
    """

    def __init__(self, parent, name: str, a: Wire, v: int, r: Wire):
        super().__init__(parent, name)

        from .bitwise import BitsLSBF
        from .bitwise import Minterm
        from .bitwise import Buf
        from .bitwise import Not

        # we save the values for Verilog generation
        self.a = self.addIn("a", a)
        self.r = self.addOut("r", r)
        self.v = v

        w = a.getWidth()
        
        if (w == 1):
            # very simple case
            if (v == 0):
                Not(self, 'buf', a, r)
            else:
                Buf(self, 'not', a, r)
                
        else:
            bits = self.wires('b', a.getWidth(), 1)   
            BitsLSBF(self, "bits", a, bits)
            Minterm(self, 'm{}'.format(v), bits, v, r)



class Equal(Logic):
    """
    An Equal comparator circuit
    """

    def __init__(self, parent, name: str, a: Wire, b: Wire, r: Wire):
        super().__init__(parent, name)

        from .bitwise import BitsLSBF
        from .bitwise import Minterm
        from .bitwise import Buf
        from .bitwise import Xor2
        from .bitwise import Nor
        from .bitwise import Not


        a = self.addIn("a", a)
        b = self.addIn("b", b)
        r = self.addOut("r", r)

        # save them for RTL 
        self.a = a
        self.b = b
        self.r = r

        w = a.getWidth()
        
        xor = self.wire('xor', w)
        
        if (w == 1):
            # simple case
            Xor2(self, 'xor', a, b, xor)
            Not(self, 'not', xor, r)
            
        else:
            Xor2(self, 'xor', a, b, xor)
            
            bits = self.wires('bits', w, 1)
            BitsLSBF(self, 'bits', xor, bits)
            
            Nor(self, 'nor', bits, r)
        
class Comparator(Logic):
    """
    A Greater Than, Equal and Less Than comparator circuit
    """

    def __init__(self, parent:Logic, name: str, a: Wire, b: Wire, gt: Wire, eq: Wire, lt: Wire):
        """
        Constructor of the comparator circuit

        Parameters
        ----------
        parent : Logic
            parent circuit.
        name : str
            instance name.
        a : Wire
            operand a.
        b : Wire
            operand b.
        gt : Wire
            1 if a > b.
        eq : Wire
            1 if a == b.
        lt : Wire
            1 if a < b.

        Returns
        -------
        the object.

        """
        
        from .bitwise import Equal
        from .bitwise import And2
        from .bitwise import Not
        from .bitwise import Mux2
        from .arithmetic import Sub
        from .arithmetic import Sign

        super().__init__(parent, name)
        
        if (a.getWidth() != b.getWidth()):
            raise Exception('a and b must have equal width')
            
        a = self.addIn("a", a)
        b = self.addIn("b", b)
        gt = self.addOut("gt", gt)
        eq = self.addOut("eq", eq)
        lt = self.addOut("lt", lt)

        sub = Wire(self, "sub", a.getWidth()+1)
        notLT = Wire(self, "nLT", 1)
        notEQ = Wire(self, "nEQ", 1)

        Sub(self, "Comparison", a, b, sub)

        # LT
        Sign(self, "LessThan", sub, lt)

        # EQ
        EqualConstant(self, "Equal", sub, 0, eq)

        # GT
        Not(self, "nLT", lt, notLT)
        Not(self, "nEQ", eq, notEQ)
        And2(self, "GT", notEQ, notLT, gt)


class ComparatorSignedUnsigned(Logic):
    """
    A Greater Than, Equal and Less Than comparator circuit that considers a and b having sign or not
    """

    def __init__(self, parent:Logic, name: str, a: Wire, b: Wire, gtu: Wire, eq: Wire, ltu: Wire, gt:Wire, lt:Wire):
        """
        Constructor of the comparator circuit

        Parameters
        ----------
        parent : Logic
            parent circuit.
        name : str
            instance name.
        a : Wire
            operand a.
        b : Wire
            operand b.
        gt : Wire
            1 if a > b.
        eq : Wire
            1 if a == b.
        lt : Wire
            1 if a < b.

        Returns
        -------
        the object.

        """
        
        from .bitwise import Equal
        from .bitwise import And2
        from .bitwise import Not
        from .bitwise import Xor2
        from .bitwise import Mux2
        from .arithmetic import Sub
        from .arithmetic import Sign

        super().__init__(parent, name)
        
        if (a.getWidth() != b.getWidth()):
            raise Exception('a and b must have equal width')
            
        a = self.addIn("a", a)
        b = self.addIn("b", b)
        gt = self.addOut("gt", gt)
        gtu = self.addOut("gtu", gtu)
        eq = self.addOut("eq", eq)
        lt = self.addOut("lt", lt)
        ltu = self.addOut("ltu", ltu)

        sa = self.wire('sa')
        sb = self.wire('sb')
        difs = self.wire('difs')
        
        Sign(self, "signA", a, sa)
        Sign(self, "signB", b, sb)
        Xor2(self, 'diff_signs', sa, sb, difs)
        

        sub = Wire(self, "sub", a.getWidth()+1)
        notLTU = Wire(self, "nLTU", 1)
        notEQ = Wire(self, "nEQ", 1)

        Sub(self, "Comparison", a, b, sub)

        # LT
        Sign(self, "LessThanUnsigned", sub, ltu)
        Xor2(self, 'lt', ltu, difs, lt)

        # EQ
        EqualConstant(self, "Equal", sub, 0, eq)

        # GT
        Not(self, "nLTU", ltu, notLTU)
        Not(self, "nEQ", eq, notEQ)
        And2(self, "GTU", notEQ, notLTU, gtu)
        Xor2(self, 'gt', gtu, difs, gt)
        
class Max2(Logic):
    """
    A circuit that computes the maximum from two inputs
    """

    def __init__(self, parent:Logic, name: str, a: Wire, b: Wire, r: Wire):
        """
        Implements the function r = max(a,b)

        Parameters
        ----------
        parent : Logic
            DESCRIPTION.
        name : str
            DESCRIPTION.
        a : Wire
            DESCRIPTION.
        b : Wire
            DESCRIPTION.
        r : Wire
            DESCRIPTION.

        Returns
        -------
        None.

        """
        from .bitwise import Mux2
        
        super().__init__(parent, name)
        
        a = self.addIn('a', a)
        b = self.addIn('b', b)
        r = self.addOut('r', r)
        
        gt = self.wire('gt')
        eq = self.wire('eq')
        lt = self.wire('lt')
        
        Comparator(self, 'comp', a, b, gt, eq, lt)
        
        Mux2(self, 'mux', lt, a, b, r)
        
        
class FPComparator_SP(Logic):
    
    def __init__(self, parent:Logic, name:str, a:Wire, b:Wire, gt:Wire, eq:Wire, lt:Wire, absolute:bool=False):
        """
        Compares two floating point numbers.
        It supports a normal mode than checks (a>b), (a==b), (a<b)
        and a absolute mode that checks (|a|>|b|),(|a|==|b|),(|a|<|b|)         

        Parameters
        ----------
        parent : Logic
            parent circuit.
        name : str
            instance name.
        a : Wire
            first input.
        b : Wire
            second input.
        gt : Wire
            Active if a > b (normal mode) or |a| > |b| (absolute mode).
        eq : Wire
            Active if a == b (normal mode) or |a| == |b| (absolute mode).
        lt : Wire
            Active if a < b (normal mode) or |a| < |b| (absolute mode).
.
        absolute : bool, optional
            Selects the absolute mode. The default is False.

        Returns
        -------
        Returns the circuit object.

        """
        super().__init__(parent, name)
        
        from .bitwise import Bit
        from .bitwise import And
        from .bitwise import Or
        from .bitwise import Range
        import sys
        
        # This is really cumbersome
        if not('..' in sys.path):
            sys.path.append ('..')
            
        import py4hw.helper
        
        a = self.addIn('a', a)
        b = self.addIn('b', b)
        gt = self.addOut('gt', gt)
        eq = self.addOut('eq', eq)
        lt = self.addOut('lt', lt)
        
        sa = self.wire('sa')
        sb = self.wire('sb')
        ea = self.wire('ea', 8)
        eb = self.wire('eb', 8)
        ma = self.wire('ma', 23)
        mb = self.wire('mb', 23)
        
        Bit(self, 'sa',a, 31, sa)
        Bit(self, 'sb',b, 31, sb)
        Range(self, 'ea', a, 30, 23, ea)
        Range(self, 'eb', b, 30, 23, eb)
        Range(self, 'ma', a, 22, 0, ma)
        Range(self, 'mb', b, 22, 0, mb)
        
        s_eq = self.wire('s_eq')
        
        Equal(self, 's_eq', sa, sb, s_eq)        
        
        e_gt = self.wire('e_gt')
        e_eq = self.wire('e_eq')
        e_lt = self.wire('e_lt')
        
        Comparator(self, 'cmp_e', ea, eb, e_gt, e_eq, e_lt)
        
        m_gt = self.wire('m_gt')
        m_eq = self.wire('m_eq')
        m_lt = self.wire('m_lt')
        
        Comparator(self, 'cmp_m', ma, mb, m_gt, m_eq, m_lt)

        
        # we use the helper to speed up writing combinational 
        # expressions
        g = py4hw.helper.LogicHelper(self)

        if (absolute):
            # In absolute mode we ignore the sign
            gt_if1 = e_gt 
            gt_if2 = g.hw_and2(e_eq, m_gt)
    
            Or(self, 'gt', [gt_if1, gt_if2], gt)
            
            And(self, 'eq', [e_eq, m_eq], eq)
            
            lt_if1 = e_lt
            lt_if2 = g.hw_and2(e_eq, m_lt)
            
            Or(self, 'lt', [lt_if1, lt_if2], lt)
        else:
            gt_if0 = g.hw_and2(g.hw_not(sa), sb)
            gt_if1 = g.hw_and2(s_eq, g.hw_mux2(sa, e_gt, e_lt) )
            gt_if2 = g.hw_and3(s_eq, e_eq, g.hw_mux2(sa, m_gt, m_lt))
    
            Or(self, 'gt', [gt_if0, gt_if1, gt_if2], gt)
            
            And(self, 'eq', [s_eq, e_eq, m_eq], eq)
            
            lt_if0 = g.hw_and2(sa, g.hw_not(sb)) 
            lt_if1 = g.hw_and2(s_eq, g.hw_mux2(sa, e_lt, e_gt))
            lt_if2 = g.hw_and3(s_eq, e_eq, g.hw_mux2(sa, m_lt, m_gt))
            
            Or(self, 'lt', [lt_if0, lt_if1, lt_if2], lt)
        
        

class Swap(Logic):
    """
    A circuit that computes the maximum from two inputs
    """

    def __init__(self, parent:Logic, name: str, a: Wire, b: Wire, swap:Wire, ra: Wire, rb:Wire):
        """
        Swaps a and b if swap is active

        Parameters
        ----------
        parent : Logic
            DESCRIPTION.
        name : str
            DESCRIPTION.
        a : Wire
            DESCRIPTION.
        b : Wire
            DESCRIPTION.
        swap : Wire
            DESCRIPTION.
        ra : Wire
            DESCRIPTION.
        rb : Wire
            DESCRIPTION.

        Returns
        -------
        None.

        """
        from .bitwise import Mux2
        
        super().__init__(parent, name)
        
        a = self.addIn('a', a)
        b = self.addIn('b', b)
        swap = self.addIn('swap', swap)
        ra = self.addOut('ra', ra)
        rb = self.addOut('rb', rb)
        
        Mux2(self, 'muxa', swap, a, b, ra)
        Mux2(self, 'muxb', swap, b, a, rb)
        

class FixedPointComparator(Logic):
    """
    A Greater Than, Equal and Less Than comparator circuit
    """

    def __init__(self, parent:Logic, name: str, a: Wire, af, b: Wire, bf, gt: Wire, eq: Wire, lt: Wire):
        """
        Constructor of the comparator circuit

        Parameters
        ----------
        parent : Logic
            parent circuit.
        name : str
            instance name.
        a : Wire
            operand a.
        b : Wire
            operand b.
        gt : Wire
            1 if a > b.
        eq : Wire
            1 if a == b.
        lt : Wire
            1 if a < b.

        Returns
        -------
        the object.

        """
        
        from .bitwise import Equal
        from .bitwise import And2
        from .bitwise import Not
        from .bitwise import Mux2
        from .arithmetic_fxp import FixedPointSub
        from .arithmetic_fxp import FixedPointSign

        super().__init__(parent, name)
        
        if (a.getWidth() != b.getWidth()):
            raise Exception('a and b must have equal width')
            
        a = self.addIn("a", a)
        b = self.addIn("b", b)
        gt = self.addOut("gt", gt)
        eq = self.addOut("eq", eq)
        lt = self.addOut("lt", lt)

        sub = Wire(self, "sub", a.getWidth())
        notLT = Wire(self, "nLT", 1)
        notEQ = Wire(self, "nEQ", 1)

        FixedPointSub(self, "Comparison", a, af, b, bf, sub, af)

        # LT
        if (not(lt is None)):
            FixedPointSign(self, "LessThan", sub, af, lt)

        # EQ
        if (not(eq is None)):
            EqualConstant(self, "Equal", sub, 0, eq)

        # GT
        if (not(gt is None)):
            Not(self, "nLT", lt, notLT)
            Not(self, "nEQ", eq, notEQ)
            And2(self, "GT", notEQ, notLT, gt)

        