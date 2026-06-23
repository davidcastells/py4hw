# -*- coding: utf-8 -*-
"""
Created on Wed Jan 19 12:53:47 2022

@author: dcr
"""
from .. import *
from .bitwise import *

from deprecated import deprecated


class Add(Logic):

    def __init__(self, parent, name: str, a: Wire, b: Wire, r: Wire, ci=None, co=None, width_check=True):
        """
        Initialize the Add logic circuit.

        Parameters
        ----------
        parent : Logic
            Parent circuit.
        name : str
            Name of the instance.
        a : Wire
            First input wire.
        b : Wire
            Second input wire.
        r : Wire
            Output wire.
        ci : Wire, optional
            Carry-in wire. Defaults to None.
        co : Wire, optional
            Carry-out wire. Defaults to None.
        width_check : bool, optional
            Whether to perform width checks. Defaults to True.
        """
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)
        
        if (ci is None):
            ci = self.wire('ci')
            Constant(self, 'ci', 0, ci)
            self.ci = None
            
        else:
            self.ci = self.addIn('ci', ci)
            
        aw = a.getWidth()
        bw = b.getWidth()
        rw = r.getWidth()
        
        if (co is None):
            if (width_check): assert((rw  - max(aw,bw)) in [0,1])
            AddCarryIn(self, "add", a, b, r, ci)
            self.co = None
        else:
            if (width_check): assert(rw  == max(aw,bw) + 1 )
            self.co = self.addOut('co', co)
            pre_r = self.wire('pre_r', rw + 1)
            AddCarryIn(self, "add", a, b, pre_r, ci)
            Range(self, 'r', pre_r, rw-1, 0, r)
            Bit(self, 'co', pre_r, rw, co)
            
    def structureName(self):
        if (self.a.getWidth() == self.r.getWidth()) and (self.a.getWidth() == self.b.getWidth()):
            s =  f'Add{self.a.getWidth()}'
        else:
            s = f'Add{self.a.getWidth()}_{self.b.getWidth()}_{self.r.getWidth()}'
            
        if not(self.ci is None):
            s += '_ci'
        if not(self.co is None):
            s += '_co'
        return s
        
class SignedAdd(Logic):

    def __init__(self, parent, name: str, a: Wire, b: Wire, r: Wire, ci=None, co=None, width_check=True):
        """
        Initialize the SignedAdd logic circuit.

        Parameters
        ----------
        parent : Logic
            Parent circuit.
        name : str
            Name of the instance.
        a : Wire
            First input wire.
        b : Wire
            Second input wire.
        r : Wire
            Output wire.
        ci : Wire, optional
            Carry-in wire. Defaults to None.
        co : Wire, optional
            Carry-out wire. Defaults to None.
        width_check : bool, optional
            Whether to perform width checks. Defaults to True.
        """
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)
        
        aw = a.getWidth()
        bw = b.getWidth()
        rw = r.getWidth()
        
        assert(rw >= aw)
        assert(rw >= bw)
        
        if (rw > aw): 
            sa = self.wire('sa', rw)
            SignExtend(self, 'sa', a, sa)
        else:
            sa = a
            
        if (rw > bw):
            sb = self.wire('sb', rw)
            SignExtend(self, 'sb', b, sb)
        else:
            sb = b
            
        Add(self, 'add', sa, sb, r, ci, co, width_check=False)
        
    # def propagate(self):
    #     from ..helper import IntegerHelper    
        
    #     sa = IntegerHelper.c2_to_signed(self.a.get(), self.a.getWidth())
    #     sb = IntegerHelper.c2_to_signed(self.b.get(), self.b.getWidth())
    #     mask = (1 << self.r.getWidth()) - 1
    #     newValue = (sa + sb) & mask
    #     self.r.put(newValue)
        
class AddCarryIn(Logic):

    def __init__(self, parent, name: str, a: Wire, b: Wire, r: Wire, ci: Wire):
        """
        Initialize the AddCarryIn logic circuit.

        Parameters
        ----------
        parent : Logic
            Parent circuit.
        name : str
            Name of the instance.
        a : Wire
            First input wire.
        b : Wire
            Second input wire.
        r : Wire
            Output wire.
        ci : Wire
            Carry-in wire.
        """
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)
        
        assert(r.getWidth() >= a.getWidth() )
        self.ci = self.addIn('ci', ci)
        

    def propagate(self):
        self.r.put(self.a.get() + self.b.get() + self.ci.get())        


