# -*- coding: utf-8 -*-
"""
Created on Wed Jan 19 12:36:38 2022

@author: dcr
"""
from .. import *
from .relational import *
from deprecated import deprecated
import math



class ShiftLeft(Logic):
    def __init__(self, parent, name: str, a: Wire, n: int, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn('a', a)
        self.r = self.addOut('r', r)
        self.n = n

    def propagate(self):
        self.r.put(self.a.get() << self.n)



class And2(Logic):
    """
    Binary And
    """

    def __init__(self, parent, name: str, a: Wire, b: Wire, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)

    def propagate(self):
        self.r.put(self.a.get() & self.b.get())
        
        
class And(Logic):
    def __init__(self, parent, name:str, ins, r: Wire):
        super().__init__(parent, name)
        lins = []
        r = self.addOut('r', r)
        w = r.getWidth()
        
        for idx, inv in enumerate(ins):
            lins.append(self.addIn('in{}'.format(idx), inv))

        # store inputs/outputs for RTL generation
        self.r = r
        self.ins = lins
        
        num = len(ins)

        if (num == 2):
            And2(self, 'and2', ins[0], ins[1], r)
            return
            
        if (num < 3):
            raise Exception('List should be > 2')

        # by now we do an inefficient ladder structure, we should
        # do a more fancy logarithmic design
        
        auxin = lins[0]
        auxout = self.wire('and{}'.format(0), w)
        
        for i in range(num-1):
            # print('creating and{} input0: {}'.format(i, auxin.getFullPath()))
            # print('creating and{} input1: {}'.format(i, lins[i+1].getFullPath()))
            # print('creating and{} output: {}'.format(i, auxout.getFullPath()))
            And2(self, 'and{}'.format(i),  auxin, lins[i+1], auxout)
            auxin = auxout
            if (i == num-3):
                auxout = r
            else:
                auxout = self.wire('and{}'.format(i+1), w)
                
                        
                
class Bit(Logic):
    """ 
    Gets one bit from a wire
    """

    def __init__(self, parent: Logic, name: str, a: Wire, bit, r: Wire):
        super().__init__(parent, name)

        self.a = self.addIn('a', a)
        self.r = self.addOut('r', r)

        self.bit = bit

    def propagate(self):
        value = self.a.get()
        newvalue = (value >> self.bit) & 1
        self.r.put(newvalue)



class Bits(Logic):
    """
    splits the bits of a wire into individual wires
    """

    def __init__(self, parent: Logic, name: str, a: Wire, bits):
        super().__init__(parent, name)

        self.a = self.addIn('a', a)

        w = a.getWidth()

        self.bits = []
        for i in range(w):
            self.bits.append(self.addOut('b{}'.format(i), bits[i]))

    def propagate(self):
        w = self.a.getWidth()
        v = self.a.get()

        for i in range(w):
            self.bits[i].put((v >> i) & 1)

    def fromWire(parent: Logic, name: str, a: Wire):
        bits = parent.wires(name + '_bits', a.getWidth(), 1)
        Bits(parent, name, a, bits)
        return bits
    
class Buf(Logic):
    def __init__(self, parent, name: str, a: Wire, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn('a', a)
        self.r = self.addOut('r', r)

    def propagate(self):
        self.r.put(self.a.get())


class Constant(Logic):
    """
    A constant value
    """

    def __init__(self, parent: Logic, name: str, value: int, r: Wire):
        super().__init__(parent, name)
        self.value = value
        self.r = self.addOut("r", r)

    def propagate(self):
        self.r.put(self.value)
        #print(self.name, '=', self.value)
        
class Nand2(Logic):
    """
    Binary Nand
    """

    def __init__(self, parent, name: str, a: Wire, b: Wire, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)

        self.mid = self.wire("Mid", a.getWidth())

        And2(self, "And", a, b, self.mid)
        Not(self, "Not", self.mid, r)

class Nor(Logic):
    """
    Binary Nand
    """

    def __init__(self, parent, name: str, ins, r: Wire):
        super().__init__(parent, name)
        
        lins = []
        
        for idx, inv in enumerate(ins):
            lins.append(self.addIn('in{}'.format(idx), inv))

        r = self.addOut("r", r)

        mid = self.wire("Mid", lins[0].getWidth())
        
        # save inputs/outputs for RTL generation
        self.r = r
        self.ins = lins

        Or(self, "Or", lins, mid)
        Not(self, "Not", mid, r)


class Nor2(Logic):
    """
    Binary Nand
    """

    def __init__(self, parent, name: str, a: Wire, b: Wire, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)

        self.mid = self.wire("Mid", a.getWidth())

        Or2(self, "Or", a, b, self.mid)
        Not(self, "Not", self.mid, r)

class Not(Logic):
    def __init__(self, parent, name: str, a: Wire, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.r = self.addOut("r", r)

    def propagate(self):
        self.r.put(~self.a.get())

    def getSymbol(self, x, y):
        return NotSymbol(self, x, y)


class Or2(Logic):
    """
    Binary And
    """

    def __init__(self, parent, name: str, a: Wire, b: Wire, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)

    def propagate(self):
        self.r.put(self.a.get() | self.b.get())

class Or(Logic):
    def __init__(self, parent, name:str, ins, r: Wire):
        super().__init__(parent, name)
        lins = []
        r = self.addOut('r', r)
        w = r.getWidth()
        
        for idx, inv in enumerate(ins):
            lins.append(self.addIn('in{}'.format(idx), inv))

        # save inputs/outputs for RTL generation
        self.r = r
        self.ins = lins
        
        num = len(ins)

        if (num == 2):
            Or2(self, 'and2', ins[0], ins[1], r)
            return
            
        if (num < 3):
            raise Exception('List should be > 2')

        # by now we do an inefficient ladder structure, we should
        # do a more fancy logarithmic design
        
        auxin = lins[0]
        auxout = self.wire('and{}'.format(0), w)
        
        for i in range(num-1):
            # print('creating and{} input0: {}'.format(i, auxin.getFullPath()))
            # print('creating and{} input1: {}'.format(i, lins[i+1].getFullPath()))
            # print('creating and{} output: {}'.format(i, auxout.getFullPath()))
            Or2(self, 'and{}'.format(i),  auxin, lins[i+1], auxout)
            auxin = auxout
            if (i == num-3):
                auxout = r
            else:
                auxout = self.wire('and{}'.format(i+1), w)    

                
class Xor2(Logic):
    """
    Binary Xor
    """

    def __init__(self, parent, name: str, a: Wire, b: Wire, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)

        mid = self.wire("Mid", a.getWidth())
        xout = self.wire("XOut", a.getWidth())
        yout = self.wire("YOut", a.getWidth())

        Nand2(self, "NandMid", a, b, mid)
        Nand2(self, "NandX", a, mid, xout)
        Nand2(self, "NandY", b, mid, yout)
        Nand2(self, "NandR", xout, yout, r)


class Xor(Logic):
    def __init__(self, parent, name:str, ins, r: Wire):
        super().__init__(parent, name)
        lins = []
        r = self.addOut('r', r)
        w = r.getWidth()
        
        for idx, inv in enumerate(ins):
            lins.append(self.addIn('in{}'.format(idx), inv))

        num = len(ins)

        if (num == 2):
            Xor2(self, 'and2', ins[0], ins[1], r)
            return
            
        if (num < 3):
            raise Exception('List should be > 2')

        # by now we do an inefficient ladder structure, we should
        # do a more fancy logarithmic design
        
        auxin = lins[0]
        auxout = self.wire('and{}'.format(0), w)
        
        for i in range(num-1):
            # print('creating and{} input0: {}'.format(i, auxin.getFullPath()))
            # print('creating and{} input1: {}'.format(i, lins[i+1].getFullPath()))
            # print('creating and{} output: {}'.format(i, auxout.getFullPath()))
            Xor2(self, 'and{}'.format(i),  auxin, lins[i+1], auxout)
            auxin = auxout
            if (i == num-3):
                auxout = r
            else:
                auxout = self.wire('and{}'.format(i+1), w)
                

class Mux(Logic):
    def __init__(self, parent, name: str, sel: Wire, ins, r: Wire):
        super().__init__(parent, name)
        
        sel = self.addIn('sel', sel)
        r = self.addOut('r', r)
        bits = Bits.fromWire(self, 'sel', sel)

        lins = []
        for idx, inv in enumerate(ins):
            lins.append(self.addIn('in{}'.format(idx), inv))

        if (len(bits) != int(math.log2(len(ins)))):
            raise Exception('Invalid length sel bits: {} # ins: {}'.format(bits, ins))
            
        fp, ip = math.modf(math.log2(len(ins)))
        
        if (fp != 0):
            raise Exception('Input wires are not a power of 2')

        w = len(ins) // 2
        auxin = ins
        auxout = self.wires('l{}'.format(0), w, r.getWidth())

        for i in range(len(bits)):
            for k in range(w):
                Mux2(self, 'm{}_{}'.format(i, k), bits[i], auxin[k * 2 + 0], auxin[k * 2 + 1], auxout[k])

            auxin = auxout
            w = w // 2
            if (w == 1):
                auxout = [r]
            else:
                auxout = self.wires('l{}'.format(i + 1), w, r.getWidth())

class Mux2(Logic):
    def __init__(self, parent, name: str, sel: Wire, sel0: Wire, sel1: Wire, r: Wire):
        super().__init__(parent, name)
        self.sel = self.addIn("sel", sel)
        self.sel0 = self.addIn("sel0", sel0)
        self.sel1 = self.addIn("sel1", sel1)
        self.r = self.addOut("r", r)

    def propagate(self):
        if (self.sel.get() & 1):
            self.r.put(self.sel1.get())
        else:
            self.r.put(self.sel0.get())


class Repeat(Logic):
    def __init__(self, parent, name: str, i: Wire, r: Wire):
        super().__init__(parent, name)

        if (i.getWidth() != 1):
            raise Exception('input wire should be 1 bit')
        self.i = self.addIn('in', i)
        self.r = self.addOut('r', r)

    def propagate(self):
        w = self.r.getWidth()
        wp = (1 << w) - 1
        wf = 0

        v = self.i.get()
        if (v):
            self.r.put(wp)
        else:
            self.r.put(wf)


class Select(Logic):
    def __init__(self, parent, name: str, sels, ins, r: Wire):
        super().__init__(parent, name)

        final = []

        for idx, sel in enumerate(sels):
            inv = ins[idx]
            self.addIn('sel{}'.format(idx), sel)
            self.addIn('in{}'.format(idx), inv)
            selx = self.wire('selx{}'.format(idx), inv.getWidth())
            and_sel = self.wire('and_sel{}'.format(idx), inv.getWidth())

            Repeat(self, 'sel{}'.format(idx), sel, selx)
            And(self, 'and{}'.format(idx), selx, inv, and_sel)
            final.append(and_sel)

        self.addOut('r', r)
        Or.fromList(self, 'or', final, r)



        



class Decoder(Logic):
    """
    A decoder
    """

    def __init__(self, parent: Logic, name: str, a: Wire, b):
        """
        Creates a decoder. The outputs are dynamically created

        Parameters
        ----------
        parent : Logic
            Parent circuit.
        name : str
            Name of the instance.
        a : Wire
            Input signal.
        b : List of Wire
            List of the output signals.

        Returns
        -------
        None.

        """
        super().__init__(parent, name)
        a = self.addIn("a", a)

        for i in range(len(b)):
            lb = self.addOut('b{}'.format(i), b[i])

            EqualConstant(self, 'eq{}'.format(i), a, i, lb)


class Minterm(Logic):
    """
    A minterm in a boolean expression
    """

    def __init__(self, parent: Logic, name: str, bits, value: int, r: Wire):
        """

        Parameters
        ----------
        parent : Logic
            DESCRIPTION.
        name : str
            DESCRIPTION.
        bits : List of Wires (least significant order first)
            DESCRIPTION.
        value : int
            DESCRIPTION.
        r : Wire
            DESCRIPTION.

        Returns
        -------
        None.

        """
        super().__init__(parent, name)
        r = self.addOut('r', r)
        parts = []
        lbits = []
        for i in range(len(bits)):
            lbits.append(self.addIn('b{}'.format(i), bits[i]))
            v = (value >> i) & 1
            if (v == 0):
                nbit = self.wire('n{}'.format(i), 1)
                Not(self, 'n{}'.format(i), lbits[i], nbit)
                parts.append(nbit)
            else:
                parts.append(lbits[i])

        And(self, 'prod', parts, r)
        

class Concatenate(Logic):
    def __init__(self, parent: Logic, name: str, ins, r: Wire):
        super().__init__(parent, name)

        self.ins = []

        for idx, item in enumerate(ins):
            self.ins.append(self.addIn('in{}'.format(idx), item))

        self.r = self.addOut('r', r)

    def propagate(self):
        value = 0
        last = 0
        for idx, item in enumerate(self.ins):
            value = value << last
            value = value | item.get()
            last = item.getWidth()

        self.r.put(value)
        

class Range(Logic):
    def __init__(self, parent: Logic, name: str, a: Wire, high: int, low: int, r: Wire):
        super().__init__(parent, name)

        self.a = self.addIn('a', a)
        self.r = self.addOut('r', r)
        self.high = high
        self.low = low

    def propagate(self):
        value = self.a.get()
        mask = (1 << (self.high - self.low + 1)) - 1
        newvalue = (value >> self.low) & mask
        self.r.put(newvalue)

