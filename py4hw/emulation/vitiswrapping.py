from __future__ import annotations

import py4hw
import py4hw.logic.bus.axi as axi
import os
import math
import glob


class Axi2Reg(py4hw.Logic):
    
    def __init__(self, parent, name, ap_start, ap_reset, stream:axi.AXI4StreamInterface, q, loaded):
        '''
        Captures the first 64 bits of an AXI4-Stream word into a register.
        Translates the Verilog axi2reg module.
        Remember that in a kernel ap_start always comes before the inputs are pushed to the AXI streams.

        Parameters
        ----------
        parent : Logic
            Parent object.
        name : str
            instance name.

        ap_start : Wire
            Kernel start signal.
        ap_reset : Wire
            Kernel reset signal.
        stream : axi.AXI4StreamInterface
            AXI streaming interface that we will acquire.
        q : Wire
            Value that we are acquiring.
        loaded : Wire
            Signal that tells if the value is loaded with data.

        Returns
        -------
        None.

        '''
        super().__init__(parent, name)

        # Add Ports

        self.addIn("ap_start", ap_start)
        self.addIn("ap_reset", ap_reset)
        
        self.addInterfaceSink('', stream)
        
        self.addOut("q", q)
        self.addOut("loaded", loaded)

        py4hw.Constant(self, "tready", 1, stream.tready)
        
        # 3. Handshake Logic (valid && ready)
        handshake = py4hw.Wire(self, "handshake", 1)
        py4hw.And2(self, "and_handshake", stream.tvalid, stream.tready, handshake)

        # 4. Extract first 64 bits of tdata
        tdata_64 = py4hw.Wire(self, "tdata_64", 64)
        py4hw.Range(self, "range_data", stream.tdata, 63, 0, tdata_64)

        # 5. Register for reg_out
        # In Verilog: if (handshake) reg_out <= data; else if (areset) reg_out <= 0;
        # py4hw.Reg(parent, name, d, q, enable, reset, reset_value)
        py4hw.Reg(self, "reg_data", d=tdata_64, q=q, enable=handshake, reset=ap_reset)

        # 6. Logic for 'loaded'
        # 'loaded' goes to 1 on the handshake (ready & valid) and stays set 
        # It is cleared only by a real reset (ap_reset), not by ap_start
       
        
        py4hw.Reg(self, "loaded", d=handshake, q=loaded, enable=handshake, reset=ap_reset)


  
class Reg2Axi(py4hw.Logic):

    def __init__(self, parent, name, ap_start, ap_reset, load_outs,
                 reg_in, stream: axi.AXI4StreamInterface, sent):
        '''
        Sends a register value out through an AXI4-Stream interface.
        Translates the Verilog reg2axi module.

        Parameters
        ----------
        parent : Logic
        name : str
        reset : Wire        -- areset
        ap_start : Wire     -- ap_start (rearm)
        ap_reset : Wire     -- ap_reset (rearm)
        load_outs : Wire    -- pulse that means "load the outputs"
        reg_in : Wire       -- value to send (W bits)
        stream : AXI4StreamInterface  -- output AXI-Stream (master)
        sent : Wire         -- 1 when the transaction has completed
        '''
        super().__init__(parent, name)

        W = reg_in.getWidth()
        AXIS_W = stream.tdata.getWidth()

        # Ports

        self.addIn('ap_start',  ap_start)
        self.addIn('ap_reset',  ap_reset)
        self.addIn('load_outs', load_outs)
        self.addIn('reg_in',    reg_in)

        self.addInterfaceSource('', stream)   # master: we generate tvalid

        self.addOut('sent', sent)
        
        
        # @todo remove it, not use it
        hlp = py4hw.LogicHelper(self)

        pending     = self.wire('pending')
        handshake   = self.wire('handshake')
        pending_set = self.wire('pending_set')   # load_outs & ~handshake; not use it

        # handshake = tvalid & tready  (tvalid = pending)
        py4hw.And2(self, 'and_hs',  pending, stream.tready, handshake)

        one_bit = self.wire('one', 1)
        py4hw.Constant(self, 'c1', 1, one_bit)

        reset_pending = self.wire('reset_pending')
        py4hw.Or(self, 'or_rst_pending', [ap_reset, handshake], reset_pending)
        
        py4hw.Reg(self, 'reg_pending',
                  d=one_bit, q=pending,
                  enable=load_outs,
                  reset=reset_pending)

        # tvalid = pending
        py4hw.Buf(self, 'tvalid_buf', pending, stream.tvalid)

        # tdata: reg_in in the lower bits, zeros to the rest
        py4hw.ZeroExtend(self, 'tdata_ext', reg_in, stream.tdata)

        # tkeep: ceil(W/8) valid bytes to the lower bits
        #import math (#REMOVE, it is already on top)
        n_bytes_valid = math.ceil(W / 8)
        n_bytes_total = AXIS_W // 8    #not use it
        tkeep_val = (1 << n_bytes_valid) - 1   # e.g. W=32 -> 0xF, W=8 -> 0x1
        py4hw.Constant(self, 'tkeep_const', tkeep_val, stream.tkeep)

        # tlast = tvalid (single-beat package)
        py4hw.Buf(self, 'tlast_buf',  pending, stream.tlast)

        # sent = handshake
        py4hw.Buf(self, 'sent_buf',   handshake, sent)


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