class Abs(Logic):

    def __init__(self, parent, name: str, a: Wire, r: Wire, inverted: Wire = None):
        """
        Initialize the Abs logic circuit.

        Parameters
        ----------
        parent : Logic
            Parent circuit.
        name : str
            Name of the instance.
        a : Wire
            Input wire.
        r : Wire
            Output wire with the absolute value of a.
        inverted : Wire, optional
            Output wire indicating whether a was negated. Defaults to None.
        """
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.r = self.addOut("r", r)

        if not(inverted is None):
            s = self.addOut('inverted', inverted)
        else:
            s = self.wire('sign')

        neg = self.wire('neg', a.getWidth())
        Sign(self, 'sign', a, s)
        Neg(self, 'neg', a, neg)
        Mux2(self, 'mux', s, a, neg, r)
        
    def structureName(self):
        if (self.a.getWidth() == self.r.getWidth()):
            return f'Abs{self.a.getWidth()}'
        else:
            return f'Abs{self.a.getWidth()}_{self.r.getWidth()}'


class Neg(Logic):
    def __init__(self, parent, name: str, a: Wire, r: Wire):
        """
        Initialize the Neg logic circuit.

        Parameters
        ----------
        parent : Logic
            Parent circuit.
        name : str
            Name of the instance.
        a : Wire
            Input wire.
        r : Wire
            Output wire with the negated value of a.
        """
        super().__init__(parent, name)

        self.a = self.addIn("a", a)
        self.r = self.addOut("r", r)

        zero = self.wire('zero', r.getWidth())
        Constant(self, 'zero', 0, zero)    
        Sub(self, 'sub', zero, a, r)

    def structureName(self):
        if (self.a.getWidth() == self.r.getWidth()):
            return f'Neg{self.a.getWidth()}'
        else:
            return f'Neg{self.a.getWidth()}_{self.r.getWidth()}'


class Sign(Logic):

    def __init__(self, parent, name: str, a: Wire, r: Wire):
        """
        Initialize the Sign logic circuit.

        This circuit determines the sign of the input wire `a` and outputs the result on wire `r`.
        The output `r` is 0 if `a` is non-negative and 1 if `a` is negative.

        Parameters
        ----------
        parent : Logic
            Parent circuit.
        name : str
            Name of the instance.
        a : Wire
            Input wire.
        r : Wire
            Output wire indicating the sign of `a`.
        """
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.r = self.addOut("r", r)

        assert(r.getWidth() == 1)
        Bit(self, "signBit", a, a.getWidth() - 1, r)
        
    def structureName(self):
        return f'Sign{self.a.getWidth()}'

class SignExtend(Logic):

    def __init__(self, parent: Logic, name: str, a: Wire, r: Wire):
        """
        Initialize the SignExtend logic circuit.

        This circuit extends the sign bit of the input wire `a` to the width of the output wire `r`.
        The sign bit of `a` is replicated to fill the additional bits in `r`, effectively sign-extending the value.

        Parameters
        ----------
        parent : Logic
            Parent circuit.
        name : str
            Name of the instance.
        a : Wire
            Input wire.
        r : Wire
            Output wire with sign-extended value of `a`.
        """
        super().__init__(parent, name)
        self.a = self.addIn('a', a)
        self.r = self.addOut('r', r)

    def propagate(self):
        """
        Propagate the sign extension operation.

        This method extends the sign bit of the input wire `a` to the width of the output wire `r`.
        The sign bit of `a` is replicated to fill the additional bits in `r`, effectively sign-extending the value.
        """
        value = self.a.get()
        hb = value >> (self.a.getWidth() - 1)
        for i in range(self.a.getWidth(), self.r.getWidth()):
            value = value | (hb << i)

        self.r.put(value)


class ZeroExtend(Logic):

    def __init__(self, parent: Logic, name: str, a: Wire, r: Wire):
        """
        Initialize the ZeroExtend logic circuit.

        This circuit extends the input wire `a` with zeros to the width of the output wire `r`.
        The additional bits in `r` are set to zero, effectively zero-extending the value.

        Parameters
        ----------
        parent : Logic
            Parent circuit.
        name : str
            Name of the instance.
        a : Wire
            Input wire.
        r : Wire
            Output wire with zero-extended value of `a`.
        """
        super().__init__(parent, name)
        self.a = self.addIn('a', a)
        self.r = self.addOut('r', r)

    def propagate(self):
        """
        Propagate the zero extension operation.

        This method extends the input wire `a` with zeros to the width of the output wire `r`.
        The additional bits in `r` are set to zero, effectively zero-extending the value.
        """
        value = self.a.get()
        self.r.put(value)



