# -*- coding: utf-8 -*-
"""
Created on Wed Jul 29 09:08:37 2026

@author: dcr
"""

import py4hw

from edalize.flows.vivado import Vivado
import os


class HDMIInterface(py4hw.Interface):
    def __init__(self, parent, name:str):
        super().__init__(parent, name)
        
        self.d_p = self.addSourceToSink('d_p', 3)
        self.d_n = self.addSourceToSink('d_n', 3)
        self.clk_p = self.addSourceToSink('clk_p', 1)
        self.clk_n = self.addSourceToSink('clk_n', 1)
        
        self.hpdn = self.addSinkToSource('hpdn', 1)

        
class VGAInternalControllerInterface(py4hw.Interface):
    def __init__(self, parent, name:str):
        super().__init__(parent, name)
        
        self.R = self.addSourceToSink('R', 8)
        self.G = self.addSourceToSink('G', 8)
        self.B = self.addSourceToSink('B', 8)
        
        self.VS = self.addSourceToSink('VS', 1)
        self.HS = self.addSourceToSink('HS', 1)
        
        self.VE = self.addSourceToSink('VE', 1)

class Pynq_Z2(py4hw.HWSystem):
    def __init__(self):
        super().__init__(name='Pynq_Z2')
        
        clk125 = self.wire('sysclk')
        
        clockDriver = py4hw.ClockDriver('sysclk', 125E6, 0, wire=clk125)
        
        self.clockDriver = clockDriver
        
        
    def getInputKey(self):
        key = self.wire('btn', 4)
        self.addIn('btn', key)

        return key
        
    def getLEDs(self):
        key = self.wire('led', 4)
        self.addOut('led', key)

        return key
        
    def getVGAController(self, reset, vga_clk):
        '''
        Connections to VGA connector
        

        Returns
        -------
        None.

        '''
        hdmi_ext = HDMIInterface(self, 'hdmi_tx')
        vga_int = VGAInternalControllerInterface(self, 'vga')
        
        self.addInterfaceSource('hdmi_tx', hdmi_ext)
        
        Vga2hdmi = py4hw.AbstractLogic('Vga2Hdmi')
        obj = Vga2hdmi(self, 'vga2hdmi')
        
        obj.addInterfaceSource('hdmi_tx', hdmi_ext)
        obj.addInterfaceSink('vga', vga_int)
        
        obj.addIn('reset', reset)
        obj.addOut('vga_clk', vga_clk)
        
        sysclk_freq = self.clockDriver.freq
        
        vga_clk_freq = 25.175E6
        
        serial_clk_freq = vga_clk_freq * 5
        

        serial_clk = obj.wire('serial_clk')
        
        vga_clk_drv = py4hw.ClockDriver('vga_clk', 25.175E6, wire=vga_clk)
        serial_clk_drv = py4hw.ClockDriver('serial_clk', 25.175E6*5, wire=serial_clk)
        
        from py4hw.external.xilinx.ip.mmcm import xilinx_mmcm
        from py4hw.logic.protocol.tmds.encoder import tmds_encoder
        from py4hw.external.xilinx.ip.serdes import serializer_10to1
        from py4hw.external.xilinx.io import OuputBufferDifferential
        from py4hw.external.xilinx.io import ClockBufferIO
        from py4hw.external.xilinx.io import ClockBufferRegional
        vco_min = 700E6
        vco_max = 1100E6

        #mmcm_vga_clk = obj.wire('mmcm_vga_clk')        
        mmcm_serial_clk = obj.wire('mmcm_serial_clk')
        
        #xilinx_mmcm(self, 'mmcm', sysclk_freq, serial_clk, vga_clk, serial_clk_freq, vga_clk_freq, vco_min=vco_min, vco_max=vco_max )
        #xilinx_mmcm(obj, 'mmcm', sysclk_freq, mmcm_serial_clk, mmcm_vga_clk, mult=8, div1=8, div2=40 )
        xilinx_mmcm(obj, 'mmcm', sysclk_freq, mmcm_serial_clk, None, serial_clk_freq, None, vco_min=vco_min, vco_max=vco_max )
        
        ClockBufferIO(obj, 'serial_clk', mmcm_serial_clk, serial_clk)
        ClockBufferRegional(obj, 'vga_clk', mmcm_serial_clk, vga_clk, div=5)
        
        one = self.wire('one')
        zero = self.wire('zero')
        blank = self.wire('blank')
        
        py4hw.Not(obj, 'blank', vga_int.VE, blank)
        

        
        tmds_red = obj.wire('tmds_red', 10)
        tmds_green = obj.wire('tmds_green', 10)
        tmds_blue = obj.wire('tmds_blue', 10)
        
        py4hw.Constant(obj, 'one', 1, one)
        py4hw.Constant(obj, 'zero', 0, zero)
        
        enc = tmds_encoder(obj, 'encode_r', data=vga_int.R, c0=zero, c1=zero, blank=blank, encoded=tmds_red)
        enc.clockDriver = vga_clk_drv
         
        enc = tmds_encoder(obj, 'encode_g', data=vga_int.G, c0=zero, c1=zero, blank=blank, encoded=tmds_green)
        enc.clockDriver = vga_clk_drv
        
        enc = tmds_encoder(obj, 'encode_b', data=vga_int.B, c0=vga_int.HS, c1=vga_int.VS, blank=blank, encoded=tmds_blue)
        enc.clockDriver = vga_clk_drv

        tmds_ser_r = obj.wire('tmds_ser_r')
        tmds_ser_g = obj.wire('tmds_ser_g')
        tmds_ser_b = obj.wire('tmds_ser_b')

        

        ser = serializer_10to1  (obj, 'ser_r',  clk_pixel = vga_clk, reset=reset, data_in = tmds_red, serial_out = tmds_ser_r);
        ser.clockDriver = serial_clk_drv 
        
        ser = serializer_10to1  (obj, 'ser_g', clk_pixel = vga_clk, reset=reset, data_in = tmds_green, serial_out = tmds_ser_g);
        ser.clockDriver = serial_clk_drv
        
        ser = serializer_10to1  (obj, 'ser_b',  clk_pixel = vga_clk, reset=reset, data_in = tmds_blue,  serial_out= tmds_ser_b);
        ser.clockDriver = serial_clk_drv
        
        
        
        tmds_ser_r_p = obj.wire('tmds_ser_r_p')
        tmds_ser_g_p = obj.wire('tmds_ser_g_p')
        tmds_ser_b_p = obj.wire('tmds_ser_b_p')
        tmds_ser_r_n = obj.wire('tmds_ser_r_n')
        tmds_ser_g_n = obj.wire('tmds_ser_g_n')
        tmds_ser_b_n = obj.wire('tmds_ser_b_n')        
        
        OuputBufferDifferential(obj, 'rdiff', tmds_ser_r, tmds_ser_r_p, tmds_ser_r_n)
        OuputBufferDifferential(obj, 'gdiff', tmds_ser_g, tmds_ser_g_p, tmds_ser_g_n)
        OuputBufferDifferential(obj, 'bdiff', tmds_ser_b, tmds_ser_b_p, tmds_ser_b_n)
        
        py4hw.ConcatenateLSBF(obj, 'd_p', [tmds_ser_b_p, tmds_ser_g_p, tmds_ser_r_p], hdmi_ext.d_p)
        py4hw.ConcatenateLSBF(obj, 'd_n', [tmds_ser_b_n, tmds_ser_g_n, tmds_ser_r_n], hdmi_ext.d_n)
        
        OuputBufferDifferential(obj, 'clk_diff', vga_clk, hdmi_ext.clk_p, hdmi_ext.clk_n)
                    
        return vga_int        
        
    def getXdc(self):
        s = '''
set_property -dict { PACKAGE_PIN H16   IOSTANDARD LVCMOS33 } [get_ports { sysclk }]; #IO_L13P_T2_MRCC_35 Sch=sysclk
create_clock -add -name sys_clk_pin -period 8.00 -waveform {0 4} [get_ports { sysclk }];
set_input_jitter sys_clk_pin 0.100

# LEDs

set_property -dict { PACKAGE_PIN R14   IOSTANDARD LVCMOS33 } [get_ports { led[0] }]; #IO_L6N_T0_VREF_34 Sch=led[0]
set_property -dict { PACKAGE_PIN P14   IOSTANDARD LVCMOS33 } [get_ports { led[1] }]; #IO_L6P_T0_34 Sch=led[1]
set_property -dict { PACKAGE_PIN N16   IOSTANDARD LVCMOS33 } [get_ports { led[2] }]; #IO_L21N_T3_DQS_AD14N_35 Sch=led[2]
set_property -dict { PACKAGE_PIN M14   IOSTANDARD LVCMOS33 } [get_ports { led[3] }]; #IO_L23P_T3_35 Sch=led[3]

##Buttons

set_property -dict { PACKAGE_PIN D19   IOSTANDARD LVCMOS33 } [get_ports { btn[0] }]; #IO_L4P_T0_35 Sch=btn[0]
set_property -dict { PACKAGE_PIN D20   IOSTANDARD LVCMOS33 } [get_ports { btn[1] }]; #IO_L4N_T0_35 Sch=btn[1]
set_property -dict { PACKAGE_PIN L20   IOSTANDARD LVCMOS33 } [get_ports { btn[2] }]; #IO_L9N_T1_DQS_AD3N_35 Sch=btn[2]
set_property -dict { PACKAGE_PIN L19   IOSTANDARD LVCMOS33 } [get_ports { btn[3] }]; #IO_L9P_T1_DQS_AD3P_35 Sch=btn[3]

set_property -dict { PACKAGE_PIN L17   IOSTANDARD TMDS_33  } [get_ports { hdmi_tx_clk_n }]; #IO_L11N_T1_SRCC_35 Sch=hdmi_tx_clk_n
set_property -dict { PACKAGE_PIN L16   IOSTANDARD TMDS_33  } [get_ports { hdmi_tx_clk_p }]; #IO_L11P_T1_SRCC_35 Sch=hdmi_tx_clk_p
set_property -dict { PACKAGE_PIN K18   IOSTANDARD TMDS_33  } [get_ports { hdmi_tx_d_n[0] }]; #IO_L12N_T1_MRCC_35 Sch=hdmi_tx_d_n[0]
set_property -dict { PACKAGE_PIN K17   IOSTANDARD TMDS_33  } [get_ports { hdmi_tx_d_p[0] }]; #IO_L12P_T1_MRCC_35 Sch=hdmi_tx_d_p[0]
set_property -dict { PACKAGE_PIN J19   IOSTANDARD TMDS_33  } [get_ports { hdmi_tx_d_n[1] }]; #IO_L10N_T1_AD11N_35 Sch=hdmi_tx_d_n[1]
set_property -dict { PACKAGE_PIN K19   IOSTANDARD TMDS_33  } [get_ports { hdmi_tx_d_p[1] }]; #IO_L10P_T1_AD11P_35 Sch=hdmi_tx_d_p[1]
set_property -dict { PACKAGE_PIN H18   IOSTANDARD TMDS_33  } [get_ports { hdmi_tx_d_n[2] }]; #IO_L14N_T2_AD4N_SRCC_35 Sch=hdmi_tx_d_n[2]
set_property -dict { PACKAGE_PIN J18   IOSTANDARD TMDS_33  } [get_ports { hdmi_tx_d_p[2] }]; #IO_L14P_T2_AD4P_SRCC_35 Sch=hdmi_tx_d_p[2]

        '''
        return s


    def build(self, projectDir):
        if not os.path.exists(projectDir):
            print('Creating the directory', projectDir)
            os.makedirs(projectDir)

        rtl = py4hw.VerilogGenerator(self)

        rtl_code = rtl.getVerilogForHierarchy(noInstanceNumberInTopEntity=True)
        xdc_code = self.getXdc()
        top_name = self.name

        verilog_file = os.path.join(projectDir, top_name + '.v')
        xdc_file = os.path.join(projectDir, top_name + '.xdc')

        with open(verilog_file, 'w') as file:
            file.write(rtl_code)

        with open(xdc_file, 'w') as file:
            file.write(xdc_code)

        files = [
            {'name': verilog_file, 'file_type': 'verilogSource'},
            {'name': xdc_file, 'file_type': 'xdc'},
        ]
        parameters = {
            'clk_freq_hz': {'datatype': 'int', 'default': int(self.clockDriver.freq), 'paramtype': 'vlogparam'},
            'vcd': {'datatype': 'bool', 'paramtype': 'plusarg'},
        }

        edam = {
            'files': files,
            'name': top_name,
            'parameters': parameters,
            'toplevel': top_name,
            'flow_options': {
                'part': 'xc7z020clg400-1'  # PYNQ-Z2 part number
            }
        }

        flow = Vivado(edam=edam, work_root=projectDir, verbose=True)

        print('Configure Edalize')
        flow.configure()

        print('Build Edalize')
        flow.build()
        

    def download(self, projectDir):
        top_name = self.name

        files = []
        edam = {
            'name': top_name,
            'files': files,
            'toplevel': top_name,
            'flow_options': {
                'part': 'xc7z020clg400-1',   # PYNQ-Z2 part number
                'pgm': 'vivado',             # tells Vivado to program the device on run()
                # Optional, if you need to target a specific connected board:
                # 'hw_target': '*/xilinx_tcf/*/*',
            }
        }

        flow = Vivado(edam=edam, work_root=projectDir)
        print('Download bitstream')
        # flow.configure()   # (re)generates the project/tcl scripts in work_root
        flow.run()          # runs the programming tcl script in Vivado batch mode        