class HILPlatform:
    
    def __init__(self, platform, projectDir, dutName, dut):
        self.platform = platform
        self.projectDir = projectDir
        self.dutName = dutName
        self.dut = dut 
        
        
    def build(self):
        
        # clean the directory to start from zero
        if os.path.exists(self.projectDir):
            shutil.rmtree(self.projectDir)
        os.makedirs(self.projectDir, exist_ok=True)
        
        # 1. Generate rtl_kernel_example Verilog file. The DUT will be generated separatelly because it is a living object
        # from an existing HWSystem different from the one that we use to synthesize for the FPGA.
        
        kernel = self.platform.children['rtl_kernel_example']
        
        # HERE we generate rtl_kernel_example.v ourselves with py4hw
        # (flat module: the Axi2Reg/Reg2Axi wrapping + load_outs, no parameters)
        rtl = py4hw.VerilogGenerator(kernel)
        rtl_code = rtl.getVerilogForHierarchy(noInstanceNumberInTopEntity=False, createdStructures=[self.dutName])

        verilog_file = os.path.join(self.projectDir, 'rtl_kernel_example.v')
        dut_file = os.path.join(self.projectDir, f'{self.dutName}.v' )
    
        with open(verilog_file, 'w') as file:
            file.write(rtl_code)  
	
        print('[GEN]', verilog_file)
        
        # 2. Generate the Verilog for the DUT.
        # This is a separate step because the DUT is a living object
        
        dut_rtl = py4hw.VerilogGenerator(self.dut)
        dut_code = dut_rtl.getVerilogForHierarchy(noInstanceNumberInTopEntity=False)
        with open(dut_file, 'w') as file:
            file.write(dut_code)

        
        # 3. Generate TCLs
        generate_create_project_tcl(self.dut, [verilog_file, dut_file], self.projectDir)
        generate_package_tcl(kernel, [verilog_file, dut_file], self.projectDir)
        
        # 4. Generate Reader & Writer
        generate_reader(self.dut, self.projectDir)        
        generate_writer(self.dut, self.projectDir)
        generate_connectivity(self.dut, self.projectDir)
        
        # 5. Run Vivado to create the XO
        generate_rtl_kernel(self.projectDir, self.dutName)
        
        # 6. Create a script to build xclbin
        generate_build_script(self.projectDir)
        
      
    def download(self, values=None):
        import pyxrt
        if values is None:
            values = {}

        xclbin_path = os.path.join(self.projectDir, 'hil.xclbin')
        if not os.path.exists(xclbin_path):
            print('[download] not found:', xclbin_path,
                  '-> build it first with build_xclbin.sh')
            return

        io_dtype  = make_io_dtype()
        in_table  = build_input_table(self.dut, values, io_dtype)
        out_table = build_output_table(self.dut, io_dtype)
        print_table_inputs_dynamic(in_table, self.dut)

        print('\nLoading xclbin:', xclbin_path)
        device = pyxrt.device(0)
        uuid = device.load_xclbin(xclbin_path)

        krnl_reader = pyxrt.kernel(device, uuid, 'krnl_reader')
        krnl_mid    = pyxrt.kernel(device, uuid, 'rtl_kernel')
        krnl_writer = pyxrt.kernel(device, uuid, 'krnl_writer')

        # these kernels have no 'num' argument:
        #   reader: in  = arg 0
        #   writer: out = arg N, where N = number of output streams (streams come first)
        bo_in  = pyxrt.bo(device, in_table.nbytes,  pyxrt.bo.flags.normal, krnl_reader.group_id(0))
        bo_out = pyxrt.bo(device, out_table.nbytes, pyxrt.bo.flags.normal, krnl_writer.group_id(len(self.dut.outPorts)))

        bo_in.write(in_table.tobytes(), 0)
        bo_out.write(out_table.tobytes(), 0)
        bo_in.sync(pyxrt.xclBOSyncDirection.XCL_BO_SYNC_BO_TO_DEVICE, in_table.nbytes, 0)
        bo_out.sync(pyxrt.xclBOSyncDirection.XCL_BO_SYNC_BO_TO_DEVICE, out_table.nbytes, 0)
        bo_out_map = bo_out.map()

        run_reader = pyxrt.run(krnl_reader)
        run_writer = pyxrt.run(krnl_writer)
        run_reader.set_arg(0, bo_in)
        run_writer.set_arg(len(self.dut.outPorts), bo_out)

        print('\nRunning...')
        run_writer.start()                 # consumer first
        try:
            run_mid = pyxrt.run(krnl_mid)  # middle processor (RTL kernel)
            run_mid.start()
        except Exception as e:
            print('[download] rtl_kernel has no start() control:', e)
        run_reader.start()                 # feeder last

        run_reader.wait()
        run_writer.wait()
        print('Execution finished.')

        result = copy_bo_to_array(bo_out, bo_out_map, io_dtype, len(out_table))
        print_table_outputs_dynamic(result, self.dut)
        return {self.dut.outPorts[int(r["index"])].name: int(r["valor"]) for r in result}  # NEW
        
        
        
        
        
        

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

