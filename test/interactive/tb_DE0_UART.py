# -*- coding: utf-8 -*-
"""
Created on Thu Oct  3 16:43:25 2024

@author: 2016570
"""

import py4hw
import math
import py4hw.external.platforms as plt
import py4hw.logic.protocol.uart as UART
import serial # If not there, install it with "pip install pyserial"
import time
import sys

class MsgToHex(py4hw.Logic):
    def __init__(self, parent, name, ready, valid, v, hex):
        super().__init__(parent, name)
        
        self.valid = self.addIn('valid', valid)
        self.ready = self.addOut('ready', ready)
        self.v = self.addIn('v', v)
        
        self.hex = hex
        
        for idx, item in enumerate(hex):
            self.addOut(f'hex{idx}', hex[idx])
        
        self.digit_count = 0
        self.hex_count = 0
        self.state = 0
        self.temp = 0
        
    def clock(self):
        if (self.state == 0): # IDLE
            if (self.valid.get()):
                # I am always ready
                self.state = 1
                self.ready.prepare(0)

                print('v=', self.v.get(), 'temp=', self.temp, 'digit count=', self.digit_count)

                if (self.v.get() >= ord('0') and self.v.get() <= ord('9')):
                    self.temp = (self.temp << 4) + self.v.get() - ord('0')
                    
                    if (self.digit_count == 0):
                        self.digit_count += 1
                    else:
                        self.digit_count = 0
                        self.state = 2
                elif (self.v.get() >= ord('A') and self.v.get() <= ord('F')):
                    self.temp = (self.temp << 4) + self.v.get() + 10 - ord('A')
                    
                    if (self.digit_count == 0):
                        self.digit_count += 1
                    else:
                        self.digit_count = 0
                        self.state = 2
                else:
                    # any other character produces a reset
                    self.digit_count = 0
                    self.hex_count = 0
                    self.temp = 0
            else:
                self.ready.prepare(1)
        elif (self.state == 1): # VALID
            self.state = 0
            self.ready.prepare(1)
            
        elif (self.state == 2): # Output HEX, INC hex count
            self.hex[self.hex_count].prepare(self.temp)
            self.temp = 0
            self.hex_count += 1
            self.state = 1
            
    def verilogBody(self):
        ret = ''

        ret += 'reg [1:0] state = 0;\n'
        ret += 'reg [6:0] temp = 0;\n'
        ret += 'reg rready = 0;\n'
        ret += 'reg [7:0] digit_count = 0;\n'
        ret += 'reg [7:0] hex_count = 0;\n'
        
        for idx, item in enumerate(self.hex):
            ret += f'reg [6:0] rhex{idx} = 0;\n'
            
        ret += 'assign ready = rready;\n'
        
        for idx, item in enumerate(self.hex):
            ret += f'assign hex{idx} = rhex{idx};\n'

        drv = py4hw.getObjectClockDriver(self)
        
        ret += f'always @(posedge {drv.name}) begin\n'
        
        ret += 'if (state == 0)\n'
        ret += '    begin\n'
        ret += '    if (valid == 1)\n'
        ret += '        begin\n'
        ret += '        state <= 1;\n'
        ret += '        rready <= 0;\n'
        ret += f"        if (v >= {ord('0')} && v <= {ord('9')})\n"
        ret += '            begin\n'
        ret += f"            temp <= (temp << 4) | (v - {ord('0')});\n"
        ret += '            if (digit_count == 0)\n'
        ret += '                begin\n'
        ret += '                digit_count <= digit_count + 1;\n'
        ret += '                end\n'
        ret += '            else\n'
        ret += '                begin\n'
        ret += '                digit_count <= 0;\n'
        ret += '                state <= 2;\n'
        ret += '                end\n'
        ret += '            end\n'
        ret += f"        else if (v >= {ord('A')} && v <= {ord('F')})\n"
        ret += '            begin\n'
        ret += f"            temp <= (temp << 4) | (v + 10 - {ord('A')});\n"
        ret += '            if (digit_count == 0)\n'
        ret += '                begin\n'
        ret += '                digit_count <= digit_count + 1;\n'
        ret += '                end\n'
        ret += '            else\n'
        ret += '                begin\n'
        ret += '                digit_count <= 0;\n'
        ret += '                state <= 2;\n'
        ret += '                end\n'
        ret += '            end\n'
        ret += '        else\n'
        ret += '            begin\n'
        ret += '            digit_count <= 0;\n'
        ret += '            hex_count <= 0;\n'
        ret += '            temp <= 0;\n'
        ret += '            end\n'
        ret += '        end\n'
        ret += '    else\n'
        ret += '        rready <= 1;\n'
        ret += '    end\n'
        ret += 'else if (state == 1) \n'
        ret += '    begin\n'
        ret += '    state <= 0;\n'
        ret += '    rready <= 1;\n'
        ret += '    end\n'
        ret += 'else if (state == 2) \n'
        ret += '    begin\n'
        ret += '                case (hex_count)\n'
        for idx, item in enumerate(self.hex):
            ret += f'                  {idx}: rhex{idx} <= temp;\n'
        ret += '                endcase \n'
        ret += '    temp <= 0;\n'
        ret += '    hex_count <= hex_count + 1;\n'
        ret += '    state <= 1;\n'
        ret += '    end\n'
        ret += '    end\n'
        return ret


def uartSend(ser, m):
    for c in m:
        ser.write(c.encode())
        #time.sleep(0.01)
        
    
