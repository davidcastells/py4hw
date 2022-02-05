# -*- coding: utf-8 -*-
"""
Created on Sat Oct 31 11:52:40 2020

@author: dcr
"""

# -*- coding: utf-8 -*-
"""
Created on Sat Oct 31 11:19:05 2020

@author: dcr
"""
import py4hw
import py4hw.debug
import pytest


class Test_Minterm:

    def test_integrity(self):
        sys = py4hw.HWSystem()
        
        a = sys.wire("a", 2)
        
        bits = sys.wires('b', 2, 1)
        minterm = sys.wire('minterm',1)
        
        py4hw.BitsLSBF(sys, 'bits', a, bits)
        py4hw.Minterm(sys, 'minterm', bits, 0, minterm)
        py4hw.Constant(sys, "a", 0, a)
        
        for i in range(len(bits)):
            py4hw.Scope(sys, 'b{}'.format(i), bits[i])
        
        py4hw.Scope(sys, 'minterm_5', minterm)
        
        
        py4hw.debug.checkIntegrity(sys)
        
    def test_1(self):
        print('testing minterms equal to 5')
        sys = py4hw.HWSystem()
        r = sys.wire("r", 1)
        a0 = sys.wire("a0", 1)
        a1 = sys.wire("a1", 1)
        a2 = sys.wire("a2", 1)
        
        exp_a0 = [0,1,0,1,0,1,0,1]
        exp_a1 = [0,0,1,1,0,0,1,1]
        exp_a2 = [0,0,0,0,1,1,1,1]
        py4hw.Sequence(sys, "a0", exp_a0, a0)
        py4hw.Sequence(sys, "a1", exp_a1, a1)
        py4hw.Sequence(sys, "a2", exp_a2, a2)

        py4hw.Minterm(sys, 'minterm', [a0, a1, a2], 5, r)
        
        for i in range(8):
            sys.getSimulator().clk(1)
            rv = r.get()
            a0v = a0.get()
            a1v = a1.get()
            a2v = a2.get()
            print(a2v, a1v, a0v, rv)
            
            assert (a0v == exp_a0[i])
            assert (a1v == exp_a1[i])
            assert (a2v == exp_a2[i])
        #self.assertEqual(first, second)
        
if __name__ == '__main__':
    pytest.main(args=['-q', 'Test_Minterm.py'])