# -*- coding: utf-8 -*-
"""
Created on Thu Mar 14 11:04:18 2024

@author: dcr
"""
from py4hw.base import *

class AXI4Interface(Interface):

    def __init__(self, parent, name:str, aw, dw, aridw=None, ridw=None):
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
        self.bresp = self.addSinkToSource('bresp', 2)

        
        self.arvalid = self.addSourceToSink('arvalid', 1)
        self.arready = self.addSinkToSource('arready', 1)
        self.araddr = self.addSourceToSink('araddr', aw)
        self.arlen = self.addSourceToSink('arlen', 8)
        self.arsize = self.addSourceToSink('arsize', 3) # data transfer size in bytes = 2^awsize

        if not(aridw is None):
            self.arid = self.addSourceToSink('arid', aridw)
        else:
            self.arid = None
        
        self.rvalid = self.addSinkToSource('rvalid', 1)
        self.rready = self.addSourceToSink('rready', 1)
        self.rdata = self.addSinkToSource('rdata', dw)
        self.rlast = self.addSinkToSource('rlast', 1)
        self.rresp = self.addSinkToSource('rresp', 2)
        
        if not(ridw is None):
            self.rid = self.addSinkToSource('rid', ridw)
        else:
            self.rid = None

    def getWriteSubInterface(self):
        sub = Interface(self.parent, '{}_sub_write'.format(self.name))
        
        sub.awvalid = sub.addSourceToSinkRef(self, 'awvalid')
        sub.awready = sub.addSinkToSourceRef(self, 'awready')
        sub.awaddr = sub.addSourceToSinkRef(self, 'awaddr')
        sub.awlen = sub.addSourceToSinkRef(self, 'awlen')
        sub.awsize = sub.addSourceToSinkRef(self, 'awsize') # data transfer size in bytes = 2^awsize
        
        sub.wvalid = sub.addSourceToSinkRef(self, 'wvalid')
        sub.wready = sub.addSinkToSourceRef(self, 'wready')
        sub.wdata = sub.addSourceToSinkRef(self, 'wdata')
        sub.wstrb = sub.addSourceToSinkRef(self, 'wstrb')
        sub.wlast = sub.addSourceToSinkRef(self, 'wlast')
        
        sub.bvalid = sub.addSinkToSourceRef(self, 'bvalid')
        sub.bready = sub.addSourceToSinkRef(self, 'bready')
        sub.bresp = sub.addSinkToSourceRef(self, 'bresp')
        
        return sub
    
    def getReadSubInterface(self):
        sub = Interface(self.parent, '{}_sub_read'.format(self.name))
        
        sub.arvalid = sub.addSourceToSinkRef(self, 'arvalid')
        sub.arready = sub.addSinkToSourceRef(self, 'arready')
        sub.araddr = sub.addSourceToSinkRef(self, 'araddr')
        sub.arlen = sub.addSourceToSinkRef(self, 'arlen')
        sub.arsize = sub.addSourceToSinkRef(self, 'arsize') # data transfer size in bytes = 2^awsize

        if not(self.arid is None):
            sub.arid = sub.addSourceToSinkRef(self, 'arid')
        
        sub.rvalid = sub.addSinkToSourceRef(self, 'rvalid')
        sub.rready = sub.addSourceToSinkRef(self, 'rready')
        sub.rdata = sub.addSinkToSourceRef(self, 'rdata')
        sub.rlast = sub.addSinkToSourceRef(self, 'rlast')
        sub.rresp = sub.addSinkToSourceRef(self, 'rresp')
        
        if not(self.rid is None):
            sub.rid = sub.addSinkToSourceRef(self, 'rid')
            
        return sub
        
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
        