banner_subset = '    '        
char_to_code = {' ':'00', '\n':'x', 
                'H':'76', 'E':'79', 'L':'38', 'O':'3F',
                'F':'71', 'R':'77', 'M':'37',
                'P':'73', 'Y':'72', 'T':'31', 'N':'37'}

def uartSendChar(ser, c):
    uartSend(ser, char_to_code[c])
    
def addBannerChar(ser, c):
    global banner_subset
    banner_subset = banner_subset + c
    banner_subset = banner_subset[1:5]
    
    for i in range(4):
        uartSendChar(ser, banner_subset[3-i])
        
    uartSendChar(ser, '\n')
    
hw = plt.DE0()

print('DE0 clk driver', hw.clockDriver.name)

inc = hw.wire('inc')
reset = hw.wire('reset')

N = 10000
binary_digits = int(math.ceil(math.log2(N)))
bcd_digits = int(math.ceil(math.log10(N)))

count = hw.wire('count', binary_digits)
count_bcd = hw.wire('count_bcd', 4*bcd_digits) # 2 digits are enough
carryout = hw.wire('carryout')

key = hw.getInputKey()

py4hw.Bit(hw, 'reset', key, 0, reset)
py4hw.Bit(hw, 'inc', key, 1, inc)

# sys.addOut('count', count)

#py4hw.Constant(sys, 'inc', 1, inc)
#py4hw.Constant(sys, 'reset', 0, reset)
#py4hw.ModuloCounter(sys, 'cout', N, reset, inc, count, carryout)
#py4hw.BinaryToBCD(sys, 'bcd', count, count_bcd)

numHexs = 4

hexs = [hw.getOutputHex(i) for i in range(numHexs)]
#bcds = [None] * bcd_digits

#for i in range(bcd_digits):
#    bcd_name = 'bcd{}'.format(i)
#    hex_name = 'hex{}'.format(i)
#    bcds[i] = sys.wire(bcd_name, 4)
#    py4hw.Range(sys, bcd_name, count_bcd, 4*i+3, 4*i, bcds[i])
#
#    py4hw.Digit7Segment(sys, hex_name, bcds[i], hexs[i])


#for i in range(bcd_digits, numHexs):
#    py4hw.Constant(sys, 'hex{}'.format(i), 0, hexs[i])


#vga_clk = sys.wire('VGA_CLK')
#py4hw.ClockDivider(sys, 'VGA_CLK', sys.clockDriver.freq, 25E6, vga_clk)
#
#vga_if = sys.getVGAController(vga_clk)
#
#
#vga_pattern = VGATestPattern(sys, 'vga', vga_if)
#vga_pattern.clockDriver = py4hw.ClockDriver('clk25', 25E6, wire=vga_clk)

#uart = sys.getUART()
gpio_in, gpio_out, gpio_oe = hw.getGPIO(0)

sysFreq = 50E6
uartFreq = 115200

py4hw.Constant(hw, 'tx_oe', 1, gpio_oe[0])


# dut = UART.UARTMsgGenerator(sys, 'msg', gpio_out[0], sysFreq, uartFreq, 'Hello crazy World\r\n')

msg_ready = hw.wire('msg_ready')
msg_valid = hw.wire('msg_valid')
ser_ready = hw.wire('ser_ready')
ser_valid = hw.wire('ser_valid')
des_ready = hw.wire('des_ready')
des_valid = hw.wire('des_valid')
msg_char = hw.wire('msg_char', 8)


UART.MsgSequencer(hw, 'msg_generator', msg_ready, msg_valid, msg_char,  'Hello crazy World\r\n')

uartClk = hw.wire('uart_clk')
tx_clk_pulse = hw.wire('tx_clk_pulse')

tx = gpio_out[0]
rx = gpio_in[1]

desync = hw.wire('desync')
rx_sample = hw.wire('rx_sample')

UART.ClockGenerationAndRecovery(hw, 'uart_clock', rx, desync, tx_clk_pulse, rx_sample, sysFreq, uartFreq)


UART.UARTSerializer(hw, 'ser', ser_ready, ser_valid, msg_char, tx_clk_pulse, tx)
UART.ReadyFlowControl(hw, 'flowcontrol', msg_ready, msg_valid, tx_clk_pulse, ser_ready, ser_valid, 20)


des_v = hw.wire('des_v', 8)

UART.UARTDeserializer(hw, 'des', rx, rx_sample, des_ready, des_valid, des_v, desync)

MsgToHex(hw, 'msg_to_hex', des_ready, des_valid, des_v, hexs)


if __name__ == "__main__":
    program = True
    
    if len(sys.argv) > 1:
        if 'gui' in sys.argv[1:]:
            py4hw.gui.Workbench(hw)
            
        if 'noprogram' in sys.argv[1:]:
            program = False

    if (program):
        dir = '/tmp/testDE0'
        hw.build(dir)
        hw.download(dir)


    ser = serial.Serial(port = '/dev/ttyUSB0', baudrate=115200, timeout=1, rtscts=False, dsrdtr=False)
    if not(ser.is_open):
        raise Exception('port not open')
        
    msg = ser.readline().decode('utf-8').strip()
    print('UART Rx=', msg)

    banner = 'HELLO FROM PYTHON '
    i = 0

    while True:
        addBannerChar(ser, banner[i])    
        i = (i +1 ) % len(banner)
        time.sleep(1)