def createHILVitis(dut, projectDir):
    '''
    Create the platform that will be used to synthesize the FPGA version of the DUT
    
    '''
    platform = py4hw.HWSystem()
    platform.clockDriver =  py4hw.ClockDriver('ap_clk', 50E6, 0, wire=platform.wire('ap_clk'))
    
    dutStructureNameWithoutInstanceNumber = py4hw.getVerilogModuleName(dut, noInstanceNumber=True)
    dutStructureNameWithInstanceNumber = py4hw.getVerilogModuleName(dut, noInstanceNumber=False)
    
    # use instance number if necessary
    dutStructureName = dutStructureNameWithoutInstanceNumber if (dutStructureNameWithoutInstanceNumber == dutStructureNameWithInstanceNumber) else dutStructureNameWithInstanceNumber

    hil_plt = HILPlatform(platform, projectDir, dutStructureName, dut)  
    
    
    if not(os.path.exists(projectDir)):
        print('Creating the directory', projectDir)
        os.makedirs(projectDir)
        
    # First create verilog for the dut        
    # @todo maybe we should move this to the build function of the platform
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
    
    
    rtl_kernel_class = AbstractClass('rtl_kernel_example')
    rtl_kernel = rtl_kernel_class(platform, 'rtl_kernel_example')


    fake_ins = []
    fake_outs = []
        
    ap_start = platform.wire('ap_start')
    ap_rst_n = platform.wire('ap_rst_n')
    ap_reset = platform.wire('ap_reset')
    
    ap_idle = platform.wire('ap_idle')
    ap_done = platform.wire('ap_done')
    ap_ready = platform.wire('ap_ready')
    
                
    rtl_kernel.addIn('ap_start', ap_start)
    rtl_kernel.addIn('ap_rst_n', ap_rst_n)
    rtl_kernel.addOut('ap_idle', ap_idle)
    rtl_kernel.addOut('ap_done', ap_done)
    rtl_kernel.addOut('ap_ready', ap_ready)        
        
    
    py4hw.Not(rtl_kernel, 'ap_reset', ap_rst_n, ap_reset)
    
    stream_ins = []
    loaded_wires = [] 
        
    for i in range(num_ins):
        ip = dut.inPorts[i]
        in_name = ip.name
        iw = ip.wire.getWidth()
        in_wire = rtl_kernel.wire(f'in{i}', iw)
        fake_ins.append((in_name, in_wire))

        from py4hw.logic.bus.axi import AXI4StreamInterface
        stream_in = AXI4StreamInterface(platform, f'axis{i:02}', 64, has_tlast=True, has_tkeep=True)
	
        stream_in = rtl_kernel.addInterfaceSink(f'axis{i:02}', stream_in)
	
        loaded = rtl_kernel.wire(f'loaded{i}')
        loaded_wires.append(loaded)   # NEW
        Axi2Reg(rtl_kernel, f'axis{i:02}',  ap_start, ap_reset, stream_in, in_wire, loaded)
        

    load_outs = rtl_kernel.wire('load_outs')
    if len(loaded_wires) == 1:
        py4hw.Buf(rtl_kernel, 'c_load_outs', loaded_wires[0], load_outs)
    else:
        py4hw.And(rtl_kernel, 'c_load_outs', loaded_wires, load_outs)

    for i in range(num_outs):
        op = dut.outPorts[i]
        out_name = op.name
        ow = op.wire.getWidth()
        out_wire = rtl_kernel.wire(f'out{i}', ow)
        fake_outs.append((out_name, out_wire))

        from py4hw.logic.bus.axi import AXI4StreamInterface
        stream_out = AXI4StreamInterface(platform, f'axis{num_ins + i:02}', 64,  has_tlast=True, has_tkeep=True)
        stream_out = rtl_kernel.addInterfaceSource(f'axis{num_ins + i:02}', stream_out)

        sent = rtl_kernel.wire(f'sent{i}')
        Reg2Axi(rtl_kernel, f'reg2axi{i}', ap_start, ap_reset, load_outs, out_wire, stream_out, sent)


    # Black Box Placeholder
    abstract_class = AbstractClass(dutStructureName)
    obj = abstract_class(rtl_kernel, dutStructureName)

    
    for i in range(len(fake_ins)):
        obj.addIn(fake_ins[i][0], fake_ins[i][1])

    for i in range(len(fake_outs)):
        obj.addOut(fake_outs[i][0], fake_outs[i][1])
    
    return hil_plt
    

def generate_connectivity(dut, output_path):
    dut_kernel_name="rtl_kernel"
    reader_kernel_name="krnl_reader"
    writer_kernel_name="krnl_writer"
    
    reader_inst = f"{reader_kernel_name}_1"
    dut_inst = f"{dut_kernel_name}_1"
    writer_inst = f"{writer_kernel_name}_1"

    lines = []

    lines.append("[connectivity]")
    lines.append(f"nk={reader_kernel_name}:1:{reader_inst}")
    lines.append(f"nk={dut_kernel_name}:1:{dut_inst}")
    lines.append(f"nk={writer_kernel_name}:1:{writer_inst}")
    lines.append("")


    lines.append("# Reader -> DUT")
    #no clk stream (createHILVitis does not create one)
    #lines.append(f"sc={reader_inst}.s_out0:{dut_inst}.axis00 \t # axis00 = clk / axis2clk")


    for i, inp in enumerate(dut.inPorts):
        reader_stream = i   # before: i + 1
        dut_axis = i        # before: i + 1

        lines.append(f"sc={reader_inst}.s_out{reader_stream}:{dut_inst}.axis{dut_axis:02d} \t # axis{dut_axis:02d} = {inp.name}")

    lines.append("")

    first_output_axis = len(dut.inPorts)  # before: 1 + len(dut.inPorts)

    lines.append("# DUT -> Writer")

    for i, outp in enumerate(dut.outPorts):
        dut_axis = first_output_axis + i

        lines.append(f"sc={dut_inst}.axis{dut_axis:02d}:{writer_inst}.s_in{i} \t # axis{dut_axis:02d} = {outp.name}")

    output_file = os.path.join(output_path, 'connectivity.cfg') 
    with open(output_file, 'w') as f:
        f.write("\n".join(lines) + "\n")

    print(f"File created: {output_file}")




def generate_reader(dut, output_path):
    stream_args = [] # This are the parameters of the stream kernel
    stream_pragmas = []
    writes = []

    # s_out0 will be reserved for clock / axis2clk.(not now)
    # The remaining streams correspond to the inputs of the DUT.
    total_out_streams = len(dut.inPorts)  # before: 1 + len(dut.inPorts)

    #link = ','
    link = ''

# It used to be like this (with the clk):
#    for stream_id in range(total_out_streams):
#        
#        if stream_id == 0:
#            comment = "clk"
#        else:
#            inp = dut.inPorts[stream_id -1]
#            comment = inp.name
#the end of before

    for stream_id in range(total_out_streams):
        inp = dut.inPorts[stream_id]
        comment = inp.name

        #stream_args.append(f"    {link} hls::stream<ap_uint<64>>& s_out{stream_id}  // {comment}")
        stream_args.append(f"     {link} hls::stream<ap_uint<64>>& s_out{stream_id}")
        
        link = ','

    for i in range(total_out_streams):
        stream_pragmas.append(f"#pragma HLS INTERFACE axis port=s_out{i}")

    # in[0] will be reserved for the clock. (not now)
    # in[1+i] corresponds to the i input of the DUT. (not now)
    
    # writes.append("    s_out0.write(in[0].valor);")
    for i, inp in enumerate(dut.inPorts):
        stream_id = i      # before: i + 1
        table_index = i    # before: i + 1
        name = inp.name

        writes.append(f"    s_out{stream_id}.write(in[{table_index}].valor);")
        

    code = f"""#include <ap_int.h>
#include <hls_stream.h>
#include <stdint.h>

struct io_t {{
    uint32_t index;
    uint32_t width;
    uint64_t valor;
}};

extern "C" void krnl_reader(
    const io_t* in,   // pointer to the input table
{chr(10).join(stream_args)}
) {{
#pragma HLS INTERFACE m_axi port=in offset=slave bundle=gmem
#pragma HLS INTERFACE s_axilite port=in bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control

{chr(10).join(stream_pragmas)}

    // Generic format of the input table:
    //   in[i] = i DUT input
    //   (CHECK THIS) in[0] = clk / number of cycles
"""

    for i, inp in enumerate(dut.inPorts):
        code += f"    //   in[{i+1}] = {inp.name} ({inp.wire.getWidth()} bits)\n"

    code += f"""
{chr(10).join(writes)}
}}
"""
    
    output_file = os.path.join(output_path, 'krnl_reader.cpp') 
    with open(output_file, 'w') as f:
        f.write(code)

    print(f"File created: {output_file}")




