# -*- coding: utf-8 -*-
"""
Created on Sat Sep 30 09:01:29 2023

@author: dcr
"""

'''
from edalize import edatool
import os

work_root = '/tmp/test_quartus'

files = [
  {'name' : os.path.relpath('Counter.v', work_root), 'file_type' : 'verilogSource'},
]

parameters = {'clk_freq_hz' : {'datatype' : 'int', 'default' : 1000, 'paramtype' : 'vlogparam'},
              'vcd' : {'datatype' : 'bool', 'paramtype' : 'plusarg'}}

tool = 'quartus'

edam = {
  'files'        : files,
  'name'         : 'Counter',
  'parameters'   : parameters,
  'toplevel'     : 'Counter'
}

backend = edalize.edatool.get_edatool(tool)(edam=edam, work_root=work_root)
backend.configure()
'''

class DE10:
    
    def __init__(self):
        pass
    
    
    def getEdalizeProperties(self):
        pass
    
    
    def build(self, obj, projectDir):
        pass
    
    def programBitstream(self):
        pass