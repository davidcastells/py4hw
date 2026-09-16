import py4hw

class TristateBuffer(py4hw.Logic):
    def __init__(self, parent, name, i, t, o, io):
        super().__init__(parent, name)
        
        assert(i.getWidth() == 1)
        assert(t.getWidth() == 1)
        assert(o.getWidth() == 1)
        assert(io.getWidth() == 1)

        self.addIn('i', i)
        self.addIn('t', t)
        self.addOut('o', o)
        self.addInOut('io', io)
        
    def propagate(self):
        pass

    def structureName(self):
        return 'TristateBuffer'
                
    def verilogBody(self):
        return 'IOBUF iobuf_inst (.I(i), .T(t), .O(o), .IO(io) );'
    
class OuputBufferDifferential(py4hw.Logic):
    def __init__(self, parent, name, a, p, n):
        super().__init__(parent, name)
        
        assert(a.getWidth() == 1)
        self.addIn('a', a)
        self.addOut('p', p)
        self.addOut('n', n)
        
    def propagate(self):
        pass

    def structureName(self):
        return 'OuputBufferDifferential'
                
    def verilogBody(self):
        return 'OBUFDS obufds_inst (.I(a), .O(p), .OB(n) );'
        
        
class ClockBufferIO(py4hw.Logic):
    def __init__(self, parent, name, a, r):
        super().__init__(parent, name)
        
        assert(a.getWidth() == 1)
        self.addIn('a', a)
        self.addOut('r', r)
        
    def propagate(self):
        pass
        
    def structureName(self):
        return 'ClockBufferIO'
        
    def verilogBody(self):
        return 'BUFIO inst (.I(a), .O(r) );'
        
class ClockBufferRegional(py4hw.Logic):
    def __init__(self, parent, name, a, r, div):
        super().__init__(parent, name)
        
        assert(a.getWidth() == 1)
        self.addIn('a', a)
        self.addOut('r', r)
        self.div = div
        
    def propagate(self):
        pass
        
    def structureName(self):
        return 'ClockBufferRegional'
        
    def verilogBody(self):
        return f'BUFR #(.BUFR_DIVIDE("{self.div}"),.SIM_DEVICE("7SERIES")) bufr_pixel (.I(a), .O(r), .CE(1), .CLR(0));'