def generate_writer(dut, output_path):
    stream_args = []
    stream_pragmas = []
    reads = []

    slink = ''
    for i, outp in enumerate(dut.outPorts):
        stream_args.append(f"    hls::stream<ap_uint<64>>& s_in{i},  // {outp.name}")
        stream_pragmas.append(f"#pragma HLS INTERFACE axis port=s_in{i}")
        slink = ','

    for i, outp in enumerate(dut.outPorts):
        name = outp.name
        width = outp.wire.getWidth()

        reads.append(f"    // {name}")
        
        reads.append(f"    out[{i}].index = {i};")
        reads.append(f"    out[{i}].width = {width};")
        reads.append(f"    out[{i}].valor = (uint64_t) s_in{i}.read();")
        reads.append("")

    code = f"""#include <ap_int.h>
#include <hls_stream.h>
#include <stdint.h>

struct io_t {{
    uint32_t index;
    uint32_t width;
    uint64_t valor;
}};

extern "C" void krnl_writer(
{chr(10).join(stream_args)}
    //io_t* out,
    io_t* out
) {{
{chr(10).join(stream_pragmas)}

#pragma HLS INTERFACE m_axi port=out offset=slave bundle=gmem
#pragma HLS INTERFACE s_axilite port=out bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control

    // Generic format of the output table:
"""

    for i, outp in enumerate(dut.outPorts):
        name = outp.name
        width = outp.wire.getWidth()
        code += f"    //   out[{i}] = {name} ({width} bits)\n"

    code += f"""
{chr(10).join(reads)}
}}
"""
    output_file = os.path.join(output_path, 'krnl_writer.cpp') 

    with open(output_file, 'w') as f:
        f.write(code)
    
    print(f"File created: {output_file}")
   
    
def strip_param_override(imports_dir):
    import re
    path = os.path.join(imports_dir, 'rtl_kernel.v')
    with open(path) as f:
        src = f.read()
    src = re.sub(r'rtl_kernel_example\s*#\s*\(.*?\)\s*inst_example',
                 'rtl_kernel_example inst_example', src, flags=re.DOTALL)
    with open(path, 'w') as f:
        f.write(src)
    print('[PATCH] parameter override removed from rtl_kernel.v')    



def generate_rtl_kernel(output_path, dutName):
    # Phase 1: project + IP wizard + example design (creates rtl_kernel_ex/imports/...)
    tcl_path = os.path.join(output_path, 'create_project.tcl')
    cmd = f'vivado -mode batch -source {tcl_path}'
    print('[RUN]', cmd)
    os.system(cmd)

    imports_dir = os.path.join(output_path, 'rtl_kernel_ex', 'imports')
    
    # delete rtl_kernel_exemple files created by the wizard
    for f in glob.glob(os.path.join(imports_dir, 'rtl_kernel_example*')):
        os.remove(f)

    # copy the generated verilog files to the final position        
    shutil.copy(os.path.join(output_path, 'rtl_kernel_example.v'), os.path.join(imports_dir, 'rtl_kernel_example.v'))
    shutil.copy(os.path.join(output_path, f'{dutName}.v'), os.path.join(imports_dir, f'{dutName}.v'))
    
    strip_param_override(imports_dir)
    
    # package  IP + generate  .xo 
    tcl_path = os.path.join(output_path, 'package_rtl_kernel.tcl')
    cmd = f'vivado -mode batch -source {tcl_path}'
    print('[RUN]', cmd)
    os.system(cmd)
    

def generate_build_script(output_path):
   
    platform = 'xilinx_u55c_gen3x16_xdma_3_202210_1'
    target = 'hw'
    build_dir = 'xclbin_build'
    logs_dir = 'xclbin_logs'
    exports_dir = os.path.join(output_path, 'rtl_kernel_ex', 'exports')
    
    reader_kernel_name = 'krnl_reader'    
    writer_kernel_name = 'krnl_writer'
    reader_cpp_path = os.path.join(output_path, 'krnl_reader.cpp') 
    writer_cpp_path = os.path.join(output_path, 'krnl_writer.cpp') 
    rtl_xo_path = os.path.join(exports_dir, 'rtl_kernel.xo')
    reader_xo_path = os.path.join(output_path, 'krnl_reader.xo') 
    writer_xo_path = os.path.join(output_path, 'krnl_writer.xo') 
    
    #xclbin_path = output_path
    xclbin_path = os.path.join(output_path, 'hil.xclbin')
    connectivity_path = os.path.join(output_path, 'connectivity.cfg') 
            
    script = f"""#!/usr/bin/env bash
set -euo pipefail

PLATFORM="${{PLATFORM:-{platform}}}"
TARGET="${{TARGET:-{target}}}"

mkdir -p {build_dir}
mkdir -p {logs_dir}

echo "======================================"
echo " BUILD XCLBIN"
echo " PLATFORM: $PLATFORM"
echo " TARGET:   $TARGET"
echo "======================================"

echo "[1/3] Compiling reader..."
v++ -c -t "$TARGET" --platform "$PLATFORM" \\
    -k {reader_kernel_name} \\
    -o {reader_xo_path} \\
    {reader_cpp_path} \\
    2>&1 | tee {os.path.join(logs_dir, "compile_reader.log")}

echo "[2/3] Compiling writer..."
v++ -c -t "$TARGET" --platform "$PLATFORM" \\
    -k {writer_kernel_name} \\
    -o {writer_xo_path} \\
    {writer_cpp_path} \\
    2>&1 | tee {os.path.join(logs_dir , "compile_writer.log")}



echo "[3/3] Final XCLBIN link..."
v++ -l -t "$TARGET" --platform "$PLATFORM" \\
    --config {connectivity_path} \\
    -o {xclbin_path} \\
    {reader_xo_path} \\
    {rtl_xo_path} \\
    {writer_xo_path} \\
    2>&1 | tee {os.path.join(logs_dir , "link_xclbin.log")}

echo "======================================"
echo "XCLBIN generated:"
echo "{xclbin_path}"
echo "======================================"
"""
    build_script = os.path.join(output_path, 'build_xclbin.sh')

    write_text(build_script, script)
    make_executable(build_script)
    
    
    print("[OK] build_xclbin.sh generated")

    
     


