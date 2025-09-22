# -*- coding: utf-8 -*-
"""
Created on Thu Oct 29 17:10:01 2020

@author: dcr
"""
from .. import *
from .bitwise import Buf

from deprecated import deprecated

class Latch(Logic):
    '''
    This is an asynchronous LATCH
    '''
    def __init__(self, parent, name, d:Wire, q:Wire, enable:Wire):
        super().__init__(parent, name)
        self.d = self.addIn("d", d)
        self.q = self.addOut("q", q)
        self.e = self.addIn("e", enable)
        
    def propagate(self):
        
        if (self.e.get()):
            self.q.put(self.d.get())
            
    def structureName(self):
        msg = 'Latch{}'.format(self.q.getWidth())
        return msg
    
class Reg(Logic):
    """
    This is a D flip flop with (optional) enable and (optional) reset
    """
    def __init__(self, parent, name:str, d:Wire, q:Wire, enable:Wire=None, reset:Wire=None, reset_value:int=None ):
        """
        
        D flip flop with (optional) enable and (optional) reset

        Parameters
        ----------
        parent : TYPE
            parent.
        name : str
            name.
        d : Wire
            input.
        q : Wire
            output.
        enable : Wire, optional
            Enable signal. The default is None.
        reset : Wire, optional
            Synchronous reset signal. The default is None.

        Returns
        -------
        the object.

        """
        super().__init__(parent, name)
        self.d = self.addIn("d", d)
        self.q = self.addOut("q", q)

        if not(enable is None):
            self.e = self.addIn("e", enable)
        else:
            self.e = None
            
        if not(reset is None):
            self.r = self.addIn("r", reset)
        else:
            self.r = None
            
        if not(reset_value is None):
            self.reset_value = reset_value
        else:
            self.reset_value = 0
            
        self.value = self.reset_value
        
    def clock(self):
        setValue = True
        resetValue = False

        if not(self.e is None):
            if (self.e.get() == 0):
                setValue = False
        if not(self.r is None):
            if (self.r.get() == 1):
                resetValue = 1
                
        if (resetValue):
            self.value = self.reset_value
        elif (setValue):
            self.value = self.d.get()
        #else:
        #   maintain the same value            
            
        self.q.prepare(self.value)

    def structureName(self):
        msg = 'Reg{}'.format(self.q.getWidth())
        
        if not(self.r is None): msg += 'R'
        if not(self.e is None): msg += 'E'
        if not(self.reset_value == 0): msg += '_v{}'.format(self.reset_value)
        
        return msg
            
class TReg(Logic):
    def __init__(self, parent, name:str, t:Wire, q:Wire, enable:Wire=None, reset:Wire=None ):
        from .bitwise import Not
        from .bitwise import Mux2
        
        super().__init__(parent, name)
        
        self.addIn("t", t)
        
        if not(enable is None):
            self.addIn("e", enable)

        if not(reset is None):
            self.addIn("r", reset)
        
        self.addOut("q", q)
        
        nq = self.wire('nq', 1)
        Not(self, 'nq', q, nq)
        
        d = self.wire('d', 1)
        Mux2(self, 'mux', t, q, nq, d)
        Reg(self, 'reg', d, q, enable=enable, reset=reset)
        
class DelayLine(Logic):
    def __init__(self, parent, name:str, a:Wire, en:Wire, reset:Wire, r:Wire, delay:int):
        """
        Daisy-chained number of registers, typically used to create a 
        fixed-length delay line
        
        Parameters
        ----------
        parent : Logic
            Parent entity.
        name : str
            instance name.
        a : Wire
            input.
        en : Wire
            enable signal.
        r : Wire
            output.
        delay : int
            number of registers in the delay line.

        Returns
        -------
        None.

        """
        
        super().__init__(parent, name)
        
        self.addIn('a', a)
        if not(en is None): self.addIn('en', en)
        if not(reset is None): self.addIn('reset', reset)
        self.addOut('r', r)

        last = a
        for i in range(delay):
            newlast = self.wire('r{}'.format(i), a.getWidth())
            Reg(self, 'r{}'.format(i), last, newlast, enable=en, reset=reset)
            last = newlast
            
        Buf(self, 'buf', last, r)
        
        
