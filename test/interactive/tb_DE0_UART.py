# -*- coding: utf-8 -*-
"""
Created on Thu Oct  3 16:43:25 2024

@author: 2016570
"""

import py4hw
import math
import py4hw.external.platforms as plt
import py4hw.logic.protocol.uart as UART


sys = plt.DE0()

print('DE0 clk driver', sys.clockDriver.name)

inc = sys.wire('inc')
reset = sys.wire('reset')

N = 10000
binary_digits = int(math.ceil(math.log2(N)))
bcd_digits = int(math.ceil(math.log10(N)))

count = sys.wire('count', binary_digits)
count_bcd = sys.wire('count_bcd', 4*bcd_digits) # 2 digits are enough
carryout = sys.wire('carryout')

key = sys.getInputKey()

py4hw.Bit(sys, 'reset', key, 0, reset)
py4hw.Bit(sys, 'inc', key, 1, inc)

# sys.addOut('count', count)

#py4hw.Constant(sys, 'inc', 1, inc)
#py4hw.Constant(sys, 'reset', 0, reset)
py4hw.ModuloCounter(sys, 'cout', N, reset, inc, count, carryout)
py4hw.BinaryToBCD(sys, 'bcd', count, count_bcd)

numHexs = 4

hexs = [sys.getOutputHex(i) for i in range(numHexs)]
bcds = [None] * bcd_digits

for i in range(bcd_digits):
    bcd_name = 'bcd{}'.format(i)
    hex_name = 'hex{}'.format(i)
    bcds[i] = sys.wire(bcd_name, 4)
    py4hw.Range(sys, bcd_name, count_bcd, 4*i+3, 4*i, bcds[i])

    py4hw.Digit7Segment(sys, hex_name, bcds[i], hexs[i])


for i in range(bcd_digits, numHexs):
    py4hw.Constant(sys, 'hex{}'.format(i), 0, hexs[i])


#vga_clk = sys.wire('VGA_CLK')
#py4hw.ClockDivider(sys, 'VGA_CLK', sys.clockDriver.freq, 25E6, vga_clk)
#
#vga_if = sys.getVGAController(vga_clk)
#
#
#vga_pattern = VGATestPattern(sys, 'vga', vga_if)
#vga_pattern.clockDriver = py4hw.ClockDriver('clk25', 25E6, wire=vga_clk)

#uart = sys.getUART()
gpio_in, gpio_out, gpio_oe = sys.getGPIO(0)

sysFreq = 50E6
uartFreq = 115200

py4hw.Constant(sys, 'tx_oe', 1, gpio_oe[0])
dut = UART.UARTMsgGenerator(sys, 'msg', gpio_out[0], sysFreq, uartFreq, 'Hello crazy World\r\n')


py4hw.gui.Workbench(sys)


if (True):
    dir = '/tmp/testDE0'
    sys.build(dir)
    sys.download(dir)