import sys
import json
import numpy as np


def make_io_dtype():
    io_dtype = np.dtype(
        [
            ("index", np.uint32),
            ("width", np.uint32),
            ("valor", np.uint64),
        ],
        align=True,
    )

    if io_dtype.itemsize != 16:
        raise RuntimeError(
            f"io_dtype incorrect: {io_dtype.itemsize} bytes, expected 16"
        )

    return io_dtype


# -----------------------------------------------------------------------------
# Read values passed from the command line
#
# Example:
#   R=135 G=206 B=235
#
# It also accepts hexadecimal:
#   R=0x87
# -----------------------------------------------------------------------------
def parse_input_values(args):
    values = {}

    for arg in args:
        if "=" not in arg:
            raise RuntimeError(
                f"Incorrect argument '{arg}'. Expected format: nom=valor"
            )

        name, value_str = arg.split("=", 1)

        if name == "":
            raise RuntimeError(
                f"Empty input name in the argument '{arg}'"
            )

        value = int(value_str, 0)
        values[name] = value

    return values


# -----------------------------------------------------------------------------
# Dynamically build the input table from the DUT
# -----------------------------------------------------------------------------
def build_input_table(dut, values, io_dtype):
       
    rows = []
    for index, inp in enumerate(dut.inPorts):
        name = inp.name
        width = inp.wire.getWidth()
        # value from the command line; if not given, default 0
        value = int(values.get(name, 0))
        if width < 64:
            max_value = (1 << width) - 1
            if value < 0 or value > max_value:
                raise RuntimeError(
                    f"Value out of range for '{name}': {value}. "
                    f"Width={width}, allowed range=[0,{max_value}]")
        rows.append((index, width, value))
    return np.array(rows, dtype=io_dtype)


# -----------------------------------------------------------------------------
# Dynamically build the output table from the DUT
# -----------------------------------------------------------------------------
def build_output_table(dut, io_dtype):
    rows = []

    for index, outp in enumerate(dut.outPorts):
        width = outp.wire.getWidth()
        rows.append((index, width, 0))
    return np.array(rows, dtype=io_dtype)


# -----------------------------------------------------------------------------
# Copy the output XRT buffer to a numpy array.
# -----------------------------------------------------------------------------
def copy_bo_to_array(bo, bo_map, dtype, count):
    import pyxrt
    size_bytes = dtype.itemsize * count

    bo.sync(
        pyxrt.xclBOSyncDirection.XCL_BO_SYNC_BO_FROM_DEVICE,
        size_bytes,
        0,
    )

    return np.frombuffer(
        bo_map,
        dtype=dtype,
        count=count,
    ).copy()


# -----------------------------------------------------------------------------
# Show input table
# -----------------------------------------------------------------------------
def print_table_inputs_dynamic(in_table, dut):
    print("\nINPUT TABLE")
    print("#in\tname\twidth\tvalue")
    names_by_index = {i: p.name for i, p in enumerate(dut.inPorts)}
    for row in in_table:
        index = int(row["index"])
        width = int(row["width"])
        value = int(row["valor"])   # 'valor' is the io_dtype field name
        name = names_by_index.get(index, f"in{index}")
        print(f"{index}\t{name}\t{width}\t{value}")


# -----------------------------------------------------------------------------
# Show output table
# -----------------------------------------------------------------------------
def print_table_outputs_dynamic(out_table, dut):
    print("\nOUPUT TABLE")
    print("#out\tname\twidth\tvalue")
    names_by_index = {i: p.name for i, p in enumerate(dut.outPorts)}
    for row in out_table:
        index = int(row["index"])
        width = int(row["width"])
        value = int(row["valor"])   # 'valor' is the io_dtype field name
        name = names_by_index.get(index, f"out{index}")
        print(f"{index}\t{name}\t{width}\t{value}  (0x{value & ((1 << width) - 1):x})")



def run_inference_on_fpga(kernels, buffers, dut, values, io_dtype):
    '''
    Runs ONE inference on the FPGA and returns {output_port_name: value}.
    Single source of truth for the XRT execution, shared by the proxy
    (and optionally by HILPlatform.download(), see note below).
    The device/kernels/buffers are created by the caller and passed in.
    '''
    import pyxrt
    krnl_reader, krnl_mid, krnl_writer = kernels
    bo_in, bo_out, bo_out_map = buffers
    n_out = len(dut.outPorts)

    in_table  = build_input_table(dut, values, io_dtype)
    out_table = build_output_table(dut, io_dtype)

    # Load buffers and push them to the device
    bo_in.write(in_table.tobytes(), 0)
    bo_out.write(out_table.tobytes(), 0)
    bo_in.sync(pyxrt.xclBOSyncDirection.XCL_BO_SYNC_BO_TO_DEVICE,  in_table.nbytes, 0)
    bo_out.sync(pyxrt.xclBOSyncDirection.XCL_BO_SYNC_BO_TO_DEVICE, out_table.nbytes, 0)

    # Launch kernels -- consumer-first ordering (prevents the output-FIFO deadlock)
    run_writer = pyxrt.run(krnl_writer); run_writer.set_arg(n_out, bo_out)
    run_reader = pyxrt.run(krnl_reader); run_reader.set_arg(0, bo_in)
    #run_mid = pyxrt.run(krnl_mid)

    run_reader.start()                       # feeder first
    #try:
    pyxrt.run(krnl_mid).start()       # middle RTL kernel
    #except Exception as e:
    # print('[hil] rtl_kernel has no start() control:', e)
    run_writer.start()                       # consumer last
    run_reader.wait()
    run_writer.wait()
    
    run_reader.start()                       # feeder first
    #try:
    pyxrt.run(krnl_mid).start()       # middle RTL kernel
    #except Exception as e:
    # print('[hil] rtl_kernel has no start() control:', e)
    run_writer.start()                       # consumer last
    run_reader.wait()
    run_writer.wait()
    
    run_reader.start()                       # feeder first
    #try:
    pyxrt.run(krnl_mid).start()       # middle RTL kernel
    #except Exception as e:
    # print('[hil] rtl_kernel has no start() control:', e)
    run_writer.start()                       # consumer last
    run_reader.wait()
    run_writer.wait()

    # Read results back
    result = copy_bo_to_array(bo_out, bo_out_map, io_dtype, len(out_table))
    return {int(r["index"]): int(r["valor"]) for r in result}


