import py4hw
import py4hw.logic.bus.axi as axi
import os

class Axi2Reg(py4hw.Logic):
    """
    Captures the first 64 bits of an AXI4-Stream word into a register.
    Translates the Verilog axi2reg module.
    """
    def __init__(self, parent, name, reset, ap_start, ap_reset, stream:axi.AXI4StreamInterface, q, loaded):
        super().__init__(parent, name)

        # Add Ports
        self.addIn("areset", reset)
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
        py4hw.Reg(self, "reg_data", d=tdata_64, q=q, enable=handshake, reset=reset)

        # 6. Logic for 'loaded'
        # In Verilog, loaded is 1 only during the cycle of the handshake, 
        # but cleared by areset, ap_start, or ap_reset.
        
        # Rearm/Reset logic for loaded: (areset || ap_start || ap_reset)
        
        rearm_final = py4hw.Wire(self, "rearm_final", 1)
        
        py4hw.Or(self, "rearm_final", [reset, ap_start, ap_reset], rearm_final)

        # loaded_next = handshake ? 1 : 0 (effectively just the handshake wire)
        # We use a register to capture the state
        py4hw.Reg(self, "loaded", d=handshake, q=loaded, enable=handshake, reset=rearm_final)


def generate_connectivity(dut, output_path):
    
    
    dut_kernel_name="krnl_rtl"
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

    # ---------------------------------------------------------------------
    # Reader -> DUT
    # ---------------------------------------------------------------------
    # axis00 is reserved for clock / axis2clk.
    # The rest is created from input meta["inputs"].
    # ---------------------------------------------------------------------

    lines.append("# Reader -> DUT")
    lines.append(f"sc={reader_inst}.s_out0:{dut_inst}.axis00 \t # axis00 = clk / axis2clk")

    for i, inp in enumerate(dut.inPorts):
        reader_stream = i + 1
        dut_axis = i + 1

        lines.append(f"sc={reader_inst}.s_out{reader_stream}:{dut_inst}.axis{dut_axis:02d} \t # axis{dut_axis:02d} = {inp.name}")

    lines.append("")

    # ---------------------------------------------------------------------
    # DUT -> Writer
    # ---------------------------------------------------------------------
    # Output start after inputs:
    #   axis00 + number of inputs of the DUT
    # ---------------------------------------------------------------------

    first_output_axis = 1 + len(dut.inPorts)

    lines.append("# DUT -> Writer")

    for i, outp in enumerate(dut.outPorts):
        dut_axis = first_output_axis + i

        lines.append(f"sc={dut_inst}.axis{dut_axis:02d}:{writer_inst}.s_in{i} \t # axis{dut_axis:02d} = {outp.name}")

    output_file = os.path.join(output_path, 'connectivity.cfg') 
    #output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        f.write("\n".join(lines) + "\n")

    print(f"File created: {output_file}")




def generate_reader(dut, output_path):
    

    stream_args = [] # This are the parameters of the stream kernel
    stream_pragmas = []
    writes = []

    # s_out0 es reserva per al clock / axis2clk.
    # La resta de streams corresponen a les entrades del DUT.
    total_out_streams = 1 + len(dut.inPorts)

    link = ''

    for stream_id in range(total_out_streams):
        
        if stream_id == 0:
            comment = "clk"
        else:
            inp = dut.inPorts[stream_id -1]
            comment = inp.name

        stream_args.append(f"    hls::stream<ap_uint<64>>& s_out{stream_id}{link}  // {comment}")
        
        link = ','

    for i in range(total_out_streams):
        stream_pragmas.append(f"#pragma HLS INTERFACE axis port=s_out{i}")

    # in[0] es reserva per al clock.
    # in[1+i] correspon a l'entrada i del DUT.
    #writes.append("    ap_uint<64> clk = 0;")
    #writes.append("    clk = (ap_uint<64>)in[0].valor;")
    writes.append("    s_out0.write(in[0].valor);")
    

    for i, inp in enumerate(dut.inPorts):
        stream_id = i + 1
        table_index = i + 1
        name = inp.name

        #writes.append(f"    // {name}")
        #writes.append(f"    ap_uint<64> v_{name} = 0;")
        #writes.append(            f"    v_{name} = (ap_uint<64>)in[{table_index}].valor;"        )
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
#pragma HLS INTERFACE s_axilite port=num bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control

