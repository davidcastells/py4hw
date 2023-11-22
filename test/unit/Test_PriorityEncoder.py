# -*- coding: utf-8 -*-
import py4hw
import py4hw.debug
import pytest

class Test_Add:
    
    
        
    def test_1(self):
        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 32)
        b = sys.wire("b", 32)
        ab = sys.wires('ab', 32, 1)
        bb = sys.wires('bb', 32, 1)
        
        py4hw.BitsLSBF(sys, "ab", a, ab)
        py4hw.PriorityEncoder(sys, 'bb', ab, bb)
        py4hw.ConcatenateLSBF(sys, 'b', bb, b)
        
        py4hw.Constant(sys, "a", 127, a)
        
        sim = sys.getSimulator()
        sim.clk(1)

        #print('B=', b.get())
        assert(b.get() == 64)
        # print()
        # print('CLK')
        

if __name__ == '__main__':
    pytest.main(args=['-q', 'Test_PriorityEncoder.py'])