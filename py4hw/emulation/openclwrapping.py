# -*- coding: utf-8 -*-
"""
Created on Sat Jan 29 19:38:40 2022

@author: dcr
"""

#  add this to main __init__.py
#from .emulation.openclwrapping import *

class OpenCLWrapper:
    
    def __init__(self):
        pass
    
    
    def getXml(self):
        str = ''
        
        str += '<RTL_SPEC>\n'
        str += '<FUNCTION name="rtl_wrapper" module="RTLWrapper4OpenCL">\n'
        str += '<ATTRIBUTES>\n'
        str += '<IS_STALL_FREE value="no"/>\n'
        str += '<IS_FIXED_LATENCY value="no"/>\n'
        str += '<EXPECTED_LATENCY value="31"/>\n'
        str += '<CAPACITY value="1"/>\n'
        str += '<HAS_SIDE_EFFECTS value="yes"/>\n'
        str += '<ALLOW_MERGING value="no"/>\n'
        str += '</ATTRIBUTES>\n' 
        str += '<INTERFACE>\n'
        str += '<AVALON port="clock" type="clock"/>\n'
        str += '<AVALON port="resetn" type="resetn"/>\n'
        str += '<AVALON port="ivalid" type="ivalid"/>\n'
        str += '<AVALON port="iready" type="iready"/>\n'
        str += '<AVALON port="ovalid" type="ovalid"/>\n'
        str += '<AVALON port="oready" type="oready"/>\n'
        str += '<INPUT port="datain" width="64"/>\n'
        str += '<OUTPUT port="dataout" width="64"/>\n'
        str += '</INTERFACE>\n'
        str += '<C_MODEL>\n'
        str += '<FILE name="rtl_wrapper.cl" />\n'
        str += '</C_MODEL>\n'
        str += '<REQUIREMENTS>\n'
        str += '<FILE name="RTLWrapper4OpenCL.v" />\n'
        str += '</REQUIREMENTS>\n'
        str += '<RESOURCES>\n'
        str += '<ALUTS value="1000"/>\n'
        str += '<FFS value="1000"/>\n'
        str += '<RAMS value="1"/>\n'
        str += '<MLABS value="1"/>\n'
        str += '<DSPS value="1"/>\n'
        str += '</RESOURCES>\n'
        str += '</FUNCTION>\n'
        str += '</RTL_SPEC>\n'
        return str;
    
    def getIncludeFile(self):
        return "rtl_wrapper.h"
    
    def getPrototype(self):
        # write it to rtl_wrapper.h
        return "long rtl_wrapper(long v);"
    
    def getCModel(self):
        return "long rtl_wrapper(long v) { return 0; }"
    
    
    def compileWrapper(self):
        return "aoc -rtl RTLWrapper4OpenCL.xml -o RTLWrapper4OpenCL.aoco"
    
    def linkLibrary(self):
        return "aocl library create -o RTLWrapper4OpenCL.aoclib  RTLWrapper4OpenCL.aoco"
    
    
    def getPlatforms(self):
        import pyopencl
        platforms = pyopencl.get_platforms()
        plt = platforms[1]
        print(plt)
        devs = plt.get_devices()
        print(devs)