class Mul(Logic):

    def __init__(self, parent, name: str, a: Wire, b: Wire, r: Wire):
        """
        Initialize the Mul logic circuit.

        Parameters
        ----------
        parent : Logic
            Parent circuit.
        name : str
            Name of the instance.
        a : Wire
            First input wire.
        b : Wire
            Second input wire.
        r : Wire
            Output wire.
        """
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)

    def propagate(self):
        """
        Propagate the multiplication operation.

        Parameters
        ----------
        propagate_down : bool, optional
            Whether to propagate the result to downstream components. Defaults to True.
        """
        self.r.put(self.a.get() * self.b.get())

class SignedMul(Logic):

    def __init__(self, parent, name: str, a: Wire, b: Wire, r: Wire):
        """
        Initialize the SignedMul logic circuit.

        This circuit performs signed multiplication of two input wires `a` and `b` and outputs the result on wire `r`.
        The inputs are treated as signed integers, and the result is also a signed integer.

        Parameters
        ----------
        parent : Logic
            Parent circuit.
        name : str
            Name of the instance.
        a : Wire
            First input wire.
        b : Wire
            Second input wire.
        r : Wire
            Output wire containing the result of the signed multiplication.
        """
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)

    def propagate(self):
        """
        Propagate the signed multiplication operation.

        This method performs signed multiplication of the input wires `a` and `b` and outputs the result on wire `r`.
        The inputs are treated as signed integers, and the result is also a signed integer.
        """
        from ..helper import IntegerHelper    
        
        sa = IntegerHelper.c2_to_signed(self.a.get(), self.a.getWidth())
        sb = IntegerHelper.c2_to_signed(self.b.get(), self.b.getWidth())
        mask = (1 << self.r.getWidth()) - 1
        newValue = (sa * sb) & mask
        self.r.put(newValue)
        
class Div(Logic):

    def __init__(self, parent, name: str, a: Wire, b: Wire, r: Wire):
        """
        Initialize the Div logic circuit.

        This circuit performs integer division of two input wires `a` and `b` and outputs the result on wire `r`.
        The division is performed as integer division, and the result is the quotient.

        Parameters
        ----------
        parent : Logic
            Parent circuit.
        name : str
            Name of the instance.
        a : Wire
            Dividend input wire.
        b : Wire
            Divisor input wire.
        r : Wire
            Output wire containing the quotient of the division.
        """
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)

    def propagate(self):
        """
        Propagate the integer division operation.

        This method performs integer division of the input wires `a` and `b` and outputs the result on wire `r`.
        The division is performed as integer division, and the result is the quotient.
        If the divisor `b` is zero, a random value is assigned to the output wire `r` to avoid division by zero.
        """
        # @todo verilog implementation of div is unpredictable
        import random
        if (self.b.get() == 0):
            self.r.put(random.randint(0, 1<<self.r.getWidth()))
        else:
            self.r.put(self.a.get() // self.b.get())

class Mod(Logic):

    def __init__(self, parent, name: str, a: Wire, b: Wire, r: Wire):
        """
        Initialize the Mod logic circuit.

        This circuit computes the remainder of the division of two input wires `a` and `b` and outputs the result on wire `r`.
        The operation performed is the modulo operation, and the result is the remainder.

        Parameters
        ----------
        parent : Logic
            Parent circuit.
        name : str
            Name of the instance.
        a : Wire
            Dividend input wire.
        b : Wire
            Divisor input wire.
        r : Wire
            Output wire containing the remainder of the division.
        """
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)

    def propagate(self):
        """
        Propagate the modulo operation.

        This method computes the remainder of the division of the input wires `a` and `b` and outputs the result on wire `r`.
        The operation performed is the modulo operation, and the result is the remainder.
        If the divisor `b` is zero, a random value is assigned to the output wire `r` to avoid division by zero.
        """
        # @todo verilog implementation of div is unpredictable
        import random
        if (self.b.get() == 0):
            self.r.put(random.randint(0, 1<<self.r.getWidth()))
        else:
            self.r.put(self.a.get() % self.b.get())


