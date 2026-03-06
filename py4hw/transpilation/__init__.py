# -*- coding: utf-8 -*-
"""
Created on Sun Apr  2 14:23:01 2023

@author: dcr
"""

from .. import *


# From                              |  To                               | Class                                            | Instance / Class
# Structural py4hw                  | Verilog                           | VerilogGenerator                                 | Instance
# Behavioural combinational py4hw   | Verilog                           | VerilogGenerator -> python2verilog_transpiler    | Instance
# Behavioural sequential py4hw      | Verilog                           | VerilogGenerator -> python2verilog_transpiler    | Instance
# Algorithmic Timed py4hw           | Verilog                           | ?
# Behavioural combinational py4hw   | Structuural py4hw                 | ?
# Behavioural combinational py4hw   | Structuural py4hw                 | ? 
# Algorithmic Timed py4hw           | Behavioural combinational py4hw   | Py4hwGenerator
 