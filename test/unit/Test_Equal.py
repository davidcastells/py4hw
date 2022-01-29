import py4hw
import py4hw.debug
import pytest

class Test_Equal:

    def test_integrity(self):

        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 2)
        r = sys.wire("r", 1)
        
        py4hw.Constant(sys, "a", 0, a)
        
        py4hw.EqualConstant(sys, 'equal', a, 0, r)
        
        py4hw.debug.checkIntegrity(sys)

    def test_1(self):

        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 2)
        r = sys.wire("r", 1)
        
        py4hw.Constant(sys, "a", 0, a)
        
        py4hw.EqualConstant(sys, 'equal', a, 0, r)
        
        sys.getSimulator().clk(1)
        
        assert (r.get() == 1)
        
    def test_notEqual(self):

        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 2)
        r = sys.wire("r", 1)
        
        py4hw.Constant(sys, "a", 3, a)
        
        py4hw.EqualConstant(sys, 'equal', a, 0, r)
        
        sys.getSimulator().clk(1)
        
        assert (r.get() == 0)
        
    def test_equal5(self):

        print('check values = 5')
        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 3)
        r = sys.wire("1", 1)
        
        py4hw.Sequence(sys, "a", [0,1,2,3,4,5,6,7], a)
        
        py4hw.EqualConstant(sys, 'equal', a, 5, r)
        
        for i in range(8):
            sys.getSimulator().clk(1)  
            v = a.get()
            rv = r.get()
            exp = 1 if (v==5) else 0
            print(v, exp, rv)
            assert (rv == exp)    
            
    def test_oneBitWire(self):
        print('check values = 1')
        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 1)
        r = sys.wire("1", 1)
        
        py4hw.Sequence(sys, "a", [0,1], a)
        
        py4hw.EqualConstant(sys, 'equal', a, 1, r)
        
        for i in range(8):
            sys.getSimulator().clk(1)  
            v = a.get()
            exp = 1 if (v==1) else 0
            print(v, exp, r.get())
            assert (r.get() == exp)    
            
    def test_EqualWire(self):
        print('check values = 5')
        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 3)
        b = sys.wire("b", 3)
        c = sys.wire("c", 3)
        r1 = sys.wire("r1", 1)
        r2 = sys.wire("r2", 1)
        
        
        py4hw.Constant(sys, "a", 3, a)
        py4hw.Constant(sys, "b", 3, b)
        py4hw.Constant(sys, "c", 5, c)
        
        py4hw.Equal(sys, 'equal1', a, b, r1)
        py4hw.Equal(sys, 'equal2', a, c, r2)
        
        sys.getSimulator().clk(1)
        assert (r1.get() == 1)
        assert (r2.get() == 0)

if __name__ == '__main__':
    pytest.main(args=['-q', 'Test_Equal.py'])