class SignedDiv(Logic):

    def __init__(self, parent, name: str, a: Wire, b: Wire, r: Wire):
        """
        Initialize the SignedDiv logic circuit.

        This circuit performs signed integer division of two input wires `a` and `b` and outputs the result on wire `r`.
        The inputs are treated as signed integers, and the result is also a signed integer.

        Parameters
        ----------
        parent : Logic
            Parent circuit.
        name : str
            Name of the instance.
        a : Wire
            Dividend input wire.
        b : Wire
            Divisor input wire.
        r : Wire
            Output wire containing the quotient of the signed division.
        """
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)

        abs_a = self.wire('abs_a', a.getWidth())
        abs_b = self.wire('abs_b', b.getWidth())
        
        Abs(self, 'abs_a', a, abs_a)
        Abs(self, 'abs_b', b, abs_b)
        
        sign_a = self.wire('sign_a')
        sign_b = self.wire('sign_b')
        
        Sign(self, 'sign_a', a, sign_a)
        Sign(self, 'sign_b', b, sign_b)
       
        q = self.wire('q', r.getWidth())        
        neg_q = self.wire('neg_q', r.getWidth())
        
        Div(self, 'div', abs_a, abs_b, q)
        Neg(self, 'neg', q, neg_q)
        
        sign_r = self.wire('sign_r')
        Xor2(self, 'sign_r', sign_a, sign_b, sign_r) 
        
        Mux2(self, 'r', sign_r, q, neg_q, r)        
        

class Sub(Logic):

    def __init__(self, parent, name: str, a: Wire, b: Wire, r: Wire):
        """
        Initialize the Sub logic circuit.

        This circuit performs subtraction of two input wires `a` and `b` and outputs the result on wire `r`.
        The operation performed is `a - b`.

        Parameters
        ----------
        parent : Logic
            Parent circuit.
        name : str
            Name of the instance.
        a : Wire
            Minuend input wire.
        b : Wire
            Subtrahend input wire.
        r : Wire
            Output wire containing the result of the subtraction.
        """
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)

    def propagate(self):
        """
        Propagate the subtraction operation.

        This method performs subtraction of the input wires `a` and `b` and outputs the result on wire `r`.
        The operation performed is `a - b`.
        """
        mask = (1 << self.r.getWidth()) - 1
        newValue = (self.a.get() - self.b.get()) & mask
        self.r.put(newValue)


class SignedSub(Logic):

    def __init__(self, parent, name: str, a: Wire, b: Wire, r: Wire):
        """
        Initialize the SignedSub logic circuit.

        This circuit performs signed subtraction of two input wires `a` and `b` and outputs the result on wire `r`.
        The inputs are treated as signed integers, and the result is also a signed integer.
        The operation performed is `a - b`.

        Parameters
        ----------
        parent : Logic
            Parent circuit.
        name : str
            Name of the instance.
        a : Wire
            Minuend input wire.
        b : Wire
            Subtrahend input wire.
        r : Wire
            Output wire containing the result of the signed subtraction.
        """
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)
        
        aw = a.getWidth()
        bw = b.getWidth()
        rw = r.getWidth()
        
        # Ensure the result wire is wide enough for the inputs
        assert(rw >= aw)
        assert(rw >= bw)

        # --- 1. Sign Extend A ---
        if (rw > aw): 
            sa = self.wire('sa', rw)
            SignExtend(self, 'sa', a, sa)
        else:
            sa = a
            
        # --- 2. Sign Extend B ---
        if (rw > bw):
            sb = self.wire('sb', rw)
            SignExtend(self, 'sb', b, sb)
        else:
            sb = b
            
        # --- 3. Invert Sign Extended B (One's Complement) ---
        # We need the inverted B for A + (~B) + 1
        not_sb = self.wire('not_sb', rw)
        Not(self, 'not_sb', sb, not_sb)
        
        add_ci = self.wire('ci_one', 1)
        Constant(self, 'const_one', 1, add_ci)
            
        # --- 4. Perform Addition (A + (~B) + 1) ---
        # A - B = A + (~B) + 1
        # Add 'sa' (A) and 'inverted_sb' (~B).
        # The '1' is accounted for by setting the carry-in (ci) to 1.
        
        # Perform the final addition: sa + inverted_sb + ci (which is 1 for non-chained subtraction)
        Add(self, 'sub_add', sa, not_sb, r, add_ci, co=None, width_check=False)
        
    # def propagate(self):
    #     from ..helper import IntegerHelper    
        
    #     sa = IntegerHelper.c2_to_signed(self.a.get(), self.a.getWidth())
    #     sb = IntegerHelper.c2_to_signed(self.b.get(), self.b.getWidth())
    #     mask = (1 << self.r.getWidth()) - 1
    #     newValue = (sa - sb) & mask
    #     self.r.put(newValue)
        
