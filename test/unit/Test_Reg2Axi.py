# -*- coding: utf-8 -*-
"""
Unit testbench for Reg2Axi module
Tests register to AXI4-Stream conversion functionality

@author: dcr
"""

import pytest
import py4hw
from py4hw.logic.bus.axi import AXI4StreamInterface
from py4hw.emulation.vitiswrapping import Reg2Axi

class Test_Reg2Axi:
    
    def test_basic_transmission(self):
        """Test basic transmission of 64-bit value on handshake"""
        sys = py4hw.HWSystem()
        
        # Create signals
        ap_start = sys.wire("ap_start", 1)
        ap_reset = sys.wire("ap_reset", 1)
        ap_done = sys.wire("ap_done", 1)
        load_outs = sys.wire("load_outs", 1)
        reg_in = sys.wire("reg_in", 64)
        sent = sys.wire("sent", 1)
        active = sys.wire("active", 1)
        
        # Create AXI stream interface (master output)
        stream = AXI4StreamInterface(sys, "stream", dw=64, has_tlast=True, has_tkeep=True)
        
        # Instantiate DUT
        Reg2Axi(sys, "reg2axi", ap_start, ap_reset, ap_done, load_outs, reg_in, stream, sent, active)
        
        # Initial reset
        ap_reset.put(1)
        sys.getSimulator().clk(1)
        ap_reset.put(0)
        sys.getSimulator().clk(1)
        
        # Verify initial state
        assert sent.get() == 0, 'sent should be zero initially'
        assert stream.tvalid.get() == 0, 'tvalid should be zero initially'
        
        # Load a test value
        test_data = 0x123456789ABCDEF0
        reg_in.put(test_data)
        load_outs.put(1)
        sys.getSimulator().clk(1)
        load_outs.put(0)
        sys.getSimulator().clk(1)
        
        # Should not transmit without ap_start
        assert stream.tvalid.get() == 0, 'tvalid should be zero without ap_start'
        assert sent.get() == 0, 'sent should be zero without ap_start'
        
        # Apply ap_start to start transmission
        ap_start.put(1)        
        load_outs.put(1)
        sys.getSimulator().clk(2)  # Give time for handshake
        ap_start.put(0)
        
        # Should transmit when tready is high (ready is always high in simulation)
        # In real hardware, tready comes from downstream
        assert stream.tvalid.get() == 1, 'tvalid should be high during transmission'
        assert stream.tdata.get() == test_data, 'tdata should contain test_data'
        
        # Complete the handshake by asserting tready
        stream.tready.put(1)
        sys.getSimulator().clk(1)
        
        # After handshake, tvalid should go low and sent should pulse
        assert stream.tvalid.get() == 0, 'tvalid should go low after handshake'
        assert sent.get() == 1, 'sent should be high after transmission'

        ap_done.put(1)
        sys.getSimulator().clk(1)
        ap_done.put(0)
        assert sent.get() == 0, 'sent should be cleared by ap_done'
        
        # sent should be cleared on next ap_start or load_outs
        load_outs.put(0)
        ap_start.put(1)
        sys.getSimulator().clk(1)
        ap_start.put(0)
        sys.getSimulator().clk(1)
        assert sent.get() == 1, 'sent should be set by next ap_start cycle'
    
    def test_ap_start_clears_sent(self):
        """Test that ap_start clears the sent signal"""
        sys = py4hw.HWSystem()
        
        ap_start = sys.wire("ap_start", 1)
        ap_reset = sys.wire("ap_reset", 1)
        ap_done = sys.wire("ap_done", 1)
        load_outs = sys.wire("load_outs", 1)
        reg_in = sys.wire("reg_in", 64)
        sent = sys.wire("sent", 1)
        active = sys.wire("active", 1)
        
        stream = AXI4StreamInterface(sys, "stream", dw=64, has_tlast=True, has_tkeep=True)
        
        dut = Reg2Axi(sys, "reg2axi", ap_start, ap_reset, ap_done, load_outs, reg_in, stream, sent, active)
        
        # Initial reset
        ap_reset.put(1)
        sys.getSimulator().clk(1)
        
        assert active.get() == 0, 'active should be 0 after ap_reset'
        assert sent.get() == 0, 'sent should be zero on reset'
        assert stream.tvalid.get() == 0, 'tvalid should be 0 after ap_reset'
        
        ap_reset.put(0)
        sys.getSimulator().clk(1)
        
        # Load and transmit
        test_data = 0xCCCCCCCCCCCCCCCC
        reg_in.put(test_data)
        
        ap_start.put(1)
        sys.getSimulator().clk(1)
        
        
        assert active.get() == 1, 'circuit should become active'
        assert dut._wires['set_tvalid'].get() == 0, 'set_tvalid should be 0'
        assert stream.tvalid.get() == 0, 'tvalid should be 0'
        
        load_outs.put(1)
        stream.tready.put(1)
        assert dut._wires['reset_tvalid'].get() == 0, 'reset_tvalid should be 0'
        ap_start.put(0)
        sys.getSimulator().clk(1)
        
        
        # Verify transmission completed
        assert dut._wires['set_tvalid'].get() == 1, 'set_tvalid should be 1'
        
        assert stream.tvalid.get() == 1, 'tvalid should be 1'
        assert dut._wires['handshake'].get() == 1, 'handshake should be 1'
        sys.getSimulator().clk(1)
        assert sent.get() == 1, 'sent should be high after transmission'
        
        # Apply ap_start again (should clear sent)
        ap_start.put(1)
        sys.getSimulator().clk(1)
        
        assert sent.get() == 1, 'sent should be one if another ap_start comes, but circuit was active'

        ap_done.put(1)
        sys.getSimulator().clk(1)
        ap_done.put(0)
        ap_start.put(0)

        assert sent.get() == 0, 'sent should be zero after ap_done'
        
        # Verify can transmit again
        
        ap_start.put(1)
        load_outs.put(0)
        sys.getSimulator().clk(1)
        
        
        load_outs.put(1)
        sys.getSimulator().clk(1)
        load_outs.put(0)
        sys.getSimulator().clk(2)
        ap_start.put(0)
        
        assert sent.get() == 1, 'sent should be high again after second transmission'
    
    def test_ap_reset_behavior(self):
        """Test ap_reset clears sent signal and resets state"""
        sys = py4hw.HWSystem()
        
        ap_start = sys.wire("ap_start", 1)
        ap_reset = sys.wire("ap_reset", 1)
        ap_done = sys.wire("ap_done", 1)
        load_outs = sys.wire("load_outs", 1)
        reg_in = sys.wire("reg_in", 64)
        sent = sys.wire("sent", 1)
        active = sys.wire("active", 1)
        
        stream = AXI4StreamInterface(sys, "stream", dw=64, has_tlast=True, has_tkeep=True)
        
        Reg2Axi(sys, "reg2axi", ap_start, ap_reset, ap_done,  load_outs, reg_in, stream, sent, active)
        
        # Initial reset
        ap_reset.put(1)
        sys.getSimulator().clk(1)
        ap_reset.put(0)
        sys.getSimulator().clk(1)
        
        # Load and transmit
        test_data = 0xEEEEEEEEEEEEEEEE
        reg_in.put(test_data)
        load_outs.put(1)
        sys.getSimulator().clk(1)
        load_outs.put(0)
        
        ap_start.put(1)
        stream.tready.put(1)
        sys.getSimulator().clk(2)
        ap_start.put(0)
        
        assert sent.get() == 0, 'sent should be low if load was pulsed before ap_start'
        
        # Apply ap_reset (should clear sent and tvalid)
        ap_reset.put(1)
        sys.getSimulator().clk(2)
        ap_reset.put(0)
        
        assert sent.get() == 0, 'sent should be cleared by ap_reset'
        assert stream.tvalid.get() == 0, 'tvalid should be cleared by ap_reset'
        
        # Verify can transmit again after reset
        
        ap_start.put(1)
        sys.getSimulator().clk(1)
        
        
        load_outs.put(1)
        sys.getSimulator().clk(2)
        ap_start.put(0)
        
        assert sent.get() == 1, 'sent should be high after reset and retransmit'
    
    def test_tready_handshake(self):
        """Test that transmission only completes when tready is asserted"""
        sys = py4hw.HWSystem()
        
        ap_start = sys.wire("ap_start", 1)
        ap_reset = sys.wire("ap_reset", 1)
        ap_done = sys.wire("ap_done", 1)
        load_outs = sys.wire("load_outs", 1)
        reg_in = sys.wire("reg_in", 64)
        sent = sys.wire("sent", 1)
        active = sys.wire("active", 1)
        
        stream = AXI4StreamInterface(sys, "stream", dw=64, has_tlast=True, has_tkeep=True)
        
        Reg2Axi(sys, "reg2axi", ap_start, ap_reset, ap_done, load_outs, reg_in, stream, sent, active)
        
        # Initial reset
        ap_reset.put(1)
        sys.getSimulator().clk(1)
        ap_reset.put(0)
        sys.getSimulator().clk(1)
        
        # Load data and start transmission
        test_data = 0x123456789ABCDEF0
        reg_in.put(test_data)
        load_outs.put(1)
        sys.getSimulator().clk(1)
        
        ap_start.put(1)
        sys.getSimulator().clk(2)
        ap_start.put(0)
        
        # tready is low, so data should be waiting but not completed
        stream.tready.put(0)
        assert stream.tvalid.get() == 1, 'tvalid should be high even without tready'
        assert sent.get() == 0, 'sent should be 0 before handshake completes'
        
        # Assert tready to complete handshake
        stream.tready.put(1)
        sys.getSimulator().clk(1)
        
        # Handshake completes
        assert stream.tvalid.get() == 0, 'tvalid should go low after handshake'
        assert sent.get() == 1, 'sent should be high after handshake'
    
    def test_load_outs_pulse(self):
        """Test that load_outs loads the register and clears sent"""
        sys = py4hw.HWSystem()
        
        ap_start = sys.wire("ap_start", 1)
        ap_reset = sys.wire("ap_reset", 1)
        ap_done = sys.wire("ap_done", 1)
        load_outs = sys.wire("load_outs", 1)
        reg_in = sys.wire("reg_in", 64)
        sent = sys.wire("sent", 1)
        active = sys.wire("active", 1)
        
        stream = AXI4StreamInterface(sys, "stream", dw=64, has_tlast=True, has_tkeep=True)
        
        Reg2Axi(sys, "reg2axi", ap_start, ap_reset, ap_done, load_outs, reg_in, stream, sent, active)
        
        # Initial reset
        ap_reset.put(1)
        sys.getSimulator().clk(1)
        ap_reset.put(0)
        sys.getSimulator().clk(1)
        
        # Load first value
        test_data1 = 0x1111111111111111
        reg_in.put(test_data1)
        load_outs.put(1)
        sys.getSimulator().clk(1)
        load_outs.put(0)
        
        # Transmit
        ap_start.put(1)
        stream.tready.put(1)
        sys.getSimulator().clk(2)
        ap_start.put(0)
        
        assert sent.get() == 0, 'sent should be low after load_outs pulse before ap_start'
        
        # Load second value (should clear sent)
        test_data2 = 0x2222222222222222
        reg_in.put(test_data2)
        load_outs.put(1)
        sys.getSimulator().clk(2)
        load_outs.put(0)
        
        assert sent.get() == 1, 'sent should be high after load_outs pulse after ap_start'
        
        # Transmit second value
        ap_start.put(1)
        sys.getSimulator().clk(2)
        ap_start.put(0)
        
        assert stream.tdata.get() == test_data2, 'tdata should contain second test_data'
        assert sent.get() == 1, 'sent should be high after second transmission'
    
    def test_multiple_loads_before_transmission(self):
        """Test loading multiple values before starting transmission"""
        sys = py4hw.HWSystem()
        
        ap_start = sys.wire("ap_start", 1)
        ap_reset = sys.wire("ap_reset", 1)
        ap_done = sys.wire("ap_done", 1)
        load_outs = sys.wire("load_outs", 1)
        reg_in = sys.wire("reg_in", 64)
        sent = sys.wire("sent", 1)
        active = sys.wire("active", 1)
        
        stream = AXI4StreamInterface(sys, "stream", dw=64, has_tlast=True, has_tkeep=True)
        
        Reg2Axi(sys, "reg2axi", ap_start, ap_reset, ap_done, load_outs, reg_in, stream, sent, active)
        
        # Initial reset
        ap_reset.put(1)
        sys.getSimulator().clk(1)
        ap_reset.put(0)
        sys.getSimulator().clk(1)
        
        # Load multiple values
        values = [0xAAAAAAAAAAAAAAAA, 0xBBBBBBBBBBBBBBBB, 0xCCCCCCCCCCCCCCCC]
        
        for val in values:
            ap_start.put(1)
            stream.tready.put(1)
            sys.getSimulator().clk(2)
            ap_start.put(0)
            
            reg_in.put(val)
            load_outs.put(1)
            sys.getSimulator().clk(1)
            load_outs.put(0)
            sys.getSimulator().clk(1)
            
            # Latest value should be latched
            assert sent.get() == 1, 'sent should be 1'
        
        # Start transmission - should send the last loaded value
        
        
        assert stream.tdata.get() == values[-1], 'should transmit the last loaded value'
        assert sent.get() == 1, 'sent should be high after transmission'
    
    def test_edge_cases(self):
        """Test edge cases like maximum and minimum values"""
        sys = py4hw.HWSystem()
        
        ap_start = sys.wire("ap_start", 1)
        ap_reset = sys.wire("ap_reset", 1)
        ap_done = sys.wire("ap_done", 1)
        load_outs = sys.wire("load_outs", 1)
        reg_in = sys.wire("reg_in", 64)
        sent = sys.wire("sent", 1)
        active = sys.wire("active", 1)
        
        stream = AXI4StreamInterface(sys, "stream", dw=64, has_tlast=True, has_tkeep=True)
        
        Reg2Axi(sys, "reg2axi", ap_start, ap_reset, ap_done, load_outs, reg_in, stream, sent, active)
        
        # Initial reset
        ap_reset.put(1)
        sys.getSimulator().clk(1)
        ap_reset.put(0)
        sys.getSimulator().clk(1)
        
        ap_start.put(1)
        stream.tready.put(1)
        sys.getSimulator().clk(2)
        ap_start.put(0)
        
        # Test all zeros
        reg_in.put(0)
        load_outs.put(1)
        sys.getSimulator().clk(2)
        load_outs.put(0)
        
        
        
        assert stream.tdata.get() == 0, 'should transmit all zeros'
        assert sent.get() == 1, 'sent should be high'
        
        # Clear sent
        load_outs.put(1)
        sys.getSimulator().clk(1)
        load_outs.put(0)
        
        # Test all ones
        reg_in.put((1 << 64) - 1)
        load_outs.put(1)
        sys.getSimulator().clk(1)
        load_outs.put(0)
        
        ap_start.put(1)
        sys.getSimulator().clk(2)
        ap_start.put(0)
        
        assert stream.tdata.get() == (1 << 64) - 1, 'should transmit all ones'
        assert sent.get() == 1, 'sent should be high'
        
        # Clear sent
        load_outs.put(1)
        sys.getSimulator().clk(1)
        load_outs.put(0)
        
        # Test alternating pattern
        pattern = 0x5555555555555555
        reg_in.put(pattern)
        load_outs.put(1)
        sys.getSimulator().clk(1)
        load_outs.put(0)
        
        ap_start.put(1)
        sys.getSimulator().clk(2)
        ap_start.put(0)
        
        assert stream.tdata.get() == pattern, 'should transmit alternating pattern'
        assert sent.get() == 1, 'sent should be high'
    
    def test_ap_start_without_load(self):
        """Test ap_start when no value has been loaded"""
        sys = py4hw.HWSystem()
        
        ap_start = sys.wire("ap_start", 1)
        ap_reset = sys.wire("ap_reset", 1)
        ap_done = sys.wire("ap_done", 1)
        load_outs = sys.wire("load_outs", 1)
        reg_in = sys.wire("reg_in", 64)
        sent = sys.wire("sent", 1)
        active = sys.wire("active", 1)
        
        stream = AXI4StreamInterface(sys, "stream", dw=64, has_tlast=True, has_tkeep=True)
        
        Reg2Axi(sys, "reg2axi", ap_start, ap_reset, ap_done, load_outs, reg_in, stream, sent, active)
        
        # Initial reset
        ap_reset.put(1)
        sys.getSimulator().clk(1)
        ap_reset.put(0)
        sys.getSimulator().clk(1)
        
        # No load_outs - reg_in has default value (0)
        ap_start.put(1)
        stream.tready.put(1)
        sys.getSimulator().clk(2)
        ap_start.put(0)
        
        # Should transmit whatever is in the register (likely 0)
        assert stream.tvalid.get() == 0, 'tvalid should be low after transmission'
        assert stream.tdata.get() == 0, 'tdata should be 0 by default'
        assert sent.get() == 0, 'sent should be 0'
    
    def test_consecutive_transmissions(self):
        """Test multiple consecutive transmissions"""
        sys = py4hw.HWSystem()
        
        ap_start = sys.wire("ap_start", 1)
        ap_reset = sys.wire("ap_reset", 1)
        ap_done = sys.wire("ap_done", 1)
        load_outs = sys.wire("load_outs", 1)
        reg_in = sys.wire("reg_in", 64)
        sent = sys.wire("sent", 1)
        active = sys.wire("active", 1)
        
        stream = AXI4StreamInterface(sys, "stream", dw=64, has_tlast=True, has_tkeep=True)
        
        Reg2Axi(sys, "reg2axi", ap_start, ap_reset, ap_done, load_outs, reg_in, stream, sent, active)
        
        # Initial reset
        ap_reset.put(1)
        sys.getSimulator().clk(1)
        ap_reset.put(0)
        sys.getSimulator().clk(1)
        
        # Transmit 5 consecutive values
        for i in range(5):
            ap_start.put(1)
            stream.tready.put(1)
            sys.getSimulator().clk(2)
            ap_start.put(0)
            
            test_val = i * 0x1111111111111111
            reg_in.put(test_val)
            load_outs.put(1)
            sys.getSimulator().clk(1)
            load_outs.put(0)
            sys.getSimulator().clk(1)
            
            
            
            assert stream.tdata.get() == test_val, f'transmission {i} should have correct value'
            assert sent.get() == 1, f'sent should be high for transmission {i}'
            
            # Clear sent for next iteration (load_outs will clear it)
    
    def test_tready_behavior(self):
        """Test tready behavior at different times"""
        sys = py4hw.HWSystem()
        
        ap_start = sys.wire("ap_start", 1)
        ap_reset = sys.wire("ap_reset", 1)
        ap_done = sys.wire("ap_done", 1)
        load_outs = sys.wire("load_outs", 1)
        reg_in = sys.wire("reg_in", 64)
        sent = sys.wire("sent", 1)
        active = sys.wire("active", 1)
        
        stream = AXI4StreamInterface(sys, "stream", dw=64, has_tlast=True, has_tkeep=True)
        
        Reg2Axi(sys, "reg2axi", ap_start, ap_reset, ap_done, load_outs, reg_in, stream, sent, active)
        
        # Initial reset
        ap_reset.put(1)
        sys.getSimulator().clk(1)
        ap_reset.put(0)
        sys.getSimulator().clk(1)

        # Start without tready
        ap_start.put(1)
        sys.getSimulator().clk(2)
        ap_start.put(0)

        
        test_data = 0x123456789ABCDEF0
        reg_in.put(test_data)
        load_outs.put(1)
        sys.getSimulator().clk(1)
        load_outs.put(0)
        
        
        assert stream.tvalid.get() == 1, 'tvalid should be high waiting for tready the first time'
        assert sent.get() == 0, 'sent should be 0 while waiting for tready'
        
        # Assert tready
        stream.tready.put(1)
        sys.getSimulator().clk(1)
        
        assert stream.tvalid.get() == 0, 'tvalid should go low after handshake'
        assert sent.get() == 1, 'sent should be high after handshake'
        
        # De-assert tready for next transmission
        stream.tready.put(0)
        
        ap_done.put(1)
        sys.getSimulator().clk(2)
        ap_done.put(0)
        
        ap_start.put(1)
        sys.getSimulator().clk(2)
        ap_start.put(0)
        
        assert sent.get() == 0, 'sent should be 0 after ap_start'
        
        # Try another transmission
        test_data2 = 0xFEDCBA9876543210
        reg_in.put(test_data2)
        load_outs.put(1)
        sys.getSimulator().clk(1)
        load_outs.put(0)
        
        
        
        assert stream.tvalid.get() == 1, 'tvalid should be high waiting for tready'
        assert stream.tdata.get() == test_data2, 'tdata should have new data'
        assert sent.get() == 0, 'sent should still be 0 if tready never asserted'
        
        # Assert tready to complete
        stream.tready.put(1)
        sys.getSimulator().clk(1)
        
        assert sent.get() == 1, 'sent should be high after second handshake'

if __name__ == '__main__':
    pytest.main(args=['-s', __file__])