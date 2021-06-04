# -*- coding: utf-8 -*-

from .base import Logic
from .base import Wire
import math
import tkinter

class Buf(Logic):
    def __init__(self, parent, name:str, a:Wire, r:Wire):
        super().__init__(parent, name)
        self.a = self.addIn('a', a)
        self.r = self.addOut('r', r)
        
    def propagate(self):
        self.r.put(self.a.get())
    
class ShiftLeft(Logic):
    def __init__(self, parent, name:str, a:Wire, n:int, r:Wire):
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
    
    def __init__(self, parent, name:str, a:Wire, b:Wire, r:Wire):
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)
        
    def propagate(self):
        self.r.put(self.a.get() | self.b.get())
        
    def fromList(parent, name:str, list, r:Wire):
        if (len(list) < 2):
            #raise Exception('List should be > 1')
            Buf(parent, name, list[0], r)
            return;

        auxin = list[0]
        w = auxin.getWidth()
        idx =0
        if (len(list) == 2):
            aux = r
        else:
            aux = parent.wire('{}{}'.format(name, idx), w)
        idx = idx+1            
        for i in range(len(list)-1):
            Or(parent, '{}{}'.format(name,i), auxin, list[i+1], aux)
            
            auxin = aux
            
            if (i == (len(list)-3)):
                aux = r
            else:
                aux = parent.wire('{}{}'.format(name,idx), w)
                idx = idx+1            

    def getSymbol(self,x,y):
        return OrSymbol(self,x,y)

    
    
class OrSymbol:
    def __init__(self, obj, x, y):
        self.obj = obj
        self.x = x
        self.y = y
        
    def draw(self, canvas):
        x = self.x
        y = self.y
        
        canvas.create_text(x, y, text=self.obj.name, anchor='w')
        y = y+8
        
        y = y+10
        
        canvas.create_line(x, y, x+40, y)
        canvas.create_line(x, y+40, x+40, y+40)
        canvas.create_line(x, y, x, y+40)
        canvas.create_arc(x+20, y, x+50, y+40, start=-90, extent=180, style=tkinter.ARC, outline='black',  fill='white')
    
    def getHeight(self):
        return 30
    
    def getWidth(self):
        return 50
    
class And(Logic):
    """
    Binary And
    """
    
    def __init__(self, parent, name:str, a:Wire, b:Wire, r:Wire):
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)
        
    def propagate(self):
        self.r.put(self.a.get()&self.b.get())
        
    def fromList(parent, name:str, list, r:Wire):
        if (len(list) < 2):
            raise Exception('List should be > 2')

        auxin = list[0]
        idx =0
        aux = parent.wire('a{}'.format(idx))
        idx = idx+1            
        for i in range(len(list)-1):
            And(parent, 'a{}'.format(i), auxin, list[i+1], aux)
            
            auxin = aux
            
            if (i == (len(list)-3)):
                aux = r
            else:
                aux = parent.wire('a{}'.format(idx))
                idx = idx+1            

    def getSymbol(self,x,y):
        return AndSymbol(self,x,y)

    
    
class AndSymbol:
    def __init__(self, obj, x, y):
        self.obj = obj
        self.x = x
        self.y = y
        
    def draw(self, canvas):
        x = self.x
        y = self.y
        
        canvas.create_text(x, y, text=self.obj.name, anchor='w')
        y = y+8
        
        y = y+10
        
        canvas.create_line(x, y, x+40, y)
        canvas.create_line(x, y+40, x+40, y+40)
        canvas.create_line(x, y, x, y+40)
        canvas.create_arc(x+20, y, x+50, y+40, start=-90, extent=180, style=tkinter.ARC, outline='black',  fill='white')
    
    def getHeight(self):
        return 30
    
    def getWidth(self):
        return 50
    
class Not(Logic):
    def __init__(self, parent, name:str, a:Wire,r:Wire):
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.r = self.addOut("r", r)
        
    def propagate(self):
        self.r.put(~self.a.get())
        
    def getSymbol(self,x,y):
        return NotSymbol(self,x,y)
        
class NotSymbol:
    def __init__(self, obj, x, y):
        self.obj = obj
        self.x = x
        self.y = y
        
    def draw(self, canvas):
        x = self.x
        y = self.y
        
        canvas.create_text(x, y, text=self.obj.name, anchor='w')
        y = y+8
        
        y = y+10
        
        canvas.create_polygon(x, y, x+20, y+10, x, y+20, outline='black',  fill='white')
        canvas.create_oval(x+20, y+5, x+30, y+15, outline='black',  fill='white')
    def getHeight(self):
        return 30
    
    def getWidth(self):
        return 30
    
class Add(Logic):
    """
    Combinational Arithmetic Add
    """
    
    def __init__(self, parent, name:str, a:Wire, b:Wire, r:Wire):
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)
        
    def propagate(self):
        self.r.put(self.a.get()+self.b.get())

class Mul(Logic):
    """
    Combinational Arithmetic Multiplier
    """
    
    def __init__(self, parent, name:str, a:Wire, b:Wire, r:Wire):
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)
        
    def propagate(self):
        self.r.put(self.a.get()*self.b.get())

class Sub(Logic):
    """
    Arithmetic Add
    """
    
    def __init__(self, parent, name:str, a:Wire, b:Wire, r:Wire):
        super().__init__(parent, name)
        self.a = self.addIn("a", a)
        self.b = self.addIn("b", b)
        self.r = self.addOut("r", r)
        
    def propagate(self):
        mask = (1 << self.r.getWidth()) -1
        newValue = (self.a.get()-self.b.get()) & mask
        self.r.put(newValue)
    
    
