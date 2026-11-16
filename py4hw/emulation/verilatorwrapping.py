#!/usr/bin/env python3
"""
verilator_pybind_gen.py

Given a Verilog/SystemVerilog file, this script:
  1. Parses the top module's ANSI-style port list (direction + width).
  2. Runs Verilator to translate the design into C++ (`verilator --cc`).
  3. Generates a pybind11 C++ wrapper exposing a clock-driven `Sim` class:
        - step(num_cycles=1)   -> toggles the clock and evals each half cycle
        - reset(cycles=2)      -> pulses the reset port (if you gave one)
        - eval()               -> raw combinational eval
        - one Python property per port (get/set for inputs & inouts,
          read-only for outputs)
  4. Compiles wrapper + verilated sources into a Python extension module (.so)
     you can `import` directly.

Requirements (must already be installed / on PATH):
  - verilator
  - g++ with C++17 support
  - Python package `pybind11`  (pip install pybind11)

Usage:
  python3 verilator_pybind_gen.py design.sv --top my_module \par
      --outdir build

Then in Python:
  import sys; sys.path.insert(0, "build")
  import my_module_sim
  sim = my_module_sim.Sim()
  sim.reset()
  sim.data_in = 5
  sim.step(1)
  print(sim.data_out)

Notes / limitations:
  - Only ANSI-style port lists (`module foo (input wire clk, ...);`) are
    parsed. Old-style (non-ANSI) port declarations are not supported.
  - Port widths that depend on unresolved parameters fall back to 32 bits
    with a warning -- fix the generated build/wrapper.cpp manually if that's
    wrong for your design.
  - Ports wider than 64 bits are exposed as List[int] (32-bit words, index 0
    = least-significant word), matching Verilator's internal WData layout.
  - step() assumes the clock is idle-low / posedge-triggered: each cycle
    drives clk=0, eval(), clk=1, eval(). Edit the generated wrapper.cpp if
    your design needs different clocking.
"""

import argparse
import os
import re
import subprocess
import sys
import sysconfig
from pathlib import Path

# --------------------------------------------------------------------------
# Verilog port parsing (regex/manual, ANSI-style port lists only)
# --------------------------------------------------------------------------

DIR_RE = re.compile(r'^\s*(input|output|inout)\b')
TYPE_RE = re.compile(r'^\s*(wire|reg|logic|tri|signed|unsigned)\b')


def strip_comments(text: str) -> str:
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    text = re.sub(r'//.*', '', text)
    return text


def find_module_port_list(text: str, top: str) -> str:
    """Return the raw text between the outer parens of `module <top> ( ... );`"""
    m = re.search(r'\bmodule\s+' + re.escape(top) + r'\b', text)
    if not m:
        raise ValueError(f"Could not find 'module {top}' in source")
    j = m.end()
    while j < len(text) and text[j] in ' \t\r\n':
        j += 1
    # skip an optional #( ... ) parameter block
    if j < len(text) and text[j] == '#':
        k = text.index('(', j)
        depth, p = 0, k
        while p < len(text):
            if text[p] == '(':
                depth += 1
            elif text[p] == ')':
                depth -= 1
                if depth == 0:
                    break
            p += 1
        j = p + 1
        while j < len(text) and text[j] in ' \t\r\n':
            j += 1
    if j >= len(text) or text[j] != '(':
        raise ValueError(
            f"Could not locate an ANSI-style port list for module {top} "
            f"(non-ANSI modules are not supported by this script)"
        )
    k = j
    depth, p = 0, k
    while p < len(text):
        if text[p] == '(':
            depth += 1
        elif text[p] == ')':
            depth -= 1
            if depth == 0:
                break
        p += 1
    return text[k + 1:p]


