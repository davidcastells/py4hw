# -*- coding: utf-8 -*-
"""
Created on Sat Dec 21 13:17:38 2024

@author: 2016570
"""

import py4hw
from edalize import edatool
import os

class C10LP(py4hw.HWSystem):
    
    def __init__(self):
        
        super().__init__(name='C10LP')
        
        clk50 = self.wire('c10_clk50m')
        #clk50 = self.addIn('CLOCK_50', clk50)
        clockDriver = py4hw.ClockDriver('c10_clk50m', 50E6, 0, wire=clk50)
        
        print('Initial', self.getFullPath(),  self._wires)
        
        self.clockDriver = clockDriver
    
    
    
    def build(self,  projectDir, createdStructures=[]):
        if not(os.path.exists(projectDir)):
            print('Creating the directory', projectDir)
            os.makedirs(projectDir)
            
        rtl = py4hw.VerilogGenerator(self)
        
        rtl_code = rtl.getVerilogForHierarchy(noInstanceNumberInTopEntity=True, createdStructures=createdStructures)
        qsf_code = self.getQsf()
        top_name = self.name
        
        verilog_file = os.path.join(projectDir, top_name+'.v')
        qsf_file = os.path.join(projectDir, top_name+'_pins.qsf')
        sdc_file = os.path.join(projectDir, 'CLOCK_50.sdc')

        # Create Verilog file
        with open(verilog_file, 'w') as file:
            file.write(rtl_code)

        # Create Verilog file
        with open(qsf_file, 'w') as file:
            file.write(qsf_code)
            
        with open(sdc_file, 'w') as file:
            file.write('create_clock  -period 20 [get_ports c10_clk50m]\n')
            
        tool = 'quartus'
        
        files = [  {'name' : verilog_file, 'file_type' : 'verilogSource'},
                 {'name' : sdc_file, 'file_type' : 'SDC'},
                 {'name' : qsf_file, 'file_type' : 'tclSource'}
                 ]

        info = self.getFPGADeviceInfo()

        parameters = {'clk_freq_hz' : {'datatype' : 'int', 'default' : 50000000, 'paramtype' : 'vlogparam'},
              'vcd' : {'datatype' : 'bool', 'paramtype' : 'plusarg'},
              'family': {'datatype': 'string', 'paramtype': 'generic', 'default':'Cyclone 10'},
              'device': {'datatype': 'string', 'paramtype': 'generic', 'default':info['device']},
              }

        tool_options = {'family':info['family'],
                        'flags': ['--64bit'],
                        'quartus': {'flags': ['--64bit']}
                        }

        edam = {
          'files'        : files,
          'name'         : top_name,
          'parameters'   : parameters,
          'toplevel'     : top_name,
          'tool_options' : tool_options
        }        
        
        backend = edatool.get_edatool(tool)(edam=edam, work_root=projectDir, verbose=True)
        
        print('Configure Edalize')
        backend.configure()
        
        print('Build Edalize')
        backend.build()
    
    def download(self, projectDir):
        tool='quartus'
        top_name = self.name
        
        files=[]
        parameters={
              'cable': {'datatype': 'string', 'paramtype': 'generic', 'default':'USB-Blaster'},
              'board_device_index': {'datatype': 'string', 'paramtype': 'generic', 'default':'1'},
              }

        edam = {
          'files'        : files,
          'name'         : top_name,
          'parameters'   : parameters,
          'toplevel'     : top_name,
        }        

        backend = edatool.get_edatool(tool)(edam=edam, work_root=projectDir, verbose=True)

        print('Download bitstream')
        backend.run()

    def getInputKey(self):
        key = self.wire('user_pb', 4)
        self.addIn('user_pb', key)
        keyn = self.wire('user_pbn', 4)
        py4hw.Not(self, 'user_pbn', key, keyn)
        return keyn
        
    def getOutputLED(self):
        led = self.wire('user_led', 4)
        ledn = self.wire('user_ledn', 4)
        
        py4hw.Not(self, 'user_ledn', ledn, led)
        self.addOut('user_led', led)
        return ledn
    
    def getGPIO(self, connector:int):
        assert(False)
        from py4hw.external.altera.ip.cycloneiii import cycloneiii_io_buf
        name = f'GPIO{connector}_D'
        #wbidirs = self.wires(name + '_bidir', 32, 1)
        
        wbidirs = []
        
        for i in range(32):
            wbidirs.append( py4hw.FakeWire(f'{name}[{i}]'))
        
        self.addInOut(name, self.wire(name, 32))
        
        win = self.wire(name + '_in', 32) # out
        wout = self.wire(name + '_out', 32) # in
        woe = self.wire(name + '_oe', 32) # in
        
        wins = self.wires(name + '_in', 32, 1)
        wouts = self.wires(name + '_out', 32, 1)
        woes = self.wires(name + '_oe', 32, 1)
        
        for i in range(32):
            cycloneiii_io_buf(self, f'{name}_{i}', wins[i], wouts[i], woes[i], wbidirs[i])
        
        
        
        #py4hw.BitsLSBF(self, 'wins', win, wins)
        #py4hw.ConcatenateLSBF(self, 'wouts', wouts, wout)
        #py4hw.ConcatenateLSBF(self, 'woes', woes, woe)
        
        return [wins, wouts, woes]
    
    
    def getI2C(self):
        assert(False)
        fpga_i2c_sclk = self.addOut('FPGA_I2C_SCLK', self.wire('FPGA_I2C_SCLK'))
        fpga_i2c_sdat = self.addInOut('FPGA_I2C_SDAT', self.wire('FPGA_I2C_SDAT'))
        
        i2c = I2CInterface(self, 'fpga')
        
        py4hw.Buf(self, 'SCL', i2c.SCL, fpga_i2c_sclk)
        py4hw.BidirBuf(self, 'SDA', i2c.SDA_IN, i2c.SDA_OUT, i2c.SDA_OE, fpga_i2c_sdat)
        
        return i2c
    
    def getUART(self):
        #uart_txd = self.addOut('UART_TXD', self.wire('UART_TXD'))
        #uart_rxd = self.addIn('UART_RXD', self.wire('UART_RXD'))
        # uart_rts = self.addOut('UART_RTS', self.wire('UART_RTS'))
        # uart_cts = self.addIn('UART_CTS', self.wire('UART_CTS'))
        assert(False)
        uart = UARTInterface(self, 'uart')
        
        self.addInterfaceSource('', uart)
        
        return uart


    def getAudio(self):
        assert(False)
        audio = AudioInterface(self, 'audio')
        
        self.addInterfaceSource('', audio)
        
        return audio
    
    def getVGAController(self, vga_clk):
        assert(False)
        '''
        Connections to VGA connector
        

        Returns
        -------
        None.

        '''
        vga_ext = VGAExternalControllerInterface(self, 'DE0_EXT_VGA_CTRL', 4, useDAC=False)
        vga_int = VGAInternalControllerInterface(self, 'DE0_INT_VGA_CTRL')
        
        self.addInterfaceSource('VGA', vga_ext)
        
        py4hw.Range(self, 'R', vga_int.R, 7, 4, vga_ext.R)
        py4hw.Range(self, 'G', vga_int.G, 7, 4, vga_ext.G)
        py4hw.Range(self, 'B', vga_int.B, 7, 4, vga_ext.B)
        
        py4hw.Buf(self, 'HS', vga_int.HS, vga_ext.HS)
        py4hw.Buf(self, 'VS', vga_int.VS, vga_ext.VS)
        
        #py4hw.Buf(self, 'SYNC_N', vga_int.HS, vga_ext.SYNC_N)
        #py4hw.Buf(self, 'BLANK_N', vga_int.VS, vga_ext.BLANK_N)
        #py4hw.Buf(self, 'CLK', vga_clk, vga_ext.CLK)
        
        return vga_int
        
    def getFPGADeviceInfo(self):
        info = {'family':'"Cyclone 10 LP"', 'device':'10CL025YU256I7G',
                # 'package':'FBGA', 'pin_count':'896', 'speed_grade':'6'
                }
        return info
        
    def getPinAssignments(self):
        ##set_location_assignment PIN_C1  -to 'qspi_sdo     
        ##set_location_assignment PIN_D2  -to 'qspi_sce     
        ##set_location_assignment PIN_H1  -to 'qspi_dclk    
        ##set_location_assignment PIN_H2  -to 'qspi_data0   


        pins = {
            'c10_clk50m':'PIN_E1','c10_resetn':'PIN_J15',
            'enet_clk_125m':'PIN_T8','enet_rx_clk':'PIN_B8','enet_rx_dv':'PIN_A5',
            'enet_rx_d[0]':'PIN_A7','enet_rx_d[1]':'PIN_B7','enet_rx_d[2]':'PIN_A6','enet_rx_d[3]':'PIN_B6',
            'enet_tx_clk':'PIN_D3','enet_tx_en':'PIN_D6',
            'enet_tx_d[0]':'PIN_E6','enet_tx_d[1]':'PIN_A3','enet_tx_d[2]':'PIN_B3','enet_tx_d[3]':'PIN_A2',
            'enet_resetn':'PIN_C6','enet_mdc':'PIN_B4','enet_mdio':'PIN_A4','enet_int':'PIN_B5',
            'user_dip[0]':'PIN_M16','user_dip[1]':'PIN_A8','user_dip[2]':'PIN_A9','user_led[0]':'PIN_L14',
            'user_led[1]':'PIN_K15','user_led[2]':'PIN_J14','user_led[3]':'PIN_J13',
            'user_pb[0]':'PIN_E15','user_pb[1]':'PIN_F14','user_pb[2]':'PIN_C11','user_pb[3]':'PIN_D9',
            'arduino_io[0]':'PIN_B1','arduino_io[1]':'PIN_C2','arduino_io[2]':'PIN_F3','arduino_io[3]':'PIN_D1',
            'arduino_io[4]':'PIN_G2','arduino_io[5]':'PIN_G1','arduino_io[6]':'PIN_J2','arduino_io[7]':'PIN_J1',
            'arduino_io[8]':'PIN_K2','arduino_io[9]':'PIN_K5','arduino_io[10]':'PIN_L4','arduino_io[11]':'PIN_K1',
            'arduino_io[12]':'PIN_L2','arduino_io[13]':'PIN_L1','arduino_rstn':'PIN_L3','arduino_adc_sda':'PIN_C8',
            'arduino_adc_scl':'PIN_D8','arduino_scl':'PIN_N1','arduino_sda':'PIN_N2',
            'hbus_clk_50m':'PIN_M15','hbus_intn':'PIN_P11','hbus_rston':'PIN_T15',
            'hbus_dq[0]':'PIN_T12','hbus_dq[1]':'PIN_T13','hbus_dq[2]':'PIN_T11','hbus_dq[3]':'PIN_R10',
            'hbus_dq[4]':'PIN_T10','hbus_dq[5]':'PIN_R11','hbus_dq[6]':'PIN_R12','hbus_dq[7]':'PIN_R13',
            'hbus_cs2n':'PIN_P9','hbus_cs1n':'PIN_N12','hbus_rstn':'PIN_N9','hbus_rwds':'PIN_T14',
            'hbus_clk0p':'PIN_P14','hbus_clk0n':'PIN_R14',
            'c10_clk_adj':'PIN_E16',
            'c10_m10_io[0]':'PIN_E8','c10_m10_io[1]':'PIN_E7','c10_m10_io[2]':'PIN_F8','c10_m10_io[3]':'PIN_C3',
            'pmod_d[0]':'PIN_D16','pmod_d[1]':'PIN_F13','pmod_d[2]':'PIN_D15','pmod_d[3]':'PIN_F16',
            'pmod_d[4]':'PIN_C16','pmod_d[5]':'PIN_F15','pmod_d[6]':'PIN_C15','pmod_d[7]':'PIN_B16',
            'usb_data[0]':'PIN_A15','usb_data[1]':'PIN_B14','usb_data[2]':'PIN_A14','usb_data[3]':'PIN_B13',
            'usb_data[4]':'PIN_A13','usb_data[5]':'PIN_B12','usb_data[6]':'PIN_A12','usb_data[7]':'PIN_B10',
            'usb_addr[0]':'PIN_A10','usb_addr[1]':'PIN_A11',
            'usb_full':'PIN_D12','usb_empty':'PIN_D14',
            'usb_scl':'PIN_C14','usb_sda':'PIN_E9',
            'usb_oe_n':'PIN_F9','usb_rd_n':'PIN_D11','usb_wr_n':'PIN_B11',
            'usb_reset_n':'PIN_C9','c10_usb_clk':'PIN_B9',
            'gpio[0]':'PIN_L13','gpio[1]':'PIN_L16','gpio[2]':'PIN_L15','gpio[3]':'PIN_K16',
            'gpio[4]':'PIN_P16','gpio[5]':'PIN_R16','gpio[6]':'PIN_N16','gpio[7]':'PIN_N15',
            'gpio[8]':'PIN_N14','gpio[9]':'PIN_P15','gpio[10]':'PIN_N8','gpio[11]':'PIN_P8',
            'gpio[12]':'PIN_M8','gpio[13]':'PIN_L8','gpio[14]':'PIN_R7','gpio[15]':'PIN_T7',
            'gpio[16]':'PIN_L7','gpio[17]':'PIN_M7','gpio[18]':'PIN_R6','gpio[19]':'PIN_T6',
            'gpio[20]':'PIN_T2','gpio[21]':'PIN_M6','gpio[22]':'PIN_R5','gpio[23]':'PIN_T5',
            'gpio[24]':'PIN_N5','gpio[25]':'PIN_N6','gpio[26]':'PIN_R4','gpio[27]':'PIN_T4',
            'gpio[28]':'PIN_N3','gpio[29]':'PIN_P3','gpio[30]':'PIN_R3','gpio[31]':'PIN_T3',
            'gpio[32]':'PIN_P6','gpio[33]':'PIN_P2','gpio[34]':'PIN_P1','gpio[35]':'PIN_R1',                
            }
        return pins
        
    def getQsf(self):
        info = self.getFPGADeviceInfo()
        qsf = '# build by py4hw\n'
        qsf += 'set_global_assignment -name FAMILY {}\n'.format(info['family'])
        qsf += 'set_global_assignment -name DEVICE {}\n'.format(info['device'])
        # qsf += 'set_global_assignment -name DEVICE_FILTER_PACKAGE {}\n'.format(info['package'])
        # qsf += 'set_global_assignment -name DEVICE_FILTER_PIN_COUNT {}\n'.format(info['pin_count'])
        # qsf += 'set_global_assignment -name DEVICE_FILTER_SPEED_GRADE {}\n'.format(info['speed_grade'])

        pins = self.getPinAssignments()
        
        for key in pins.keys():
            qsf += 'set_location_assignment {} -to {}\n'.format(pins[key], key)

        # by default all are 3.3 LVTTL
        lvpins = ['hbus_intn','hbus_rston','hbus_dq[0]','hbus_dq[1]',
                  'hbus_dq[2]','hbus_dq[3]','hbus_dq[4]','hbus_dq[5]',
                  'hbus_dq[6]','hbus_dq[7]','hbus_cs2n','hbus_cs1n',
                  'hbus_rstn','hbus_rwds','hbus_clk0p','hbus_clk0n']

        for key in pins.keys():
            if key in lvpins:
                qsf += 'set_instance_assignment -name IO_STANDARD "1.8 V" -to {}\n'.format(key)
            else:
                qsf += 'set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to {}\n'.format(key)

        qsf += 'set_global_assignment -name ENABLE_OCT_DONE OFF'
        qsf += 'set_global_assignment -name ENABLE_CONFIGURATION_PINS OFF'
        qsf += 'set_global_assignment -name ENABLE_BOOT_SEL_PIN OFF'
        qsf += 'set_global_assignment -name STRATIXV_CONFIGURATION_SCHEME "PASSIVE SERIAL"'
        qsf += 'set_global_assignment -name USE_CONFIGURATION_DEVICE OFF'
        qsf += 'set_global_assignment -name CRC_ERROR_OPEN_DRAIN OFF'
        qsf += 'set_global_assignment -name CYCLONEII_RESERVE_NCEO_AFTER_CONFIGURATION "USE AS REGULAR IO"\n'
        
        return qsf
