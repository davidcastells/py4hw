# py4hw

[![PyPI version](https://badge.fury.io/py/py4hw.svg)](https://badge.fury.io/py/py4hw)

py4hw is an HDL library based on python to create digital circuits (mainly) following a structural design methodology. 
It is highly influenced by some principles used in JHDL but using the power of Python.

When people see Python and HDL in the same sentence they automatically associate it with two ideas:

1. This is an attempt to generate Verilog from Python code with an HLS approach
2. This will generate terribly inefficient Verilog

The answer to both questions is **NO**.
py4hw is **NOT** [yet] intended to be a python HLS tool. It actually starts from a bottom-up approach modelling basic logic gates.
In fact, you can generate Verilog code at a very fine-grain.
 
## Features ##

- Cycle-based Simulation
- Clear separation of design styles 
   - Structural
   - Behavioural
      - Combinational
      - Sequential (RTL)
      - Algorithmic
- Schematic Rendering
- Interactive Simulation
- Verilog Generation (for Structural, Combinational and Sequential design styles)
- WaveDrom generation
- Library of predefined circuits
- Pypi based distribution
- Jupyter Notebook integration
- Integration with edalize
- Support for existing Hardware platforms (Terasic DE0, and DE1SoC so far)


[Follow the jump start tutorial in a jypyter notebook!](tutorial/README.md) or access the static html version [here](https://davidcastells.github.io/py4hw/)


## Contributing ##

Contributors are more than welcome :-)

I've identifyied a number of low-effort aspects that should be done

- change the use of nbwavedrom by wavedrom
- correct synchronization of wire names and waveforms in WaveformWindow and support for scrolling, zooming and paning.
- avoid complete redrawing in interactive workbench

..and other high effort tasks

- improve the place & route algorithm in the schematic viewer
- collapse interfaces in the schematic viewer
- support additional hardware platforms 
- transpile algorithmic into RTL

## Publications ##

Cite as

```
@inproceedings{castells2026py4hw,
  title={py4hw: An Object-Oriented Python Framework for FPGA-Based Design and Education: Special Session Paper},
  author={Castells-Rufas, David and Oliva-Abell{\'o}, Ariadna and Novo, David and Martorell, Xavier},
  booktitle={2026 Forum on Specification \& Design Languages (FDL)},
  pages={1--2},
  year={2026},
  organization={IEEE},
  doi = {10.1109/FDL71572.2026.11724688}
}
```

```
@conference{castells2023streamlining,
  author       = {David Castells-Rufas and Gemma Rotger and David Novo},
  title        = {Streamlining FPGA Circuit Design and Verification with Python and py4hw},
  booktitle    = {XI Southern Programmable Logic Conference},
  year         = 2023,
  month        = mar,
  address      = {San Luis, Argentina},
  doi          = {10.5281/zenodo.8325670}
}
```