def split_top_level(s: str, sep: str = ',') -> list:
    parts, depth, cur = [], 0, ''
    for ch in s:
        if ch in '([{':
            depth += 1
        elif ch in ')]}':
            depth -= 1
        if ch == sep and depth == 0:
            parts.append(cur)
            cur = ''
        else:
            cur += ch
    if cur.strip():
        parts.append(cur)
    return parts


def eval_const(expr: str) -> int:
    return int(eval(expr.strip(), {"__builtins__": {}}, {}))


def compute_width(rng):
    if rng is None:
        return 1
    parts = rng.split(':')
    if len(parts) != 2:
        return None
    try:
        msb, lsb = eval_const(parts[0]), eval_const(parts[1])
        return abs(msb - lsb) + 1
    except Exception:
        return None


def parse_ports(port_list_text: str) -> list:
    entries = split_top_level(port_list_text)
    ports = []
    cur_dir, cur_range = None, None
    for entry in entries:
        e = entry.strip()
        if not e:
            continue
        m = DIR_RE.match(e)
        if m:
            cur_dir = m.group(1)
            e = e[m.end():].strip()
            while True:
                tm = TYPE_RE.match(e)
                if not tm:
                    break
                e = e[tm.end():].strip()
            rm = re.match(r'^\[([^\]]+)\]', e)
            if rm:
                cur_range = rm.group(1)
                e = e[rm.end():].strip()
            else:
                cur_range = None
        else:
            rm = re.match(r'^\[([^\]]+)\]', e)
            if rm:
                cur_range = rm.group(1)
                e = e[rm.end():].strip()
        if cur_dir is None:
            continue
        name_m = re.match(r'^([A-Za-z_][A-Za-z0-9_$]*)', e)
        if not name_m:
            continue
        name = name_m.group(1)
        ports.append({'name': name, 'dir': cur_dir, 'range': cur_range,
                       'width': compute_width(cur_range)})
    return ports


# --------------------------------------------------------------------------
# Verilator invocation
# --------------------------------------------------------------------------

def get_verilator_root() -> str:
    try:
        out = subprocess.run(['verilator', '--getenv', 'VERILATOR_ROOT'],
                              capture_output=True, text=True, check=True)
        root = out.stdout.strip()
        if root:
            return root
    except Exception:
        pass
    try:
        out = subprocess.run(['verilator', '-V'], capture_output=True, text=True, check=True)
        m = re.search(r'VERILATOR_ROOT\s*=\s*(\S+)', out.stdout)
        if m:
            return m.group(1)
    except Exception:
        pass
    raise RuntimeError("Could not determine VERILATOR_ROOT; is verilator installed and on PATH?")


def run_verilator(source: str, top: str, outdir: str, is_sv: bool) -> str:
    obj_dir = os.path.join(outdir, 'obj_dir')
    os.makedirs(obj_dir, exist_ok=True)
    cmd = ['verilator', '-Wall', '--cc', '--top-module', top, '-Mdir', obj_dir]
    if is_sv:
        cmd.append('-sv')
    cmd.append(source)
    print('Running:', ' '.join(cmd))
    subprocess.run(cmd, check=True)
    return obj_dir


# --------------------------------------------------------------------------
# pybind11 wrapper generation
# --------------------------------------------------------------------------

def c_type_for_width(width):
    if width is None:
        return None
    if width <= 8:
        return 'uint8_t'
    if width <= 16:
        return 'uint16_t'
    if width <= 32:
        return 'uint32_t'
    if width <= 64:
        return 'uint64_t'
    return None  # wide signal, handled separately


