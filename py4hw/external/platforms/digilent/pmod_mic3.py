# -*- coding: utf-8 -*-
"""
Created on Sat Sep 19 20:44:23 2026

@author: dcr
"""

import py4hw

class MIC3ReaderFSM(py4hw.Logic):
    def __init__(self, parent, name, reset, sclk_tick, sclk, sdata, m_ready, m_valid, m_data, cs_n):
        super().__init__(parent, name)

        self.reset = self.addIn('reset', reset)
        self.sclk_tick = self.addIn('sclk_tick', sclk_tick)
        self.sclk = self.addOut('sclk', sclk)
        self.sdata = self.addIn('sdata', sdata)
        self.m_ready = self.addIn('m_ready', m_ready)
        self.m_valid = self.addOut('m_valid', m_valid)
        self.m_data = self.addOut('m_data', m_data)
        self.cs_n = self.addOut('cs_n', cs_n)

        self.state = 0 # Idle
        self.bit_cnt = 0
        self.shift_reg = 0

    def clock(self):
        if (self.reset.get()):
            self.state = 0 # Idle
            self.cs_n.prepare(1)
            self.sclk.prepare(1)
            self.m_valid.prepare(0)
            self.m_data.prepare(0)
            self.bit_cnt = 0
            self.shift_reg = 0
        else:
            # Handshake logic: Clear valid flag once downstream consumer accepts data
            if (self.m_valid.get() and self.m_ready.get()):
                self.m_valid.prepare(0)

            if (self.state == 0): # Idle
                self.sclk.prepare(1)
                
                if (self.m_valid.get() == 0) and (self.m_ready.get() == 1):
                    # Wait until we get a ready signal to start sampling
                    self.cs_n.prepare(0)
                    self.bit_cnt = 0
                    self.shift_reg = 0
                    self.state = 1 # Start
                else:
                    self.cs_n.prepare(1)

            elif (self.state == 1): # Start
                if (self.sclk_tick.get()):
                    self.sclk.prepare(0)
                    self.state = 2 # SCLK_LOW
                    
            elif (self.state == 2): # SCLK_LOW
                if (self.sclk_tick.get()):
                    self.state = 3 # Read
                    self.sclk.prepare(1)
                    
            elif (self.state == 3): # Read
                # We should sample in the rising edge of SCLK
                if (self.sclk_tick.get()):
                    self.shift_reg = self.shift_reg << 1 | self.sdata.get()

                    if (self.bit_cnt == 15):
                        self.state = 4 # Out

                    else:
                        self.sclk.prepare(0)
                        self.state = 2 # SCLK_LOW
                        self.bit_cnt += 1

            elif (self.state == 4): # Out
                self.cs_n.prepare(1)
                self.sclk.prepare(1)
                self.m_data.prepare(self.shift_reg)
                self.m_valid.prepare(1)
                self.state = 0
            else:
                self.state = 0 # Idle
            
class MIC3Reader(py4hw.Logic):
    def __init__(self, parent, name, reset, sclk_ref, sclk, sdata, cs_n, m_ready, m_valid, m_data):
        '''
        It is reading ADCS7476
        '''
        super().__init__(parent, name)

        self.addIn('reset', reset)

        # SPI Physical Interface
        self.addIn('sclk_ref', sclk_ref) # Serial Clock input/reference
        self.addOut('sclk', sclk) # Serial Clock input/reference
        self.addIn('sdata', sdata) # Serial Data input from microphone
        self.addOut('cs_n', cs_n) # Active-low Chip Select output
    
        # Ready/Valid Data Interface
        self.addIn('m_ready', m_ready) # Downstream receiver ready
        self.addOut('m_valid', m_valid) # Data valid indicator
        self.addOut('m_data',  m_data) # 12-bit microphone sample

        assert (m_data.getWidth() == 16)

        sclk_tick = self.wire('sclk_tick')
        py4hw.EdgeDetector(self, 'edge', sclk_ref, sclk_tick, 'neg')

        MIC3ReaderFSM(self, 'fsm', reset, sclk_tick, sclk, sdata, m_ready, m_valid, m_data, cs_n)


