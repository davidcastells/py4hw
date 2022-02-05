# -*- coding: utf-8 -*-
"""
Created on Wed Feb  2 09:40:27 2022

@author: dcr
"""

import py4hw
import py4hw.debug
import pytest

class Test_Concatenate:
    
    
    def test_concat_msbf_1(self):
        sys = py4hw.HWSystem()
        a = sys.wire("a", 8)
        b = sys.wire("b", 8)
        r = sys.wire("r", 16)

        av = 0x5F
        bv = 0x37
        
        py4hw.ConcatenateMSBF(sys, "concat", [a,b], r)
        
        a.put(av)
        b.put(bv)
        
        sys.getSimulator().clk(1);
        assert (r.get() == 0x5F37)

    def test_concat_lsbf_1(self):
        sys = py4hw.HWSystem()
        a = sys.wire("a", 8)
        b = sys.wire("b", 8)
        r = sys.wire("r", 16)

        av = 0x5F
        bv = 0x37
        
        py4hw.ConcatenateLSBF(sys, "concat", [a,b], r)
        
        a.put(av)
        b.put(bv)
        
        sys.getSimulator().clk(1);
        assert (r.get() == 0x375F)
        
    def test_concat_msbf_2(self):
        sys = py4hw.HWSystem()
        a = sys.wire("a", 8)
        b = sys.wire("b", 8)
        c = sys.wire("c", 8)
        r = sys.wire("r", 24)

        av = 0x5F
        bv = 0x37
        cv = 0xD1
        
        py4hw.ConcatenateMSBF(sys, "concat", [a,b,c], r)
        
        a.put(av)
        b.put(bv)
        c.put(cv)
        
        sys.getSimulator().clk(1);
        assert (r.get() == 0x5F37D1)
        
    def test_concat_lsbf_2(self):
        sys = py4hw.HWSystem()
        a = sys.wire("a", 8)
        b = sys.wire("b", 8)
        c = sys.wire("c", 8)
        r = sys.wire("r", 24)

        av = 0x5F
        bv = 0x37
        cv = 0xD1
        
        py4hw.ConcatenateLSBF(sys, "concat", [a,b,c], r)
        
        a.put(av)
        b.put(bv)
        c.put(cv)
        
        sys.getSimulator().clk(1);
        assert (r.get() == 0xD1375F)

    def test_msbf_3(self):
        sys = py4hw.HWSystem()
        a = sys.wire("a", 1)
        b = sys.wire("b", 8)
        c = sys.wire("c", 23)
        r = sys.wire("r", 32)

        av = 0
        bv = 127
        cv = 2516585
        ev = (127 << 23) | cv
        
        py4hw.ConcatenateMSBF(sys, "concat", [a,b,c], r)
        
        a.put(av)
        b.put(bv)
        c.put(cv)
        
        sys.getSimulator().clk(1);
        assert (r.get() == ev)

    def test_lsbf_3(self):
        sys = py4hw.HWSystem()
        a = sys.wire("a", 1)
        b = sys.wire("b", 8)
        c = sys.wire("c", 23)
        r = sys.wire("r", 32)

        av = 0
        bv = 127
        cv = 2516585
        ev = (((cv << 8) | bv) << 1) | av
        
        py4hw.ConcatenateLSBF(sys, "concat", [a,b,c], r)
        
        a.put(av)
        b.put(bv)
        c.put(cv)
        
        sys.getSimulator().clk(1);
        assert (r.get() == ev)

    def test_2(self):
        sys = py4hw.HWSystem()
        a = sys.wire("a", 5)
        b = sys.wire("b", 7)
        c = sys.wire("c", 11)
        r = sys.wire("r", 32)

        av = 11
        bv = 23
        cv = 111
        ev = (((av << 7) | bv ) << 11) | cv
        
        py4hw.ConcatenateMSBF(sys, "concat", [a,b,c], r)
        
        a.put(av)
        b.put(bv)
        c.put(cv)
        
        sys.getSimulator().clk(1);
        assert (r.get() == ev)
        
        
    def test_3(self):
        # concatenating larger wires should raise an error
        sys = py4hw.HWSystem()
        a = sys.wire("a", 13)
        b = sys.wire("b", 23)
        c = sys.wire("c", 11)
        r = sys.wire("r", 32)

        av = 11
        bv = 23
        cv = 111
        
        try:
            py4hw.ConcatenateMSBF(sys, "concat", [a,b,c], r)
            
            a.put(av)
            b.put(bv)
            c.put(cv)
            
            sys.getSimulator().clk(1);
            exception = False
        except:
            exception = True
            
        assert(exception)

if __name__ == '__main__':
    pytest.main(args=['-q', 'Test_Concatenate.py'])