{chr(10).join(stream_pragmas)}

    // Format generic de la taula d'entrada:
    //   in[0] = clk / nombre de cicles
"""

    for i, inp in enumerate(dut.inPorts):
        code += f"    //   in[{i+1}] = {inp.name} ({inp.wire.getWidth()} bits)\n"

    code += f"""
{chr(10).join(writes)}
}}
"""

    
    output_file = os.path.join(output_path, 'krnl_reader.cpp') 
    #output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        f.write(code)

    print(f"File created: {output_file}")




def generate_writer(dut, output_path):
    

    stream_args = []
    stream_pragmas = []
    reads = []


    for i, outp in enumerate(dut.outPorts):
        # Sempre posem coma despres de cada stream, perque despres venen out i num.
        stream_args.append(f"    hls::stream<ap_uint<64>>& s_in{i},  // {outp.name}")
        stream_pragmas.append(f"#pragma HLS INTERFACE axis port=s_in{i}")

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

extern "C" void krnl_writer_generic(
{chr(10).join(stream_args)}
    io_t* out,
) {{
{chr(10).join(stream_pragmas)}

#pragma HLS INTERFACE m_axi port=out offset=slave bundle=gmem
#pragma HLS INTERFACE s_axilite port=out bundle=control
#pragma HLS INTERFACE s_axilite port=num bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control

    // Format generic de la taula de sortida:
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
    #output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        f.write(code)
    
    print(f"File created: {output_file}")
    
    
    
'''
#!/usr/bin/env python3
# -*- coding: latin-1 -*-

import sys
import json
import numpy as np
import pyxrt


# -----------------------------------------------------------------------------
# Tipus de dades equivalent (hardcoded per es part del protocol no del DUT especific):
#
# struct alignas(16) io_t {
#     uint32_t index;
#     uint32_t width;
#     uint64_t valor;
# };
#
# Cada fila ocupa 16 bytes.
# -----------------------------------------------------------------------------


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
            f"io_dtype incorrecte: {io_dtype.itemsize} bytes, esperat 16"
        )

    return io_dtype


# -----------------------------------------------------------------------------
# Carregar fitxer de metadades JSON
# -----------------------------------------------------------------------------


def load_metadata(meta_path):
    with open(meta_path, "rb") as f:
        raw = f.read()

    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")

    meta = json.loads(text)

    required_fields = [
        "kernels",
        "args",
        "inputs",
        "outputs_raw",
    ]

    for field in required_fields:
        if field not in meta:
            raise RuntimeError(
                f"Falta el camp obligatori '{field}' al fitxer JSON"
            )

    return meta

# -----------------------------------------------------------------------------
# Llegir valors passats per terminal
#
# Exemple:
#   R=135 G=206 B=235
#
# Tamb accepta hexadecimal:
#   R=0x87
# -----------------------------------------------------------------------------


def parse_input_values(args):
    values = {}

    for arg in args:
        if "=" not in arg:
            raise RuntimeError(
                f"Argument incorrecte '{arg}'. Format esperat: nom=valor"
            )

        name, value_str = arg.split("=", 1)

        if name == "":
            raise RuntimeError(
                f"Nom d'entrada buit a l'argument '{arg}'"
            )

        value = int(value_str, 0)
        values[name] = value

    return values


# -----------------------------------------------------------------------------
# Construir la taula d'entrada dinamicament a partir del JSON
# -----------------------------------------------------------------------------


def build_input_table(meta, values, io_dtype):
    rows = []

    for inp in meta["inputs"]:
        index = int(inp["index"])
        name = inp["name"]
        width = int(inp["width"])

        # Si l'usuari passa el valor per terminal, es fa servir aquell.
        # Si no, es fa servir el valor default del JSON.
        # Si tampoc existeix default, es posa 0.
        value = int(values.get(name, inp.get("default", 0)))

        # Comprovacio de rang segons l'amplada de bits
        if width < 64:
            max_value = (1 << width) - 1

            if value < 0 or value > max_value:
                raise RuntimeError(
                    f"Valor fora de rang per a '{name}': {value}. "
                    f"Width={width}, rang perms=[0,{max_value}]"
                )

        rows.append((index, width, value))

    return np.array(rows, dtype=io_dtype)


# -----------------------------------------------------------------------------
# Construir la taula de sortida dinamicament a partir del JSON
# -----------------------------------------------------------------------------


def build_output_table(meta, io_dtype):
    rows = []

    for out in meta["outputs_raw"]:
        index = int(out["index"])
        width = int(out["width"])

        rows.append((index, width, 0))

    return np.array(rows, dtype=io_dtype)


# -----------------------------------------------------------------------------
# Copiar buffer XRT de sortida cap a array numpy
# -----------------------------------------------------------------------------


def copy_bo_to_array(bo, bo_map, dtype, count):
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
# Mostrar taula d'entrades
# -----------------------------------------------------------------------------


def print_table_inputs_dynamic(in_table, meta):
    print("\nTAULA D'ENTRADES")
    print("#entrada\tname\twidth\tvalor")

    names_by_index = {}

    for inp in meta["inputs"]:
        names_by_index[int(inp["index"])] = inp["name"]

    for row in in_table:
        index = int(row["index"])
        width = int(row["width"])
        value = int(row["valor"])

        name = names_by_index.get(index, f"entrada{index}")

        print(f"{index}\t\t{name}\t{width}\t{value}")


# -----------------------------------------------------------------------------
# Mostrar taula de sortides
# -----------------------------------------------------------------------------


def print_table_outputs_dynamic(out_table, meta):
    print("\nTAULA DE SORTIDES")
    print("#sortida\twidth\tvalor")

    # Si el JSON te outputs_display, es mostra la interpretacio final.
    # En el meu cas del RGB2YCbCr:
    #   raw[2] -> Y
    #   raw[1] -> Cb
    #   raw[0] -> Cr
    if "outputs_display" in meta:
        for i, out in enumerate(meta["outputs_display"]):
            name = out["name"]
            pos = int(out["from_raw"])

            if pos < 0 or pos >= len(out_table):
                raise RuntimeError(
                    f"outputs_display incorrecte: from_raw={pos} "
                    f"per noms hi ha {len(out_table)} sortides raw"
                )

            value = int(out_table[pos]["valor"])
            width = int(out_table[pos]["width"])

            print(
                f"sortida{i}\t{width}\t{value} "
                f"(0x{value & 0xFF:02x})  -> {name}"
            )

        print("\nINTERPRETACIO DE SORTIDA")

        for i, out in enumerate(meta["outputs_display"]):
            name = out["name"]
            pos = int(out["from_raw"])
            value = int(out_table[pos]["valor"])

            print(f"sortida{i} = {name} = {value}")

    # Si no hi ha outputs_display, es mostra l'ordre raw tal com arriba.
    else:
        for i, row in enumerate(out_table):
            width = int(row["width"])
            value = int(row["valor"])

            print(
                f"sortida{i}\t{width}\t{value} "
                f"(0x{value & 0xFF:02x})"
            )


# -----------------------------------------------------------------------------
# Programa principal
# -----------------------------------------------------------------------------


def main():
    if len(sys.argv) < 3:
        print(
            f"Us:\n"
            f"  {sys.argv[0]} build_hw/kernel.xclbin meta.json R=135 G=206 B=235\n\n"
            f"Exemple:\n"
            f"  {sys.argv[0]} build_hw/kernel.xclbin src/meta/rgb2ycbcr_meta.json R=135 G=206 B=235",
            file=sys.stderr,
        )
        return 1

    xclbin_path = sys.argv[1]
    meta_path = sys.argv[2]

    # -------------------------------------------------------------------------
    # Llegir metadades i valors d'entrada
    # -------------------------------------------------------------------------

    meta = load_metadata(meta_path)
    values = parse_input_values(sys.argv[3:])

    io_dtype = make_io_dtype()

    # -------------------------------------------------------------------------
    # Crear taules d'entrada i sortida
    # -------------------------------------------------------------------------

    in_table = build_input_table(meta, values, io_dtype)
    out_table = build_output_table(meta, io_dtype)

    in_size_bytes = in_table.nbytes
    out_size_bytes = out_table.nbytes

    print("\nHOST XRT DINAMIC")
    print(f"DUT/projecte: {meta.get('name', 'sense_nom')}")
    print(f"xclbin: {xclbin_path}")
    print(f"metadata: {meta_path}")

    print_table_inputs_dynamic(in_table, meta)

    # -------------------------------------------------------------------------
    # Obrir FPGA i carregar xclbin
    # -------------------------------------------------------------------------

    print(f"\nCarregant xclbin: {xclbin_path}")

    device = pyxrt.device(0)
    uuid = device.load_xclbin(xclbin_path)

    # -------------------------------------------------------------------------
    # Obrir kernels segons el JSON
    # -------------------------------------------------------------------------

    reader_name = meta["kernels"]["reader"]
    mid_name = meta["kernels"]["mid"]
    writer_name = meta["kernels"]["writer"]

    print("\nObrint kernels:")
    print(f"  reader: {reader_name}")
    print(f"  mid:    {mid_name}")
    print(f"  writer: {writer_name}")

    krnl_reader = pyxrt.kernel(device, uuid, reader_name)
    krnl_mid = pyxrt.kernel(device, uuid, mid_name)
    krnl_writer = pyxrt.kernel(device, uuid, writer_name)

    # -------------------------------------------------------------------------
    # Llegir indexs dels arguments des del JSON
    # -------------------------------------------------------------------------

    reader_arg_in = int(meta["args"]["reader"]["in"])
    reader_arg_num = int(meta["args"]["reader"]["num"])

    writer_arg_out = int(meta["args"]["writer"]["out"])
    writer_arg_num = int(meta["args"]["writer"]["num"])

    print("\nArguments:")
    print(f"  reader in  -> arg {reader_arg_in}")
    print(f"  reader num -> arg {reader_arg_num}")
    print(f"  writer out -> arg {writer_arg_out}")
    print(f"  writer num -> arg {writer_arg_num}")

    # -------------------------------------------------------------------------
    # Crear buffers XRT
    # -------------------------------------------------------------------------

    bo_in = pyxrt.bo(
        device,
        in_size_bytes,
        pyxrt.bo.flags.normal,
        krnl_reader.group_id(reader_arg_in),
    )

    bo_out = pyxrt.bo(
        device,
        out_size_bytes,
        pyxrt.bo.flags.normal,
        krnl_writer.group_id(writer_arg_out),
    )

    # -------------------------------------------------------------------------
    # Copiar dades host -> FPGA
    # -------------------------------------------------------------------------

    bo_in.write(in_table.tobytes(), 0)
    bo_out.write(out_table.tobytes(), 0)

    bo_in.sync(
        pyxrt.xclBOSyncDirection.XCL_BO_SYNC_BO_TO_DEVICE,
        in_size_bytes,
        0,
    )

    bo_out.sync(
        pyxrt.xclBOSyncDirection.XCL_BO_SYNC_BO_TO_DEVICE,
        out_size_bytes,
        0,
    )

    # Mapejar buffer de sortida per llegir-lo despres
    bo_out_map = bo_out.map()

    # -------------------------------------------------------------------------
    # Crear runs
    # -------------------------------------------------------------------------

    run_reader = pyxrt.run(krnl_reader)
    run_mid = pyxrt.run(krnl_mid)
    run_writer = pyxrt.run(krnl_writer)

    run_reader.set_arg(reader_arg_in, bo_in)
    run_reader.set_arg(reader_arg_num, int(len(in_table)))

    run_writer.set_arg(writer_arg_out, bo_out)
    run_writer.set_arg(writer_arg_num, int(len(out_table)))

    # El kernel RTL del mig nomes te AXI-Stream i control AXI-Lite.
    # Els AXI-Stream ja estan connectats al connectivity.cfg.
    # Per aixo no fem set_arg() per al kernel del mig.

    # -------------------------------------------------------------------------
    # Executar kernels
    # -------------------------------------------------------------------------

    print("\nExecutant writer...")
    run_writer.start()

    print("Executant RTL mid...")
    run_mid.start()

    print("Executant reader...")
    run_reader.start()

    print("\nEsperant reader...")
    run_reader.wait()
    print("Reader acabat.")

    print("Esperant RTL mid...")
    run_mid.wait()
    print("RTL mid acabat.")

    print("Esperant writer...")
    run_writer.wait()
    print("Writer acabat.")

    print("\nExecucio acabada.")

    # -------------------------------------------------------------------------
    # Llegir resultats FPGA -> host
    # -------------------------------------------------------------------------

    out_table_result = copy_bo_to_array(
        bo_out,
        bo_out_map,
        io_dtype,
        len(out_table),
    )

    print_table_outputs_dynamic(out_table_result, meta)

    return 0


'''    