class PipelinePhase(Logic):
    def __init__(self, parent, name, reset, ins, outs):
        super().__init__(parent, name)
        assert(len(ins) == len(outs))
        
        self.addIn('reset', reset)
        
        for i in range(len(ins)):
            self.addIn('in{}'.format(i), ins[i])
            self.addOut('out{}'.format(i), outs[i])
            
            Reg(self, 'r{}'.format(i), ins[i], outs[i], reset=reset)
            
            
class AsynchronousMemory(Logic):
    def __init__(self, parent, name, read_address, write_address, write, readdata, writedata):
        super().__init__(parent, name)
        
        self.read_address = self.addIn('read_address', read_address)
        self.write_address = self.addIn('write_address', write_address)
        self.write = self.addIn('write', write)
        self.readdata = self.addOut('readdata', readdata)
        self.writedata = self.addIn('writedata', writedata)
        
        if (read_address.getWidth() != write_address.getWidth()):
            raise Exception(f'read and write address must have the same width')
            
        if (read_address.getWidth() > 10):
            raise Exception(f'Memory too big! address width = {address.getWidth()}')
            
        numcells = 1 << read_address.getWidth()
        
        
        self.data = [0] * numcells
        
    def propagate(self):
        radd = self.read_address.get()
        wadd = self.write_address.get()
        
        # always reading
        #print(f'reading address {add} = {self.data[add]}')
        self.readdata.put(self.data[radd])
        
        if (self.write.get()):
            self.data[wadd] = self.writedata.get()
            
        
    def verilogBody(self):
        
        numcells = 1 << self.read_address.getWidth()
        w = self.readdata.getWidth()
        
        s = f'reg [{w-1}:0] mem [{numcells-1}:0];\n'
        s += "assign readdata =  mem[read_address];\n"

        s += 'always @(*) begin\n'
        s += 'if (write) \n'
        s += ' mem[write_address] = writedata;\n'
        s += 'end\n'
    
        return s
        
    
    


class SynchronousMemory(Logic):
    def __init__(self, parent, name, read_address, write_address, write, readdata, writedata):
        super().__init__(parent, name)
        
        self.read_address = self.addIn('read_address', read_address)
        self.write_address = self.addIn('write_address', write_address)
        self.write = self.addIn('write', write)
        self.readdata = self.addOut('readdata', readdata)
        self.writedata = self.addIn('writedata', writedata)
        
        if (read_address.getWidth() != write_address.getWidth()):
            raise Exception(f'read and write address must have the same width')
            
        if (read_address.getWidth() > 10):
            raise Exception(f'Memory too big! address width = {address.getWidth()}')
            
        numcells = 1 << read_address.getWidth()
        
        
        self.data = [0] * numcells
        
    def clock(self):
        radd = self.read_address.get()
        wadd = self.write_address.get()
        
        # always reading
        #print(f'reading address {add} = {self.data[add]}')
        self.readdata.prepare(self.data[radd])
        
        if (self.write.get()):
            self.data[wadd] = self.writedata.get()
            


    def verilogBody(self):
        numcells = 1 << self.read_address.getWidth()
        w = self.readdata.getWidth()
        
        s = f'(* ramstyle = "no_rw_check" *) reg [{w-1}:0] mem [0:{numcells-1}];\n'

        s += f'reg [{w-1}:0] rreaddata;\n'
        s += 'always @(posedge clk) begin\n'
        s += 'if (write) \n'
        s += ' mem[write_address] <= writedata;\n'
        s += ' rreaddata <= mem[read_address];\n'
        s += 'end\n'
    
        s += 'assign readdata = rreaddata;\n'

        return s
        
        
