# -*- coding: utf-8 -*-
"""
Created on Thu Mar 14 11:04:18 2024

@author: dcr
"""
from py4hw.base import *

class AXI4Interface(Interface):

    def __init__(self, parent, name:str, aw, dw, idw):
        super().__init__(parent, name)

        # output -> source to sink
        # input -> sink to source
        self.awvalid = self.addSourceToSink('awvalid', 1)
        self.awready = self.addSinkToSource('awready', 1)
        self.awaddr = self.addSourceToSink('awaddr', aw)
        self.awlen = self.addSourceToSink('awlen', 8)
        self.awsize = self.addSourceToSink('awsize', 3) # data transfer size in bytes = 2^awsize
        self.awid = self.addSourceToSink('awid', idw)
        self.awburst = self.addSourceToSink('awburst', 2)
        self.awlock = self.addSourceToSink('awlock', 2)
        self.awcache = self.addSourceToSink('awcache', 4)
        self.awprot = self.addSourceToSink('awprot', 3)
        self.awqos = self.addSourceToSink('awqos', 4)
        self.awregion = self.addSourceToSink('awregion', 4)
        
        self.wvalid = self.addSourceToSink('wvalid', 1)
        self.wready = self.addSinkToSource('wready', 1)
        self.wdata = self.addSourceToSink('wdata', dw)
        self.wstrb = self.addSourceToSink('wstrb', dw//8)
        self.wlast = self.addSourceToSink('wlast', 1)
        
        self.bvalid = self.addSinkToSource('bvalid', 1)
        self.bready = self.addSourceToSink('bready', 1)
        self.bresp = self.addSinkToSource('bresp', 2)
        self.bid = self.addSinkToSource('bid', idw)
        
        self.arvalid = self.addSourceToSink('arvalid', 1)
        self.arready = self.addSinkToSource('arready', 1)
        self.araddr = self.addSourceToSink('araddr', aw)
        self.arlen = self.addSourceToSink('arlen', 8)
        self.arsize = self.addSourceToSink('arsize', 3) # data transfer size in bytes = 2^awsize
        self.arid = self.addSourceToSink('arid', idw)
        self.arburst = self.addSourceToSink('arburst', 2)
        self.arlock = self.addSourceToSink('arlock', 2)
        self.arcache = self.addSourceToSink('arcache', 4)
        self.arprot = self.addSourceToSink('arprot', 3)
        self.arqos = self.addSourceToSink('arqos', 4)
        self.arregion = self.addSourceToSink('arregion', 4)
        
        self.rvalid = self.addSinkToSource('rvalid', 1)
        self.rready = self.addSourceToSink('rready', 1)
        self.rdata = self.addSinkToSource('rdata', dw)
        self.rlast = self.addSinkToSource('rlast', 1)
        self.rresp = self.addSinkToSource('rresp', 2)
        self.rid = self.addSinkToSource('rid', idw)

    def getWriteSubInterface(self):
        sub = Interface(self.parent, '{}_sub_write'.format(self.name))
        
        sub.awvalid = sub.addSourceToSinkRef(self, 'awvalid')
        sub.awready = sub.addSinkToSourceRef(self, 'awready')
        sub.awaddr = sub.addSourceToSinkRef(self, 'awaddr')
        sub.awlen = sub.addSourceToSinkRef(self, 'awlen')
        sub.awsize = sub.addSourceToSinkRef(self, 'awsize') # data transfer size in bytes = 2^awsize
        sub.awid = sub.addSourceToSinkRef(self, 'awid')
        sub.awburst = sub.addSourceToSinkRef(self, 'awburst')
        sub.awlock = sub.addSourceToSinkRef(self, 'awlock')
        sub.awcache = sub.addSourceToSinkRef(self, 'awcache')
        sub.awprot = sub.addSourceToSinkRef(self, 'awprot')
        sub.awqos = sub.addSourceToSinkRef(self, 'awqos')
        sub.awregion = sub.addSourceToSinkRef(self, 'awregion')
        
        sub.wvalid = sub.addSourceToSinkRef(self, 'wvalid')
        sub.wready = sub.addSinkToSourceRef(self, 'wready')
        sub.wdata = sub.addSourceToSinkRef(self, 'wdata')
        sub.wstrb = sub.addSourceToSinkRef(self, 'wstrb')
        sub.wlast = sub.addSourceToSinkRef(self, 'wlast')
        
        sub.bvalid = sub.addSinkToSourceRef(self, 'bvalid')
        sub.bready = sub.addSourceToSinkRef(self, 'bready')
        sub.bresp = sub.addSinkToSourceRef(self, 'bresp')
        sub.bid = sub.addSinkToSourceRef(self, 'bid')
        
        return sub
    
    def getReadSubInterface(self):
        sub = Interface(self.parent, '{}_sub_read'.format(self.name))
        
        sub.arvalid = sub.addSourceToSinkRef(self, 'arvalid')
        sub.arready = sub.addSinkToSourceRef(self, 'arready')
        sub.araddr = sub.addSourceToSinkRef(self, 'araddr')
        sub.arlen = sub.addSourceToSinkRef(self, 'arlen')
        sub.arsize = sub.addSourceToSinkRef(self, 'arsize') # data transfer size in bytes = 2^awsize
        sub.arid = sub.addSourceToSinkRef(self, 'arid')
        sub.arburst = sub.addSourceToSinkRef(self, 'arburst')
        sub.arlock = sub.addSourceToSinkRef(self, 'arlock')
        sub.arcache = sub.addSourceToSinkRef(self, 'arcache')
        sub.arprot = sub.addSourceToSinkRef(self, 'arprot')
        sub.arqos = sub.addSourceToSinkRef(self, 'arqos')
        sub.arregion = sub.addSourceToSinkRef(self, 'arregion')
        
        sub.rvalid = sub.addSinkToSourceRef(self, 'rvalid')
        sub.rready = sub.addSourceToSinkRef(self, 'rready')
        sub.rdata = sub.addSinkToSourceRef(self, 'rdata')
        sub.rlast = sub.addSinkToSourceRef(self, 'rlast')
        sub.rresp = sub.addSinkToSourceRef(self, 'rresp')        
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
        self.awprot = self.addSourceToSink('awprot', 3)
        
        self.wvalid = self.addSourceToSink('wvalid', 1)
        self.wready = self.addSinkToSource('wready', 1)
        self.wdata = self.addSourceToSink('wdata', dw)
        self.wstrb = self.addSourceToSink('wstrb', dw//8)
        
        self.arvalid = self.addSourceToSink('arvalid', 1)
        self.arready = self.addSinkToSource('arready', 1)
        self.araddr = self.addSourceToSink('araddr', aw)
        self.arprot = self.addSourceToSink('arprot', 3)
        
        self.rvalid = self.addSinkToSource('rvalid', 1)
        self.rready = self.addSourceToSink('rready', 1)
        self.rdata = self.addSinkToSource('rdata', dw)
        self.rresp = self.addSinkToSource('rresp', 2)
        
        self.bvalid = self.addSinkToSource('bvalid', 1)
        self.bready = self.addSourceToSink('bready', 1)
        self.bresp = self.addSinkToSource('bresp', 2)
        