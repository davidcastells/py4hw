# -*- coding: utf-8 -*-
"""
Created on Sat Sep 30 09:01:29 2023

@author: dcr
"""



import py4hw
from edalize import edatool
import os

class VGAExternalControllerInterface(py4hw.Interface):
    def __init__(self, parent, name:str, w=8, useDAC=True):
        super().__init__(parent, name)
        
        self.R = self.addSourceToSink('R', w)
        self.G = self.addSourceToSink('G', w)
        self.B = self.addSourceToSink('B', w)
        
        if (useDAC):
            self.CLK = self.addSourceToSink('CLK', 1)
            self.SYNC_N = self.addSourceToSink('SYNC_N', 1)
            self.BLANK_N = self.addSourceToSink('BLANK_N', 1)

        self.VS = self.addSourceToSink('VS', 1)
        self.HS = self.addSourceToSink('HS', 1)
        
class VGAInternalControllerInterface(py4hw.Interface):
    def __init__(self, parent, name:str):
        super().__init__(parent, name)
        
        self.R = self.addSourceToSink('R', 8)
        self.G = self.addSourceToSink('G', 8)
        self.B = self.addSourceToSink('B', 8)
        
        self.VS = self.addSourceToSink('VS', 1)
        self.HS = self.addSourceToSink('HS', 1)
        
class I2CInterface(py4hw.Interface):
    def __init__(self, parent, name:str):
        super().__init__(parent, name)
        
        self.SCL = self.addSourceToSink('SCL', 1)
        self.SDA_OUT = self.addSourceToSink('SDA_OUT', 1)
        self.SDA_OE = self.addSourceToSink('SDA_OE', 1)
        self.SDA_IN = self.addSinkToSource('SDA_IN', 1)

class UARTInterface(py4hw.Interface):
    def __init__(self, parent, name:str):
        super().__init__(parent, name)
        
        self.tx = self.addSourceToSink('UART_TXD', 1)
        self.rx = self.addSinkToSource('UART_RXD', 1)
        self.rts = self.addSourceToSink('UART_RTS', 1)
        self.cts = self.addSinkToSource('UART_CTS', 1)


class AudioInterface(py4hw.Interface):
    def __init__(self, parent, name:str):
        super().__init__(parent, name)
        
        self.AUD_ADCLRCK = self.addSourceToSink('AUD_ADCLRCK', 1)
        self.AUD_ADCDAT =  self.addSinkToSource('AUD_ADCDAT', 1)
        self.AUD_DACLRCK = self.addSourceToSink('AUD_DACLRCK', 1)
        self.AUD_DACDAT = self.addSourceToSink('AUD_DACDAT', 1)
        self.AUD_XCK = self.addSourceToSink('AUD_XCK', 1)
        self.AUD_BCLK = self.addSourceToSink('AUD_BCLK', 1)

    
