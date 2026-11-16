import py4hw

class serializer_10to1(py4hw.Logic):
    def __init__(self, parent, name, reset, clk_pixel, data_in, serial_out):
        super().__init__(parent, name)
        
        assert(data_in.getWidth() == 10)
        
        self.addIn('reset', reset)
        self.addIn('clk_pixel', clk_pixel)
        self.addIn('data_in', data_in)
        self.addOut('serial_out', serial_out)
        
    def clock(self):
        pass
        
    def verilogBody(self):
        s = ''
        
        clk_name = py4hw.getObjectClockDriver(self).name
        
        s += '''
        wire shift1, shift2;

    OSERDESE2 #(
        .DATA_RATE_OQ("DDR"),
        .DATA_RATE_TQ("SDR"),
        .DATA_WIDTH(10),
        .TRISTATE_WIDTH(1),
        .SERDES_MODE("MASTER")
    ) oserdes_master (
        .OQ(serial_out),
        .OFB(),
        .TQ(),
        .TFB(),
        .SHIFTOUT1(),
        .SHIFTOUT2(),
        .TBYTEOUT(),
        '''
        s += f'.CLK({clk_name}),\n'
        s += '''
        .CLKDIV(clk_pixel),
        .D1(data_in[0]),
        .D2(data_in[1]),
        .D3(data_in[2]),
        .D4(data_in[3]),
        .D5(data_in[4]),
        .D6(data_in[5]),
        .D7(data_in[6]),
        .D8(data_in[7]),
        .TCE(1'b1),
        .OCE(1'b1),
        .TBYTEIN(1'b0),
        .RST(reset),
        .SHIFTIN1(shift1),
        .SHIFTIN2(shift2),
        .T1(1'b0), .T2(1'b0), .T3(1'b0), .T4(1'b0)
    );

    OSERDESE2 #(
        .DATA_RATE_OQ("DDR"),
        .DATA_RATE_TQ("SDR"),
        .DATA_WIDTH(10),
        .TRISTATE_WIDTH(1),
        .SERDES_MODE("SLAVE")
    ) oserdes_slave (
        .OQ(),
        .OFB(),
        .TQ(),
        .TFB(),
        .SHIFTOUT1(shift1),
        .SHIFTOUT2(shift2),
        .TBYTEOUT(),
        '''
        s += f'.CLK({clk_name}),\n'
        s += '''
        .CLKDIV(clk_pixel),
        .D1(1'b0),
        .D2(1'b0),
        .D3(data_in[8]),
        .D4(data_in[9]),
        .D5(1'b0),
        .D6(1'b0),
        .D7(1'b0),
        .D8(1'b0),
        .TCE(1'b1),
        .OCE(1'b1),
        .TBYTEIN(1'b0),
        .RST(reset),
        .SHIFTIN1(1'b0),
        .SHIFTIN2(1'b0),
        .T1(1'b0), .T2(1'b0), .T3(1'b0), .T4(1'b0)
    );
    '''
        return s
        
