# -*- coding: utf-8 -*-
"""
Created on Wed Jan 19 12:53:47 2022

@author: dcr
"""
from .. import *
from .bitwise import *

from deprecated import deprecated


class Add(Logic):
    """
    Combinational Arithmetic Add
    """

    def __init__(self, parent, name: str, a: Wire, b: Wire, r: Wire, ci=None, co=None):
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)
        
        if (ci is None):
            self.ci = None
        else:
            self.ci = self.addIn('ci', ci)
            
        if (co is None):
            self.co = None
        else:
            self.co = self.addOut('co', co)

    def propagate(self):
        if (not(self.ci is None)):
            vci = self.ci.get()
        else:
            vci = 0

        vr = self.a.get() + self.b.get() + vci
        
        if (not(self.co is None)):
            self.co.put(vr >> self.r.getWidth())
            
        self.r.put(vr)

class Abs(Logic):
    """
    Absolute value
    """
    def __init__(self, parent, name: str, a: Wire, r: Wire, inverted:Wire=None):
        """
        Creates ans absolute value circuit r = abs(a), inverted=sign(a)

        Parameters
        ----------
        parent : TYPE
            parent.
        name : str
            name.
        a : Wire
            input.
        r : Wire
            absolute value of a.
        inverted : Wire, optional
            indicates wether a was negated. The default is None.

        Returns
        -------
        None.

        """
        super().__init__(parent, name)
        a = self.addIn("a", a)
        r = self.addOut("r", r)

        if not(inverted is None):
            s = self.addOut('inverted', inverted)
        else:
            s = self.wire('sign')

        zero = self.wire('zero', r.getWidth())
        neg = self.wire('neg', a.getWidth())
        Constant(self, 'zero', 0, zero)
        Sign(self, 'sign', a, s)
        Sub(self, 'sub', zero, a, neg)
        Mux2(self, 'mux', s, a, neg, r)


class Neg(Logic):
    def __init__(self, parent, name: str, a: Wire, r: Wire):
        super().__init__(parent, name)

        self.addIn("a", a)
        self.addOut("r", r)

        zero = self.wire('zero', r.getWidth())
        Constant(self, 'zero', 0, zero)    
        Sub(self, 'sub', zero, a, r)