class DE0(py4hw.HWSystem):
    
    def __init__(self):
        
        super().__init__(name='DE0')
        
        clk50 = self.wire('CLOCK_50')
        #clk50 = self.addIn('CLOCK_50', clk50)
        clockDriver = py4hw.ClockDriver('CLOCK_50', 50E6, 0, wire=clk50)
        
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
            file.write('create_clock  -period 20 [get_ports CLOCK_50]\n')
            
        tool = 'quartus'
        
        files = [  {'name' : verilog_file, 'file_type' : 'verilogSource'},
                 {'name' : sdc_file, 'file_type' : 'SDC'},
                 {'name' : qsf_file, 'file_type' : 'tclSource'}
                 ]

        info = self.getFPGADeviceInfo()

        parameters = {'clk_freq_hz' : {'datatype' : 'int', 'default' : 50000000, 'paramtype' : 'vlogparam'},
              'vcd' : {'datatype' : 'bool', 'paramtype' : 'plusarg'},
              'family': {'datatype': 'string', 'paramtype': 'generic', 'default':'Cyclone III'},
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
        key = self.wire('BUTTON', 3)
        self.addIn('BUTTON', key)
        keyn = self.wire('BUTTONn', 3)
        py4hw.Not(self, 'BUTTONn', key, keyn)
        return keyn
        
    def getOutputHex(self, i):
        assert(i >= 0 and i <= 5)
        name = 'HEX{}_D'.format(i)
        namen = 'HEXn{}'.format(i)
        p = self.wire(name, 7)
        pn = self.wire(namen, 7)
        
        py4hw.Not(self, namen, pn, p)
        self.addOut(name, p)
        return pn
    
    def getGPIO(self, connector:int):
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
        
        uart = UARTInterface(self, 'uart')
        
        self.addInterfaceSource('', uart)
        
        return uart


    def getAudio(self):
        
        audio = AudioInterface(self, 'audio')
        
        self.addInterfaceSource('', audio)
        
        return audio
    
    def getVGAController(self, vga_clk):
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
        info = {'family':'"Cyclone III"', 'device':'EP3C16F484C6',
                # 'package':'FBGA', 'pin_count':'896', 'speed_grade':'6'
                }
        return info
        
    def getPinAssignments(self):
        pins = {'LEDG[9]':'PIN_B1', 'LEDG[8]':'PIN_B2', 'LEDG[7]':'PIN_C2', 'LEDG[6]':'PIN_C1', 'LEDG[5]':'PIN_E1', 
                'LEDG[4]':'PIN_F2', 'LEDG[3]':'PIN_H1', 'LEDG[2]':'PIN_J3', 'LEDG[1]':'PIN_J2', 'LEDG[0]':'PIN_J1', 
                'SW[9]':'PIN_D2', 'SW[8]':'PIN_E4', 'SW[7]':'PIN_E3', 'SW[6]':'PIN_H7', 'SW[5]':'PIN_J7', 
                'SW[4]':'PIN_G5', 'SW[3]':'PIN_G4', 'SW[2]':'PIN_H6', 'SW[1]':'PIN_H5', 'SW[0]':'PIN_J6', 
                'BUTTON[2]':'PIN_F1', 'BUTTON[1]':'PIN_G3', 'BUTTON[0]':'PIN_H2',
                'FL_ADDR[21]':'PIN_R2', 'FL_ADDR[20]':'PIN_P3', 'FL_ADDR[19]':'PIN_P1', 'FL_ADDR[18]':'PIN_M6', 'FL_ADDR[17]':'PIN_M5',
                'FL_ADDR[16]':'PIN_AA2', 'FL_ADDR[15]':'PIN_L6', 'FL_ADDR[14]':'PIN_L7', 'FL_ADDR[13]':'PIN_M1', 'FL_ADDR[12]':'PIN_M2',
                'FL_ADDR[11]':'PIN_M3', 'FL_ADDR[10]':'PIN_N1', 'FL_ADDR[9]':'PIN_N2', 'FL_ADDR[8]':'PIN_P2', 'FL_ADDR[7]':'PIN_M4',
                'FL_ADDR[6]':'PIN_M8', 'FL_ADDR[5]':'PIN_N6', 'FL_ADDR[4]':'PIN_N5', 'FL_ADDR[3]':'PIN_N7', 'FL_ADDR[2]':'PIN_P6',
                'FL_ADDR[1]':'PIN_P5', 'FL_ADDR[0]':'PIN_P7', 'FL_BYTE_N':'PIN_AA1', 'FL_CE_N':'PIN_N8', 
                'FL_DQ[0]':'PIN_R7', 'FL_DQ[1]':'PIN_P8', 'FL_DQ[2]':'PIN_R8', 'FL_DQ[3]':'PIN_U1', 'FL_DQ[4]':'PIN_V2',
                'FL_DQ[5]':'PIN_V3', 'FL_DQ[6]':'PIN_W1', 'FL_DQ[7]':'PIN_Y1', 'FL_DQ[8]':'PIN_T5', 'FL_DQ[9]':'PIN_T7',
                'FL_DQ[10]':'PIN_T4', 'FL_DQ[11]':'PIN_U2', 'FL_DQ[12]':'PIN_V1', 'FL_DQ[13]':'PIN_V4', 'FL_DQ[14]':'PIN_W2', 
                'FL_OE_N':'PIN_R6', 'FL_RST_N':'PIN_R1', 'FL_RY':'PIN_M7', 'FL_WE_N':'PIN_P4', 'FL_WP_N':'PIN_T3', 'FL_DQ15_AM1':'PIN_Y2',
                'GPIO0_D[31]':'PIN_U7', 'GPIO0_D[30]':'PIN_V5', 'GPIO0_D[29]':'PIN_W6', 'GPIO0_D[28]':'PIN_W7',
                'GPIO0_D[27]':'PIN_V8', 'GPIO0_D[26]':'PIN_T8', 'GPIO0_D[25]':'PIN_W10', 'GPIO0_D[24]':'PIN_Y10',
                'GPIO0_D[23]':'PIN_V11', 'GPIO0_D[22]':'PIN_R10', 'GPIO0_D[21]':'PIN_V12', 'GPIO0_D[20]':'PIN_U13',
                'GPIO0_D[19]':'PIN_W13', 'GPIO0_D[18]':'PIN_Y13', 'GPIO0_D[17]':'PIN_U14', 'GPIO0_D[16]':'PIN_V14',
                'GPIO0_D[15]':'PIN_AA4', 'GPIO0_D[14]':'PIN_AB4', 'GPIO0_D[13]':'PIN_AA5', 'GPIO0_D[12]':'PIN_AB5',
                'GPIO0_D[11]':'PIN_AA8', 'GPIO0_D[10]':'PIN_AB8', 'GPIO0_D[9]':'PIN_AA10', 'GPIO0_D[8]':'PIN_AB10',
                'GPIO0_D[7]':'PIN_AA13', 'GPIO0_D[6]':'PIN_AB13', 'GPIO0_D[5]':'PIN_AB14', 'GPIO0_D[4]':'PIN_AA14',
                'GPIO0_D[3]':'PIN_AB15', 'GPIO0_D[2]':'PIN_AA15', 'GPIO0_D[1]':'PIN_AA16', 'GPIO0_D[0]':'PIN_AB16',
                'GPIO0_CLKIN[0]':'PIN_AB12', 'GPIO0_CLKIN[1]':'PIN_AA12', 'GPIO0_CLKOUT[0]':'PIN_AB3', 'GPIO0_CLKOUT[1]':'PIN_AA3',
                'GPIO1_CLKIN[1]':'PIN_AA11', 'GPIO1_CLKIN[0]':'PIN_AB11', 'GPIO1_CLKOUT[1]':'PIN_T16', 'GPIO1_CLKOUT[0]':'PIN_R16',
                'GPIO1_D[31]':'PIN_V7', 'GPIO1_D[30]':'PIN_V6', 'GPIO1_D[29]':'PIN_U8', 'GPIO1_D[28]':'PIN_Y7',
                'GPIO1_D[27]':'PIN_T9', 'GPIO1_D[26]':'PIN_U9', 'GPIO1_D[25]':'PIN_T10', 'GPIO1_D[24]':'PIN_U10',
                'GPIO1_D[23]':'PIN_R12', 'GPIO1_D[22]':'PIN_R11', 'GPIO1_D[21]':'PIN_T12', 'GPIO1_D[20]':'PIN_U12',
                'GPIO1_D[19]':'PIN_R14', 'GPIO1_D[18]':'PIN_T14', 'GPIO1_D[17]':'PIN_AB7', 'GPIO1_D[16]':'PIN_AA7',
                'GPIO1_D[15]':'PIN_AA9', 'GPIO1_D[14]':'PIN_AB9', 'GPIO1_D[13]':'PIN_V15', 'GPIO1_D[12]':'PIN_W15', 
                'GPIO1_D[11]':'PIN_T15', 'GPIO1_D[10]':'PIN_U15', 'GPIO1_D[9]':'PIN_W17', 'GPIO1_D[8]':'PIN_Y17',
                'GPIO1_D[7]':'PIN_AB17', 'GPIO1_D[6]':'PIN_AA17', 'GPIO1_D[5]':'PIN_AA18', 'GPIO1_D[4]':'PIN_AB18',
                'GPIO1_D[3]':'PIN_AB19', 'GPIO1_D[2]':'PIN_AA19', 'GPIO1_D[1]':'PIN_AB20', 'GPIO1_D[0]':'PIN_AA20',
                'PS2_KBCLK':'PIN_P22', 'PS2_KBDAT':'PIN_P21', 'PS2_MSCLK':'PIN_R21', 'PS2_MSDAT':'PIN_R22',
                'UART_RXD':'PIN_U22', 'UART_TXD':'PIN_U21', 'UART_RTS':'PIN_V22', 'UART_CTS':'PIN_V21',
                'SD_CLK':'PIN_Y21', 'SD_CMD':'PIN_Y22', 'SD_DAT0':'PIN_AA22', 'SD_DAT3':'PIN_W21', 'SD_WP_N':'PIN_W20',
                'LCD_DATA[7]':'PIN_C20', 'LCD_DATA[6]':'PIN_D20', 'LCD_DATA[5]':'PIN_B21', 'LCD_DATA[4]':'PIN_B22',
                'LCD_DATA[3]':'PIN_C21', 'LCD_DATA[2]':'PIN_C22', 'LCD_DATA[1]':'PIN_D21', 'LCD_DATA[0]':'PIN_D22',
                'LCD_RW':'PIN_E22', 'LCD_RS':'PIN_F22', 'LCD_EN':'PIN_E21', 'LCD_BLON':'PIN_F21',
                'VGA_G[3]':'PIN_J21', 'VGA_G[2]':'PIN_K17', 'VGA_G[1]':'PIN_J17', 'VGA_G[0]':'PIN_H22', 
                'VGA_HS':'PIN_L21', 'VGA_VS':'PIN_L22',
                'VGA_R[3]':'PIN_H21', 'VGA_R[2]':'PIN_H20', 'VGA_R[1]':'PIN_H17', 'VGA_R[0]':'PIN_H19',
                'VGA_B[3]':'PIN_K18', 'VGA_B[2]':'PIN_J22', 'VGA_B[1]':'PIN_K21', 'VGA_B[0]':'PIN_K22',
                'CLOCK_50':'PIN_G21',
                'HEX0_D[0]':'PIN_E11', 'HEX0_D[1]':'PIN_F11', 'HEX0_D[2]':'PIN_H12', 'HEX0_D[3]':'PIN_H13', 
                'HEX0_D[4]':'PIN_G12', 'HEX0_D[5]':'PIN_F12', 'HEX0_D[6]':'PIN_F13', 'HEX0_DP':'PIN_D13',
                'HEX1_D[6]':'PIN_A15', 'HEX1_D[5]':'PIN_E14', 'HEX1_D[4]':'PIN_B14', 'HEX1_D[3]':'PIN_A14',
                'HEX1_D[2]':'PIN_C13', 'HEX1_D[1]':'PIN_B13', 'HEX1_D[0]':'PIN_A13', 'HEX1_DP':'PIN_B15',
                'HEX2_D[6]':'PIN_F14', 'HEX2_D[5]':'PIN_B17', 'HEX2_D[4]':'PIN_A17', 'HEX2_D[3]':'PIN_E15',
                'HEX2_D[2]':'PIN_B16', 'HEX2_D[1]':'PIN_A16', 'HEX2_D[0]':'PIN_D15', 'HEX2_DP':'PIN_A18',
                'HEX3_D[6]':'PIN_G15', 'HEX3_D[5]':'PIN_D19', 'HEX3_D[4]':'PIN_C19', 'HEX3_D[3]':'PIN_B19',
                'HEX3_D[2]':'PIN_A19', 'HEX3_D[1]':'PIN_F15', 'HEX3_D[0]':'PIN_B18', 'HEX3_DP':'PIN_G16',   
                'DRAM_CAS_N':'PIN_G8', 'DRAM_CS_N':'PIN_G7', 'DRAM_CLK':'PIN_E5', 'DRAM_CKE':'PIN_E6',
                'DRAM_BA_0':'PIN_B5', 'DRAM_BA_1':'PIN_A4', 'DRAM_DQ[15]':'PIN_F10', 'DRAM_DQ[14]':'PIN_E10',
                'DRAM_DQ[13]':'PIN_A10', 'DRAM_DQ[12]':'PIN_B10', 'DRAM_DQ[11]':'PIN_C10', 'DRAM_DQ[10]':'PIN_A9',
                'DRAM_DQ[9]':'PIN_B9', 'DRAM_DQ[8]':'PIN_A8', 'DRAM_DQ[7]':'PIN_F8', 'DRAM_DQ[6]':'PIN_H9',
                'DRAM_DQ[5]':'PIN_G9', 'DRAM_DQ[4]':'PIN_F9', 'DRAM_DQ[3]':'PIN_E9', 'DRAM_DQ[2]':'PIN_H10',
                'DRAM_DQ[1]':'PIN_G10', 'DRAM_DQ[0]':'PIN_D10', 'DRAM_LDQM':'PIN_E7', 'DRAM_UDQM':'PIN_B8',
                'DRAM_RAS_N':'PIN_F7', 'DRAM_WE_N':'PIN_D6', 'CLOCK_50_2':'PIN_B12', 'DRAM_ADDR[12]':'PIN_C8',
                'DRAM_ADDR[11]':'PIN_A7', 'DRAM_ADDR[10]':'PIN_B4', 'DRAM_ADDR[9]':'PIN_B7', 'DRAM_ADDR[8]':'PIN_C7',
                'DRAM_ADDR[7]':'PIN_A6', 'DRAM_ADDR[6]':'PIN_B6', 'DRAM_ADDR[5]':'PIN_C6', 'DRAM_ADDR[4]':'PIN_A5',
                'DRAM_ADDR[3]':'PIN_C3', 'DRAM_ADDR[2]':'PIN_B3', 'DRAM_ADDR[1]':'PIN_A3', 'DRAM_ADDR[0]':'PIN_C4',
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
        for key in pins.keys():
            qsf += 'set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to {}\n'.format(key)
            
        qsf += 'set_global_assignment -name CYCLONEII_RESERVE_NCEO_AFTER_CONFIGURATION "USE AS REGULAR IO"\n'

        
        return qsf
        

    
class DE1SoC(py4hw.HWSystem):
    
    def __init__(self):
        
        super().__init__(name='DE1SoC')
        
        self.clk_freq = 50E6
        clk50 = self.wire('CLOCK_50')
        #clk50 = self.addIn('CLOCK_50', clk50)
        clockDriver = py4hw.ClockDriver('CLOCK_50', self.clk_freq , 0, wire=clk50)
        
        print('Initial', self.getFullPath(),  self._wires)
        
        self.clockDriver = clockDriver
        
    
    def setTargetClkFreq(self, freq):
        self.clk_freq = freq
    
    def build(self,  projectDir):
        if not(os.path.exists(projectDir)):
            print('Creating the directory', projectDir)
            os.makedirs(projectDir)
            
        rtl = py4hw.VerilogGenerator(self)
        
        rtl_code = rtl.getVerilogForHierarchy(noInstanceNumberInTopEntity=True)
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
            period_in_ns = 1E9 / self.clk_freq
            file.write('create_clock  -period {} [get_ports CLOCK_50]\n'.format(period_in_ns))
            
        tool = 'quartus'
        
        files = [  {'name' : verilog_file, 'file_type' : 'verilogSource'},
                 {'name' : sdc_file, 'file_type' : 'SDC'},
                 {'name' : qsf_file, 'file_type' : 'tclSource'}
                 ]

        parameters = {'clk_freq_hz' : {'datatype' : 'int', 'default' : int(self.clk_freq), 'paramtype' : 'vlogparam'},
              'vcd' : {'datatype' : 'bool', 'paramtype' : 'plusarg'},
              'family': {'datatype': 'string', 'paramtype': 'generic', 'default':'Cyclone V'},
              'device': {'datatype': 'string', 'paramtype': 'generic', 'default':'5CSEMA5F31C6'},
              }

        tool_options = {'family':'Cyclone V'}

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
              'cable': {'datatype': 'string', 'paramtype': 'generic', 'default':'DE-SoC'},
              'board_device_index': {'datatype': 'string', 'paramtype': 'generic', 'default':'2'},
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
        key = self.wire('KEY', 4)
        self.addIn('KEY', key)
        keyn = self.wire('KEYn', 4)
        py4hw.Not(self, 'KEYn', key, keyn)
        return keyn
        
    def getOutputHex(self, i):
        assert(i >= 0 and i <= 5)
        name = 'HEX{}'.format(i)
        namen = 'HEXn{}'.format(i)
        p = self.wire(name, 7)
        pn = self.wire(namen, 7)
        
        py4hw.Not(self, namen, pn, p)
        self.addOut(name, p)
        return pn
    
    def getI2C(self):
        #set_location_assignment PIN_J12 -to FPGA_I2C_SCLK
        #set_location_assignment PIN_K12 -to FPGA_I2C_SDAT
        fpga_i2c_sclk = self.addOut('FPGA_I2C_SCLK', self.wire('FPGA_I2C_SCLK'))
        fpga_i2c_sdat = self.addInOut('FPGA_I2C_SDAT', self.wire('FPGA_I2C_SDAT'))
        
        i2c = I2CInterface(self, 'fpga')
        
        py4hw.Buf(self, 'SCL', i2c.SCL, fpga_i2c_sclk)
        py4hw.BidirBuf(self, 'SDA', i2c.SDA_IN, i2c.SDA_OUT, i2c.SDA_OE, fpga_i2c_sdat)
        
        return i2c
    
    def getAudio(self):
        
        audio = AudioInterface(self, 'audio')
        
        self.addInterfaceSource('', audio)
        
        return audio
    
    def getVGAController(self, vga_clk):
        '''
        Connections to the ADV7123
        

        Returns
        -------
        None.

        '''
        vga_ext = VGAExternalControllerInterface(self, 'DE1SoC_EXT_VGA_CTRL')
        vga_int = VGAInternalControllerInterface(self, 'DE1SoC_INT_VGA_CTRL')
        
        self.addInterfaceSource('VGA', vga_ext)
        
        py4hw.Buf(self, 'R', vga_int.R, vga_ext.R)
        py4hw.Buf(self, 'G', vga_int.G, vga_ext.G)
        py4hw.Buf(self, 'B', vga_int.B, vga_ext.B)
        
        py4hw.Buf(self, 'HS', vga_int.HS, vga_ext.HS)
        py4hw.Buf(self, 'VS', vga_int.VS, vga_ext.VS)
        
        py4hw.Buf(self, 'SYNC_N', vga_int.HS, vga_ext.SYNC_N)
        py4hw.Buf(self, 'BLANK_N', vga_int.VS, vga_ext.BLANK_N)
        
        py4hw.Buf(self, 'CLK', vga_clk, vga_ext.CLK)
        
        return vga_int
        
    def getFPGADeviceInfo(self):
        info = {'family':'"Cyclone V"', 'device':'5CSEMA5F31C6', 'package':'FBGA', 'pin_count':'896', 'speed_grade':'6'}
        return info
        
    def getPinAssignments(self):
        pins = {'ADC_CONVST':'PIN_AJ4', 'ADC_DIN':'PIN_AK4', 'ADC_DOUT':'PIN_AK3', 'ADC_SCLK':'PIN_AK2',
                'AUD_ADCDAT':'PIN_K7', 'AUD_ADCLRCK':'PIN_K8', 'AUD_BCLK':'PIN_H7', 'AUD_DACDAT':'PIN_J7', 'AUD_DACLRCK':'PIN_H8', 'AUD_XCK':'PIN_G7',
                'CLOCK2_50':'PIN_AA16', 'CLOCK3_50':'PIN_Y26', 'CLOCK4_50':'PIN_K14', 'CLOCK_50':'PIN_AF14',
                'DRAM_ADDR[0]':'PIN_AK14', 'DRAM_ADDR[1]':'PIN_AH14', 'DRAM_ADDR[2]':'PIN_AG15', 'DRAM_ADDR[3]':'PIN_AE14',
                'DRAM_ADDR[4]':'PIN_AB15', 'DRAM_ADDR[5]':'PIN_AC14', 'DRAM_ADDR[6]':'PIN_AD14', 'DRAM_ADDR[7]':'PIN_AF15',
                'DRAM_ADDR[8]':'PIN_AH15', 'DRAM_ADDR[9]':'PIN_AG13', 'DRAM_ADDR[10]':'PIN_AG12', 'DRAM_ADDR[11]':'PIN_AH13',
                'DRAM_ADDR[12]':'PIN_AJ14', 'DRAM_BA[0]':'PIN_AF13', 'DRAM_BA[1]':'PIN_AJ12', 'DRAM_CAS_N':'PIN_AF11',
                'DRAM_CKE':'PIN_AK13', 'DRAM_CLK':'PIN_AH12', 'DRAM_CS_N':'PIN_AG11',
                'DRAM_DQ[0]':'PIN_AK6', 'DRAM_DQ[1]':'PIN_AJ7', 'DRAM_DQ[2]':'PIN_AK7', 'DRAM_DQ[3]':'PIN_AK8', 
                'DRAM_DQ[4]':'PIN_AK9', 'DRAM_DQ[5]':'PIN_AG10', 'DRAM_DQ[6]':'PIN_AK11', 'DRAM_DQ[7]':'PIN_AJ11',
                'DRAM_DQ[8]':'PIN_AH10', 'DRAM_DQ[9]':'PIN_AJ10', 'DRAM_DQ[10]':'PIN_AJ9', 'DRAM_DQ[11]':'PIN_AH9',
                'DRAM_DQ[12]':'PIN_AH8', 'DRAM_DQ[13]':'PIN_AH7', 'DRAM_DQ[14]':'PIN_AJ6', 'DRAM_DQ[15]':'PIN_AJ5',
                'DRAM_LDQM':'PIN_AB13', 'DRAM_RAS_N':'PIN_AE13', 'DRAM_UDQM':'PIN_AK12', 'DRAM_WE_N':'PIN_AA13',
                'FPGA_I2C_SCLK':'PIN_J12', 'FPGA_I2C_SDAT':'PIN_K12',
                'HEX0[0]':'PIN_AE26', 'HEX0[1]':'PIN_AE27', 'HEX0[2]':'PIN_AE28', 'HEX0[3]':'PIN_AG27', 'HEX0[4]':'PIN_AF28', 
                'HEX0[5]':'PIN_AG28', 'HEX0[6]':'PIN_AH28',
                'HEX1[0]':'PIN_AJ29', 'HEX1[1]':'PIN_AH29', 'HEX1[2]':'PIN_AH30', 'HEX1[3]':'PIN_AG30', 'HEX1[4]':'PIN_AF29', 
                'HEX1[5]':'PIN_AF30', 'HEX1[6]':'PIN_AD27', 
                'HEX2[0]':'PIN_AB23', 'HEX2[1]':'PIN_AE29', 'HEX2[2]':'PIN_AD29', 'HEX2[3]':'PIN_AC28', 'HEX2[4]':'PIN_AD30', 
                'HEX2[5]':'PIN_AC29', 'HEX2[6]':'PIN_AC30', 
                'HEX3[0]':'PIN_AD26', 'HEX3[1]':'PIN_AC27', 'HEX3[2]':'PIN_AD25', 'HEX3[3]':'PIN_AC25', 'HEX3[4]':'PIN_AB28', 
                'HEX3[5]':'PIN_AB25', 'HEX3[6]':'PIN_AB22', 
                'HEX4[0]':'PIN_AA24', 'HEX4[1]':'PIN_Y23', 'HEX4[2]':'PIN_Y24', 'HEX4[3]':'PIN_W22', 'HEX4[4]':'PIN_W24', 
                'HEX4[5]':'PIN_V23', 'HEX4[6]':'PIN_W25', 
                'HEX5[0]':'PIN_V25', 'HEX5[1]':'PIN_AA28', 'HEX5[2]':'PIN_Y27', 'HEX5[3]':'PIN_AB27', 'HEX5[4]':'PIN_AB26',
                'HEX5[5]':'PIN_AA26', 'HEX5[6]':'PIN_AA25',
                'IRDA_RXD':'PIN_AA30', 'IRDA_TXD':'PIN_AB30',
                'KEY[0]':'PIN_AA14', 'KEY[1]':'PIN_AA15', 'KEY[2]':'PIN_W15', 'KEY[3]':'PIN_Y16',
                'LEDR[0]':'PIN_V16', 'LEDR[1]':'PIN_W16', 'LEDR[2]':'PIN_V17', 'LEDR[3]':'PIN_V18', 'LEDR[4]':'PIN_W17', 
                'LEDR[5]':'PIN_W19', 'LEDR[6]':'PIN_Y19', 'LEDR[7]':'PIN_W20', 'LEDR[8]':'PIN_W21', 'LEDR[9]':'PIN_Y21',
                'PS2_CLK':'PIN_AD7', 'PS2_CLK2':'PIN_AD9', 'PS2_DAT':'PIN_AE7', 'PS2_DAT2':'PIN_AE9',
                'SW[0]':'PIN_AB12', 'SW[1]':'PIN_AC12', 'SW[2]':'PIN_AF9', 'SW[3]':'PIN_AF10', 'SW[4]':'PIN_AD11', 
                'SW[5]':'PIN_AD12', 'SW[6]':'PIN_AE11', 'SW[7]':'PIN_AC9', 'SW[8]':'PIN_AD10', 'SW[9]':'PIN_AE12', 
                'TD_CLK27':'PIN_H15', 'TD_DATA[0]':'PIN_D2', 'TD_DATA[1]':'PIN_B1', 'TD_DATA[2]':'PIN_E2', 'TD_DATA[3]':'PIN_B2', 
                'TD_DATA[4]':'PIN_D1', 'TD_DATA[5]':'PIN_E1', 'TD_DATA[6]':'PIN_C2', 'TD_DATA[7]':'PIN_B3', 'TD_HS':'PIN_A5', 
                'TD_RESET_N':'PIN_F6', 'TD_VS':'PIN_A3',
                'VGA_BLANK_N':'PIN_F10', 'VGA_B[0]':'PIN_B13', 'VGA_B[1]':'PIN_G13', 'VGA_B[2]':'PIN_H13', 
                'VGA_B[3]':'PIN_F14', 'VGA_B[4]':'PIN_H14', 'VGA_B[5]':'PIN_F15', 'VGA_B[6]':'PIN_G15', 'VGA_B[7]':'PIN_J14', 
                'VGA_CLK':'PIN_A11', 'VGA_G[0]':'PIN_J9', 'VGA_G[1]':'PIN_J10', 'VGA_G[2]':'PIN_H12', 'VGA_G[3]':'PIN_G10', 
                'VGA_G[4]':'PIN_G11', 'VGA_G[5]':'PIN_G12', 'VGA_G[6]':'PIN_F11', 'VGA_G[7]':'PIN_E11', 'VGA_HS':'PIN_B11', 
                'VGA_R[0]':'PIN_A13', 'VGA_R[1]':'PIN_C13', 'VGA_R[2]':'PIN_E13', 'VGA_R[3]':'PIN_B12', 'VGA_R[4]':'PIN_C12', 
                'VGA_R[5]':'PIN_D12', 'VGA_R[6]':'PIN_E12', 'VGA_R[7]':'PIN_F13', 'VGA_SYNC_N':'PIN_C10', 'VGA_VS':'PIN_D11',
                
                }
        return pins
        
    def getQsf(self):
        info = self.getFPGADeviceInfo()
        qsf = '# build by py4hw\n'
        qsf += 'set_global_assignment -name FAMILY {}\n'.format(info['family'])
        qsf += 'set_global_assignment -name DEVICE {}\n'.format(info['device'])
        qsf += 'set_global_assignment -name DEVICE_FILTER_PACKAGE {}\n'.format(info['package'])
        qsf += 'set_global_assignment -name DEVICE_FILTER_PIN_COUNT {}\n'.format(info['pin_count'])
        qsf += 'set_global_assignment -name DEVICE_FILTER_SPEED_GRADE {}\n'.format(info['speed_grade'])

        pins = self.getPinAssignments()
        
        for key in pins.keys():
            qsf += 'set_location_assignment {} -to {}\n'.format(pins[key], key)

        # by default all are 3.3 LVTTL
        for key in pins.keys():
            qsf += 'set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to {}\n'.format(key)
        
        return qsf
