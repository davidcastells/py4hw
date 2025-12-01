# -*- coding: utf-8 -*-
import py4hw
import py4hw.debug
import pytest

class Test_SignedAdd:
    
    
    def test_1(self):
        sys = py4hw.HWSystem()
        a = sys.wire("a", 32)
        b = sys.wire("b", 32)
        r1 = sys.wire("r", 32)
        py4hw.Constant(sys, "a", 20, a)
        py4hw.Constant(sys, "b", -10, b)
        py4hw.SignedAdd(sys, "add1", a,b, r1)
        sys.getSimulator().clk(1);
        assert (r1.get() == 10)
    
    def test_2(self):
        sys = py4hw.HWSystem()
        a = sys.wire("a", 32)
        b = sys.wire("b", 32)
        r1 = sys.wire("r", 32)
        py4hw.Constant(sys, "a", -20, a)
        py4hw.Constant(sys, "b", 10, b)
        py4hw.SignedAdd(sys, "add1", a,b, r1)
        sys.getSimulator().clk(1);
        assert (r1.get() == (-10 & ((1<<32) -1)))
        
    def test_3(self):
        sys = py4hw.HWSystem()
        a = sys.wire("a", 32)
        b = sys.wire("b", 32)
        r1 = sys.wire("r", 32)
        py4hw.Constant(sys, "a", -20, a)
        py4hw.Constant(sys, "b", -10, b)
        py4hw.SignedAdd(sys, "add1", a,b, r1)
        sys.getSimulator().clk(1);
        assert (r1.get() == (-30 & ((1<<32) -1)))
        
    def test_Integrity(self):
        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 32)
        b = sys.wire("b", 32)
        c = sys.wire("c", 32)
        r1 = sys.wire("r", 32)
        r2 = sys.wire("r2", 32)
        
        py4hw.SignedAdd(sys, "add1", a,b, r1)
        py4hw.SignedAdd(sys, "add2", r1, c, r2)
        
        py4hw.Constant(sys, "a", 10, a)
        py4hw.Constant(sys, "b", 20, b)
        py4hw.Constant(sys, "c", 5, c)
        py4hw.Scope(sys, "r2", r2)
        
        py4hw.debug.checkIntegrity(sys)
        # py4hw.debug.printHierarchy(sys)
        
        # print('RESET')
        # sim = sys.getSimulator()
        
        # print()
        # print('CLK')
        # sim.clk(1)

    def test_verilog_gen(self):
        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 32)
        b = sys.wire("b", 32)
        r = sys.wire("r", 32)
        
        dut = py4hw.SignedAdd(sys, "abs", a, b, r)

        rtl = py4hw.VerilogGenerator(dut)
        print(rtl.getVerilogForHierarchy(dut))

if __name__ == '__main__':
    pytest.main(args=['-s', 'Test_SignedAdd.py'])