class Counter(Logic):
    def __init__(self, parent, name: str, reset: Wire, inc: Wire, q: Wire):
        """
        Initialize the Counter logic circuit.

        This circuit counts up to the value specified by the width of the output wire `q` and returns to zero.
        The counting can be incremented by a signal on the `inc` wire and reset to zero by a signal on the `reset` wire.

        Parameters
        ----------
        parent : Logic
            Parent circuit.
        name : str
            Name of the instance.
        reset : Wire
            Input wire to reset the counter to zero.
        inc : Wire
            Input wire to increment the counter.
        q : Wire
            Output wire containing the current count value.
        """
        super().__init__(parent, name)
        
        from .bitwise import Constant
        from .bitwise import Or2
        from .bitwise import Mux2
        from .storage import Reg
        
        if not(reset is None):
            reset = self.addIn('reset', reset)
        if not(inc is None):
            inc = self.addIn('inc', inc)
        
        q = self.addOut('q', q)
    
        one = self.wire('one', q.getWidth())
        zero = self.wire('zero', q.getWidth())
        add = self.wire('add', q.getWidth())
        d = self.wire('d', q.getWidth())
        d1 = self.wire('d1', q.getWidth())
        e_add = self.wire('e_add', 1)
        
        Constant(self, 'one', 1, one)
        Constant(self, 'zero', 0, zero)
        
        if (inc is None):
            inc = one
        if (reset is None):
            reset = zero
            
        Mux2(self, 'muxinc', inc, q, add, d1)
        Mux2(self, 'muxreset', reset, d1, zero, d)

        #py4hw.Select(self, 'select', [reset, inc], [zero, add], d)
        Or2(self, 'e_add', reset, inc, e_add)
        #py4hw.Mux(self, 'mux', )
        Add(self, 'add', q, one, add)
        Reg(self, 'reg', d, q, e_add)
        
class ModuloCounter(Logic):
    def __init__(self, parent, name: str, mod: int, reset: Wire, inc: Wire, q: Wire, carryout: Wire):
        """

        This circuit counts up to the value specified by `mod` and returns to zero.
        The counting can be incremented by a signal on the `inc` wire and reset to zero by a signal on the `reset` wire.
        When the counter reaches `mod-1`, it generates a carry-out signal on the `carryout` wire.

        Parameters
        ----------
        parent : Logic
            Parent circuit.
        name : str
            Name of the instance.
        mod : int
            The modulus value up to which the counter counts.
        reset : Wire
            Input wire to reset the counter to zero.
        inc : Wire
            Input wire to increment the counter.
        q : Wire
            Output wire containing the current count value.
        carryout : Wire
            Output wire that generates a signal when the counter reaches `mod-1`.
        """
        super().__init__(parent, name)
        
        from .bitwise import Constant
        from .bitwise import Or2
        from .bitwise import Mux2
        from .storage import Reg
        from .relational import EqualConstant
        
        reset = self.addIn('reset', reset)
        inc = self.addIn('inc', inc)
        q = self.addOut('q', q)
        carryout = self.addOut('carryout', carryout)
    
        one = self.wire('one', q.getWidth())
        zero = self.wire('zero', q.getWidth())
        add = self.wire('add', q.getWidth())
        d = self.wire('d', q.getWidth())
        d1 = self.wire('d1', q.getWidth())
        e_add = self.wire('e_add', 1)
        anyreset = self.wire('anyreset', 1)
        
        Constant(self, 'one', 1, one)
        Constant(self, 'zero', 0, zero)
        
        Or2(self, 'anyreset', reset, carryout, anyreset)
        Mux2(self, 'muxinc', inc, q, add, d1)
        Mux2(self, 'muxreset', anyreset,  d1,zero, d)

        #py4hw.Select(self, 'select', [reset, inc], [zero, add], d)
        Or2(self, 'e_add', reset, inc, e_add)
        #py4hw.Mux(self, 'mux', )
        Add(self, 'add', q, one, add)
        Reg(self, 'reg', d, q, enable=e_add)
        EqualConstant(self, 'eq{}'.format(mod-1), q, mod-1, carryout)
        
        