class Mux2(Logic):
    def __init__(self, parent, name:str, sel:Wire, sel0:Wire, sel1:Wire, r:Wire):
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
    def __init__(self, parent, name:str, i:Wire, r:Wire):
        super().__init__(parent, name)
        
        if (i.getWidth() != 1):
            raise Exception('input wire should be 1 bit')
        self.i = self.addIn('in', i)
        self.r = self.addOut('r', r)
        
    def propagate(self):
        w = self.r.getWidth()
        wp = (1 << w) -1;
        wf = 0;
        
        v = self.i.get()
        if (v):
            self.r.put(wp)
        else:
            self.r.put(wf)
        
class Select(Logic):
    def __init__(self, parent, name:str, sels, ins, r:Wire):
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
    def __init__(self, parent, name:str, sel:Wire, ins, r:Wire):
        super().__init__(parent, name)
        self.addIn('sel', sel)
        self.addOut('r', r)
        bits = Bits.fromWire(self, 'sel', sel)
                
        for i in range(len(ins)):
            self.addIn('in{}'.format(i), ins[i])
        
        if (len(bits) != int(math.log2(len(ins)))):
            raise Exception('Invalid length')
        
        w = len(ins)//2
        auxin = ins
        auxout = self.wires('l{}'.format(1), w, r.getWidth())
        
        for i in range(len(bits)):
            for k in range(w):
                Mux2(self, 'm{}_{}'.format(i,k), bits[i], auxin[k*2+0], auxin[k*2+1], auxout[k])
                
            auxin = auxout
            w = w // 2
            if (w == 1):
                auxout = [r]
            else:
                auxout = self.wires('l{}'.format(i+1), w, r.getWidth())
    
        
class Constant(Logic):
    """
    A constant value
    """
    def __init__(self, parent:Logic, name:str, value, r:Wire):
        super().__init__(parent, name)
        self.value = value;
        self.r = self.addOut("r", r)
        
    def propagate(self):
        self.r.put(self.value)
        #print(self.name, '=', self.value)
        
class SignExtend(Logic):
    def __init__(self, parent:Logic, name:str, a:Wire, r:Wire):
        super().__init__(parent, name)
        self.a = self.addIn('a', a)
        self.r = self.addOut('r', r)
    
    def propagate(self):
        value = self.a.get()
        hb = value >> (self.a.getWidth()-1)
        for i in range(self.a.getWidth(), self.r.getWidth()):
            value = value | (hb << i)
            
        self.r.put(value)

class ZeroExtend(Logic):
    def __init__(self, parent:Logic, name:str, a:Wire, r:Wire):
        super().__init__(parent, name)
        self.a = self.addIn('a', a)
        self.r = self.addOut('r', r)
    
    def propagate(self):
        value = self.a.get()
        self.r.put(value)

        
class Range(Logic):
    def __init__(self, parent:Logic, name:str, a:Wire, high:int, low:int, r:Wire):
        super().__init__(parent, name)
        
        self.a = self.addIn('a', a)
        self.r = self.addOut('r', r)
        self.high = high
        self.low = low;
        
    def propagate(self):
        value = self.a.get()
        mask = (1<<(self.high-self.low+1))-1;
        newvalue = (value >> self.low) & mask
        self.r.put(newvalue)
        
class Concatenate(Logic):
    def __init__(self, parent:Logic, name:str, ins, r:Wire):
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
    def __init__(self, parent:Logic, name:str, a:Wire, bit, r:Wire):
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
    def __init__(self, parent:Logic, name:str, a:Wire, bits):
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
            self.bits[i].put((v >> i)&1)
            
    def fromWire(parent:Logic, name:str, a:Wire):
        bits = parent.wires(name+'_bits', a.getWidth(), 1)
        Bits(parent, name, a, bits)
        return bits;
                
class Decoder(Logic):
    """
    A decoder
    """
    def __init__(self, parent:Logic, name:str, a:Wire, b):
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
    def __init__(self, parent:Logic, name:str, bits, value:int, r:Wire):
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
                nbit = self.wire('n{}'.format(i),1 )
                Not(self, 'n{}'.format(i), bits[i], nbit)
                parts.append(nbit)
            else:
                parts.append(bits[i])
            
        And.fromList(self, 'prod', parts, r)
        
class Equal(Logic):
    """
    An Equal comparator circuit
    """
    def __init__(self, parent, name:str, a:Wire, v:int, r:Wire):
        super().__init__(parent, name)
        
        self.addIn("a", a)
        self.addOut("r", r)
        
        bits = self.wires('b', a.getWidth(), 1)
        
        Bits(self, "bits", a, bits)
        
        Minterm(self, 'm{}'.format(v), bits, v, r)    
    
class Scope(Logic):
    
    def __init__(self, parent, name:str, x:Wire):
        """
        

        Parameters
        ----------
        parent : TYPE
            Parent cell.
        name : str
            Name of the instance.
        x : Wire
            Wire to monitor.

        Returns
        -------
        None.

        """
        super().__init__(parent, name)
        self.name = name
        self.x = self.addIn("x", x)
        
    def propagate(self):
        print("{}={}".format(self.name, self.x.get()) )