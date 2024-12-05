import py4hw

class CMDRequest(py4hw.Logic):
    def __init__(self, parent, name, ready, valid, c,  ena_in, v_in, ena_out, set_ena_in, set_v_in, set_ena_out, clk_pulse, start_resp):
        super().__init__(parent, name)
        
        self.ready = self.addOut('ready', ready)
        self.valid = self.addIn('valid', valid)
        self.c = self.addIn('c', c)
        
        self.ena_in = self.addOut('ena_in', ena_in)
        self.v_in = self.addOut('v_in', v_in)
        self.ena_out = self.addOut('ena_out', ena_out)
        
        self.set_ena_in = self.addOut('set_ena_in', set_ena_in)
        self.set_v_in = self.addOut('set_v_in', set_v_in)
        self.set_ena_out = self.addOut('set_ena_out', set_ena_out)
        
        self.clk_pulse = self.addOut('clk_pulse', clk_pulse)
        self.start_resp = self.addOut('start_resp', start_resp)
        
        self.state = 0
        self.cur_type = 0
        self.new_c = 0
        self.temp = 0
        
    def clock(self):
        if (self.state == 0): # UNKNOWN
            self.ready.prepare(1)
            self.set_ena_in.prepare(0)
            self.set_v_in.prepare(0)
            self.set_ena_out.prepare(0)
            self.state = 1 
        elif (self.state == 1): #READY
            if (self.valid.get()):
                # I'm sure that ready is active
                self.ready.prepare(0)
                self.new_c = self.c.get()
                self.state = 2
            else:
                self.ready.prepare(1)
        elif (self.state == 2): # CONSUME CHAR
            if (self.new_c == ord('I')):
                self.cur_type = 1 # input
                self.temp = 0
                self.state = 0
            elif (self.new_c == ord('=')):
                self.state = 3 # -> consolidate ena_in
                self.cur_type = 2 # value
            elif (self.new_c == ord('O')):
                self.cur_type = 3 # output
                self.temp = 0
                self.state = 0
            elif (self.new_c == ord('K')):
                self.cur_type = 4 # clk
                self.temp = 0
                self.state = 0
            elif (self.new_c == ord('!')):
                self.state = 5 # -> consolidate v_in
            elif (self.new_c == ord('?')):
                self.state = 6 # -> consolidate ena_out
            elif (self.new_c == ord(';')):
                self.state = 8 # -> clk
                
            elif (self.new_c >= ord('0') and self.new_c <= ord('9')):
                # we receive hex digits in MSBF order
                self.temp = (self.temp << 4) | (self.new_c - ord('0'))
                self.state = 0
            elif (self.new_c >= ord('A') and self.new_c <= ord('F')):
                # we receive hex digits in MSBF order
                self.temp = (self.temp << 4) | (self.new_c + 10 - ord('A'))
                self.state = 0
            else:
                self.state = 4 # reset temp if unknown char is received
                
        elif (self.state == 3): # CONSOLIDATE ENA IN
            self.ena_in.prepare(self.temp)
            self.set_ena_in.prepare(1)
            self.state = 4 # -> reset temp
            
        elif (self.state == 4): # RESET TEMP
            self.temp = 0
            self.start_resp.prepare(0)
            self.set_ena_in.prepare(0)
            self.set_v_in.prepare(0)
            self.set_ena_out.prepare(0)
            self.state = 0
            
        elif (self.state == 5): # CONSOLIDATE V_IN
            self.v_in.prepare(self.temp)
            self.set_v_in.prepare(1)
            self.state = 4 # -> reset temp
            
        elif (self.state == 6): # CONSOLIDATE ENA_OUT
            self.ena_out.prepare(self.temp)
            self.set_ena_out.prepare(1)
            self.state = 7 # -> start resp
            
        elif (self.state == 7): # START RESP
            self.set_ena_out.prepare(0)
            self.start_resp.prepare(1)
            self.state = 4
        
        elif (self.state == 8): # CLK 0
            if (self.temp == 0):
                self.state = 4
                self.clk_pulse.prepare(0)
            else:
                self.temp = self.temp - 1
                self.state = 9
                self.clk_pulse.prepare(1)
                
        elif (self.state == 9): # CLK 1
            self.clk_pulse.prepare(0)
            self.state = 8
            
            
