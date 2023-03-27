import py4hw
import py4hw.debug
import pytest

class Test_Mul:

    def test_integrity(self):

        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 4)
        b = sys.wire("b", 4)
        r1 = sys.wire("r1", 4)
        r2 = sys.wire("r2", 4)
        
        py4hw.Constant(sys, "a", 7, a)
        py4hw.Constant(sys, "b", 3, b)
        
        py4hw.Mul(sys, 'mul', a, b, r1)
        py4hw.SignedMul(sys, 'signed_mul', a, b, r2)
        
        py4hw.debug.checkIntegrity(sys)


    def test_mul(self):

        sys = py4hw.HWSystem()
        
        w=8
        a = sys.wire("a", w)
        b = sys.wire("b", w)
        r = sys.wire("r", w)
        
        py4hw.Constant(sys, "a", 7, a)
        py4hw.Constant(sys, "b", 3, b)
        
        py4hw.Mul(sys, 'mul', a, b, r)
        
        sys.getSimulator().clk(1)
        
        assert(r.get() == (7*3))    
        
        
    def test_neg(self):

        sys = py4hw.HWSystem()
        w = 32
        va = 21
        vb = -3
        vr = va * vb
        
        a = sys.wire("a", w)
        b = sys.wire("b", w)
        r = sys.wire("r", w)
        
        py4hw.Constant(sys, "a", va, a)
        py4hw.Constant(sys, "b", vb, b)
        
        py4hw.SignedMul(sys, 'equal', a, b, r)
        
        sys.getSimulator().clk(1)
        
        assert(r.get() == (vr & ((1<<w)-1)))
        

    # def test_random(self):
    #     import random
    #     sys = py4hw.HWSystem()
        
    #     w = 32
    #     a = sys.wire("a", w)
    #     b = sys.wire("b", w)
    #     r = sys.wire("r", w)
        
    #     ca = py4hw.Constant(sys, "a", 7, a)
    #     cb = py4hw.Constant(sys, "b", 3, b)
        
    #     py4hw.Div(sys, 'equal', a, b, r)
        
    #     for i in range(10000):
    #         va = int((random.random()-0.5) * ((1<<w)-1))
    #         vb =  int((random.random()-0.5) * ((1<<w)-1))
    #         vr = va * vb
    #         ca.value = va            
    #         cb.value = vb            
    #         sys.getSimulator().clk(1)
        
    #         assert(r.get() == (vr & ((1<<w)-1)))


if __name__ == '__main__':
    pytest.main(args=['-s', 'Test_Mul.py'])