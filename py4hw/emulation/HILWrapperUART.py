# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 16:35:27 2024

@author: 2016570
"""
import py4hw
import os
import math
import py4hw.logic.protocol.uart as UART

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
                
class HILPlatform:
    
    def __init__(self, platform, projectDir, dutName):
        self.platform = platform
        self.projectDir = projectDir
        self.dutName = dutName
        
        
    def build(self):
        self.platform.build(self.projectDir, createdStructures=[self.dutName])    
        
    def download(self):
        self.platform.download(self.projectDir)

def getDUTValidIns(dut):
    # we only support a maximum of 32 bits per input by now
    for i in range(len(dut.inPorts)):
        assert(dut.inPorts[i].wire.getWidth() <= 32)
    return len(dut.inPorts)

def getDUTValidOuts(dut):
    # we only support a maximum of 32 bits per input by now
    for i in range(len(dut.outPorts)):
        assert(dut.outPorts[i].wire.getWidth() <= 32)
    return len(dut.outPorts)
    
def AbstractClassInit(self, parent:py4hw.Logic, name:str):
    super(self.__class__, self).__init__(parent, name)

def AbstractClassStructureName(self):
    return self.name
    
def AbstractClass(class_name):
    return type(class_name, # class name
                (py4hw.Logic,), # base classes
                {
                    '__init__': AbstractClassInit,              # constructor
                    'structureName': AbstractClassStructureName # structure name
                }
                )

def createHILUART(platform, dut, projectDir):
    dutStructureNameWithoutInstanceNumber = py4hw.getVerilogModuleName(dut, noInstanceNumber=True)
    dutStructureNameWithInstanceNumber = py4hw.getVerilogModuleName(dut, noInstanceNumber=False)
    
    # use instance number if necessary
    dutStructureName = dutStructureNameWithoutInstanceNumber if (dutStructureNameWithoutInstanceNumber == dutStructureNameWithInstanceNumber) else dutStructureNameWithInstanceNumber

    hil_plt = HILPlatform(platform, projectDir, dutStructureName)
    
    if not(os.path.exists(projectDir)):
        print('Creating the directory', projectDir)
        os.makedirs(projectDir)
        
    # First create verilog for the dut        
    rtl = py4hw.VerilogGenerator(dut)
    
    rtl_code = rtl.getVerilogForHierarchy(noInstanceNumberInTopEntity=False)
    verilog_file = os.path.join(projectDir, dutStructureName+'.v')
    
    with open(verilog_file, 'w') as file:
        file.write(rtl_code)
            
    # Create the wrapping elements -----------------------------------------------------
    
    ready_req = platform.wire('ready_req')
    valid_req = platform.wire('valid_req')
    c_req = platform.wire('c_req', 8)
    
    ser_ready = platform.wire('ser_ready')
    ser_valid = platform.wire('ser_valid')
    ser_v = platform.wire('ser_v', 8)

    num_ins = getDUTValidIns(dut)
    num_outs = getDUTValidOuts(dut)
    
    ena_in_w = int(math.ceil(math.log2(num_ins)))
    num_ins_up = 1 << ena_in_w
    
    ena_out_w = int(math.ceil(math.log2(num_outs)))
    num_outs_up = 1 << ena_out_w

    ena_in_list = platform.wires('ena_in', num_ins_up, 1) # create extra ins because the decoder has to be a power of 2
    ena_out_list = platform.wires('ena_out', num_outs_up, 1) # create extra outs because the decoder has to be a power of 2

    ena_in = platform.wire('ena_in', 1)
    v_in = platform.wire('v_in', 32)
    ena_out = platform.wire('ena_out', 1)
    
    set_ena_in = platform.wire('set_ena_in')
    set_v_in = platform.wire('set_v_in')
    set_ena_out = platform.wire('set_ena_out')
    clk_pulse = platform.wire('clk_pulse')
    start_resp = platform.wire('start_resp')

    hlp = py4hw.LogicHelper(platform)
    
    # input registers
    py4hw.Decoder(platform, 'decode_ena_in', ena_in, ena_in_list)
    py4hw.Decoder(platform, 'decode_ena_out', ena_out, ena_out_list)

    fake_ins = []
    fake_outs = []
    
    for i in range(num_ins):
        ip = dut.inPorts[i]
        in_name = ip.name
        iw = ip.wire.getWidth()
        in_wire = platform.wire(f'in{i}')
        fake_ins.append((in_name, in_wire))
        
        py4hw.Reg(platform, f'in{i}', d=v_in,  q=in_wire, enable=hlp.hw_and2(ena_in_list[i], set_v_in))

    resp_v = platform.wire('resp_v', 32)
    resp_size = platform.wire('resp_size', 8)
    reg_out = platform.wires('reg_out', num_outs_up, 32)
    size_out = platform.wires('size_out', num_outs_up, 8)

    for i in range(num_outs_up):
        if (i < num_outs):
            op = dut.outPorts[i]
            out_name = op.name
            ow = op.wire.getWidth()
            out_wire = platform.wire(f'out{i}')
            fake_outs.append((out_name, out_wire))
            
            py4hw.Reg(platform, f'out{i}', d=out_wire, q=reg_out[i], enable=hlp.hw_and2(ena_out_list[i], set_ena_out))
            
            py4hw.Constant(platform, f'out_size{i}', 8, size_out[i])
        else:
            py4hw.Constant(platform, f'out_{i}', 0, reg_out[i])
            py4hw.Constant(platform, f'out_size{i}', 0, size_out[i])

    py4hw.Mux(platform, 'resp_v', ena_out, reg_out, resp_v)
    py4hw.Mux(platform, 'resp_size', ena_out, size_out, resp_size)

    desync = platform.wire('desync')
    tx_clk_pulse = platform.wire('tx_clk_pulse')
    rx_sample = platform.wire('rx_sample')
    
    CMDRequest(platform, 'cmd_req', ready_req, valid_req, c_req,  ena_in, v_in, ena_out, set_ena_in, set_v_in, set_ena_out, clk_pulse, start_resp)

    CMDResponse(platform, 'cmd_resp', resp_v, resp_size, start_resp, ser_ready, ser_valid, ser_v)

    sysFreq = 50E6 # @todo this frequency should be obtained from the clock source
    uartFreq = 115200

    UART.ClockGenerationAndRecovery(platform, 'uart_clock', platform.rx, desync, tx_clk_pulse, rx_sample, sysFreq, uartFreq)

    des = UART.UARTDeserializer(platform, 'des', platform.rx, rx_sample, ready_req, valid_req, c_req, desync)
    ser = UART.UARTSerializer(platform, 'ser', ser_ready, ser_valid, ser_v, tx_clk_pulse, platform.tx)

    abstract_class = AbstractClass(dutStructureName)
    obj = abstract_class(platform, dutStructureName)
    
    for i in range(len(fake_ins)):
        obj.addIn(fake_ins[i][0], fake_ins[i][1])
        
    for i in range(len(fake_outs)):
        obj.addIn(fake_outs[i][0], fake_outs[i][1])
    
    return hil_plt
    
    