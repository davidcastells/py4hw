# -*- coding: utf-8 -*-
"""
Created on Wed Jan 19 12:36:38 2022

@author: dcr
"""
from .. import *
from .relational import *
from deprecated import deprecated
import math





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

        if (num == 1):
            Buf(self, 'and1', ins[0], r)
            return
        
        if (num == 2):
            And2(self, 'and2', ins[0], ins[1], r)
            return
            
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


class BitsMSBF(Logic):
    """
    Returns a list of 1 bit wires from a wider wire 
    in least significant bit first order
    """

    def __init__(self, parent: Logic, name: str, a: Wire, bits):
        super().__init__(parent, name)

        self.a = self.addIn('a', a)

        w = a.getWidth()

        self.bits = []
        for i in range(w):
            self.bits.append(self.addOut('b{}'.format(i), bits[i]))

        self.bits.reverse()
        
    def propagate(self):
        w = self.a.getWidth()
        v = self.a.get()

        for i in range(w):
            self.bits[i].put((v >> i) & 1)
            
class BitsLSBF(Logic):
    """
    Returns a list of 1 bit wires from a wider wire 
    in least significant bit first order
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

    @deprecated
    def fromWire(parent: Logic, name: str, a: Wire):
        bits = parent.wires(name + '_bits', a.getWidth(), 1)
        BitsLSBF(parent, name, a, bits)
        return bits
    
class Buf(Logic):
    def __init__(self, parent, name: str, a: Wire, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn('a', a)
        self.r = self.addOut('r', r)

    def propagate(self):
        self.r.put(self.a.get())

    
class BidirBuf(Logic):
    
    def __init__(self, parent, name: str, pin : Wire , pout : Wire, poe : Wire, bidir : BidirWire):
        super().__init__(parent, name)
        
        if (poe.getWidth() != 1):
            raise Exception('BidirBuf only supports 1 bit output enable')
            
        self.bidir = self.addInOut('bidir', bidir)
        self.pin = self.addOut('pin', pin)
        self.pout = self.addIn('pout', pout)
        self.poe = self.addIn('poe', poe)
        
    def propagate(self):
        if (self.poe.get() ==1):
            self.bidir.put(self.pout.get())
        else:
            self.pin.put(self.bidir.get())

class BufEnable(Logic):
    # This is just a way to control set to zero all bits of a signal
    # depending on an enable signal
    def __init__(self, parent, name, a, en, r):
        super().__init__(parent, name)
        
        self.a = self.addIn('a', a)
        self.en = self.addIn('en', en)
        self.r = self.addOut('r', r)
   
        assert(a.getWidth() == r.getWidth())
    
        re = self.wire('re', r.getWidth())
        Repeat(self, 're', en, re)
        And2(self, 'r', a, re, r)
        
    def structureName(self):
        return 'BufEnable{}'.format(self.a.getWidth())
    

class Constant(Logic):
    """
    A constant value
    """

    def __init__(self, parent: Logic, name: str, value: int, r: Wire):
        super().__init__(parent, name)
        assert(isinstance(value, int))
        assert(isinstance(r, Wire))
        self.value = value
        self.r = self.addOut("r", r)

    def propagate(self):
        self.r.put(self.value)
        #print(self.name, '=', self.value)
        
class Demux(Logic):
    def __init__(self, parent, name, a, sel, r):
        super().__init__(parent, name)
        
        self.addIn('a', a)
        self.addIn('sel', sel)
        
        assert(2**sel.getWidth() == len(r))
        
        ss = self.wires('ss', 2**sel.getWidth(), 1)
        Decoder(self, 'decoder', sel, ss)
        
        for idx, ri in enumerate(r):
            self.addOut('r{}'.format(idx), ri)
            
            BufEnable(self, 'en{}'.format(idx), a, ss[idx], ri)
            
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

class OrBits(Logic):
    def __init__(self, parent, name:str, a: Wire, r: Wire):
        super().__init__(parent, name)
        
        self.addIn('a', a)
        self.addOut('r', r)
        
        ab = self.wires('ab', a.getWidth(), 1)
        BitsLSBF(self, 'bits', a, ab)
        Or(self, 'or', ab, r)
    
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

        if (num == 1):
            Buf(self, 'or1', ins[0], r)
            return 
        
        if (num == 2):
            Or2(self, 'or2', ins[0], ins[1], r)
            return
                    
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


class ShiftLeftConstant(Logic):
    def __init__(self, parent, name: str, a: Wire, n: int, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn('a', a)
        self.r = self.addOut('r', r)
        self.addParameter('n', n)

    def propagate(self):
        self.r.put(self.a.get() << self.getParameterValue('n'))


class ShiftRightConstant(Logic):
    def __init__(self, parent, name: str, a: Wire, n: int, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn('a', a)
        self.r = self.addOut('r', r)
        self.addParameter('n', n)

    def propagate(self):
        self.r.put(self.a.get() >>  self.getParameterValue('n'))

class RotateLeftConstant(Logic):
    def __init__(self, parent, name: str, a: Wire, n: int, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn('a', a)
        self.r = self.addOut('r', r)
        self.n = n

    def propagate(self):
        a = self.a.get()
        n = self.n
        w = self.a.getWidth()
        self.r.put((a << n) | (a >> (w - n)))


class RotateRightConstant(Logic):
    def __init__(self, parent, name: str, a: Wire, n: int, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn('a', a)
        self.r = self.addOut('r', r)
        self.n = n

    def propagate(self):
        a = self.a.get()
        n = self.n
        w = self.a.getWidth()
        self.r.put((a >> n) | (a << (w - n)))
                
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
        
        if (sel.getWidth() != int(math.log2(len(ins)))):
            raise Exception('Invalid length sel bits: {} # ins: {}'.format(sel.getWidth(), int(math.log2(len(ins)))))

        sel = self.addIn('sel', sel)
        r = self.addOut('r', r)

        lins = []
        for idx, inv in enumerate(ins):
            lins.append(self.addIn('in{}'.format(idx), inv))
        
        if (sel.getWidth() == 1):
            # two inputs is a trivial case
            Mux2(self, 'mux2', sel, lins[0], lins[1], r)
            return
            
        # bits contain all the bits from the selection wire
        # which will be the base for creating a logarithmic
        # selection tree
        bits = BitsLSBF.fromWire(self, 'sel', sel)


            
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

# deprecated use OneHotMux
class Select(Logic):
    def __init__(self, parent, name: str, sels:list, ins:list, r: Wire):
        super().__init__(parent, name)

        final = []

        for idx, sel in enumerate(sels):
            inv = ins[idx]
            self.addIn('sel{}'.format(idx), sel)
            self.addIn('in{}'.format(idx), inv)
            selx = self.wire('selx{}'.format(idx), inv.getWidth())
            and_sel = self.wire('and_sel{}'.format(idx), inv.getWidth())

            Repeat(self, 'sel{}'.format(idx), sel, selx)
            And2(self, 'and{}'.format(idx), selx, inv, and_sel)
            final.append(and_sel)

        self.addOut('r', r)
        Or(self, 'or', final, r)


class OneHotMux(Logic):
    def __init__(self, parent, name: str, sels:list, ins:list, r: Wire):
        super().__init__(parent, name)

        final = []

        for idx, sel in enumerate(sels):
            inv = ins[idx]
            
            sel_name = sel.name
            in_name = inv.name 
            self.addIn(sel_name, sel)
            self.addIn(in_name, inv)
            selx = self.wire('selx{}'.format(idx), inv.getWidth())
            and_sel = self.wire('and_sel{}'.format(idx), inv.getWidth())

            Repeat(self, 'sel{}'.format(idx), sel, selx)
            And2(self, 'and{}'.format(idx), selx, inv, and_sel)
            final.append(and_sel)

        self.addOut('r', r)
        Or(self, 'or', final, r)


class OneHotDemux(Logic):
    def __init__(self, parent, name: str, sels:list, a:Wire, outs: list):
        super().__init__(parent, name)

        final = []

        a = self.addIn('a', a)

        for idx, sel in enumerate(sels):
            self.addIn('sel{}'.format(idx), sel)
            self.addOut('out{}'.format(idx), outs[idx])
            
            selx = self.wire('selx{}'.format(idx), a.getWidth())

            Repeat(self, 'sel{}'.format(idx), sel, selx)
            And2(self, 'and{}'.format(idx), selx, a, outs[idx])
            
        
class SelectDefault(Logic):
    def __init__(self, parent, name, sels, ins, default, r):
        super().__init__(parent, name)
        
        self.addIn('default', default)
        self.addOut('r', r)
        
        nextoutput = r
        
        for idx, sel in enumerate(sels):
            inv = ins[idx]
            self.addIn('sel{}'.format(idx), sel)
            self.addIn('in{}'.format(idx), inv)
            previnput = self.wire('t{}'.format(idx), r.getWidth())
            Mux2(self, 'mux{}'.format(idx), sel, previnput, inv, nextoutput)
            
            nextoutput = previnput
            
        Buf(self, 'buf', default, previnput)



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
        

class SumOfMinterms(Logic):
    def __init__(self, parent, name, a, minterms:list, r):
        super().__init__(parent, name)
        
        self.addIn('a', a)
        self.addOut('r', r)
        
        bits = self.wires('bits', a.getWidth(), 1)
        BitsLSBF(self, 'bits', a, bits)
        
        acum = []
        for idx, minterm in enumerate(minterms):
            v = self.wire('s{}'.format(idx))
            
            Minterm(self, 'minterm{}'.format(idx), bits, minterm, v)
            acum.append(v)
            
        Or(self, 'sum', acum, r)
        
class ConcatenateMSBF(Logic):
    """
    Concatenate wires circuit in MSBF order
    """
    def __init__(self, parent: Logic, name: str, ins:list, r: Wire):
        super().__init__(parent, name)

        ind_w = []
        total_w = 0
        max_w = r.getWidth()
        
        self.ins = []

        for idx, item in enumerate(ins):
            self.ins.append(self.addIn('in{}'.format(idx), item))
            total_w += item.getWidth()
            ind_w.append(item.getWidth())

        if (total_w > max_w):
            raise Exception('Combined input widths {} larger than result width {}>{}'.format(ind_w, total_w, max_w))
            
        self.r = self.addOut('r', r)

    def propagate(self):
        value = 0
        last = 0
        for idx, item in enumerate(self.ins):
            value = value << item.getWidth()
            value = value | item.get()
            
        self.r.put(value)
        
class ConcatenateLSBF(Logic):
    """
    Concatenate wires circuit in MSBF order
    """
    def __init__(self, parent: Logic, name: str, ins:list, r: Wire):
        super().__init__(parent, name)

        total_w = 0
        max_w = r.getWidth()
        
        self.ins = []

        for idx, item in enumerate(ins):
            self.ins.append(self.addIn('in{}'.format(idx), item))
            total_w += item.getWidth()

        if (total_w > max_w):
            raise Exception('Combined input widths larger than result width {}>{}'.format(total_w, max_w))
            
        self.ins.reverse()
        self.r = self.addOut('r', r)

    def propagate(self):
        value = 0
        last = 0

        for idx, item in enumerate(self.ins):
            value = value << item.getWidth()
            value = value | item.get()
            
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

class Digit7Segment(Logic):
    def __init__(self, parent, name, v, led):
        super().__init__(parent, name)
        
        assert(led.getWidth() == 7)
        
        self.addIn('v', v)
        self.addOut('led', led)
        
        
        a_minterms = [0,2,3,5,6,7,8,9,0xA,0xC,0xE,0xF]
        b_minterms = [0,1,2,3,4,7,8,9,0xA,0xd]
        c_minterms = [0,1,3,4,5,6,7,8,9,0xA,0xb,0xd]
        d_minterms = [0,2,3,5,6,8,0xb,0xC,0xd,0xE]
        e_minterms = [0,2,6,8,0xA,0xb,0xC,0xd,0xE,0xF]
        f_minterms = [0,4,5,6,8,9,0xA,0xb,0xC,0xE,0xF]
        g_minterms = [2,3,4,5,6,8,9,0xA,0xb,0xd,0xE,0xF]
        
        
        a = self.wire('a')
        b = self.wire('b')
        c = self.wire('c')
        d = self.wire('d')
        e = self.wire('e')
        f = self.wire('f')
        g = self.wire('g')
        
        na = self.wire('na')
        nb = self.wire('nb')
        nc = self.wire('nc')
        nd = self.wire('nd')
        ne = self.wire('ne')
        nf = self.wire('nf')
        ng = self.wire('ng')
        
        ConcatenateLSBF(self, 'led', [a,b,c,d,e,f,g], led)
        
        SumOfMinterms(self, 'a', v, a_minterms, a)
        SumOfMinterms(self, 'b', v, b_minterms, b)
        SumOfMinterms(self, 'c', v, c_minterms, c)
        SumOfMinterms(self, 'd', v, d_minterms, d)
        SumOfMinterms(self, 'e', v, e_minterms, e)
        SumOfMinterms(self, 'f', v, f_minterms, f)
        SumOfMinterms(self, 'g', v, g_minterms, g)
        
class PriorityEncoder(Logic):
    def __init__(self, parent, name, a, r, inc_priority=True):
        from ..helper import LogicHelper
        super().__init__(parent, name)
        assert(len(a) == len(r))

        # Make a copy so that reverse does not affect the original list
        a = a.copy()
        r = r.copy()
        
        # It the priority is decreasing, the a[0] is the more priorized
        # Otherwise is the higher index
        if (inc_priority):
            a.reverse()
            r.reverse()
        
        hlp = LogicHelper(self)
        
        last = None
        
        for i in range(len(a)):
            self.addIn('a{}'.format(i), a[i])
            self.addOut('r{}'.format(i), r[i])
            
            if (last is None):
                Buf(self, 'r{}'.format(i), a[i], r[i])
                last = hlp.hw_buf(a[i])
            else:
                And2(self, 'r{}'.format(i), a[i], hlp.hw_not(last), r[i])
                last = hlp.hw_or2(last, a[i])