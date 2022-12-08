import py4hw
import py4hw.debug
import pytest
from py4hw.helper import *

class Test_SignedDiv:

    def test_integrity(self):
        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 4)
        b = sys.wire("b", 4)
        r = sys.wire("r", 4)
        
        py4hw.Constant(sys, "a", 7, a)
        py4hw.Constant(sys, "b", 3, b)
        
        py4hw.SignedDiv(sys, 'equal', a, b, r)
        
        py4hw.debug.checkIntegrity(sys)


    def test_pos_pos(self):

        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 4)
        b = sys.wire("b", 4)
        r = sys.wire("r", 4)
        
        py4hw.Constant(sys, "a", 7, a)
        py4hw.Constant(sys, "b", 3, b)
        
        py4hw.SignedDiv(sys, 'equal', a, b, r)
        
        sys.getSimulator().clk(1)
        
        assert(r.get() == (7//3))    
        
    def test_neg_pos(self):

        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 4)
        b = sys.wire("b", 4)
        r = sys.wire("r", 4)
        
        py4hw.Constant(sys, "a", -7, a)
        py4hw.Constant(sys, "b", 3, b)
        
        py4hw.SignedDiv(sys, 'equal', a, b, r)
        
        sys.getSimulator().clk(1)
        
        assert(r.get() == IntegerHelper.signed_to_c2(-(7//3), b.getWidth()))    
        
        
    def test_pos_neg(self):

        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 4)
        b = sys.wire("b", 4)
        r = sys.wire("r", 4)
        
        py4hw.Constant(sys, "a", 7, a)
        py4hw.Constant(sys, "b", -3, b)
        
        py4hw.SignedDiv(sys, 'equal', a, b, r)
        
        sys.getSimulator().clk(1)
        
        assert(r.get() == IntegerHelper.signed_to_c2(-(7//3), b.getWidth()))
        
    def test_neg_neg(self):

        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 4)
        b = sys.wire("b", 4)
        r = sys.wire("r", 4)
        
        py4hw.Constant(sys, "a", -7, a)
        py4hw.Constant(sys, "b", -3, b)
        
        py4hw.SignedDiv(sys, 'equal', a, b, r)
        
        sys.getSimulator().clk(1)
        
        assert(r.get() == (7//3))
        
    def test_random(self):
        import random
        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 32)
        b = sys.wire("b", 32)
        r = sys.wire("r", 32)
        
        ca = py4hw.Constant(sys, "a", 7, a)
        cb = py4hw.Constant(sys, "b", 3, b)
        
        py4hw.SignedDiv(sys, 'equal', a, b, r)
        
        for i in range(10000):
            va = (1<<31) - int(random.random() * ((1<<32)-1))
            vb =  (1<<31) - int(random.random() * ((1<<32)-1))
            ca.value = IntegerHelper.signed_to_c2(va, 32)    
            cb.value = IntegerHelper.signed_to_c2(vb, 32)         
            sys.getSimulator().clk(1)
        
            vq = (abs(va)//abs(vb)) * IntegerHelper.sign(va) * IntegerHelper.sign(vb)
            if not(IntegerHelper.c2_to_signed(r.get(), 32) == vq):
                raise Exception('va: {} / vb: {} = '.format(va, vb))

if __name__ == '__main__':
    pytest.main(args=['-q', 'Test_SignedDiv.py'])