class BitsToDecimalFSM(py4hw.Logic):
    # the idea is to sample a value and size (in nibbles) and generate the
    # equivalent <n> hex digits for its hexadecimal representation

    def __init__(self, parent, name, reset, bits_ready, bits_valid, bcd, char_ready, char_valid, char_value):
        super().__init__(parent, name)

        self.reset = self.addIn('reset', reset)

        self.bits_ready = self.addOut('bits_ready', bits_ready)
        self.bits_valid = self.addIn('bits_valid', bits_valid)
        self.bcd = self.addIn('bcd', bcd)

        self.char_ready = self.addIn('char_ready', char_ready)
        self.char_valid = self.addOut('char_valid', char_valid)
        self.char_value = self.addOut('char_value', char_value)

        self.count = 5
        self.state = 0
        self.v = 0

    def clock(self):
        if (self.reset.get()):
            self.bits_ready.prepare(0)
            self.char_valid.prepare(0)
            self.state = 0 # Idle

            # 5 decimal digits are enough, by now we hardcode this value
            self.count = 5
            self.v = 0
            
        else:
            if (self.state == 0): # Idle
                if (self.char_ready.get()):
                    # We are ready to start acquiring
                    self.bits_ready.prepare(1)
                    self.state = 1 # Acquire

            elif (self.state == 1): # Acquire
                if (self.bits_valid.get()):
                    self.bits_ready.prepare(0)
                    self.state = 2 # Sampled

            elif (self.state == 2): # Sample
                self.v = self.bcd.get()
                self.count = 5
                self.state = 3 # Sampled
                
            elif (self.state == 3): # Sampled
                # Now we try to emit the characters
                self.char_value.prepare(ord('0') + ((self.v >> (4 * 4)) & 0xF)) # shift 4 nibbles
                self.char_valid.prepare(1)
                self.state = 4 # wait for ready
                
            elif (self.state == 4): # wait for ready
                # we assume char was ready
                self.char_valid.prepare(0)
                self.state = 5 # try again

            elif (self.state == 5): # try again
                # wait that we flush the character
                if (self.char_ready.get()):
                    self.count -= 1
                    self.v = self.v << 4
                    self.state = 6
                    
            elif (self.state == 6):
                if (self.count == 0):
                    self.state = 7
                else:
                    self.state = 3

            elif (self.state == 7): # emit a new line
                self.char_value.prepare(ord('\n')) # new line
                self.char_valid.prepare(1)
                self.state = 8 # wait for ready

            elif (self.state == 8):
                # we assume char was ready
                self.char_valid.prepare(0)
                self.state = 9 # try again

            elif (self.state == 9):
                # wait that we flush the character
                if (self.char_ready.get()):
                    self.state = 0

class BitsToDecimal(py4hw.Logic):
    # the idea is to sample a value and size (in nibbles) and generate the
    # equivalent <n> hex digits for its hexadecimal representation

    def __init__(self, parent, name, reset, bits_ready, bits_valid, bits_value, char_ready, char_valid, char_value):
        super().__init__(parent, name)

        self.reset = self.addIn('reset', reset)

        self.addOut('bits_ready', bits_ready)
        self.addIn('bits_valid', bits_valid)
        self.addIn('bits_value', bits_value)

        self.addIn('char_ready', char_ready)
        self.addOut('char_valid', char_valid)
        self.addOut('char_value', char_value)

        import math
        maxnum = (1 << bits_value.getWidth())-1
        bcd_digits = int(math.ceil(math.log10(maxnum)))

        bcd_width = bcd_digits * 4

        bcd = self.wire('bcd', bcd_width)
        sample_bits = self.wire('sample_bits')
        sampled_bits = self.wire('sampled_bits', bits_value.getWidth())

        py4hw.And2(self, 'sample_bits', bits_ready, bits_valid, sample_bits)

        py4hw.Reg(self, 'sampled_bits', d=bits_value, q=sampled_bits, enable=sample_bits)
        py4hw.BinaryToBCD(self, 'bcd', sampled_bits, bcd)

        BitsToDecimalFSM(self, 'fsm',  reset, bits_ready, bits_valid, bcd, char_ready, char_valid, char_value)

class MIC3Model(py4hw.Logic):
    def __init__(self, parent, name, cs_n, sclk, sdata):
        '''
        Simulates de behaviour of the PMOD MIC3 Module that contains the
        Knowles SPA2410LR5H-B Microphone
        and the Texas Instruments ADCS7476 (up to 1 MSPS)
        
        '''
        super().__init__(parent, name)

        self.cs_n = self.addIn('cs_n', cs_n)
        self.sclk = self.addIn('sclk', sclk)
        self.sdata = self.addOut('sdata', sdata)

        self.co = self.run()
        self.v = 1000
        self.bit = 0

    def clock(self):
        next(self.co)

    def run(self):
        self.sdata.prepare(0)
        yield
        yield
        
        while (True):
            # wait until Chip Select is deasserted (active low)
            while (self.cs_n.get()):
                yield

            print('MIC value:', self.v) 

            v = self.v

            self.bit = 'w'
            

            # wait until clock is low (falling edge)
            while (self.sclk.get()):
                yield

            
            for i in range(16):            
                self.bit = i
                self.sdata.prepare((v >> 15) & 1)
                v = v << 1

                # wait until the positive clock edge
                while not(self.sclk.get()):
                    yield

                self.bit = '/'
                # wait until clock is low (falling edge)
                while (self.sclk.get()):
                    yield

            self.v += 1

            yield
        