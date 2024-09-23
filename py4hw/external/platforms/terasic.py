# -*- coding: utf-8 -*-
"""
Created on Sat Sep 30 09:01:29 2023

@author: dcr
"""



import py4hw
from edalize import edatool
import os

class VGAExternalControllerInterface(py4hw.Interface):
    def __init__(self, parent, name:str):
        super().__init__(parent, name)
        
        self.R = self.addSourceToSink('R', 8)
        self.G = self.addSourceToSink('G', 8)
        self.B = self.addSourceToSink('B', 8)
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
            file.write('create_clock  -period 20 [get_ports CLOCK_50]\n')
            
        tool = 'quartus'
        
        files = [  {'name' : verilog_file, 'file_type' : 'verilogSource'},
                 {'name' : sdc_file, 'file_type' : 'SDC'},
                 {'name' : qsf_file, 'file_type' : 'tclSource'}
                 ]

        parameters = {'clk_freq_hz' : {'datatype' : 'int', 'default' : 50000000, 'paramtype' : 'vlogparam'},
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
        
        
    def getQsf(self):
        qsf =  '''
# Copyright (C) 1991-2008 Altera Corporation
# Your use of Altera Corporation's design tools, logic functions 
# and other software and tools, and its AMPP partner logic 
# functions, and any output files from any of the foregoing 
# (including device programming or simulation files), and any 
# associated documentation or information are expressly subject 
# to the terms and conditions of the Altera Program License 
# Subscription Agreement, Altera MegaCore Function License 
# Agreement, or other applicable license agreement, including, 
# without limitation, that your use is for the sole purpose of 
# programming logic devices manufactured by Altera and sold by 
# Altera or its authorized distributors.  Please refer to the 
# applicable agreement for further details.


# The default values for assignments are stored in the file
#		DE0_Default_assignment_defaults.qdf
# If this file doesn't exist, and for assignments not listed, see file
#		assignment_defaults.qdf

# Altera recommends that you do not modify this file. This
# file is updated automatically by the Quartus II software
# and any changes you make may be lost or overwritten.


set_global_assignment -name FAMILY "Cyclone III"
set_global_assignment -name DEVICE EP3C16F484C6
set_global_assignment -name TOP_LEVEL_ENTITY DE0_Default
set_global_assignment -name ORIGINAL_QUARTUS_VERSION "8.0 SP1"
set_global_assignment -name PROJECT_CREATION_TIME_DATE "15:56:36  MARCH 06, 2009"
set_global_assignment -name LAST_QUARTUS_VERSION "9.0 SP2"
set_global_assignment -name USE_GENERATED_PHYSICAL_CONSTRAINTS OFF -section_id eda_palace
set_global_assignment -name NOMINAL_CORE_SUPPLY_VOLTAGE 1.2V
set_instance_assignment -name PARTITION_HIERARCHY root_partition -to | -section_id Top
set_global_assignment -name PARTITION_NETLIST_TYPE SOURCE -section_id Top
set_global_assignment -name PARTITION_COLOR 14622752 -section_id Top
set_global_assignment -name LL_ROOT_REGION ON -section_id "Root Region"
set_global_assignment -name LL_MEMBER_STATE LOCKED -section_id "Root Region"

# Pin & Location Assignments
# ==========================
set_location_assignment PIN_B1 -to LEDG[9]
set_location_assignment PIN_B2 -to LEDG[8]
set_location_assignment PIN_C2 -to LEDG[7]
set_location_assignment PIN_C1 -to LEDG[6]
set_location_assignment PIN_E1 -to LEDG[5]
set_location_assignment PIN_F2 -to LEDG[4]
set_location_assignment PIN_H1 -to LEDG[3]
set_location_assignment PIN_J3 -to LEDG[2]
set_location_assignment PIN_J2 -to LEDG[1]
set_location_assignment PIN_J1 -to LEDG[0]
set_location_assignment PIN_D2 -to SW[9]
set_location_assignment PIN_E4 -to SW[8]
set_location_assignment PIN_E3 -to SW[7]
set_location_assignment PIN_H7 -to SW[6]
set_location_assignment PIN_J7 -to SW[5]
set_location_assignment PIN_G5 -to SW[4]
set_location_assignment PIN_G4 -to SW[3]
set_location_assignment PIN_H6 -to SW[2]
set_location_assignment PIN_H5 -to SW[1]
set_location_assignment PIN_J6 -to SW[0]
set_location_assignment PIN_F1 -to BUTTON[2]
set_location_assignment PIN_G3 -to BUTTON[1]
set_location_assignment PIN_H2 -to BUTTON[0]
set_location_assignment PIN_R2 -to FL_ADDR[21]
set_location_assignment PIN_P3 -to FL_ADDR[20]
set_location_assignment PIN_P1 -to FL_ADDR[19]
set_location_assignment PIN_M6 -to FL_ADDR[18]
set_location_assignment PIN_M5 -to FL_ADDR[17]
set_location_assignment PIN_AA2 -to FL_ADDR[16]
set_location_assignment PIN_L6 -to FL_ADDR[15]
set_location_assignment PIN_L7 -to FL_ADDR[14]
set_location_assignment PIN_M1 -to FL_ADDR[13]
set_location_assignment PIN_M2 -to FL_ADDR[12]
set_location_assignment PIN_M3 -to FL_ADDR[11]
set_location_assignment PIN_N1 -to FL_ADDR[10]
set_location_assignment PIN_N2 -to FL_ADDR[9]
set_location_assignment PIN_P2 -to FL_ADDR[8]
set_location_assignment PIN_M4 -to FL_ADDR[7]
set_location_assignment PIN_M8 -to FL_ADDR[6]
set_location_assignment PIN_N6 -to FL_ADDR[5]
set_location_assignment PIN_N5 -to FL_ADDR[4]
set_location_assignment PIN_N7 -to FL_ADDR[3]
set_location_assignment PIN_P6 -to FL_ADDR[2]
set_location_assignment PIN_P5 -to FL_ADDR[1]
set_location_assignment PIN_P7 -to FL_ADDR[0]
set_location_assignment PIN_AA1 -to FL_BYTE_N
set_location_assignment PIN_N8 -to FL_CE_N
set_location_assignment PIN_R7 -to FL_DQ[0]
set_location_assignment PIN_P8 -to FL_DQ[1]
set_location_assignment PIN_R8 -to FL_DQ[2]
set_location_assignment PIN_U1 -to FL_DQ[3]
set_location_assignment PIN_V2 -to FL_DQ[4]
set_location_assignment PIN_V3 -to FL_DQ[5]
set_location_assignment PIN_W1 -to FL_DQ[6]
set_location_assignment PIN_Y1 -to FL_DQ[7]
set_location_assignment PIN_T5 -to FL_DQ[8]
set_location_assignment PIN_T7 -to FL_DQ[9]
set_location_assignment PIN_T4 -to FL_DQ[10]
set_location_assignment PIN_U2 -to FL_DQ[11]
set_location_assignment PIN_V1 -to FL_DQ[12]
set_location_assignment PIN_V4 -to FL_DQ[13]
set_location_assignment PIN_W2 -to FL_DQ[14]
set_location_assignment PIN_R6 -to FL_OE_N
set_location_assignment PIN_R1 -to FL_RST_N
set_location_assignment PIN_M7 -to FL_RY
set_location_assignment PIN_P4 -to FL_WE_N
set_location_assignment PIN_T3 -to FL_WP_N
set_location_assignment PIN_Y2 -to FL_DQ15_AM1
set_location_assignment PIN_U7 -to GPIO0_D[31]
set_location_assignment PIN_V5 -to GPIO0_D[30]
set_location_assignment PIN_W6 -to GPIO0_D[29]
set_location_assignment PIN_W7 -to GPIO0_D[28]
set_location_assignment PIN_V8 -to GPIO0_D[27]
set_location_assignment PIN_T8 -to GPIO0_D[26]
set_location_assignment PIN_W10 -to GPIO0_D[25]
set_location_assignment PIN_Y10 -to GPIO0_D[24]
set_location_assignment PIN_V11 -to GPIO0_D[23]
set_location_assignment PIN_R10 -to GPIO0_D[22]
set_location_assignment PIN_V12 -to GPIO0_D[21]
set_location_assignment PIN_U13 -to GPIO0_D[20]
set_location_assignment PIN_W13 -to GPIO0_D[19]
set_location_assignment PIN_Y13 -to GPIO0_D[18]
set_location_assignment PIN_U14 -to GPIO0_D[17]
set_location_assignment PIN_V14 -to GPIO0_D[16]
set_location_assignment PIN_AA4 -to GPIO0_D[15]
set_location_assignment PIN_AB4 -to GPIO0_D[14]
set_location_assignment PIN_AA5 -to GPIO0_D[13]
set_location_assignment PIN_AB5 -to GPIO0_D[12]
set_location_assignment PIN_AA8 -to GPIO0_D[11]
set_location_assignment PIN_AB8 -to GPIO0_D[10]
set_location_assignment PIN_AA10 -to GPIO0_D[9]
set_location_assignment PIN_AB10 -to GPIO0_D[8]
set_location_assignment PIN_AA13 -to GPIO0_D[7]
set_location_assignment PIN_AB13 -to GPIO0_D[6]
set_location_assignment PIN_AB14 -to GPIO0_D[5]
set_location_assignment PIN_AA14 -to GPIO0_D[4]
set_location_assignment PIN_AB15 -to GPIO0_D[3]
set_location_assignment PIN_AA15 -to GPIO0_D[2]
set_location_assignment PIN_AA16 -to GPIO0_D[1]
set_location_assignment PIN_AB16 -to GPIO0_D[0]
set_location_assignment PIN_AB12 -to GPIO0_CLKIN[0]
set_location_assignment PIN_AA12 -to GPIO0_CLKIN[1]
set_location_assignment PIN_AB3 -to GPIO0_CLKOUT[0]
set_location_assignment PIN_AA3 -to GPIO0_CLKOUT[1]
set_location_assignment PIN_AA11 -to GPIO1_CLKIN[1]
set_location_assignment PIN_AB11 -to GPIO1_CLKIN[0]
set_location_assignment PIN_T16 -to GPIO1_CLKOUT[1]
set_location_assignment PIN_R16 -to GPIO1_CLKOUT[0]
set_location_assignment PIN_V7 -to GPIO1_D[31]
set_location_assignment PIN_V6 -to GPIO1_D[30]
set_location_assignment PIN_U8 -to GPIO1_D[29]
set_location_assignment PIN_Y7 -to GPIO1_D[28]
set_location_assignment PIN_T9 -to GPIO1_D[27]
set_location_assignment PIN_U9 -to GPIO1_D[26]
set_location_assignment PIN_T10 -to GPIO1_D[25]
set_location_assignment PIN_U10 -to GPIO1_D[24]
set_location_assignment PIN_R12 -to GPIO1_D[23]
set_location_assignment PIN_R11 -to GPIO1_D[22]
set_location_assignment PIN_T12 -to GPIO1_D[21]
set_location_assignment PIN_U12 -to GPIO1_D[20]
set_location_assignment PIN_R14 -to GPIO1_D[19]
set_location_assignment PIN_T14 -to GPIO1_D[18]
set_location_assignment PIN_AB7 -to GPIO1_D[17]
set_location_assignment PIN_AA7 -to GPIO1_D[16]
set_location_assignment PIN_AA9 -to GPIO1_D[15]
set_location_assignment PIN_AB9 -to GPIO1_D[14]
set_location_assignment PIN_V15 -to GPIO1_D[13]
set_location_assignment PIN_W15 -to GPIO1_D[12]
set_location_assignment PIN_T15 -to GPIO1_D[11]
set_location_assignment PIN_U15 -to GPIO1_D[10]
set_location_assignment PIN_W17 -to GPIO1_D[9]
set_location_assignment PIN_Y17 -to GPIO1_D[8]
set_location_assignment PIN_AB17 -to GPIO1_D[7]
set_location_assignment PIN_AA17 -to GPIO1_D[6]
set_location_assignment PIN_AA18 -to GPIO1_D[5]
set_location_assignment PIN_AB18 -to GPIO1_D[4]
set_location_assignment PIN_AB19 -to GPIO1_D[3]
set_location_assignment PIN_AA19 -to GPIO1_D[2]
set_location_assignment PIN_AB20 -to GPIO1_D[1]
set_location_assignment PIN_AA20 -to GPIO1_D[0]
set_location_assignment PIN_P22 -to PS2_KBCLK
set_location_assignment PIN_P21 -to PS2_KBDAT
set_location_assignment PIN_R21 -to PS2_MSCLK
set_location_assignment PIN_R22 -to PS2_MSDAT
set_location_assignment PIN_U22 -to UART_RXD
set_location_assignment PIN_U21 -to UART_TXD
set_location_assignment PIN_V22 -to UART_RTS
set_location_assignment PIN_V21 -to UART_CTS
set_location_assignment PIN_Y21 -to SD_CLK
set_location_assignment PIN_Y22 -to SD_CMD
set_location_assignment PIN_AA22 -to SD_DAT0
set_location_assignment PIN_W21 -to SD_DAT3
set_location_assignment PIN_W20 -to SD_WP_N
set_location_assignment PIN_C20 -to LCD_DATA[7]
set_location_assignment PIN_D20 -to LCD_DATA[6]
set_location_assignment PIN_B21 -to LCD_DATA[5]
set_location_assignment PIN_B22 -to LCD_DATA[4]
set_location_assignment PIN_C21 -to LCD_DATA[3]
set_location_assignment PIN_C22 -to LCD_DATA[2]
set_location_assignment PIN_D21 -to LCD_DATA[1]
set_location_assignment PIN_D22 -to LCD_DATA[0]
set_location_assignment PIN_E22 -to LCD_RW
set_location_assignment PIN_F22 -to LCD_RS
set_location_assignment PIN_E21 -to LCD_EN
set_location_assignment PIN_F21 -to LCD_BLON
set_location_assignment PIN_J21 -to VGA_G[3]
set_location_assignment PIN_K17 -to VGA_G[2]
set_location_assignment PIN_J17 -to VGA_G[1]
set_location_assignment PIN_H22 -to VGA_G[0]
set_location_assignment PIN_L21 -to VGA_HS
set_location_assignment PIN_L22 -to VGA_VS
set_location_assignment PIN_H21 -to VGA_R[3]
set_location_assignment PIN_H20 -to VGA_R[2]
set_location_assignment PIN_H17 -to VGA_R[1]
set_location_assignment PIN_H19 -to VGA_R[0]
set_location_assignment PIN_K18 -to VGA_B[3]
set_location_assignment PIN_J22 -to VGA_B[2]
set_location_assignment PIN_K21 -to VGA_B[1]
set_location_assignment PIN_K22 -to VGA_B[0]
set_location_assignment PIN_G21 -to CLOCK_50
set_location_assignment PIN_E11 -to HEX0_D[0]
set_location_assignment PIN_F11 -to HEX0_D[1]
set_location_assignment PIN_H12 -to HEX0_D[2]
set_location_assignment PIN_H13 -to HEX0_D[3]
set_location_assignment PIN_G12 -to HEX0_D[4]
set_location_assignment PIN_F12 -to HEX0_D[5]
set_location_assignment PIN_F13 -to HEX0_D[6]
set_location_assignment PIN_D13 -to HEX0_DP
set_location_assignment PIN_A15 -to HEX1_D[6]
set_location_assignment PIN_E14 -to HEX1_D[5]
set_location_assignment PIN_B14 -to HEX1_D[4]
set_location_assignment PIN_A14 -to HEX1_D[3]
set_location_assignment PIN_C13 -to HEX1_D[2]
set_location_assignment PIN_B13 -to HEX1_D[1]
set_location_assignment PIN_A13 -to HEX1_D[0]
set_location_assignment PIN_B15 -to HEX1_DP
set_location_assignment PIN_F14 -to HEX2_D[6]
set_location_assignment PIN_B17 -to HEX2_D[5]
set_location_assignment PIN_A17 -to HEX2_D[4]
set_location_assignment PIN_E15 -to HEX2_D[3]
set_location_assignment PIN_B16 -to HEX2_D[2]
set_location_assignment PIN_A16 -to HEX2_D[1]
set_location_assignment PIN_D15 -to HEX2_D[0]
set_location_assignment PIN_A18 -to HEX2_DP
set_location_assignment PIN_G15 -to HEX3_D[6]
set_location_assignment PIN_D19 -to HEX3_D[5]
set_location_assignment PIN_C19 -to HEX3_D[4]
set_location_assignment PIN_B19 -to HEX3_D[3]
set_location_assignment PIN_A19 -to HEX3_D[2]
set_location_assignment PIN_F15 -to HEX3_D[1]
set_location_assignment PIN_B18 -to HEX3_D[0]
set_location_assignment PIN_G16 -to HEX3_DP
set_location_assignment PIN_G8 -to DRAM_CAS_N
set_location_assignment PIN_G7 -to DRAM_CS_N
set_location_assignment PIN_E5 -to DRAM_CLK
set_location_assignment PIN_E6 -to DRAM_CKE
set_location_assignment PIN_B5 -to DRAM_BA_0
set_location_assignment PIN_A4 -to DRAM_BA_1
set_location_assignment PIN_F10 -to DRAM_DQ[15]
set_location_assignment PIN_E10 -to DRAM_DQ[14]
set_location_assignment PIN_A10 -to DRAM_DQ[13]
set_location_assignment PIN_B10 -to DRAM_DQ[12]
set_location_assignment PIN_C10 -to DRAM_DQ[11]
set_location_assignment PIN_A9 -to DRAM_DQ[10]
set_location_assignment PIN_B9 -to DRAM_DQ[9]
set_location_assignment PIN_A8 -to DRAM_DQ[8]
set_location_assignment PIN_F8 -to DRAM_DQ[7]
set_location_assignment PIN_H9 -to DRAM_DQ[6]
set_location_assignment PIN_G9 -to DRAM_DQ[5]
set_location_assignment PIN_F9 -to DRAM_DQ[4]
set_location_assignment PIN_E9 -to DRAM_DQ[3]
set_location_assignment PIN_H10 -to DRAM_DQ[2]
set_location_assignment PIN_G10 -to DRAM_DQ[1]
set_location_assignment PIN_D10 -to DRAM_DQ[0]
set_location_assignment PIN_E7 -to DRAM_LDQM
set_location_assignment PIN_B8 -to DRAM_UDQM
set_location_assignment PIN_F7 -to DRAM_RAS_N
set_location_assignment PIN_D6 -to DRAM_WE_N
set_location_assignment PIN_B12 -to CLOCK_50_2
set_location_assignment PIN_C8 -to DRAM_ADDR[12]
set_location_assignment PIN_A7 -to DRAM_ADDR[11]
set_location_assignment PIN_B4 -to DRAM_ADDR[10]
set_location_assignment PIN_B7 -to DRAM_ADDR[9]
set_location_assignment PIN_C7 -to DRAM_ADDR[8]
set_location_assignment PIN_A6 -to DRAM_ADDR[7]
set_location_assignment PIN_B6 -to DRAM_ADDR[6]
set_location_assignment PIN_C6 -to DRAM_ADDR[5]
set_location_assignment PIN_A5 -to DRAM_ADDR[4]
set_location_assignment PIN_C3 -to DRAM_ADDR[3]
set_location_assignment PIN_B3 -to DRAM_ADDR[2]
set_location_assignment PIN_A3 -to DRAM_ADDR[1]
set_location_assignment PIN_C4 -to DRAM_ADDR[0]


set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to BUTTON[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to BUTTON[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to BUTTON[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_DQ[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_DQ[3]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_DQ[4]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_DQ[5]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_DQ[6]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_DQ[7]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_DQ[8]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_DQ[9]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_DQ[10]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_DQ[11]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_DQ[12]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_DQ[13]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_DQ[14]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_DQ[15]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_CS_N
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_CLK
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_CKE
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_CAS_N
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_BA_1
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_BA_0
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_ADDR[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_ADDR[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_ADDR[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_ADDR[3]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_ADDR[4]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_ADDR[5]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_ADDR[6]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_ADDR[7]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_ADDR[8]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_ADDR[9]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_ADDR[10]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_ADDR[11]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_ADDR[12]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to CLOCK_50_2
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to CLOCK_50
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_CE_N
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_BYTE_N
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_ADDR[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_ADDR[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_ADDR[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_ADDR[3]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_ADDR[4]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_ADDR[5]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_ADDR[6]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_ADDR[7]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_ADDR[8]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_ADDR[9]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_ADDR[10]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_ADDR[11]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_ADDR[12]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_ADDR[13]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_ADDR[14]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_ADDR[15]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_ADDR[16]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_ADDR[17]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_ADDR[18]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_ADDR[19]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_ADDR[20]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_ADDR[21]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_WE_N
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_UDQM
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_RAS_N
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_LDQM
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_DQ[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_DQ[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_D[28]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_D[29]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_D[30]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_D[31]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_CLKOUT[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_CLKOUT[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_CLKIN[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_CLKIN[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_D[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_D[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_D[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_D[3]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_D[4]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_D[5]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_D[6]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_D[7]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_D[8]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_D[9]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_D[10]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_D[11]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_D[12]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_D[13]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_D[14]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_D[15]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_D[16]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_D[17]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_D[18]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_D[19]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_D[20]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_D[21]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_D[22]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_D[23]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_D[24]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_D[25]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_D[26]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_D[27]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_D[28]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_D[29]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_D[30]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_D[31]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_CLKOUT[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_CLKOUT[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_CLKIN[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO0_CLKIN[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_WP_N
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_WE_N
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_RY
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_RST_N
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_OE_N
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_DQ15_AM1
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_DQ[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_DQ[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_DQ[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_DQ[3]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_DQ[4]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_DQ[5]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_DQ[6]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_DQ[7]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_DQ[8]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_DQ[9]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_DQ[10]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_DQ[11]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_DQ[12]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_DQ[13]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FL_DQ[14]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX0_D[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX0_D[3]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX0_D[4]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX0_D[5]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX0_D[6]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_D[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_D[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_D[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_D[3]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_D[4]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_D[5]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_D[6]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_D[7]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_D[8]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_D[9]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_D[10]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_D[11]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_D[12]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_D[13]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_D[14]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_D[15]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_D[16]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_D[17]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_D[18]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_D[19]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_D[20]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_D[21]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_D[22]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_D[23]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_D[24]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_D[25]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_D[26]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to GPIO1_D[27]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to LCD_DATA[3]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to LCD_DATA[4]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to LCD_DATA[5]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to LCD_DATA[6]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to LCD_DATA[7]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to LCD_BLON
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX3_DP
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX3_D[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX3_D[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX3_D[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX3_D[3]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX3_D[4]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX3_D[5]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX3_D[6]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX2_DP
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX2_D[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX2_D[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX2_D[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX2_D[3]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX2_D[4]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX2_D[5]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX2_D[6]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX1_DP
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX1_D[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX1_D[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX1_D[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX1_D[3]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX1_D[4]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX1_D[5]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX1_D[6]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX0_DP
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX0_D[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX0_D[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to UART_CTS
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to SW[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to SW[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to SW[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to SW[3]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to SW[4]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to SW[5]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to SW[6]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to SW[7]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to SW[8]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to SW[9]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to SD_WP_N
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to SD_DAT3
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to SD_DAT0
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to SD_CMD
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to SD_CLK
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to PS2_MSDAT
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to PS2_MSCLK
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to PS2_KBDAT
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to PS2_KBCLK
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to LEDG[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to LEDG[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to LEDG[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to LEDG[3]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to LEDG[4]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to LEDG[5]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to LEDG[6]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to LEDG[7]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to LEDG[8]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to LEDG[9]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to LCD_RW
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to LCD_RS
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to LCD_EN
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to LCD_DATA[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to LCD_DATA[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to LCD_DATA[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_VS
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_R[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_R[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_R[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_R[3]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_HS
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_G[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_G[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_G[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_G[3]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_B[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_B[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_B[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_B[3]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to UART_TXD
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to UART_RXD
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to UART_RTS

set_global_assignment -name FORCE_CONFIGURATION_VCCIO ON
set_global_assignment -name CYCLONEII_RESERVE_NCEO_AFTER_CONFIGURATION "USE AS REGULAR IO"
set_global_assignment -name USE_CONFIGURATION_DEVICE ON
set_global_assignment -name CYCLONEIII_CONFIGURATION_DEVICE EPCS4
set_global_assignment -name MISC_FILE "D:/TERASIC_TEST/DE0/DE0_Default/DE0_Default.dpf"
set_global_assignment -name TIMEQUEST_MULTICORNER_ANALYSIS ON
set_global_assignment -name TIMEQUEST_DO_CCPP_REMOVAL ON
set_global_assignment -name MISC_FILE "E:/DE0/DE0_Default/DE0_Default.dpf"
set_global_assignment -name VERILOG_FILE V/VGA_Ctrl.v
set_global_assignment -name VERILOG_FILE V/Reset_Delay.v
set_global_assignment -name VERILOG_FILE V/IMG_RAM.v
set_global_assignment -name VERILOG_FILE V/LCD_Controller.v
set_global_assignment -name VERILOG_FILE V/LCD_TEST.v
set_global_assignment -name VERILOG_FILE V/LEDG_Driver.v
set_global_assignment -name VERILOG_FILE V/SEG7_LUT.v
set_global_assignment -name VERILOG_FILE V/SEG7_LUT_4.v
set_global_assignment -name VERILOG_FILE V/VGA_CLK.v
set_global_assignment -name VERILOG_FILE V/VGA_OSD_RAM.v


'''
        
        return qsf
    
class DE1SoC(py4hw.HWSystem):
    
    def __init__(self):
        
        super().__init__(name='DE1SoC')
        
        clk50 = self.wire('CLOCK_50')
        #clk50 = self.addIn('CLOCK_50', clk50)
        clockDriver = py4hw.ClockDriver('CLOCK_50', 50E6, 0, wire=clk50)
        
        print('Initial', self.getFullPath(),  self._wires)
        
        self.clockDriver = clockDriver
    
    
    
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
            file.write('create_clock  -period 20 [get_ports CLOCK_50]\n')
            
        tool = 'quartus'
        
        files = [  {'name' : verilog_file, 'file_type' : 'verilogSource'},
                 {'name' : sdc_file, 'file_type' : 'SDC'},
                 {'name' : qsf_file, 'file_type' : 'tclSource'}
                 ]

        parameters = {'clk_freq_hz' : {'datatype' : 'int', 'default' : 50000000, 'paramtype' : 'vlogparam'},
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
        
        
    def getQsf(self):
        qsf =  '''#============================================================
# Build by Terasic System Builder
#============================================================

set_global_assignment -name FAMILY "Cyclone V"
set_global_assignment -name DEVICE 5CSEMA5F31C6
set_global_assignment -name DEVICE_FILTER_PACKAGE FBGA
set_global_assignment -name DEVICE_FILTER_PIN_COUNT 896
set_global_assignment -name DEVICE_FILTER_SPEED_GRADE 6

#============================================================
# ADC
#============================================================
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to ADC_CONVST
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to ADC_DIN
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to ADC_DOUT
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to ADC_SCLK
set_location_assignment PIN_AJ4 -to ADC_CONVST
set_location_assignment PIN_AK4 -to ADC_DIN
set_location_assignment PIN_AK3 -to ADC_DOUT
set_location_assignment PIN_AK2 -to ADC_SCLK

#============================================================
# Audio
#============================================================
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to AUD_ADCDAT
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to AUD_ADCLRCK
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to AUD_BCLK
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to AUD_DACDAT
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to AUD_DACLRCK
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to AUD_XCK
set_location_assignment PIN_K7 -to AUD_ADCDAT
set_location_assignment PIN_K8 -to AUD_ADCLRCK
set_location_assignment PIN_H7 -to AUD_BCLK
set_location_assignment PIN_J7 -to AUD_DACDAT
set_location_assignment PIN_H8 -to AUD_DACLRCK
set_location_assignment PIN_G7 -to AUD_XCK

#============================================================
# CLOCK
#============================================================
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to CLOCK2_50
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to CLOCK3_50
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to CLOCK4_50
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to CLOCK_50
set_location_assignment PIN_AA16 -to CLOCK2_50
set_location_assignment PIN_Y26 -to CLOCK3_50
set_location_assignment PIN_K14 -to CLOCK4_50
set_location_assignment PIN_AF14 -to CLOCK_50

#============================================================
# SDRAM
#============================================================
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_ADDR[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_ADDR[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_ADDR[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_ADDR[3]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_ADDR[4]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_ADDR[5]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_ADDR[6]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_ADDR[7]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_ADDR[8]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_ADDR[9]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_ADDR[10]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_ADDR[11]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_ADDR[12]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_BA[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_BA[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_CAS_N
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_CKE
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_CLK
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_CS_N
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_DQ[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_DQ[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_DQ[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_DQ[3]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_DQ[4]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_DQ[5]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_DQ[6]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_DQ[7]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_DQ[8]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_DQ[9]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_DQ[10]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_DQ[11]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_DQ[12]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_DQ[13]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_DQ[14]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_DQ[15]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_LDQM
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_RAS_N
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_UDQM
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to DRAM_WE_N
set_location_assignment PIN_AK14 -to DRAM_ADDR[0]
set_location_assignment PIN_AH14 -to DRAM_ADDR[1]
set_location_assignment PIN_AG15 -to DRAM_ADDR[2]
set_location_assignment PIN_AE14 -to DRAM_ADDR[3]
set_location_assignment PIN_AB15 -to DRAM_ADDR[4]
set_location_assignment PIN_AC14 -to DRAM_ADDR[5]
set_location_assignment PIN_AD14 -to DRAM_ADDR[6]
set_location_assignment PIN_AF15 -to DRAM_ADDR[7]
set_location_assignment PIN_AH15 -to DRAM_ADDR[8]
set_location_assignment PIN_AG13 -to DRAM_ADDR[9]
set_location_assignment PIN_AG12 -to DRAM_ADDR[10]
set_location_assignment PIN_AH13 -to DRAM_ADDR[11]
set_location_assignment PIN_AJ14 -to DRAM_ADDR[12]
set_location_assignment PIN_AF13 -to DRAM_BA[0]
set_location_assignment PIN_AJ12 -to DRAM_BA[1]
set_location_assignment PIN_AF11 -to DRAM_CAS_N
set_location_assignment PIN_AK13 -to DRAM_CKE
set_location_assignment PIN_AH12 -to DRAM_CLK
set_location_assignment PIN_AG11 -to DRAM_CS_N
set_location_assignment PIN_AK6 -to DRAM_DQ[0]
set_location_assignment PIN_AJ7 -to DRAM_DQ[1]
set_location_assignment PIN_AK7 -to DRAM_DQ[2]
set_location_assignment PIN_AK8 -to DRAM_DQ[3]
set_location_assignment PIN_AK9 -to DRAM_DQ[4]
set_location_assignment PIN_AG10 -to DRAM_DQ[5]
set_location_assignment PIN_AK11 -to DRAM_DQ[6]
set_location_assignment PIN_AJ11 -to DRAM_DQ[7]
set_location_assignment PIN_AH10 -to DRAM_DQ[8]
set_location_assignment PIN_AJ10 -to DRAM_DQ[9]
set_location_assignment PIN_AJ9 -to DRAM_DQ[10]
set_location_assignment PIN_AH9 -to DRAM_DQ[11]
set_location_assignment PIN_AH8 -to DRAM_DQ[12]
set_location_assignment PIN_AH7 -to DRAM_DQ[13]
set_location_assignment PIN_AJ6 -to DRAM_DQ[14]
set_location_assignment PIN_AJ5 -to DRAM_DQ[15]
set_location_assignment PIN_AB13 -to DRAM_LDQM
set_location_assignment PIN_AE13 -to DRAM_RAS_N
set_location_assignment PIN_AK12 -to DRAM_UDQM
set_location_assignment PIN_AA13 -to DRAM_WE_N

#============================================================
# I2C for Audio and Video-In
#============================================================
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FPGA_I2C_SCLK
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to FPGA_I2C_SDAT
set_location_assignment PIN_J12 -to FPGA_I2C_SCLK
set_location_assignment PIN_K12 -to FPGA_I2C_SDAT

#============================================================
# SEG7
#============================================================
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX0[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX0[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX0[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX0[3]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX0[4]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX0[5]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX0[6]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX1[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX1[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX1[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX1[3]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX1[4]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX1[5]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX1[6]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX2[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX2[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX2[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX2[3]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX2[4]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX2[5]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX2[6]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX3[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX3[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX3[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX3[3]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX3[4]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX3[5]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX3[6]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX4[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX4[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX4[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX4[3]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX4[4]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX4[5]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX4[6]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX5[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX5[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX5[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX5[3]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX5[4]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX5[5]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to HEX5[6]
set_location_assignment PIN_AE26 -to HEX0[0]
set_location_assignment PIN_AE27 -to HEX0[1]
set_location_assignment PIN_AE28 -to HEX0[2]
set_location_assignment PIN_AG27 -to HEX0[3]
set_location_assignment PIN_AF28 -to HEX0[4]
set_location_assignment PIN_AG28 -to HEX0[5]
set_location_assignment PIN_AH28 -to HEX0[6]
set_location_assignment PIN_AJ29 -to HEX1[0]
set_location_assignment PIN_AH29 -to HEX1[1]
set_location_assignment PIN_AH30 -to HEX1[2]
set_location_assignment PIN_AG30 -to HEX1[3]
set_location_assignment PIN_AF29 -to HEX1[4]
set_location_assignment PIN_AF30 -to HEX1[5]
set_location_assignment PIN_AD27 -to HEX1[6]
set_location_assignment PIN_AB23 -to HEX2[0]
set_location_assignment PIN_AE29 -to HEX2[1]
set_location_assignment PIN_AD29 -to HEX2[2]
set_location_assignment PIN_AC28 -to HEX2[3]
set_location_assignment PIN_AD30 -to HEX2[4]
set_location_assignment PIN_AC29 -to HEX2[5]
set_location_assignment PIN_AC30 -to HEX2[6]
set_location_assignment PIN_AD26 -to HEX3[0]
set_location_assignment PIN_AC27 -to HEX3[1]
set_location_assignment PIN_AD25 -to HEX3[2]
set_location_assignment PIN_AC25 -to HEX3[3]
set_location_assignment PIN_AB28 -to HEX3[4]
set_location_assignment PIN_AB25 -to HEX3[5]
set_location_assignment PIN_AB22 -to HEX3[6]
set_location_assignment PIN_AA24 -to HEX4[0]
set_location_assignment PIN_Y23 -to HEX4[1]
set_location_assignment PIN_Y24 -to HEX4[2]
set_location_assignment PIN_W22 -to HEX4[3]
set_location_assignment PIN_W24 -to HEX4[4]
set_location_assignment PIN_V23 -to HEX4[5]
set_location_assignment PIN_W25 -to HEX4[6]
set_location_assignment PIN_V25 -to HEX5[0]
set_location_assignment PIN_AA28 -to HEX5[1]
set_location_assignment PIN_Y27 -to HEX5[2]
set_location_assignment PIN_AB27 -to HEX5[3]
set_location_assignment PIN_AB26 -to HEX5[4]
set_location_assignment PIN_AA26 -to HEX5[5]
set_location_assignment PIN_AA25 -to HEX5[6]

#============================================================
# IR
#============================================================
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to IRDA_RXD
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to IRDA_TXD
set_location_assignment PIN_AA30 -to IRDA_RXD
set_location_assignment PIN_AB30 -to IRDA_TXD

#============================================================
# KEY
#============================================================
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to KEY[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to KEY[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to KEY[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to KEY[3]
set_location_assignment PIN_AA14 -to KEY[0]
set_location_assignment PIN_AA15 -to KEY[1]
set_location_assignment PIN_W15 -to KEY[2]
set_location_assignment PIN_Y16 -to KEY[3]

#============================================================
# LED
#============================================================
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to LEDR[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to LEDR[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to LEDR[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to LEDR[3]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to LEDR[4]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to LEDR[5]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to LEDR[6]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to LEDR[7]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to LEDR[8]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to LEDR[9]
set_location_assignment PIN_V16 -to LEDR[0]
set_location_assignment PIN_W16 -to LEDR[1]
set_location_assignment PIN_V17 -to LEDR[2]
set_location_assignment PIN_V18 -to LEDR[3]
set_location_assignment PIN_W17 -to LEDR[4]
set_location_assignment PIN_W19 -to LEDR[5]
set_location_assignment PIN_Y19 -to LEDR[6]
set_location_assignment PIN_W20 -to LEDR[7]
set_location_assignment PIN_W21 -to LEDR[8]
set_location_assignment PIN_Y21 -to LEDR[9]

#============================================================
# PS2
#============================================================
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to PS2_CLK
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to PS2_CLK2
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to PS2_DAT
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to PS2_DAT2
set_location_assignment PIN_AD7 -to PS2_CLK
set_location_assignment PIN_AD9 -to PS2_CLK2
set_location_assignment PIN_AE7 -to PS2_DAT
set_location_assignment PIN_AE9 -to PS2_DAT2

#============================================================
# SW
#============================================================
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to SW[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to SW[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to SW[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to SW[3]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to SW[4]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to SW[5]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to SW[6]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to SW[7]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to SW[8]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to SW[9]
set_location_assignment PIN_AB12 -to SW[0]
set_location_assignment PIN_AC12 -to SW[1]
set_location_assignment PIN_AF9 -to SW[2]
set_location_assignment PIN_AF10 -to SW[3]
set_location_assignment PIN_AD11 -to SW[4]
set_location_assignment PIN_AD12 -to SW[5]
set_location_assignment PIN_AE11 -to SW[6]
set_location_assignment PIN_AC9 -to SW[7]
set_location_assignment PIN_AD10 -to SW[8]
set_location_assignment PIN_AE12 -to SW[9]

#============================================================
# Video-In
#============================================================
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to TD_CLK27
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to TD_DATA[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to TD_DATA[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to TD_DATA[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to TD_DATA[3]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to TD_DATA[4]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to TD_DATA[5]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to TD_DATA[6]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to TD_DATA[7]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to TD_HS
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to TD_RESET_N
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to TD_VS
set_location_assignment PIN_H15 -to TD_CLK27
set_location_assignment PIN_D2 -to TD_DATA[0]
set_location_assignment PIN_B1 -to TD_DATA[1]
set_location_assignment PIN_E2 -to TD_DATA[2]
set_location_assignment PIN_B2 -to TD_DATA[3]
set_location_assignment PIN_D1 -to TD_DATA[4]
set_location_assignment PIN_E1 -to TD_DATA[5]
set_location_assignment PIN_C2 -to TD_DATA[6]
set_location_assignment PIN_B3 -to TD_DATA[7]
set_location_assignment PIN_A5 -to TD_HS
set_location_assignment PIN_F6 -to TD_RESET_N
set_location_assignment PIN_A3 -to TD_VS

#============================================================
# VGA
#============================================================
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_BLANK_N
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_B[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_B[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_B[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_B[3]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_B[4]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_B[5]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_B[6]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_B[7]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_CLK
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_G[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_G[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_G[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_G[3]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_G[4]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_G[5]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_G[6]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_G[7]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_HS
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_R[0]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_R[1]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_R[2]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_R[3]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_R[4]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_R[5]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_R[6]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_R[7]
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_SYNC_N
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to VGA_VS
set_location_assignment PIN_F10 -to VGA_BLANK_N
set_location_assignment PIN_B13 -to VGA_B[0]
set_location_assignment PIN_G13 -to VGA_B[1]
set_location_assignment PIN_H13 -to VGA_B[2]
set_location_assignment PIN_F14 -to VGA_B[3]
set_location_assignment PIN_H14 -to VGA_B[4]
set_location_assignment PIN_F15 -to VGA_B[5]
set_location_assignment PIN_G15 -to VGA_B[6]
set_location_assignment PIN_J14 -to VGA_B[7]
set_location_assignment PIN_A11 -to VGA_CLK
set_location_assignment PIN_J9 -to VGA_G[0]
set_location_assignment PIN_J10 -to VGA_G[1]
set_location_assignment PIN_H12 -to VGA_G[2]
set_location_assignment PIN_G10 -to VGA_G[3]
set_location_assignment PIN_G11 -to VGA_G[4]
set_location_assignment PIN_G12 -to VGA_G[5]
set_location_assignment PIN_F11 -to VGA_G[6]
set_location_assignment PIN_E11 -to VGA_G[7]
set_location_assignment PIN_B11 -to VGA_HS
set_location_assignment PIN_A13 -to VGA_R[0]
set_location_assignment PIN_C13 -to VGA_R[1]
set_location_assignment PIN_E13 -to VGA_R[2]
set_location_assignment PIN_B12 -to VGA_R[3]
set_location_assignment PIN_C12 -to VGA_R[4]
set_location_assignment PIN_D12 -to VGA_R[5]
set_location_assignment PIN_E12 -to VGA_R[6]
set_location_assignment PIN_F13 -to VGA_R[7]
set_location_assignment PIN_C10 -to VGA_SYNC_N
set_location_assignment PIN_D11 -to VGA_VS

#============================================================
# End of pin assignments by Terasic System Builder
#============================================================


'''
        
        return qsf