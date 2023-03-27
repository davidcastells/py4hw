import py4hw
import py4hw.debug
import pytest

class Test_Div:

    def test_integrity(self):

        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 4)
        b = sys.wire("b", 4)
        r = sys.wire("r", 4)
        
        py4hw.Constant(sys, "a", 7, a)
        py4hw.Constant(sys, "b", 3, b)
        
        py4hw.Div(sys, 'equal', a, b, r)
        
        py4hw.debug.checkIntegrity(sys)


    def test_div(self):

        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 4)
        b = sys.wire("b", 4)
        r = sys.wire("r", 4)
        
        py4hw.Constant(sys, "a", 7, a)
        py4hw.Constant(sys, "b", 3, b)
        
        py4hw.Div(sys, 'equal', a, b, r)
        
        sys.getSimulator().clk(1)
        
        assert(r.get() == (7//3))    
        
        
    def test_neg_den(self):

        sys = py4hw.HWSystem()
        w = 32
        va = 21
        vb = -3
        vr = va // vb
        
        a = sys.wire("a", w)
        b = sys.wire("b", w)
        r = sys.wire("r", w)
        
        py4hw.Constant(sys, "a", va, a)
        py4hw.Constant(sys, "b", vb, b)
        
        py4hw.SignedDiv(sys, 'equal', a, b, r)
        
        sys.getSimulator().clk(1)
        
        assert(r.get() == (vr & ((1<<w)-1)))
        

    def test_random(self):
        import random
        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 32)
        b = sys.wire("b", 32)
        r = sys.wire("r", 32)
        
        ca = py4hw.Constant(sys, "a", 7, a)
        cb = py4hw.Constant(sys, "b", 3, b)
        
        py4hw.Div(sys, 'equal', a, b, r)
        
        for i in range(10000):
            va = int(random.random() * ((1<<32)-1))
            vb =  int(random.random() * ((1<<32)-1))
            ca.value = va            
            cb.value = vb            
            sys.getSimulator().clk(1)
        
            assert(r.get() == (va//vb))    


if __name__ == '__main__':
    pytest.main(args=['-q', 'Test_Div.py'])