class ShiftRight(Logic):
    def __init__(self, parent: Logic, name: str, a: Wire, b: Wire, r: Wire, arithmetic=False):
        """
        Initialize the ShiftRight logic circuit.

        This circuit performs a right shift on the input wire `a` by the number of positions specified by the input wire `b`.
        The result is stored in the output wire `r`. If `arithmetic` is True, the shift is arithmetic (sign-extended).
        If `arithmetic` is a Wire, it determines whether the shift is arithmetic or logical.

        Parameters
        ----------
        parent : Logic
            Parent circuit.
        name : str
            Name of the instance.
        a : Wire
            Input wire to be shifted.
        b : Wire
            Input wire specifying the number of positions to shift.
        r : Wire
            Output wire containing the result of the shift.
        arithmetic : bool or Wire, optional
            If True, performs an arithmetic shift (sign-extended). If a Wire, it determines the type of shift.
        """
        super().__init__(parent, name)

        a = self.addIn('a', a)
        b = self.addIn('b', b)
        r = self.addOut('r', r)
        
        last = a
        w = last.getWidth()
        wb = b.getWidth()
        
        if (isinstance(arithmetic, Wire)):
            self.addIn('arithmetic', arithmetic)
            
            signExtended = self.wire(f'sign_extended', w + (1<<wb))
            SignExtend(self, f'sign_extended', last, signExtended)
            
            zeroExtended = self.wire(f'zero_extended', w + (1<<wb))
            ZeroExtend(self, f'zero_extended', last, zeroExtended)

            last = self.wire(f'extended', w + (1<<wb))
            
            Mux2(self, 'extended', arithmetic, zeroExtended, signExtended, last)
            w = last.getWidth()           
            
        else:
            if (arithmetic):
                signExtended = self.wire(f'sign_extended', w + (1<<wb))
                SignExtend(self, f'sign_extended', last, signExtended)
                last = signExtended
                w = last.getWidth()
            else:
                pass
            

        if (wb > 6):
            print('WARNING shift registers with shifting value width > 5 are not common')
        
        
        for i in range(wb):
            shifted = self.wire('shifted{}'.format(i), w )
            
            ShiftRightConstant(self, 'shifted{}'.format(i), last, 1<<i, shifted)
            
            doShift = self.wire(f'doShift{i}')
            Bit(self, f'doShift{i}', b, i, doShift)
            prer = self.wire(f'shift_{i}', w)
            Mux2(self, f'shift_{i}', doShift, last, shifted, prer)
            last = prer
            
        Buf(self, 'r', prer, r)

class ShiftLeft(Logic):
    def __init__(self, parent: Logic, name: str, a: Wire, b: Wire, r: Wire):
        """
        Initialize the ShiftLeft logic circuit.

        This circuit performs a left shift on the input wire `a` by the number of positions specified by the input wire `b`.
        The result is stored in the output wire `r`.

        Parameters
        ----------
        parent : Logic
            Parent circuit.
        name : str
            Name of the instance.
        a : Wire
            Input wire to be shifted.
        b : Wire
            Input wire specifying the number of positions to shift.
        r : Wire
            Output wire containing the result of the shift.
        """
        super().__init__(parent, name)

        a = self.addIn('a', a)
        b = self.addIn('b', b)
        r = self.addOut('r', r)
            
        wa = a.getWidth()
        wb = b.getWidth()
        wr = r.getWidth()
        
        w = max(wa, wr)
        
        if (wb > 6):
            print('WARNING shift registers with shifting value width > 5 are not common')
            
        last = a
        for i in range(wb):
            shifted = self.wire('shifted{}'.format(i), w)
            ShiftLeftConstant(self, 'shifted{}'.format(i), last, 1<<i, shifted)
            
            doShift = self.wire(f'doShift{i}')
            Bit(self, f'doShift{i}', b, i, doShift)
            prer = self.wire(f'shift_{i}', w)
            Mux2(self, f'shift_{i}', doShift, last, shifted, prer)
            last = prer
            
        Buf(self, 'r', prer, r)