class DualPortSynchronousMemory(Logic):
    def __init__(self, parent, name, read_address_a, write_address_a, write_a, readdata_a, writedata_a,
                 read_address_b, write_address_b, write_b, readdata_b, writedata_b):
        super().__init__(parent, name)
        
        self.read_address_a = self.addIn('read_address_a', read_address_a)
        self.write_address_a = self.addIn('write_address_a', write_address_a)
        self.write_a = self.addIn('write_a', write_a)
        self.readdata_a = self.addOut('readdata_a', readdata_a)
        self.writedata_a = self.addIn('writedata_a', writedata_a)

        self.read_address_b = self.addIn('read_address_b', read_address_b)
        self.write_address_b = self.addIn('write_address_b', write_address_b)
        self.write_b = self.addIn('write_b', write_b)
        self.readdata_b = self.addOut('readdata_b', readdata_b)
        self.writedata_b = self.addIn('writedata_b', writedata_b)
        
        if ((read_address_a.getWidth() != write_address_a.getWidth()) or
            (read_address_b.getWidth() != write_address_b.getWidth()) or
            (read_address_a.getWidth() != read_address_b.getWidth())):
            raise Exception(f'read and write address must have the same width')
            
        if (read_address_a.getWidth() > 10):
            raise Exception(f'Memory too big! address width = {address.getWidth()}')
            
        numcells = 1 << read_address_a.getWidth()
               
        self.data = [0] * numcells
        
    def clock(self):
        radda = self.read_address_a.get()
        wadda = self.write_address_a.get()

        raddb = self.read_address_b.get()
        waddb = self.write_address_b.get()
        
        # always reading
        #print(f'reading address {add} = {self.data[add]}')
        self.readdata_a.prepare(self.data[radda])
        
        if (self.writea.get()):
            self.data[wadd] = self.writedataa.get()
            
        self.readdata_b.prepare(self.data[raddb])
        
        if (self.writeb.get()):
            self.data[wadd] = self.writedatab.get()


    def verilogBody(self):
        numcells = 1 << self.read_address_a.getWidth()
        w = self.readdata_a.getWidth()
        
        s = f'reg [{w-1}:0] mem [{numcells-1}:0];\n'

        s += 'always @(posedge clk) begin\n'
        s += 'if (write_a) \n'
        s += ' mem[write_address_a] <= writedata_a;\n'
        s += 'end\n'

        s += 'always @(posedge clk) begin\n'
        s += 'if (write_b) \n'
        s += ' mem[write_address_b] <= writedata_b;\n'
        s += 'end\n'

    
        s += 'assign readdata_a = mem[read_address_a];\n'
        s += 'assign readdata_b = mem[read_address_b];\n'
        return s
        

class ShiftRegisterBidirectional(Logic):
    def __init__(self, parent, name, 
                 left_in:Wire, right_in:Wire, 
                 left_out:Wire, right_out:Wire, 
                 shift_left:Wire, shift_right:Wire, depth:int):
        
        from .bitwise import Or2
        from .bitwise import Mux2
        
        super().__init__(parent, name)
        
        w = left_in.getWidth()
        assert(w == left_out.getWidth())
        assert(w == right_in.getWidth())
        assert(w == right_out.getWidth())
                
        self.addIn('left_in', left_in)
        self.addIn('right_in', right_in)
        self.addOut('left_out', left_out)
        self.addOut('right_out', right_out)
        
        self.addIn('shift_left', shift_left)
        self.addIn('shift_right', shift_right)
        
        q = self.wires('q', depth, w)
        
        # dir_r wires: left_in -> [0] -> [1] -> [2] -> right_out 
        # dir_l wires: left_out <- [0] <- [1] <- [2] <- right_in
        shift = self.wire('shift')
        Or2(self, 'shift', shift_left, shift_right, shift)
        
        for i in range(depth):
            if (i == 0):
                vl = left_in
            else:
                vl = q[i-1]
                
            if (i == depth-1):
                vr = right_in
            else:
                vr = q[i+1]
            
            rd = self.wire(f'rd{i}', w)
            # if we are shifting left, the value to input in the register 
            # should be the right one
            Mux2(self, f'rd{i}', shift_left, vl, vr, rd )
            Reg(self, f'r{i}', d=rd, q=q[i], enable=shift)
        
        Buf(self, 'left_out', q[0], left_out)
        Buf(self, 'right_out', q[depth-1], right_out)
        
class Stack_ShiftRegister(Logic):
    def __init__(self, parent, name, din, dout, push, pop, empty, full, depth):
        
        from .bitwise import Constant
        
        super().__init__(parent, name)


        # IO
        self.addIn("din", din)
        self.addIn("push", push)
        self.addIn("pop", pop)
        self.addOut("dout", dout)
        
        if not(empty is None):
            self.addOut("empty", empty)
            
        if not(full is None):
            self.addOut("full", full)

        zerow = self.wire('zerow', din.getWidth())
        pre_dout = self.wire('pre_dout', dout.getWidth())
        rout = self.wire('rout', dout.getWidth())
        
        Constant(self, 'zerow', 0 , zerow)
        ShiftRegisterBidirectional(self, 'shift', din, zerow, pre_dout, rout, pop, push, depth)
        
        # poped value is always present at the left side of the shift register, just load it 
        # into the register when poping
        Reg(self, 'dout', pre_dout, dout, enable=pop)
        
        