def generate_wrapper(ports, top, clock, reset, reset_active, module_name) -> str:
    L = []
    a = L.append
    a('#include <pybind11/pybind11.h>')
    a('#include <pybind11/stl.h>')
    a(f'#include "V{top}.h"')
    a('#include "verilated.h"')
    a('#include <cstdint>')
    a('#include <vector>')
    a('')
    a('namespace py = pybind11;')
    a('')
    a('class Sim {')
    a('public:')
    a(f'    Sim() {{ top_ = new V{top}(); }}')
    a('    ~Sim() { top_->final(); delete top_; }')
    a('')
    a('    void eval() { top_->eval(); }')
    a('')
    a('    // Advances the design by `num_cycles` full clock cycles.')
    a('    // Each cycle: clock -> 0, eval(); clock -> 1, eval().')
    a('    void step(int num_cycles = 1) {')
    a('        for (int i = 0; i < num_cycles; i++) {')
    if clock:
        a(f'            top_->{clock} = 0;')
        a('            top_->eval();')
        a(f'            top_->{clock} = 1;')
        a('            top_->eval();')
    else:
        a('            top_->eval();')
    a('        }')
    a('    }')
    a('')
    if reset:
        inactive = 0 if str(reset_active) == '1' else 1
        a('    // Pulses the reset port for `cycles` clock cycles.')
        a('    // Point of interest: active level is configured dynamic.')
        a('    void reset(int cycles = 2) {')
        a(f'        top_->{reset} = {reset_active};')
        a('        step(cycles);')
        a(f'        top_->{reset} = {inactive};')
        a('        eval();')
        a('    }')
        a('')

    for p in ports:
        name, width, direction = p['name'], p['width'], p['dir']
        ctype = c_type_for_width(width)
        if ctype is not None:
            a(f'    uint64_t get_{name}() const {{ return static_cast<uint64_t>(top_->{name}); }}')
            if direction in ('input', 'inout'):
                a(f'    void set_{name}(uint64_t v) {{ top_->{name} = static_cast<{ctype}>(v); }}')
        else:
            words = (width + 31) // 32
            a(f'    std::vector<uint32_t> get_{name}() const {{')
            a(f'        std::vector<uint32_t> out({words});')
            a(f'        for (int i = 0; i < {words}; i++) out[i] = top_->{name}[i];')
            a('        return out;')
            a('    }')
            if direction in ('input', 'inout'):
                a(f'    void set_{name}(const std::vector<uint32_t>& v) {{')
                a(f'        for (int i = 0; i < {words} && i < (int)v.size(); i++) top_->{name}[i] = v[i];')
                a('    }')
    a('')
    a('private:')
    a(f'    V{top}* top_;')
    a('};')
    a('')
    a(f'PYBIND11_MODULE({module_name}, m) {{')
    a('    py::class_<Sim>(m, "Sim")')
    a('        .def(py::init<>())')
    a('        .def("eval", &Sim::eval)')
    a('        .def("step", &Sim::step, py::arg("num_cycles") = 1)')
    if reset:
        a('        .def("reset", &Sim::reset, py::arg("cycles") = 2)')
    for p in ports:
        name = p['name']
        if p['dir'] in ('input', 'inout'):
            a(f'        .def_property("{name}", &Sim::get_{name}, &Sim::set_{name})')
        else:
            a(f'        .def_property_readonly("{name}", &Sim::get_{name})')
    a('        ;')
    a('}')
    return '\n'.join(L)


# --------------------------------------------------------------------------
# Compilation
# --------------------------------------------------------------------------