class RotateRight(Logic):
    def __init__(self, parent: Logic, name: str, a: Wire, b: Wire, r: Wire):
        """
        Initialize the RotateRight logic circuit.

        This circuit performs a right rotation on the input wire `a` by the number of positions specified by the input wire `b`.
        The result is stored in the output wire `r`.

        Parameters
        ----------
        parent : Logic
            Parent circuit.
        name : str
            Name of the instance.
        a : Wire
            Input wire to be rotated.
        b : Wire
            Input wire specifying the number of positions to rotate.
        r : Wire
            Output wire containing the result of the rotation.
        """
        super().__init__(parent, name)

        a = self.addIn('a', a)
        b = self.addIn('b', b)
        r = self.addOut('r', r)
            
        w = a.getWidth()
        wb = b.getWidth()
        
        if (wb > 6):
            print('WARNING shift registers with shifting value width > 5 are not common')
            
        last = a
        for i in range(wb):
            shifted = self.wire('shifted{}'.format(i), r.getWidth())
            RotateRightConstant(self, 'shifted{}'.format(i), last, 1<<i, shifted)
            
            doShift = self.wire(f'doShift{i}')
            Bit(self, f'doShift{i}', b, i, doShift)
            prer = self.wire(f'shift_{i}', a.getWidth())
            Mux2(self, f'shift_{i}', doShift, last, shifted, prer)
            last = prer
            
        Buf(self, 'r', prer, r)


class RotateLeft(Logic):
    def __init__(self, parent: Logic, name: str, a: Wire, b: Wire, r: Wire):
        """
        Initialize the RotateLeft logic circuit.

        This circuit performs a left rotation on the input wire `a` by the number of positions specified by the input wire `b`.
        The result is stored in the output wire `r`.

        Parameters
        ----------
        parent : Logic
            Parent circuit.
        name : str
            Name of the instance.
        a : Wire
            Input wire to be rotated.
        b : Wire
            Input wire specifying the number of positions to rotate.
        r : Wire
            Output wire containing the result of the rotation.
        """
        super().__init__(parent, name)

        a = self.addIn('a', a)
        b = self.addIn('b', b)
        r = self.addOut('r', r)
            
        w = a.getWidth()
        wb = b.getWidth()
        
        if (wb > 6):
            print('WARNING shift registers with shifting value width > 5 are not common')
            
        last = a
        for i in range(wb):
            shifted = self.wire('shifted{}'.format(i), r.getWidth())
            RotateLeftConstant(self, 'shifted{}'.format(i), last, 1<<i, shifted)
            
            doShift = self.wire(f'doShift{i}')
            Bit(self, f'doShift{i}', b, i, doShift)
            prer = self.wire(f'shift_{i}', a.getWidth())
            Mux2(self, f'shift_{i}', doShift, last, shifted, prer)
            last = prer
            
        Buf(self, 'r', prer, r)

        
class BinaryToBCD(Logic):
    
    def __init__(self, parent, name : str, a: Wire, r:Wire):
        """
        Initialize the BinaryToBCD logic circuit.

        This circuit converts a binary number represented by the input wire `a` into Binary-Coded Decimal (BCD) format.
        The result is stored in the output wire `r`.

        Parameters
        ----------
        parent : Logic
            Parent circuit.
        name : str
            Name of the instance.
        a : Wire
            Input wire containing the binary number to be converted.
        r : Wire
            Output wire containing the BCD representation of the input number.
        """
        from ..helper import LogicHelper    

        super().__init__(parent, name)
        
        a = self.addIn('a', a)
        r = self.addOut('r', r)
    
        hlp = LogicHelper(self)
        
        w = a.getWidth()
        assert(r.getWidth() % 4 == 0)
        digits = r.getWidth() // 4 # int(math.ceil(math.log10((2**w)-1)))
        print('Number of BCD digits:', digits)
        print('r width:', r.getWidth())
        
        assert(r.getWidth() >= (digits*4))
        
        ret = []
        v = a
        k10 = hlp.hw_constant(4, 10)
        
        for i in range(digits):
            rem = self.wire('mod{}'.format(i), 4)
            div = self.wire('div{}'.format(i), w)
            Mod(self, 'mod{}'.format(i), v, k10, rem)
            Div(self, 'div{}'.format(i), v, k10, div)
            ret.append(rem)
            v = div
            
        ConcatenateLSBF(self, 'r', ret, r)
        

    class _FFunction(Logic):
        """
        F function described in the paper DOI: 10.1109/TVLSI.2008.2000458
        """
        def __init__(self, parent, name : str, a: list, r:Wire):
            super().__init__(parent, name)
    
            w = len(a)
            an = []
    
            for i in range(w):
                self.addIn('in{}'.format(i), a[i])
                ann = self.wire('an{}'.format(i))
                Not(self, 'an{}'.format(i), a[i], ann)
                an.append(ann)
    
            self.addOut('r', r)
    
            products = []
            notcount = 0
            idx = w-1
            negidx_start = w-2
            negidx_stop = w-2
    
            while (True):
                prodsig = [a[idx]]
                #print('positive:', idx, 'negative:', end='')
    
                for j in range(negidx_start, negidx_stop, -2):
                    #print(j, end=',')
                    prodsig.append(an[j])
    
                #print()
                prod = self.wire('prod{}'.format(idx))
    
                if (len(prodsig) > 1):
                    And(self, 'and{}'.format(idx), prodsig, prod)
                    products.append(prod)
                else:
                    products.append(prodsig[0])
    
                idx -= 2
                negidx_stop -= 2
    
                if (idx < 0):
                    break;
    
            if (len(products) > 1):
                Or(self, 'or', products, r)
            else:
                Buf(self, 'r', products[0], r)
            
