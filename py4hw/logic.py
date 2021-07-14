# -*- coding: utf-8 -*-

from .base import Logic
from .base import Wire
import math
#import tkinter


class Buf(Logic):
    def __init__(self, parent, name: str, a: Wire, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn('a', a)
        self.r = self.addOut('r', r)

    def propagate(self):
        self.r.put(self.a.get())


class ShiftLeft(Logic):
    def __init__(self, parent, name: str, a: Wire, n: int, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn('a', a)
        self.r = self.addOut('r', r)
        self.n = n

    def propagate(self):
        self.r.put(self.a.get() << self.n)


class Or(Logic):
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

    def fromList(parent, name: str, list, r: Wire):
        if (len(list) < 2):
            #raise Exception('List should be > 1')
            Buf(parent, name, list[0], r)
            return

        auxin = list[0]
        w = auxin.getWidth()
        idx = 0
        if (len(list) == 2):
            aux = r
        else:
            aux = parent.wire('{}{}'.format(name, idx), w)
        idx = idx + 1
        for i in range(len(list) - 1):
            Or(parent, '{}{}'.format(name, i), auxin, list[i + 1], aux)

            auxin = aux

            if (i == (len(list) - 3)):
                aux = r
            else:
                aux = parent.wire('{}{}'.format(name, idx), w)
                idx = idx + 1


class And(Logic):
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

    def fromList(parent, name: str, list, r: Wire):
        if (len(list) < 2):
            raise Exception('List should be > 2')

        auxin = list[0]
        idx = 0
        aux = parent.wire('a{}'.format(idx))
        idx = idx + 1
        for i in range(len(list) - 1):
            And(parent, 'a{}'.format(i), auxin, list[i + 1], aux)

            auxin = aux

            if (i == (len(list) - 3)):
                aux = r
            else:
                aux = parent.wire('a{}'.format(idx))
                idx = idx + 1


class Nand(Logic):
    """
    Binary Nand
    """

    def __init__(self, parent, name: str, a: Wire, b: Wire, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)

        self.mid = self.wire("Mid", a.getWidth())

        And(self, "And", a, b, self.mid)
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


class Xor(Logic):
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

        Nand(self, "NandMid", a, b, mid)
        Nand(self, "NandX", a, mid, xout)
        Nand(self, "NandY", b, mid, yout)
        Nand(self, "NandR", xout, yout, r)


class Add(Logic):
    """
    Combinational Arithmetic Add
    """

    def __init__(self, parent, name: str, a: Wire, b: Wire, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)

    def propagate(self):
        self.r.put(self.a.get() + self.b.get())


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


class Sub(Logic):
    """
    Arithmetic Add
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


class Mux(Logic):
    def __init__(self, parent, name: str, sel: Wire, ins, r: Wire):
        super().__init__(parent, name)
        self.addIn('sel', sel)
        self.addOut('r', r)
        bits = Bits.fromWire(self, 'sel', sel)

        for i in range(len(ins)):
            self.addIn('in{}'.format(i), ins[i])

        if (len(bits) != int(math.log2(len(ins)))):
            raise Exception('Invalid length')

        w = len(ins) // 2
        auxin = ins
        auxout = self.wires('l{}'.format(1), w, r.getWidth())

        for i in range(len(bits)):
            for k in range(w):
                Mux2(self, 'm{}_{}'.format(i, k), bits[i], auxin[k * 2 + 0], auxin[k * 2 + 1], auxout[k])

            auxin = auxout
            w = w // 2
            if (w == 1):
                auxout = [r]
            else:
                auxout = self.wires('l{}'.format(i + 1), w, r.getWidth())


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

class Sequence(Logic):
    """
    A sequence of value
    """

    def __init__(self, parent: Logic, name: str, values: list(), r: Wire):
        super().__init__(parent, name)
        self.r = self.addOut("r", r)

        self.values = values
        self.n = len(values)
        self.i = 0
        
    def clock(self):
        self.r.prepare(self.values[self.i])
        self.i = ( self.i +1 ) % self.n

class SignExtend(Logic):
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
    def __init__(self, parent: Logic, name: str, a: Wire, r: Wire):
        super().__init__(parent, name)
        self.a = self.addIn('a', a)
        self.r = self.addOut('r', r)

    def propagate(self):
        value = self.a.get()
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
        self.addIn("a", a)

        for i in range(len(b)):
            self.addOut('b{}'.format(i), b[i])

            Equal(self, 'eq{}'.format(i), a, i, b[i])


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
        self.addOut('r', r)
        parts = []
        for i in range(len(bits)):
            self.addIn('b{}'.format(i), bits[i])
            v = (value >> i) & 1
            if (v == 0):
                nbit = self.wire('n{}'.format(i), 1)
                Not(self, 'n{}'.format(i), bits[i], nbit)
                parts.append(nbit)
            else:
                parts.append(bits[i])

        And.fromList(self, 'prod', parts, r)


class Equal(Logic):
    """
    An Equal comparator circuit
    """

    def __init__(self, parent, name: str, a: Wire, v: int, r: Wire):
        super().__init__(parent, name)

        self.addIn("a", a)
        self.addOut("r", r)

        bits = self.wires('b', a.getWidth(), 1)

        Bits(self, "bits", a, bits)

        Minterm(self, 'm{}'.format(v), bits, v, r)


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


class Comparator(Logic):
    """
    A Greater Than, Equal and Less Than comparator circuit
    """

    def __init__(self, parent, name: str, a: Wire, b: Wire, gt: Wire, eq: Wire, lt: Wire):
        super().__init__(parent, name)
        self.addIn("a", a)
        self.addIn("b", b)
        self.addOut("gt", gt)
        self.addOut("eq", eq)
        self.addOut("lt", lt)

        sub = Wire(self, "sub", a.getWidth())
        notLT = Wire(self, "~LT", 1)
        notEQ = Wire(self, "~EQ", 1)

        Sub(self, "Comparison", a, b, sub)

        # LT
        Sign(self, "LessThan", sub, lt)

        # EQ
        Equal(self, "Equal", sub, 0, eq)

        # GT
        Not(self, "~LT", lt, notLT)
        Not(self, "~EQ", eq, notEQ)
        And(self, "GreaterThan", notEQ, notLT, gt)


class Scope(Logic):

    def __init__(self, parent: Logic, name: str, wires):
        """
        Parameters
        ----------
        parent : Logic
            Parent circuit.
        name : str
            Name of the instance.
        wires
            Wire or list of wire to monitor.

        Returns
        -------
        None.
        """

        super().__init__(parent, name)
        self.wires = wires if isinstance(wires, list) else [wires]
        for x in self.wires:
            self.addIn(x.name, x)

        # Get simulator
        sim = parent
        while sim.parent != None:
            sim = sim.parent

        sim.getSimulator().addListener(self)

    def simulatorUpdated(self):
        head = f"Scope [{self.name}]:"
        print(head)

        for x in self.wires:
            print(f"{x.name}={x.get()}")

        print("-" * len(head))


class Waveform(Logic):

    def __init__(self, parent: Logic, name: str, wires):
        """

        Parameters
        ----------
        parent : Logic
              Parent circuit.
        name : str
            Name of the instance.
        wires
              Wire or list of wire to monitor.

        Returns
        -------
        None.

        """
        super().__init__(parent, name)
        self.waves = {}
        self.prevs = {}
        self.ck = {"name": "CK", "wave": "P"}

        self.wires = wires if isinstance(wires, list) else [wires]
        for x in self.wires:
            self.addIn(x.name, x)
            self.waves[x] = {"name": x.name, "wave": "x", "data": []}
            self.prevs[x] = None

        # Get simulator
        self.sim = parent
        while self.sim.parent != None:
            self.sim = self.sim.parent

        self.sim.getSimulator().addListener(self)

    def simulatorUpdated(self):
        for x in self.wires:
            if self.prevs[x] == x.get():
                self.waves[x]["wave"] += "."
            elif x.getWidth() == 1:
                self.waves[x]["wave"] += str(x.get())
            else:
                self.waves[x]["wave"] += "2"
                self.waves[x]["data"].append(x.get())

            self.prevs[x] = x.get()

        self.ck["wave"] += "."

    def get_waveform(self, with_ck=True):
        signals = list(self.waves.values())
        for x in signals:
            x["wave"] += "x"

        if with_ck:
            ck = self.ck.copy()
            ck["wave"] += "x"
            signals.insert(0, ck)

        waveform = {
            "signal": signals,
            "head": {
                "text": self.name,
                "tock": 0,
            }
        }

        return waveform