class DUTProxyXRT(py4hw.Logic):
    def __init__(self, parent, name, dut, ins, outs, xclbin_path):
        super().__init__(parent, name)
        import pyxrt
        self.dut  = dut                      # only used to read port names/widths
        self.inw  = ins
        self.outw = outs

        # Same port shape as the DUT, so it drops into the graph in its place
        for i, w in enumerate(ins):
            self.inw[i]  = self.addIn(f'in{i}', w)
        for i, w in enumerate(outs):
            self.outw[i] = self.addOut(f'out{i}', w)

        # ---- One-time XRT setup (expensive: NOT repeated per evaluation) ----
        self.io_dtype = make_io_dtype()
        n_out = len(self.dut.outPorts)

        self.device = pyxrt.device(0)
        uuid = self.device.load_xclbin(xclbin_path)
        krnl_reader = pyxrt.kernel(self.device, uuid, 'krnl_reader')
        krnl_mid    = pyxrt.kernel(self.device, uuid, 'rtl_kernel')
        krnl_writer = pyxrt.kernel(self.device, uuid, 'krnl_writer')
        self.kernels = (krnl_reader, krnl_mid, krnl_writer)

        # Persistent buffers, sized once from the DUT tables (reused every run)
        in_table  = build_input_table(self.dut, {}, self.io_dtype)
        out_table = build_output_table(self.dut, self.io_dtype)
        bo_in  = pyxrt.bo(self.device, in_table.nbytes,  pyxrt.bo.flags.normal,
                          krnl_reader.group_id(0))
        bo_out = pyxrt.bo(self.device, out_table.nbytes, pyxrt.bo.flags.normal,
                          krnl_writer.group_id(n_out))
        self.buffers = (bo_in, bo_out, bo_out.map())

    def propagate(self):
        # 1) Read simulation inputs -> dict keyed by DUT input port name
        values = {self.dut.inPorts[i].name: w.get() for i, w in enumerate(self.inw)}

        # 2-3) Run one inference on the FPGA (shared helper)
        by_index = run_inference_on_fpga(self.kernels, self.buffers,
                                         self.dut, values, self.io_dtype)

        # 4) Drive the simulation outputs with the results
        for i, w in enumerate(self.outw):
            self.outw[i].put(by_index[i]) #---


def createHILVitisProxy(dut, parent, name, ins, outs, xclbin_path):
    # Factory mirroring createHILUARTProxy(): builds the redirector in 'parent'
    return DUTProxyXRT(parent, name, dut, ins, outs, xclbin_path)
    


import stat
import shutil
from pathlib import Path




def write_text(output_file, content: str) -> None:

    with open(output_file, 'w') as f:
        f.write(content)

    print(f"[GEN] {output_file}")


def make_executable(p ) -> None:
    path = Path(p)
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def generate_create_project_tcl(dut, dut_files, output_dir):

    num_ins = getDUTValidIns(dut)
    num_outs = getDUTValidOuts(dut)

    rtl_kernel_name = 'rtl_kernel'
    xci_path = f'{output_dir}/{rtl_kernel_name}.srcs/sources_1/ip/{rtl_kernel_name}/{rtl_kernel_name}.xci'

    
    tcl =  f'create_project {rtl_kernel_name} {output_dir} -part xcu55c-fsvh2892-2L-e\n'
    tcl += f'create_ip -name rtl_kernel_wizard -vendor xilinx.com -library ip -version 1.0 -module_name {rtl_kernel_name}\n'

    tcl += f'set_property -dict [list '
    tcl += f'CONFIG.KERNEL_VENDOR {{xilinx.com}} '
    
    for i in range(num_ins):
        tcl += f'CONFIG.AXIS{i:02d}_MODE {{read_only}} '
        tcl += f'CONFIG.AXIS{i:02d}_NUM_BYTES {{8}} '  # 64-bit (8bytes) AXIS to match RTL + reader/writer (avoid 512 default (64bytes))

    for i in range(num_outs):
        tcl += f'CONFIG.AXIS{num_ins+i:02d}_MODE {{write_only}} '
        tcl += f'CONFIG.AXIS{num_ins+i:02d}_NUM_BYTES {{8}} '  # 64-bit (8bytes) AXIS to match RTL + writer (avoid 512 default (64bytes))

    tcl += f'CONFIG.NUM_AXIS {{{num_ins+num_outs}}} '
    tcl += f'       CONFIG.NUM_INPUT_ARGS {{0}} '
    tcl += f'       CONFIG.NUM_M_AXI {{0}} '
    tcl += f'       CONFIG.NUM_RESETS {{1}} '
    tcl += f'       ] [get_ips {rtl_kernel_name}] \n'
    
    tcl += f'''
    generate_target {{instantiation_template}} [get_files {xci_path}]
    update_compile_order -fileset sources_1
    open_example_project -dir {output_dir} [get_ips  {rtl_kernel_name}]
    '''
    write_text(os.path.join(output_dir, 'create_project.tcl'), tcl)
    print("[OK] create_project.tcl generated")