class CountLeadingZeros(Logic):

    def __init__(self, parent: Logic, name: str, a: Wire, r: Wire, z: Wire):
        """
        Initialize the CountLeadingZeros logic circuit.

        This circuit counts the number of leading zero bits in the input wire `a` and outputs the count on wire `r`.
        The circuit also outputs a wire `z` indicating whether the input is zero (all bits are zero).
        The design is based on the paper:
        Dimitrakopoulos, Giorgos, Kostas Galanopoulos, Christos Mavrokefalidis, 
        and Dimitris Nikolos. "Low-power leading-zero counting and anticipation 
        logic for high-speed floating point units." IEEE transactions on very large 
        scale integration (VLSI) systems 16, no. 7 (2008): 837-850.
        https://ieeexplore.ieee.org/stamp/stamp.jsp?arnumber=4539802    
        DOI: 10.1109/TVLSI.2008.2000458

        Parameters
        ----------
        parent : Logic
            Parent circuit.
        name : str
            Name of the instance.
        a : Wire
            Input wire.
        r : Wire
            Output wire containing the count of leading zero bits.
        z : Wire
            Output wire indicating whether the input is zero (all bits are zero).
        """
        super().__init__(parent, name)
        
        a = self.addIn('a', a)
        r = self.addOut('r', r)
        z = self.addOut('z', z)

        aw = a.getWidth()
        rw = r.getWidth()
        
        r_intern_w = int(math.ceil(math.log2(aw)))
        if (r_intern_w > rw):
            raise Exception('r with too small for a input')
            
        # we must extend the input to a power of 2
        # if we do that, we should subtract the extra bits from the result
        a_intern_w = int(math.pow(2, r_intern_w))
        a_intern = self.wire('a_intern', a_intern_w)
        
        ZeroExtend(self, 'zexta', a, a_intern)
            
        r_intern = self.wire('r_intern', r_intern_w)
        
        r_preout = self.wire('r_preout', r.getWidth())
        
        # we support bigger than necessary outputs by automatically
        # zero extending
        ZeroExtend(self, 'zextr', r_intern, r_preout)
        
        # Work with individual a wires
        a_bits = self.wires('a', a_intern_w, 1)
        BitsLSBF(self, 'a_bits', a_intern, a_bits)
        
        # Work with indidual wires , and concatenate them into the r_intern
        r_bits = self.wires('r_intern', r_intern_w, 1)
        
        ConcatenateLSBF(self, 'concat', r_bits, r_intern)
        
        f_bits = a_bits
        
        #print('len f_bits:', len(f_bits))
        
        for i in range(r_intern_w):
            fvalue = self.wire('f{}'.format(i))
            _FFunction(self, 'f_{}'.format(i), f_bits, fvalue)
            Not(self, 'z_{}'.format(i), fvalue, r_bits[i])
            
            next_f_bits_w = len(f_bits)//2
            next_f_bits = self.wires('f{}'.format(i), next_f_bits_w, 1)
            
            #print('level', i, next_f_bits_w)
            for j in range(next_f_bits_w):

                Or2(self, 'o{}_{}'.format(i,j), f_bits[j*2], f_bits[j*2+1], next_f_bits[j])
            
            f_bits = next_f_bits
            
        # we should end with a single wire in f_bits
        Not(self, 'not_z', f_bits[0], z)
        
        allZeroK = self.wire('allZeroK', r.getWidth())
        Constant(self, 'allZeroK', a.getWidth(), allZeroK)

        if (a_intern_w > aw):
            r_preout2 = self.wire('preout2', rw)
            extra = self.wire('extra', rw)
            Constant(self, 'extra', a_intern_w-aw, extra)
            Sub(self, 'sub', r_preout, extra, r_preout2)
            r_preout = r_preout2

        Mux2(self, 'final', z, r_preout, allZeroK, r)
        
