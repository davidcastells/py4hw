import py4hw
import py4hw.logic.bus.axi as axi
import os

class Axi2Reg(py4hw.Logic):
    
    def __init__(self, parent, name, reset, ap_start, ap_reset, stream:axi.AXI4StreamInterface, q, loaded):
        '''
        Captures the first 64 bits of an AXI4-Stream word into a register.
        Translates the Verilog axi2reg module.

        Parameters
        ----------
        parent : Logic
            Parent object.
        name : str
            instance name.
        reset : Wire
            reset signal.
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


#---------------------------------------------------------------------------
# Ariadna
from __future__ import annotations

import argparse
import importlib
import stat
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# ============================================================
# CONFIGURACI
# ============================================================

@dataclass
class BuildConfig:
    dut_name: str = "RGB2YCrCb"
    rtl_kernel_name: str = "rtl_rgb2ycbcr"
    reader_kernel_name: str = "krnl_reader"
    writer_kernel_name: str = "krnl_writer"

    platform: str = "xilinx_u55c_gen3x16_xdma_3_202210_1"
    target: str = "hw"

    generated_dir: Path = Path("/tmp/generated")
    build_dir: Path = Path("/tmp/build_hw")

    #aix ho poso pq estic treballant
    #amb el RTL .xo del projecte que vaig crear jo
    existing_rtl_xo: Path | None = None

    @property
    def rtl_dir(self) -> Path:
        return self.generated_dir / "rtl"

    @property
    def hls_dir(self) -> Path:
        return self.generated_dir / "hls"

    @property
    def cfg_dir(self) -> Path:
        return self.generated_dir / "cfg"

    @property
    def tcl_dir(self) -> Path:
        return self.generated_dir / "tcl"

    @property
    def scripts_dir(self) -> Path:
        return self.generated_dir / "scripts"

    @property
    def logs_dir(self) -> Path:
        return self.build_dir / "logs"

    @property
    def dut_verilog_path(self) -> Path:
        return self.rtl_dir / f"{self.dut_name}.v"

    @property
    def wrapper_verilog_path(self) -> Path:
        return self.rtl_dir / f"{self.rtl_kernel_name}.v"

    @property
    def reader_cpp_path(self) -> Path:
        return self.hls_dir / f"{self.reader_kernel_name}_generic.cpp"

    @property
    def writer_cpp_path(self) -> Path:
        return self.hls_dir / f"{self.writer_kernel_name}_generic.cpp"

    @property
    def connectivity_path(self) -> Path:
        return self.cfg_dir / "connectivity.cfg"

    @property
    def package_tcl_path(self) -> Path:
        return self.tcl_dir / "package_rtl_kernel.tcl"

    @property
    def build_script_path(self) -> Path:
        return self.scripts_dir / "build_xclbin.sh"

    @property
    def reader_xo_path(self) -> Path:
        return self.build_dir / f"{self.reader_kernel_name}.xo"

    @property
    def writer_xo_path(self) -> Path:
        return self.build_dir / f"{self.writer_kernel_name}.xo"

    @property
    def rtl_xo_path(self) -> Path:
        return self.build_dir / f"{self.rtl_kernel_name}.xo"

    @property
    def xclbin_path(self) -> Path:
        return self.build_dir / "kernel.xclbin"


# ============================================================
# UTILITATS
# ============================================================

def mkdirs(cfg: BuildConfig) -> None:
    for directory in [
        cfg.generated_dir,
        cfg.rtl_dir,
        cfg.hls_dir,
        cfg.cfg_dir,
        cfg.tcl_dir,
        cfg.scripts_dir,
        cfg.build_dir,
        cfg.logs_dir,
    ]:
        directory.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"[GEN] {path}")


def make_executable(path: Path) -> None:
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def p(path: Path) -> str:
    return path.as_posix()


# ============================================================
# EXTRACCI DE METADATA A PARTIR DELS WIRES
# ============================================================

def get_wire_name(wire: Any) -> str:
    """
    Intenta obtenir el nom d'un wire py4hw.
    S'ha fet flexible perqu py4hw pot guardar el nom amb atributs diferents.
    """

    for attr in ["name", "_name"]:
        if hasattr(wire, attr):
            value = getattr(wire, attr)
            if callable(value):
                value = value()
            return str(value)

    for method in ["getName", "get_name"]:
        if hasattr(wire, method):
            return str(getattr(wire, method)())

    raise ValueError(f"No puc obtenir el nom del wire: {wire}")


def get_wire_width(wire: Any) -> int:
    """
    Intenta obtenir l'amplada d'un wire py4hw.
    Si no troba amplada, assumeix 1 bit.
    """

    for attr in ["width", "_width", "bits", "size"]:
        if hasattr(wire, attr):
            value = getattr(wire, attr)
            if callable(value):
                value = value()
            return int(value)

    for method in ["getWidth", "get_width", "getBits"]:
        if hasattr(wire, method):
            return int(getattr(wire, method)())

    return 1


def metadata_from_ports(
    dut: Any,
    inputs: list[Any],
    outputs: list[Any],
    dut_name: str,
) -> dict[str, Any]:
    """
    Genera una metadata interna a partir dels objectes wire.

    Aquesta metadata es calcula automticament a partir de:
        - llista de wires d'entrada
        - llista de wires de sortida
    """

    meta = {
        "name": dut_name,
        "instance_name": getattr(dut, "name", "dut"),
        "inputs": [],
        "outputs": [],
    }

    for index, wire in enumerate(inputs):
        meta["inputs"].append({
            "index": index,
            "name": get_wire_name(wire),
            "width": get_wire_width(wire),
        })

    for index, wire in enumerate(outputs):
        meta["outputs"].append({
            "index": index,
            "name": get_wire_name(wire),
            "width": get_wire_width(wire),
        })

    return meta


# ============================================================
# GENERACI DEL VERILOG DEL DUT
# ============================================================

def generate_dut_verilog(hw: Any, dut: Any, cfg: BuildConfig) -> None:
    """
    Genera el Verilog del DUT a partir de py4hw.

    Si ja tenim una funci prpia tools/generate_dut_verilog.py,
    aquesta tindr prioritat.
    """

    try:
        from tools.generate_dut_verilog import generate_dut_verilog as gen

        gen(hw=hw, dut=dut, output_file=cfg.dut_verilog_path)
        print("[OK] Verilog del DUT generat amb tools.generate_dut_verilog")
        return

    except ImportError:
        pass

    try:
        import py4hw

        generator = py4hw.VerilogGenerator(hw)

        if hasattr(generator, "getVerilog"):
            verilog = generator.getVerilog()
        elif hasattr(generator, "generate"):
            verilog = generator.generate()
        else:
            raise AttributeError(
                "py4hw.VerilogGenerator no t getVerilog() ni generate()."
            )

        write_text(cfg.dut_verilog_path, verilog)
        print("[OK] Verilog del DUT generat amb py4hw.VerilogGenerator")

    except Exception as exc:
        raise RuntimeError(
            "No he pogut generar el Verilog del DUT. "
            "Adapta generate_dut_verilog() al vostre flux de py4hw."
        ) from exc


# ============================================================
# CRIDES ALS GENERADORS EXISTENTS
# ============================================================

def generate_reader(meta: dict[str, Any], cfg: BuildConfig) -> None:
    from tools.generate_reader_generic import generate_reader_generic as gen

    gen(
        meta=meta,
        output_path=cfg.reader_cpp_path,
        kernel_name=cfg.reader_kernel_name,
    )

    print(f"[OK] {cfg.reader_cpp_path} generat")


def generate_writer(meta: dict[str, Any], cfg: BuildConfig) -> None:
    from tools.generate_writer_generic import generate_writer_generic as gen

    gen(
        meta=meta,
        output_path=cfg.writer_cpp_path,
        kernel_name=cfg.writer_kernel_name,
    )

    print(f"[OK] {cfg.writer_cpp_path} generat")


def generate_connectivity(meta: dict[str, Any], cfg: BuildConfig) -> None:
    from tools.generate_connectivity_generic import generate_connectivity_generic as gen

    gen(
        meta=meta,
        rtl_kernel_name=cfg.rtl_kernel_name,
        reader_kernel_name=cfg.reader_kernel_name,
        writer_kernel_name=cfg.writer_kernel_name,
        output_path=cfg.connectivity_path,
    )

    print("[OK] connectivity.cfg generat")


def generate_rtl_wrapper(meta: dict[str, Any], cfg: BuildConfig) -> None:
    """
    Aquest generador ha de crear el wrapper RTL que instancia el DUT
    i connecta axi2reg / reg2axi / axi2clk.

    Si el profe ja t aquest generador, noms cal adaptar l'import.
    """

    from tools.generate_rtl_wrapper import generate_rtl_wrapper as gen

    gen(
        meta=meta,
        dut_name=cfg.dut_name,
        rtl_kernel_name=cfg.rtl_kernel_name,
        output_file=cfg.wrapper_verilog_path,
        rtl_dir=cfg.rtl_dir,
    )

    print("[OK] wrapper RTL generat")


# ============================================================
# TCL PER EMPAQUETAR EL RTL COM A .XO
# ============================================================

def collect_rtl_files(cfg: BuildConfig) -> list[Path]:
    files = []
    files.extend(sorted(cfg.rtl_dir.glob("*.v")))
    files.extend(sorted(cfg.rtl_dir.glob("*.sv")))

    if not files:
        raise FileNotFoundError(f"No hi ha fitxers RTL a {cfg.rtl_dir}")

    return files


def generate_package_tcl(cfg: BuildConfig) -> None:
    rtl_files = collect_rtl_files(cfg)

    add_files_lines = "\n".join(
        f'add_files -norecurse [file normalize "{p(file)}"]'
        for file in rtl_files
    )

    tcl = f"""# Auto-generated package RTL TCL

set kernel_name "{cfg.rtl_kernel_name}"
set top_module  "{cfg.rtl_kernel_name}"

set build_dir [file normalize "{p(cfg.build_dir)}"]
set xo_path   [file normalize "{p(cfg.rtl_xo_path)}"]
set proj_dir  [file normalize "$build_dir/vivado_$kernel_name"]
set ip_dir    [file normalize "$build_dir/ip_$kernel_name"]

file mkdir $build_dir
file delete -force $proj_dir
file delete -force $ip_dir
file delete -force $xo_path

# ATENCI:
# Aquesta part est posada per U55C.
# Si es fs servir una altra placa, s'hauria de canviar el part.
create_project -force $kernel_name $proj_dir -part xcu55c-fsvh2892-2L-e

{add_files_lines}

set_property top $top_module [current_fileset]
update_compile_order -fileset sources_1

# Comprovaci RTL
synth_design -rtl -top $top_module

# Empaquetar com a IP
ipx::package_project \\
    -root_dir $ip_dir \\
    -vendor user.org \\
    -library user \\
    -taxonomy /UserIP \\
    -import_files \\
    -set_current true

set core [ipx::current_core]
set_property sdx_kernel true $core
set_property sdx_kernel_type rtl $core
set_property vitis_drc {{ctrl_protocol ap_ctrl_hs}} $core

ipx::save_core $core
close_project

# Generar el fitxer .xo del kernel RTL
package_xo -force \\
    -xo_path $xo_path \\
    -kernel_name $kernel_name \\
    -ip_directory $ip_dir \\
    -ctrl_protocol ap_ctrl_hs

puts "XO RTL generat a: $xo_path"
"""

    write_text(cfg.package_tcl_path, tcl)
    print("[OK] package_rtl_kernel.tcl generat")


# ============================================================
# SCRIPT DE BUILD PER CREAR EL XCLBIN
# ============================================================

def generate_build_script(cfg: BuildConfig) -> None:
    if cfg.existing_rtl_xo is None:
        rtl_step = f"""echo "[3/4] Empaquetant RTL..."
vivado -mode batch -source {p(cfg.package_tcl_path)} \\
    2>&1 | tee {p(cfg.logs_dir / "package_rtl.log")}
"""
    else:
        rtl_step = f"""echo "[3/4] Saltant packaging RTL..."
echo "S'utilitza un .xo RTL existent: {p(cfg.rtl_xo_path)}"

if [ ! -f "{p(cfg.rtl_xo_path)}" ]; then
    echo "ERROR: No existeix el fitxer RTL XO esperat: {p(cfg.rtl_xo_path)}"
    exit 1
fi
"""

    script = f"""#!/usr/bin/env bash
set -euo pipefail

PLATFORM="${{PLATFORM:-{cfg.platform}}}"
TARGET="${{TARGET:-{cfg.target}}}"

mkdir -p {p(cfg.build_dir)}
mkdir -p {p(cfg.logs_dir)}

echo "======================================"
echo " BUILD XCLBIN"
echo " PLATFORM: $PLATFORM"
echo " TARGET:   $TARGET"
echo "======================================"

echo "[1/4] Compilant reader..."
v++ -c -t "$TARGET" --platform "$PLATFORM" \\
    -k {cfg.reader_kernel_name} \\
    -o {p(cfg.reader_xo_path)} \\
    {p(cfg.reader_cpp_path)} \\
    2>&1 | tee {p(cfg.logs_dir / "compile_reader.log")}

echo "[2/4] Compilant writer..."
v++ -c -t "$TARGET" --platform "$PLATFORM" \\
    -k {cfg.writer_kernel_name} \\
    -o {p(cfg.writer_xo_path)} \\
    {p(cfg.writer_cpp_path)} \\
    2>&1 | tee {p(cfg.logs_dir / "compile_writer.log")}

{rtl_step}

echo "[4/4] Link final XCLBIN..."
v++ -l -t "$TARGET" --platform "$PLATFORM" \\
    --config {p(cfg.connectivity_path)} \\
    -o {p(cfg.xclbin_path)} \\
    {p(cfg.reader_xo_path)} \\
    {p(cfg.rtl_xo_path)} \\
    {p(cfg.writer_xo_path)} \\
    2>&1 | tee {p(cfg.logs_dir / "link_xclbin.log")}

echo "======================================"
echo "XCLBIN generat:"
echo "{p(cfg.xclbin_path)}"
echo "======================================"
"""

    write_text(cfg.build_script_path, script)
    make_executable(cfg.build_script_path)
    print("[OK] build_xclbin.sh generat")


# ============================================================
# README DE SORTIDA, per tenir un "summary"
# ============================================================

def generate_readme(cfg: BuildConfig, meta: dict[str, Any]) -> None:
    lines = []

    lines.append("# Projecte generat automticament\n")
    lines.append(f"- DUT: `{cfg.dut_name}`")
    lines.append(f"- Kernel RTL: `{cfg.rtl_kernel_name}`")
    lines.append(f"- Reader: `{cfg.reader_kernel_name}`")
    lines.append(f"- Writer: `{cfg.writer_kernel_name}`")
    lines.append("")

    lines.append("## Entrades detectades\n")
    for port in meta["inputs"]:
        lines.append(f"- `{port['name']}`: {port['width']} bits")

    lines.append("\n## Sortides detectades\n")
    for port in meta["outputs"]:
        lines.append(f"- `{port['name']}`: {port['width']} bits")

    lines.append("\n## Fitxers principals\n")
    lines.append(f"- `{cfg.dut_verilog_path}`")
    lines.append(f"- `{cfg.wrapper_verilog_path}`")
    lines.append(f"- `{cfg.reader_cpp_path}`")
    lines.append(f"- `{cfg.writer_cpp_path}`")
    lines.append(f"- `{cfg.connectivity_path}`")
    lines.append(f"- `{cfg.package_tcl_path}`")
    lines.append(f"- `{cfg.build_script_path}`")

    lines.append("\n## Com compilar\n")
    lines.append("```bash")
    lines.append(f"./{cfg.build_script_path}")
    lines.append("```")

    write_text(cfg.generated_dir / "README_generated.md", "\n".join(lines))


# ============================================================
# FLUX PRINCIPAL
# ============================================================

def generate_files_from_dut(
    hw: Any,
    dut: Any,
    inputs: list[Any],
    outputs: list[Any],
    cfg: BuildConfig,
) -> None:
    """
    Flux principal:
        DUT rebut
        -> metadata a partir dels wires
        -> Verilog
        -> wrapper
        -> reader/writer
        -> connectivity
        -> TCL
        -> build script
    """

    print("\n====================================")
    print(" GENERACI FITXERS PER XCLBIN")
    print("====================================\n")

    mkdirs(cfg)

    print("[1/8] Extraient metadata del DUT...")
    meta = metadata_from_ports(
        dut=dut,
        inputs=inputs,
        outputs=outputs,
        dut_name=cfg.dut_name,
    )

    if cfg.existing_rtl_xo is None:
        print("[2/8] Generant Verilog del DUT...")
        generate_dut_verilog(hw, dut, cfg)

        print("[3/8] Generant wrapper RTL...")
        generate_rtl_wrapper(meta, cfg)

        print("[7/8] Generant TCL de packaging RTL...")
        generate_package_tcl(cfg)

    else:
        print("[2/8] Saltant generacio de Verilog del DUT...")
        print("[3/8] Usant RTL .xo existent...")

        cfg.build_dir.mkdir(parents=True, exist_ok=True)

        if not cfg.existing_rtl_xo.exists():
            raise FileNotFoundError(
                f"No existeix el .xo RTL indicat: {cfg.existing_rtl_xo}\n"
                "Comprova la ruta amb: find . -name '*.xo'"
            )

        shutil.copy2(cfg.existing_rtl_xo, cfg.rtl_xo_path)

        print(f"[OK] RTL .xo copiat a {cfg.rtl_xo_path}")


    print("[4/8] Generant reader.cpp...")
    generate_reader(meta, cfg)

    print("[5/8] Generant writer.cpp...")
    generate_writer(meta, cfg)

    print("[6/8] Generant connectivity.cfg...")
    generate_connectivity(meta, cfg)

    print("[8/8] Generant script de build...")
    generate_build_script(cfg)
    generate_readme(cfg, meta)

    print("\n====================================")
    print(" FITXERS GENERATS CORRECTAMENT")
    print("====================================")
    print(f"Directori generat: {cfg.generated_dir}")
    print(f"Per compilar:")
    print(f"  ./{cfg.build_script_path}")


# ============================================================
# EXECUCI DES DE TERMINAL
# ============================================================

def load_factory(factory_path: str):
    """
    Carrega una funci amb format:
        module.submodule:function

    Exemple:
        duts.dut_object:create_rgb2ycrcb_dut
    """

    if ":" not in factory_path:
        raise ValueError(
            "Format incorrecte. Usa: module.submodule:function"
        )

    module_name, function_name = factory_path.split(":", 1)
    module = importlib.import_module(module_name)
    return getattr(module, function_name)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dut-factory",
        default="duts.dut_object:create_rgb2ycrcb_dut",
        help="Funci que retorna hw, dut, inputs, outputs",
    )

    parser.add_argument("--dut-name", default="RGB2YCrCb")
    parser.add_argument("--rtl-kernel-name", default="rtl_rgb2ycbcr")
    parser.add_argument("--reader-kernel-name", default="krnl_reader")
    parser.add_argument("--writer-kernel-name", default="krnl_writer")
    parser.add_argument("--platform", default="xilinx_u55c_gen3x16_xdma_3_202210_1")
    parser.add_argument("--target", default="hw", choices=["hw", "hw_emu", "sw_emu"])
    parser.add_argument("--generated-dir", default="generated")
    parser.add_argument("--build-dir", default="build_hw")
    parser.add_argument(
        "--existing-rtl-xo",
        default=None,
        help="Ruta a un .xo RTL existent per reutilitzar-lo en comptes de generar-lo amb Vivado",
    )

    return parser.parse_args()


def main_ariadna() -> None:
    args = parse_args()


    cfg = BuildConfig(
        dut_name=args.dut_name,
        rtl_kernel_name=args.rtl_kernel_name,
        reader_kernel_name=args.reader_kernel_name,
        writer_kernel_name=args.writer_kernel_name,
        platform=args.platform,
        target=args.target,
        generated_dir=Path(args.generated_dir),
        build_dir=Path(args.build_dir),
        existing_rtl_xo=Path(args.existing_rtl_xo) if args.existing_rtl_xo else None,
    )

    factory = load_factory(args.dut_factory)
    result = factory()

    if not isinstance(result, tuple) or len(result) != 4:
        raise ValueError(
            "La funci del DUT ha de retornar exactament: "
            "hw, dut, inputs, outputs"
        )

    hw, dut, inputs, outputs = result

    generate_files_from_dut(
        hw=hw,
        dut=dut,
        inputs=inputs,
        outputs=outputs,
        cfg=cfg,
    )


