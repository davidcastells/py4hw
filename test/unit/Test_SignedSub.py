# -*- coding: utf-8 -*-
"""
Created on Tue Feb  1 13:46:38 2022

@author: dcr
"""
import py4hw
import pytest

# Note: The test battery relies on Python's behavior where a negative number 
# masked with (1<<w)-1 correctly yields the two's complement representation 
# that the py4hw simulator will output.

class Test_SignedSub:
    """
    Unit tests for the py4hw.SignedSub component.
    
    Tests include:
    1. Standard signed subtraction (positive and negative results).
    2. Boundary cases involving the minimum signed number (-2^(w-1)).
    3. Verilog generation integrity.
    """
    
    def get_signed_result(self, w: int, va: int, vb: int) -> int:
        """
        Helper function to instantiate and simulate a py4hw.SignedSub
        operation, returning the final result from the simulator.
        
        :param w: Bit width of the operation.
        :param va: Signed value of input A.
        :param vb: Signed value of input B.
        :return: The W-bit unsigned integer value representing the signed result.
        """
        sys = py4hw.HWSystem()

        a = sys.wire('a', w)
        b = sys.wire('b', w)
        r = sys.wire('r', w)
        
        # Use Constant to set the signed input values
        py4hw.Constant(sys, 'a_const', va, a)
        py4hw.Constant(sys, 'b_const', vb, b)
        
        # The Device Under Test (DUT)
        py4hw.SignedSub(sys, 'signed_sub_dut', a, b, r)
        
        # Run the simulation for one clock cycle
        sys.getSimulator().clk(1)
        
        # The result from r.get() is the raw W-bit unsigned value (two's complement)
        return r.get()
    
    def test_signed_subtraction(self):
        """
        Tests various signed subtraction scenarios including positive, 
        negative, and boundary results across different bit widths.
        
        Test fields: [W, Input A (signed), Input B (signed), Expected Result (signed)]
        """
        
        # 8-bit range is -128 to 127
        # 32-bit range is -2147483648 to 2147483647
        battery = [
            # 8-bit tests (W=8)
            [8, 10, 5, 5],          # 10 - 5 = 5
            [8, 5, 10, -5],         # 5 - 10 = -5 (251 in 2's complement)
            [8, -1, 1, -2],         # -1 - 1 = -2 (254 in 2's complement)
            [8, -10, -5, -5],       # -10 - (-5) = -5 (251 in 2's complement)
            [8, 127, 0, 127],       # Max positive - 0 = Max positive
            [8, -128, 0, -128],     # Max negative - 0 = Max negative
            [8, 127, -1, -128],     # 127 - (-1) = 128 -> Overflow to -128 
            [8, -128, 1, 127],      # -128 - 1 = -129 -> Underflow to 127

            # 32-bit tests (W=32)
            [32, 1000, 500, 500],
            [32, 500, 1000, -500],
            [32, -1, 1, -2],
            [32, -1000, -2000, 1000], # -1000 - (-2000) = 1000
        ]
        
        for t in battery:
            w = t[0]
            va = t[1]
            vb = t[2]
            expected_signed_result = t[3]
            
            # This calculation ensures the expected_result (vr) is the correct
            # W-bit two's complement representation, matching the hardware output.
            vr = expected_signed_result & ((1 << w) - 1)
            
            result = self.get_signed_result(w, va, vb)
            
            # Print for better debugging/visibility when running tests
            # print(f"W={w}, {va} - {vb} = {expected_signed_result} (Expected HW: {vr}, Got: {result})")
            
            assert(result == vr), f"Failed: {va} - {vb} (W={w}). Expected HW value: {vr}, Got: {result}"
            
    def test_verilog_gen_signed_sub(self):
        """
        Tests the Verilog code generation for the SignedSub component.
        """
        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 16)
        b = sys.wire("b", 16)
        r = sys.wire("r", 16)
        
        # Instantiate the SignedSub DUT
        dut = py4hw.SignedSub(sys, "signed_sub", a, b, r)

        # Generate Verilog
        rtl = py4hw.VerilogGenerator(dut)
        print('RTL:', rtl.getVerilogForHierarchy(dut))
        
        
if __name__ == '__main__':
    pytest.main(args=['-s', 'Test_SignedSub.py'])