class Sign(Logic):
    """
    Sign test.
    r = 0 if a >= 0 (positive)
    t = 1 if a < 0 (negative)
    """

    def __init__(self, parent, name: str, a: Wire, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.r = self.addOut("r", r)

        Bit(self, "signBit", a, a.getWidth() - 1, r)
        

class SignExtend(Logic):
    """
    Behaviouraly modeled sign extend
    """
    def __init__(self, parent: Logic, name: str, a: Wire, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn('a', a)
        self.r = self.addOut('r', r)

    def propagate(self):
        value = self.a.get()
        hb = value >> (self.a.getWidth() - 1)
        for i in range(self.a.getWidth(), self.r.getWidth()):
            value = value | (hb << i)

        self.r.put(value)


class ZeroExtend(Logic):
    """
    Behaviouraly modeled zero extend
    """
    def __init__(self, parent: Logic, name: str, a: Wire, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn('a', a)
        self.r = self.addOut('r', r)

    def propagate(self):
        value = self.a.get()
        self.r.put(value)



class Mul(Logic):
    """
    Combinational Arithmetic Multiplier
    """

    def __init__(self, parent, name: str, a: Wire, b: Wire, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)

    def propagate(self):
        self.r.put(self.a.get() * self.b.get())

class SignedMul(Logic):
    """
    Arithmetic Signed Multiplier
    """
    def __init__(self, parent, name: str, a: Wire, b: Wire, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)

    def propagate(self):
        from ..helper import IntegerHelper    
        
        sa = IntegerHelper.c2_to_signed(self.a.get(), self.a.getWidth())
        sb = IntegerHelper.c2_to_signed(self.b.get(), self.b.getWidth())
        mask = (1 << self.r.getWidth()) - 1
        newValue = (sa * sb) & mask
        self.r.put(newValue)
        
class Div(Logic):
    """
    Combinational Arithmetic Divider
    """

    def __init__(self, parent, name: str, a: Wire, b: Wire, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)

    def propagate(self):
        # @todo verilog implementation of div is unpredictable
        import random
        if (self.b.get() == 0):
            self.r.put(random.randint(0, 1<<self.r.getWidth()))
        else:
            self.r.put(self.a.get() // self.b.get())

class Mod(Logic):
    """
    Combinational Arithmetic Modulo (reminder of div)
    """

    def __init__(self, parent, name: str, a: Wire, b: Wire, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)

    def propagate(self):
        # @todo verilog implementation of div is unpredictable
        import random
        if (self.b.get() == 0):
            self.r.put(random.randint(0, 1<<self.r.getWidth()))
        else:
            self.r.put(self.a.get() % self.b.get())


class SignedDiv(Logic):
    """
    Combinational Arithmetic Divider
    """

    def __init__(self, parent, name: str, a: Wire, b: Wire, r: Wire):
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
    """
    Arithmetic Sub
    """

    def __init__(self, parent, name: str, a: Wire, b: Wire, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)

    def propagate(self):
        mask = (1 << self.r.getWidth()) - 1
        newValue = (self.a.get() - self.b.get()) & mask
        self.r.put(newValue)


class SignedSub(Logic):
    """
    Arithmetic Sub
    """
    

    def __init__(self, parent, name: str, a: Wire, b: Wire, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)

    def propagate(self):
        from ..helper import IntegerHelper    
        
        sa = IntegerHelper.c2_to_signed(self.a.get(), self.a.getWidth())
        sb = IntegerHelper.c2_to_signed(self.b.get(), self.b.getWidth())
        mask = (1 << self.r.getWidth()) - 1
        newValue = (sa - sb) & mask
        self.r.put(newValue)
        
class Counter(Logic):
    """
    Counts up to the value mod and returns to zero
    """
    def __init__(self, parent, name : str, reset:Wire , inc:Wire , q:Wire ):
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
    """
    Counts up to the value mod and returns to zero
    """
    def __init__(self, parent, name : str, mod : int, reset , inc , q , carryout):
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
    def __init__(self, parent:Logic, name:str, a, b, r, arithmetic=False):
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
                #
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
    def __init__(self, parent:Logic, name:str, a, b, r):
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
            ShiftLeftConstant(self, 'shifted{}'.format(i), last, 1<<i, shifted)
            
            doShift = self.wire(f'doShift{i}')
            Bit(self, f'doShift{i}', b, i, doShift)
            prer = self.wire(f'shift_{i}', a.getWidth())
            Mux2(self, f'shift_{i}', doShift, last, shifted, prer)
            last = prer
            
        Buf(self, 'r', prer, r)

class RotateRight(Logic):
    def __init__(self, parent:Logic, name:str, a, b, r):
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
    def __init__(self, parent:Logic, name:str, a, b, r):
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
    """
    Converts a binary number into BCD digits
    """
    
    def __init__(self, parent, name : str, a: Wire, r:Wire):
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
    """
    Count leading zero bits
    We implement the design described in 
    Dimitrakopoulos, Giorgos, Kostas Galanopoulos, Christos Mavrokefalidis, 
    and Dimitris Nikolos. "Low-power leading-zero counting and anticipation 
    logic for high-speed floating point units." IEEE transactions on very large 
    scale integration (VLSI) systems 16, no. 7 (2008): 837-850.
    https://ieeexplore.ieee.org/stamp/stamp.jsp?arnumber=4539802    
    DOI: 10.1109/TVLSI.2008.2000458
    """
    def __init__(self, parent, name : str, a: Wire, r:Wire, z:Wire):
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
        