def compile_extension(outdir, obj_dir, wrapper_path, module_name, verilator_root) -> str:
    ext_suffix = sysconfig.get_config_var('EXT_SUFFIX') or '.so'
    out_so = os.path.join(outdir, module_name + ext_suffix)

    try:
        pybind_includes = subprocess.run(
            [sys.executable, '-m', 'pybind11', '--includes'],
            capture_output=True, text=True, check=True
        ).stdout.strip().split()
    except Exception as e:
        raise RuntimeError(
            "Could not get pybind11 include flags. Install it with:\n"
            "    pip install pybind11"
        ) from e

    cpp_sources = sorted(str(p) for p in Path(obj_dir).glob('*.cpp'))
    verilated_cpp = os.path.join(verilator_root, 'include', 'verilated.cpp')
    verilated_threads_cpp = os.path.join(verilator_root, 'include', 'verilated_threads.cpp') 

    cmd = [
        'g++', '-O2', '-std=c++17', '-fPIC', '-shared', '-pthread',
        '-I', obj_dir,
        '-I', os.path.join(verilator_root, 'include'),
        '-I', os.path.join(verilator_root, 'include', 'vltstd'),
        *pybind_includes,
        wrapper_path, *cpp_sources, verilated_cpp, verilated_threads_cpp,
        '-o', out_so,
    ]
    print('Compiling extension:\n  ' + ' '.join(cmd))
    subprocess.run(cmd, check=True)
    return out_so


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def create_wrapper(hw, source,  module_name, outdir, obj_args, clock=None, reset=None, reset_active=None):
    
    top = module_name

    if not os.path.isfile(source):
        sys.exit(f"Source file not found: {source}")
        
    is_sv = source.endswith('.sv') or source.endswith('.svh')
    module_name = module_name or f'{top}_sim'
    outdir = os.path.abspath(outdir)
    os.makedirs(outdir, exist_ok=True)

    text = strip_comments(Path(source).read_text())
    port_list_text = find_module_port_list(text, top)
    ports = parse_ports(port_list_text)
    if not ports:
        sys.exit(f"No ports parsed for module '{top}'; "
                  f"check that it uses ANSI-style port declarations.")

    names = {p['name'] for p in ports}
    input_ports = [p['name'] for p in ports if p['dir'] == 'input']
    output_ports = [p['name'] for p in ports if p['dir'] == 'output']

    # --- Clock Auto-Discovery ---
    clock_port = clock
    if not clock_port:
        # Check exact-ish matches first (case-insensitive)
        candidates = [p for p in input_ports if p.lower() in ('clk', 'clock')]
        if not candidates:
            # Fall back to matching anything containing 'clk' or 'clock'
            candidates = [p for p in input_ports if 'clk' in p.lower() or 'clock' in p.lower()]
        
        if candidates:
            clock_port = candidates[0]
            print(f"Auto-detected clock port: '{clock_port}'")
        else:
            sys.exit("Error: Could not auto-detect a clock port. Please specify one using --clock.")
    else:
        if clock_port not in names:
            sys.exit(f"Clock port '{clock_port}' not found among parsed ports: {sorted(names)}")

    # --- Reset Auto-Discovery ---
    reset_port = reset
    
    if not reset_port:
        reset_active = '1'  # default active-high

        # Check standard names first (case-insensitive)
        candidates = [p for p in input_ports if p.lower() in ('rst', 'reset', 'rst_n', 'rstn', 'reset_n', 'resetn')]
        if not candidates:
            # Fall back to checking if 'rst' or 'reset' is a substring
            candidates = [p for p in input_ports if 'rst' in p.lower() or 'reset' in p.lower()]
        
        if candidates:
            reset_port = candidates[0]
            rp_low = reset_port.lower()
            # Determine active-low vs active-high polarity
            if rp_low.endswith('_n') or rp_low.endswith('n') or rp_low.endswith('_b') or rp_low.endswith('_bar'):
                reset_active = '0'
                polarity_str = "active-low (0)"
            else:
                reset_active = '1'
                polarity_str = "active-high (1)"
            
            print(f"Auto-detected reset port: '{reset_port}' with {polarity_str} polarity")
        else:
            print("No reset port auto-detected. Generating simulator wrapper without reset helpers.")
    else:
        if reset_port not in names:
            sys.exit(f"Reset port '{reset_port}' not found among parsed ports: {sorted(names)}")
        # If user explicitly supplied reset, but didn't supply polarity, default to active-high (1)
        reset_active = reset_active if reset_active is not None else '1'

    # Override auto-detected polarity if user specified it
    if reset_active is not None:
        reset_active = reset_active

    port_width = {}
    
    for p in ports:
        if p['width'] is None:
            print(f"WARNING: could not resolve width for port '{p['name']}' "
                  f"(range='{p['range']}'); defaulting to 32 bits. "
                  f"Edit the generated wrapper.cpp if this is wrong.")
            p['width'] = 32
            
        port_width[p['name']] = p['width']

    print(f"Parsed {len(ports)} ports for module '{top}':")
    for p in ports:
        print(f"  {p['dir']:6s} [{p['width']:>3}] {p['name']}")

    verilator_root = get_verilator_root()
    obj_dir = run_verilator(source, top, outdir, is_sv)

    wrapper_cpp = generate_wrapper(ports, top, clock_port, reset_port, reset_active, module_name)
    wrapper_path = os.path.join(outdir, 'wrapper.cpp')
    Path(wrapper_path).write_text(wrapper_cpp)
    print(f"Wrote wrapper: {wrapper_path}")

    out_so = compile_extension(outdir, obj_dir, wrapper_path, module_name, verilator_root)

    print(f"\nBuilt Python extension: {out_so}")
    print("\nUsage:")
    print(f"  import sys; sys.path.insert(0, {outdir!r})")
    print(f"  import {module_name}")
    print(f"  sim = {module_name}.Sim()")
    if reset_port:
        print("  sim.reset()")
    print("  sim.step(1)")
    import sys
    import types
    import importlib
    sys.path.append(outdir)

    
    verilator_module = importlib.import_module(module_name)
    import py4hw
    
    clazz  = py4hw.AbstractLogic(f'{module_name}_class')
    obj = clazz(hw, f'{module_name}_obj')
    
    obj.verilator_obj = verilator_module.Sim()
    
    non_clock_inputs = [p for p in input_ports if p != clock_port]
    
    for p in non_clock_inputs:
        if not(p in obj_args.keys()):
            raise Exception(f"Should provide input {p}")
            
        wire = obj_args[p]
        
        if (port_width[p] != wire.getWidth()):
            raise Exception(f'Wire {p} whould be {port_width[p]} bits wide')
        
        setattr(obj, p, obj.addIn(p, wire))
        
    for p in output_ports:

        if not(p in obj_args.keys()):
            raise Exception(f"Should provide output {p}")
            
        wire = obj_args[p]
        
        if (port_width[p] != wire.getWidth()):
            raise Exception(f'Wire {p} whould be {port_width[p]} bits wide')
        
        setattr(obj, p, obj.addOut(p, wire))
    
    def clock_fn(self):
        vobj = self.verilator_obj

        # 1. Push current wire values into the Verilator model
        for p in non_clock_inputs:
            wire = getattr(self, p)
            setattr(vobj, p, wire.get())

        # 2. Advance the simulation by one clock cycle
        vobj.step(1)

        # 3. Pull the resulting outputs back onto the py4hw wires
        for p in output_ports:
            wire = getattr(self, p)
            wire.prepare(getattr(vobj, p))

    obj.clock = types.MethodType(clock_fn, obj)
    
    return obj
    
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('source', help='Path to .v or .sv file')
    ap.add_argument('--top', required=True, help='Top module name')
    ap.add_argument('--clock', default=None, help="Clock port name (auto-detected if omitted)")
    ap.add_argument('--reset', default=None, help='Reset port name (auto-detected if omitted)')
    ap.add_argument('--reset-active', default=None, choices=['0', '1'],
                     help='Active level of reset (overrides auto-detection if specified)')
    ap.add_argument('--outdir', default='build', help='Build/output directory')
    ap.add_argument('--module-name', default=None,
                     help='Python extension module name (default: <top>_sim)')
    args = ap.parse_args()

    source = os.path.abspath(args.source)
    top = args.top
    module_name = args.module_name
    outdir = args.outdir

    create_wrapper(source,  module_name, outdir)


if __name__ == '__main__':
    main()
