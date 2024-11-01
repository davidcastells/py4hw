# -*- coding: utf-8 -*-
"""
Created on Thu Mar 14 11:04:18 2024

@author: dcr
"""
from py4hw.base import *

class AXI4Interface(Interface):

    def __init__(self, parent, name:str, aw, dw):
        super().__init__(parent, name)

        # output -> source to sink
        # input -> sink to source
        self.awvalid = self.addSourceToSink('awvalid', 1)
        self.awready = self.addSinkToSource('awready', 1)
        self.awaddr = self.addSourceToSink('awaddr', aw)
        self.awlen = self.addSourceToSink('awlen', 8)
        self.awsize = self.addSourceToSink('awsize', 3) # data transfer size in bytes = 2^awsize
        
        self.wvalid = self.addSourceToSink('wvalid', 1)
        self.wready = self.addSinkToSource('wready', 1)
        self.wdata = self.addSourceToSink('wdata', dw)
        self.wstrb = self.addSourceToSink('wstrb', dw//8)
        self.wlast = self.addSourceToSink('wlast', 1)
        
        self.bvalid = self.addSinkToSource('bvalid', 1)
        self.bready = self.addSourceToSink('bready', 1)
        self.rresp = self.addSinkToSource('rresp', 2)
        
        self.arvalid = self.addSourceToSink('arvalid', 1)
        self.arready = self.addSinkToSource('arready', 1)
        self.araddr = self.addSourceToSink('araddr', aw)
        self.arlen = self.addSourceToSink('arlen', 8)
        self.rvalid = self.addSinkToSource('rvalid', 1)
        self.rready = self.addSourceToSink('rready', 1)
        self.rdata = self.addSinkToSource('rdata', dw)
        self.rlast = self.addSinkToSource('rlast', 1)

class AXI4LiteInterface(Interface):
    def __init__(self, parent, name:str, aw, dw):
        super().__init__(parent, name)

        # input -> source to sink
        # output -> sink to source
        self.awvalid = self.addSourceToSink('awvalid', 1)
        self.awready = self.addSinkToSource('awready', 1)
        self.awaddr = self.addSourceToSink('awaddr', aw)
        
        self.wvalid = self.addSourceToSink('wvalid', 1)
        self.wready = self.addSinkToSource('wready', 1)
        self.wdata = self.addSourceToSink('wdata', dw)
        self.wstrb = self.addSourceToSink('wstrb', dw//8)
        
        self.arvalid = self.addSourceToSink('arvalid', 1)
        self.arready = self.addSinkToSource('arready', 1)
        self.araddr = self.addSourceToSink('araddr', aw)
        
        self.rvalid = self.addSinkToSource('rvalid', 1)
        self.rready = self.addSourceToSink('rready', 1)
        self.rdata = self.addSinkToSource('rdata', dw)
        self.rresp = self.addSinkToSource('rresp', 2)
        
        self.bvalid = self.addSinkToSource('bvalid', 1)
        self.bready = self.addSourceToSink('bready', 1)
        self.bresp = self.addSinkToSource('bresp', 2)
        