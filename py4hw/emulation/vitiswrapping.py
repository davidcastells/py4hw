import py4hw
import py4hw.logic.bus.axi as axi


class Axi2Reg(py4hw.Logic):
    """
    Captures the first 64 bits of an AXI4-Stream word into a register.
    Translates the Verilog axi2reg module.
    """
    def __init__(self, parent, name, reset, ap_start, ap_reset, stream:axi.AXI4StreamInterface, q, loaded):
        super().__init__(parent, name)

        # Add Ports
        self.addIn("areset", reset)
        self.addIn("ap_start", ap_start)
        self.addIn("ap_reset", ap_reset)
        
        self.addInterfaceSink('', stream)
        
        self.addOut("q", q)
        self.addOut("loaded", loaded)

        py4hw.Constant(self, "tready", 1, stream.tready)
        
        # 3. Handshake Logic (valid && ready)
        handshake = py4hw.Wire(self, "handshake", 1)
        py4hw.And2(self, "and_handshake", stream.tvalid, stream.tready, handshake)

        # 4. Extract first 64 bits of tdata
        tdata_64 = py4hw.Wire(self, "tdata_64", 64)
        py4hw.Range(self, "range_data", stream.tdata, 63, 0, tdata_64)

        # 5. Register for reg_out
        # In Verilog: if (handshake) reg_out <= data; else if (areset) reg_out <= 0;
        # py4hw.Reg(parent, name, d, q, enable, reset, reset_value)
        py4hw.Reg(self, "reg_data", d=tdata_64, q=q, enable=handshake, reset=reset)

        # 6. Logic for 'loaded'
        # In Verilog, loaded is 1 only during the cycle of the handshake, 
        # but cleared by areset, ap_start, or ap_reset.
        
        # Rearm/Reset logic for loaded: (areset || ap_start || ap_reset)
        
        rearm_final = py4hw.Wire(self, "rearm_final", 1)
        
        py4hw.Or(self, "rearm_final", [reset, ap_start, ap_reset], rearm_final)

        # loaded_next = handshake ? 1 : 0 (effectively just the handshake wire)
        # We use a register to capture the state
        py4hw.Reg(self, "loaded", d=handshake, q=loaded, enable=handshake, reset=rearm_final)