def generate_package_tcl(dut, dut_files, output_dir) -> None:
    rtl_kernel_name = 'rtl_kernel'
    rtl_xo_path = os.path.join(output_dir, rtl_kernel_name + '.xo')

    add_files_lines = "\n".join(
        f'add_files -norecurse [file normalize "{file}"]'
        for file in dut_files
    )



    tcl = f'''
# This is a generated file. Use and modify at your own risk.
################################################################################

set kernel_name    "{rtl_kernel_name}"
set kernel_vendor  "xilinx.com"
set kernel_library "kernel"


proc edit_core {{core}} {{
  set bif      [::ipx::get_bus_interfaces -of $core  "fontread_axi_m"] 
  set bifparam [::ipx::add_bus_parameter -quiet "MAX_BURST_LENGTH" $bif]
  set_property value        256          $bifparam
  set_property value_source constant     $bifparam
  set bifparam [::ipx::add_bus_parameter -quiet "NUM_READ_OUTSTANDING" $bif]
  set_property value        32           $bifparam
  set_property value_source constant     $bifparam
  set bifparam [::ipx::add_bus_parameter -quiet "NUM_WRITE_OUTSTANDING" $bif]
  set_property value        32           $bifparam
  set_property value_source constant     $bifparam


  ::ipx::associate_bus_interfaces -busif "fontread_axi_m" -clock "ap_clk" $core
  ::ipx::associate_bus_interfaces -busif "dataout_axis_m" -clock "ap_clk" $core
  set axis_bif      [::ipx::get_bus_interfaces -of $core  "dataout_axis_m"] 
  set bifparam [::ipx::add_bus_parameter -quiet "TDATA_NUM_BYTES" $axis_bif]
  set_property value        8   $bifparam
  set_property value_source constant     $bifparam
  set bifparam [::ipx::add_bus_parameter -quiet "TUSER_WIDTH" $axis_bif]
  set_property value        0   $bifparam
  set_property value_source constant     $bifparam
  set bifparam [::ipx::add_bus_parameter -quiet "TID_WIDTH" $axis_bif]
  set_property value        0   $bifparam
  set_property value_source constant     $bifparam
  set bifparam [::ipx::add_bus_parameter -quiet "TDEST_WIDTH" $axis_bif]
  set_property value        0   $bifparam
  set_property value_source constant     $bifparam
  set bifparam [::ipx::add_bus_parameter -quiet "HAS_TREADY" $axis_bif]
  set_property value        1   $bifparam
  set_property value_source constant     $bifparam
  set bifparam [::ipx::add_bus_parameter -quiet "HAS_TSTRB" $axis_bif]
  set_property value        0   $bifparam
  set_property value_source constant     $bifparam
  set bifparam [::ipx::add_bus_parameter -quiet "HAS_TKEEP" $axis_bif]
  set_property value        1   $bifparam
  set_property value_source constant     $bifparam
  set bifparam [::ipx::add_bus_parameter -quiet "HAS_TLAST" $axis_bif]
  set_property value        1   $bifparam
  set_property value_source constant     $bifparam
  ::ipx::associate_bus_interfaces -busif "s_axi_control" -clock "ap_clk" $core


  # Specify the freq_hz parameter 
  set clkbif      [::ipx::get_bus_interfaces -of $core "ap_clk"]
  set clkbifparam [::ipx::add_bus_parameter -quiet "FREQ_HZ" $clkbif]
  # Set desired frequency                   
  set_property value 250000000 $clkbifparam
  # set value_resolve_type 'user' if the frequency can vary. 
  set_property value_resolve_type user $clkbifparam
  # set value_resolve_type 'immediate' if the frequency cannot change. 
  # set_property value_resolve_type immediate $clkbifparam
  set mem_map    [::ipx::add_memory_map -quiet "s_axi_control" $core]
  set addr_block [::ipx::add_address_block -quiet "reg0" $mem_map]


  set reg      [::ipx::add_register "CTRL" $addr_block]
  set_property description    "Control signals"    $reg
  set_property address_offset 0x000 $reg
  set_property size           32    $reg
  set field [ipx::add_field AP_START $reg]
    set_property ACCESS {{read-write}} $field
    set_property BIT_OFFSET {{0}} $field
    set_property BIT_WIDTH {{1}} $field
    set_property DESCRIPTION {{Control signal Register for 'ap_start'.}} $field
    set_property MODIFIED_WRITE_VALUE {{modify}} $field
  set field [ipx::add_field AP_DONE $reg]
    set_property ACCESS {{read-only}} $field
    set_property BIT_OFFSET {{1}} $field
    set_property BIT_WIDTH {{1}} $field
    set_property DESCRIPTION {{Control signal Register for 'ap_done'.}} $field
    set_property READ_ACTION {{modify}} $field
  set field [ipx::add_field AP_IDLE $reg]
    set_property ACCESS {{read-only}} $field
    set_property BIT_OFFSET {{2}} $field
    set_property BIT_WIDTH {{1}} $field
    set_property DESCRIPTION {{Control signal Register for 'ap_idle'.}} $field
    set_property READ_ACTION {{modify}} $field
  set field [ipx::add_field AP_READY $reg]
    set_property ACCESS {{read-only}} $field
    set_property BIT_OFFSET {{3}} $field
    set_property BIT_WIDTH {{1}} $field
    set_property DESCRIPTION {{Control signal Register for 'ap_ready'.}} $field
    set_property READ_ACTION {{modify}} $field
  set field [ipx::add_field RESERVED_1 $reg]
    set_property ACCESS {{read-only}} $field
    set_property BIT_OFFSET {{4}} $field
    set_property BIT_WIDTH {{3}} $field
    set_property DESCRIPTION {{Reserved.  0s on read.}} $field
    set_property READ_ACTION {{modify}} $field
  set field [ipx::add_field AUTO_RESTART $reg]
    set_property ACCESS {{read-write}} $field
    set_property BIT_OFFSET {{7}} $field
    set_property BIT_WIDTH {{1}} $field
    set_property DESCRIPTION {{Control signal Register for 'auto_restart'.}} $field
    set_property MODIFIED_WRITE_VALUE {{modify}} $field
  set field [ipx::add_field RESERVED_2 $reg]
    set_property ACCESS {{read-only}} $field
    set_property BIT_OFFSET {{8}} $field
    set_property BIT_WIDTH {{24}} $field
    set_property DESCRIPTION {{Reserved.  0s on read.}} $field
    set_property READ_ACTION {{modify}} $field

  set reg      [::ipx::add_register "GIER" $addr_block]
  set_property description    "Global Interrupt Enable Register"    $reg
  set_property address_offset 0x004 $reg
  set_property size           32    $reg

  set reg      [::ipx::add_register "IP_IER" $addr_block]
  set_property description    "IP Interrupt Enable Register"    $reg
  set_property address_offset 0x008 $reg
  set_property size           32    $reg

  set reg      [::ipx::add_register "IP_ISR" $addr_block]
  set_property description    "IP Interrupt Status Register"    $reg
  set_property address_offset 0x00C $reg
  set_property size           32    $reg

  set reg      [::ipx::add_register -quiet "work_mode" $addr_block]
  set_property address_offset 0x010 $reg
  set_property size           [expr {4*8}]   $reg

  set reg      [::ipx::add_register -quiet "cs_count" $addr_block]
  set_property address_offset 0x018 $reg
  set_property size           [expr {4*8}]   $reg


  set reg      [::ipx::add_register -quiet "time_format" $addr_block]
  set_property address_offset 0x020 $reg
  set_property size           [expr {4*8}]   $reg

  set reg      [::ipx::add_register -quiet "time_set_val" $addr_block]
  set_property address_offset 0x028 $reg
  set_property size           [expr {4*8}]   $reg

  set reg      [::ipx::add_register -quiet "time_set_en" $addr_block]
  set_property address_offset 0x030 $reg
  set_property size           [expr {4*8}]   $reg

  set reg      [::ipx::add_register -quiet "read_addr" $addr_block]
  set_property address_offset 0x038 $reg
  set_property size           [expr {8*8}]   $reg
  set regparam [::ipx::add_register_parameter -quiet {{ASSOCIATED_BUSIF}} $reg] 
  set_property value fontread_axi_m $regparam 

  set_property slave_memory_map_ref "s_axi_control" [::ipx::get_bus_interfaces -of $core "s_axi_control"]

  set_property xpm_libraries {{XPM_CDC XPM_MEMORY XPM_FIFO}} $core
  set_property sdx_kernel true $core
  set_property sdx_kernel_type rtl $core
}}

##############################################################################

proc package_project {{path_to_packaged kernel_vendor kernel_library kernel_name}} {{
  set core [::ipx::package_project -root_dir $path_to_packaged -vendor $kernel_vendor -library $kernel_library -taxonomy "/KernelIP" -import_files -set_current false ]
  foreach user_parameter [list C_S_AXI_CONTROL_ADDR_WIDTH C_S_AXI_CONTROL_DATA_WIDTH C_FONTREAD_AXI_M_ADDR_WIDTH C_FONTREAD_AXI_M_DATA_WIDTH C_DATAOUT_AXIS_M_TDATA_WIDTH] {{
    ::ipx::remove_user_parameter $user_parameter $core
  }}
  ::ipx::create_xgui_files $core
  set_property supported_families {{ }} $core
  set_property auto_family_support_level level_2 $core
  set_property used_in {{out_of_context implementation synthesis}} [::ipx::get_files -type xdc -of_objects [::ipx::get_file_groups "xilinx_anylanguagesynthesis" -of_objects $core] *_ooc.xdc]
  edit_core $core
  ::ipx::update_checksums $core
  ::ipx::check_integrity -kernel $core
  ::ipx::check_integrity -xrt $core
  ::ipx::save_core $core
  ::ipx::unload_core $core
  unset core
}}

##############################################################################

proc package_project_dcp {{path_to_dcp path_to_packaged kernel_vendor kernel_library kernel_name}} {{
  set core [::ipx::package_checkpoint -dcp_file $path_to_dcp -root_dir $path_to_packaged -vendor $kernel_vendor -library $kernel_library -name $kernel_name -taxonomy "/KernelIP" -force]
  edit_core $core
  ::ipx::update_checksums $core
  ::ipx::check_integrity -kernel $core
  ::ipx::check_integrity -xrt $core
  ::ipx::save_core $core
  ::ipx::unload_core $core
  unset core
}}

##############################################################################

proc package_project_dcp_and_xdc {{path_to_dcp path_to_xdc path_to_packaged kernel_vendor kernel_library kernel_name}} {{
  set core [::ipx::package_checkpoint -dcp_file $path_to_dcp -root_dir $path_to_packaged -vendor $kernel_vendor -library $kernel_library -name $kernel_name -taxonomy "/KernelIP" -force]
  edit_core $core
  set rel_path_to_xdc [file join "impl" [file tail $path_to_xdc]]
  set abs_path_to_xdc [file join $path_to_packaged $rel_path_to_xdc]
  file mkdir [file dirname $abs_path_to_xdc]
  file copy $path_to_xdc $abs_path_to_xdc
  set xdcfile [::ipx::add_file $rel_path_to_xdc [::ipx::add_file_group "xilinx_implementation" $core]]
  set_property type "xdc" $xdcfile
  set_property used_in [list "implementation"] $xdcfile
  ::ipx::update_checksums $core
  ::ipx::check_integrity -kernel $core
  ::ipx::check_integrity -xrt $core
  ::ipx::save_core $core
  ::ipx::unload_core $core
  unset core
}}

##############################################################################

#Now run (commented out because the final version is below) 
#package_project {output_dir} xilinx.com kernel {rtl_kernel_name} 
#package_xo  -xo_path {rtl_xo_path} -kernel_name {rtl_kernel_name} -ip_directory {output_dir} -kernel_xml kernel.xml

open_project {output_dir}/rtl_kernel_ex/rtl_kernel_ex.xpr
#AFEGIT:
add_files -norecurse [glob -nocomplain {output_dir}/rtl_kernel_ex/imports/*.v] 
#AFEGIT:
add_files -norecurse [file normalize "{dut_files[1]}"]
update_compile_order -fileset sources_1                                     
source -notrace {output_dir}/rtl_kernel_ex/imports/package_kernel.tcl
package_project {output_dir}/rtl_kernel_ex/rtl_kernel xilinx.com kernel {rtl_kernel_name}
file delete -force {output_dir}/rtl_kernel_ex/exports/{rtl_kernel_name}.xo
package_xo -xo_path {output_dir}/rtl_kernel_ex/exports/{rtl_kernel_name}.xo -kernel_name {rtl_kernel_name} -ip_directory {output_dir}/rtl_kernel_ex/rtl_kernel -kernel_xml {output_dir}/rtl_kernel_ex/imports/kernel.xml


'''

    write_text(os.path.join(output_dir, 'package_rtl_kernel.tcl'), tcl)
    print("[OK] package_rtl_kernel.tcl generated")

