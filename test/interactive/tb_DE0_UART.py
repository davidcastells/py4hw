import py4hw
import py4hw.external.platforms as plt
import py4hw.logic.protocol.uart as UART
import HIL_UART
import serial
import time
import os


class DUT(py4hw.Logic):


    def __init__(self, parent, name, a, b, p, m):
        super().__init__(parent, name)
        
        self.addIn('a', a)
        self.addIn('b', b)
        self.addOut('p', p)
        self.addOut('m', m)
        
        py4hw.Add(self, 'add', a, b, p)
        py4hw.Sub(self, 'sub', a, b, m)






sys = plt.DE0()


print('DE0 clk driver', sys.clockDriver.name)


inc = sys.wire('inc')
reset = sys.wire('reset')




gpio_in, gpio_out, gpio_oe = sys.getGPIO(0)


sysFreq = 50E6
uartFreq = 115200


py4hw.Constant(sys, 'tx_oe', 1, gpio_oe[0])


tx = gpio_out[0]
rx = gpio_in[1]




a = sys.wire('a', 32)
b = sys.wire('b', 32)
p = sys.wire('p', 32)
m = sys.wire('m', 32)


ready_req = sys.wire('ready_req')
valid_req = sys.wire('valid_req')
c_req = sys.wire('c_req', 8)


ser_ready = sys.wire('ser_ready')
ser_valid = sys.wire('ser_valid')
ser_v = sys.wire('ser_v', 8)

fc_ready = sys.wire('fc_ready')
fc_valid = sys.wire('fc_valid')
fc_v = sys.wire('fc_v', 8)


ena_in = sys.wire('ena_in', 1)
v_in = sys.wire('v_in', 32)
ena_out = sys.wire('ena_out', 1)


set_ena_in = sys.wire('set_ena_in')
set_v_in = sys.wire('set_v_in')
set_ena_out = sys.wire('set_ena_out')
clk_pulse = sys.wire('clk_pulse')
start_resp = sys.wire('start_resp')


hlp = py4hw.LogicHelper(sys)


DUT(sys, 'dut', a, b, p, m)


ena_in_list = sys.wires('ena_in', 2, 1)
ena_out_list = sys.wires('ena_out', 2, 1)


py4hw.Decoder(sys, 'decode_ena_in', ena_in, ena_in_list)
py4hw.Decoder(sys, 'decode_ena_out', ena_out, ena_out_list)


py4hw.Reg(sys, 'a', d=v_in,  q=a, enable=hlp.hw_and2(ena_in_list[0], set_v_in))
py4hw.Reg(sys, 'b', d=v_in,  q=b, enable=hlp.hw_and2(ena_in_list[1], set_v_in))


resp_v = sys.wire('resp_v', 32)
resp_size = sys.wire('resp_size', 8)
reg_out = sys.wires('reg_out', 2, 32)
size_out = sys.wires('size_out', 2, 8)


desync = sys.wire('desync')
tx_clk_pulse = sys.wire('tx_clk_pulse')
rx_sample = sys.wire('rx_sample')


py4hw.Reg(sys, 'p', d=p, q=reg_out[0], enable=hlp.hw_and2(ena_out_list[0], set_ena_out))
py4hw.Reg(sys, 'm', d=m, q=reg_out[1], enable=hlp.hw_and2(ena_out_list[1], set_ena_out))


py4hw.Constant(sys, 'psize', 8, size_out[0])
py4hw.Constant(sys, 'msize', 8, size_out[1])


py4hw.Mux(sys, 'resp_v', ena_out, reg_out, resp_v)
py4hw.Mux(sys, 'resp_size', ena_out, size_out, resp_size)


HIL_UART.CMDRequest(sys, 'cmd_req', ready_req, valid_req, c_req,  ena_in, v_in, ena_out, set_ena_in, set_v_in, set_ena_out, clk_pulse, start_resp)




#HIL_UART.CMDResponse(sys, 'cmd_resp', resp_v, resp_size, start_resp, fc_ready, fc_valid, ser_v)
HIL_UART.CMDResponse(sys, 'cmd_resp', resp_v, resp_size, start_resp, ser_ready, ser_valid, ser_v)


UART.ClockGenerationAndRecovery(sys, 'uart_clock', rx, desync, tx_clk_pulse, rx_sample, sysFreq, uartFreq)


#HIL_UART.ReadyFlowControl(sys, 'fc', fc_ready, fc_valid, tx_clk_pulse, ser_ready,ser_valid,20)

des = UART.UARTDeserializer(sys, 'des', rx, rx_sample, ready_req, valid_req, c_req, desync)
ser = UART.UARTSerializer(sys, 'ser', ser_ready, ser_valid, ser_v, tx_clk_pulse, tx)


dir = '/tmp/testDE0'
python_time = os.path.getmtime(__file__)
sof_time = os.path.getmtime(os.path.join(dir, 'DE0.sof'))

res = python_time - sof_time
print('python_time: ' , python_time ,'\n','sof_time:', sof_time, '\n' , 'resta:', res)


if (False):
    sys.build(dir)
    sys.download(dir)


ser = serial.Serial(port = 'COM3', baudrate=115200, timeout=1, rtscts=False, dsrdtr=False)
if not(ser.is_open):
    raise Exception('port not open')


def readLine(ser):
    msg = ser.readline().decode('utf-8').strip()
    print(msg)



def uartSend(ser, m):
    for c in m:
        ser.write(c.encode())
        #time.sleep(0.01)
        #while not ser.out_waiting == 0:  # Espera hasta que el buffer de salida esté vacío
        #   pass

       
readLine(ser)
for i in range(100):
    print('Testing', i)
    uartSend(ser, 'I0=12345!\n')
    #time.sleep(0.01) # amb un time. sleep aqui entre pasar els 2 valors de les variables sembla que funciona correctament
    uartSend(ser, 'I1={:X}!\n'.format(i))
    uartSend(ser, 'O0?\n')
    readLine(ser)
    uartSend(ser, 'O1?\n')
    readLine(ser)