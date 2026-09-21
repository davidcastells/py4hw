# -*- coding: utf-8 -*-
"""
Created on Sun Sep 20 08:50:24 2026

@author: dcr
"""


import py4hw
import py4hw.debug
import pytest


class Test_RingCounter:

    def test_integrity(self):
        sys = py4hw.HWSystem()

        reset = sys.wire('reset')
        enable = sys.wire('enable')
        q = sys.wire('q', 8)

        py4hw.Constant(sys, 'reset', 0, reset)
        py4hw.Constant(sys, 'enable', 1, enable)

        py4hw.RingCounter(sys, 'ringcounter', reset, enable, q)

        py4hw.debug.checkIntegrity(sys)

    def test_integrity_init(self):
        sys = py4hw.HWSystem()

        reset = sys.wire('reset')
        enable = sys.wire('enable')
        q = sys.wire('q', 8)

        py4hw.Constant(sys, 'reset', 0, reset)
        py4hw.Constant(sys, 'enable', 1, enable)

        py4hw.RingCounter(sys, 'ringcounter', reset, enable, q, init=1)

        py4hw.debug.checkIntegrity(sys)

    def test_1(self):
        # Visual test: reset, then enable pulses (same stimulus as Test_Counter)
        sys = py4hw.HWSystem()

        reset = sys.wire('reset')
        enable = sys.wire('enable')
        q = sys.wire('q', 8)

        py4hw.Sequence(sys, 'reset', [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], reset)
        py4hw.Sequence(sys, 'enable', [0, 1, 1, 1, 0, 1, 1, 1, 0, 1], enable)

        py4hw.RingCounter(sys, 'ringcounter', reset, enable, q)

        py4hw.Scope(sys, 'q', [q])
        sys.getSimulator().clk(20)

    def test_one_hot(self):
        # ASSUMPTION: a ring counter keeps exactly one bit set while enabled.
        # Adjust if your RingCounter implementation behaves differently.
        sys = py4hw.HWSystem()

        reset = sys.wire('reset')
        enable = sys.wire('enable')
        q = sys.wire('q', 8)

        py4hw.Constant(sys, 'reset', 0, reset)
        py4hw.Constant(sys, 'enable', 1, enable)

        py4hw.RingCounter(sys, 'ringcounter', reset, enable, q, init=1)

        sim = sys.getSimulator()
        sim.clk(1)  # let the initial value settle

        for _ in range(16):  # two full rotations
            value = q.get()
            assert bin(value).count('1') == 1, f'q is not one-hot: {value:#010b}'
            sim.clk(1)


if __name__ == '__main__':
    pytest.main(args=['-q', 'Test_RingCounter.py'])