class CMDResponse(py4hw.Logic):
    # the idea is to sample a value and size (in nibbles) and generate the
    # equivalent <n> hex digits for its hexadecimal representation
    
    def __init__(self, parent, name, vin, size, start_resp, ready, valid, v):
        super().__init__(parent, name)
        
        self.vin = self.addIn('vin', vin)
        self.size = self.addIn('size', size)
        self.start_resp = self.addIn('start_resp', start_resp)
        
        self.ready = self.addIn('ready', ready)
        self.valid = self.addOut('valid', valid)
        self.v = self.addOut('v', v)
        
        self.state = 0
        self.temp = 0
        self.temp_size = 0
        self.aux = 0
        
    def clock(self):
        if (self.state == 0): #IDLE
            if (self.start_resp.get()):
                self.state = 1
                self.temp = self.vin.get()         # sample value
                self.temp_size = self.size.get() - 1  # sample size (in nibbles)
                
        elif (self.state == 1): # START RESPONSE
            if (self.ready.get()):
                self.state = 2
                self.valid.prepare(1)
                self.v.prepare(ord('='))
        elif (self.state == 2): # 
            if (self.ready.get() == 0):
                self.valid.prepare(1)
            else:
                self.valid.prepare(0)
                self.state = 3
                self.aux = (self.temp >> (self.temp_size*4))   & 0xF
        elif (self.state == 3): # SEND Most Significant Nibble
            if (self.ready.get()):
                self.state = 4
                self.valid.prepare(1)
                if (self.aux >= 0 and self.aux <= 9):
                    self.v.prepare(ord('0') + self.aux)
                else:
                    self.v.prepare(ord('A') + self.aux - 10)
                                   
        elif (self.state == 4):
            if (self.ready.get() == 0):
                # wait here
                self.valid.prepare(1)
            else:
                self.valid.prepare(0)
                if (self.temp_size == 0):
                    self.state = 5
                else:
                    self.state = 3
                    self.aux = (self.temp >> ((self.temp_size-1)*4))  & 0xF
                    self.temp_size = self.temp_size - 1                   
                    
        elif (self.state == 5): # LAST CHAR
            self.valid.prepare(1)
            self.v.prepare(ord('!'))
            self.state = 6
            
        elif (self.state == 6):
            if (self.ready.get() == 0):
                # wait here
                self.valid.prepare(1)
            else:
                self.valid.prepare(0)
                self.state = 0


class ReadyFlowControl(py4hw.Logic):
    #
    #  | msg |-> valid ------------> | in_valid      out_valid |-------------> valid ->| ser |
    #  |     |<- ready --------------| in_ready      out_ready |<------------- ready <-|     |
    #
    # we propagate the out_ready=0 inmediately to in_ready but
    # take a number (count) of pulses to propagate the out_ready=1
    #
    def __init__(self, parent, name, in_ready, in_valid, clk_enable, out_ready, out_valid, count):
        super().__init__(parent, name)        
        
        import math
        
        self.addIn('in_valid', in_valid)
        self.addOut('in_ready', in_ready)
        self.addIn('out_ready', out_ready)
        self.addOut('out_valid', out_valid)
        self.addIn('clk_enable', clk_enable)
        
        nout_ready = self.wire('nout_ready')
        
        wcount = int(math.ceil(math.log2(count)))
        q = self.wire('q', wcount)
        iseq = self.wire('iseq')
        
        py4hw.Not(self, 'nout_ready', out_ready, nout_ready)
        py4hw.Counter(self, 'count', reset=nout_ready, inc=clk_enable, q=q)
        py4hw.EqualConstant(self, 'iseq', q, count, iseq)
        
        py4hw.Reg(self, 'in_ready', d=iseq, q=in_ready, enable=iseq, reset=nout_ready)
        
        py4hw.Buf(self, 'out_valid', in_valid, out_valid)