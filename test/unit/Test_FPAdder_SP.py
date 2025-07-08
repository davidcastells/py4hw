# -*- coding: utf-8 -*-
"""
Created on Wed Feb  2 11:41:01 2022

@author: dcr
"""
import py4hw
import pytest
from py4hw.helper import BitManipulation
import random

class Test_FPAdder_SP:
    
    def test_1(self):
        
        sys = py4hw.HWSystem()
        g = py4hw.LogicHelper(sys)
        fp = py4hw.FloatingPointHelper()
        
        r = sys.wire('r', 32)
        
        av = 1.2
        bv = 0.0000002
        a = g.hw_constant(32, fp.sp_to_ieee754(av))
        b = g.hw_constant(32, fp.sp_to_ieee754(bv))
        
        fpa = py4hw.FPAdder_SP(sys, 'fpa', a, b, r)
        
        sys.getSimulator().clk(1)
        
        err = fp.ieee754_to_sp(r.get()) - (av+bv)
        assert (abs(err) < 1E-7)

    def test_2(self):
        
        sys = py4hw.HWSystem()
        g = py4hw.LogicHelper(sys)
        fp = py4hw.FloatingPointHelper()
        
        r = sys.wire('r', 32)
        
        av = 0.0000002
        bv = 1.2
        a = g.hw_constant(32, fp.sp_to_ieee754(av))
        b = g.hw_constant(32, fp.sp_to_ieee754(bv))
        
        print('TESTING: ', av, bv)

        fpa = py4hw.FPAdder_SP(sys, 'fpa', a, b, r)
        
        sys.getSimulator().clk(1)
        
        err = fp.ieee754_to_sp(r.get()) - (av+bv)
        assert (abs(err) < 1E-7)


    def test_3(self):
        
        sys = py4hw.HWSystem()
        g = py4hw.LogicHelper(sys)
        fp = py4hw.FloatingPointHelper()
        
        r = sys.wire('r', 32)
        
        av = -4.2
        bv = 3.5
        a = g.hw_constant(32, fp.sp_to_ieee754(av))
        b = g.hw_constant(32, fp.sp_to_ieee754(bv))
        
        
        fpa = py4hw.FPAdder_SP(sys, 'fpa', a, b, r)
        
        sys.getSimulator().clk(1)
        
        err = fp.ieee754_to_sp(r.get()) - (av+bv)
        
        print('TESTING: ', hex(a.get()), '+', hex(b.get()), '=', hex(r.get()))

        assert (abs(err) < 1E-6)

    def test_random(self):
        sys = py4hw.HWSystem()
        g = py4hw.LogicHelper(sys)
        fp = py4hw.FloatingPointHelper()
        
        r = sys.wire('r', 32)
        
        a = sys.wire('a', 32)
        b = sys.wire('b', 32)
        
        ca = py4hw.Constant(sys, 'a', 0, a)
        cb = py4hw.Constant(sys, 'b', 0, b)
        
        fpa = py4hw.FPAdder_SP(sys, 'fpa', a, b, r)

        for i in range(100):
            av = random.uniform(-100, 100)
            bv = random.uniform(-100, 100)
            
            ca.value = fp.sp_to_ieee754(av);
            cb.value = fp.sp_to_ieee754(bv)
            
            sys.getSimulator().clk(1)
            
            rv = fp.ieee754_to_sp(r.get())
            rerr = abs(rv - (av+bv)) / abs(av+bv)
            
            print('TESTING: ', hex(a.get()), '+', hex(b.get()), '=', hex(r.get()), 'rerr:', rerr)
    
            assert (rerr < 1E-5)


    def test_3_deep(self):
        import math
        # a detailed verification checking the steps of the algorithm
        sys = py4hw.HWSystem()
        g = py4hw.LogicHelper(sys)
        fp = py4hw.FloatingPointHelper()
        
        r = sys.wire('r', 32)
        
        av = 1.2
        bv = 0.0000002
        
        print('Computing {}+{}={}'.format(av, bv, av+bv))
        
        a = g.hw_constant(32, fp.sp_to_ieee754(av))
        b = g.hw_constant(32, fp.sp_to_ieee754(bv))
        
        sa, ea, ma = fp.sp_to_fixed_point_parts(av)
        sb, eb, mb = fp.sp_to_fixed_point_parts(bv)
        
        fpa = py4hw.FPAdder_SP(sys, 'fpa', a, b, r)
        
        sys.getSimulator().clk(1)
        
        # 
        assert(fpa.children['parts_a_raw'].getOutPortByName('e').wire.get() == ea + 127)
        assert(fpa.children['parts_b_raw'].getOutPortByName('e').wire.get() == eb + 127)
        assert(fpa.children['parts_a'].getOutPortByName('m').wire.get() == ma)
        assert(fpa.children['parts_b'].getOutPortByName('m').wire.get() == mb)

        print()        
        print('a = {},{:0X},{:06X}'.format(sa, ea, ma), av)
        print('b = {},{:0X},{:06X}'.format(sb, eb, mb), bv)

        # We swap before start, so we are sure than |a| > |b|

        #  1. Exponent subtraction: Perform subtraction of the exponents to 
        # form the absolute difference |Ea - Eb| = d.
        exp_d = abs(ea-eb)
        assert(fpa.children['ediff'].getOutPortByName('r').wire.get() == exp_d)
        print('Exponent difference = ', exp_d)
        
        # 2. Alignment: Right shift the significand of the smaller operand by d bits. 
        # The larger exponent is denoted Ef.
        significand_a = (1 << 23) | ma
        significand_b = (1 << 23) | mb
        exp_m_b_shifted = significand_b >> exp_d
        print('Shifting {} by {}'.format(hex(significand_b), exp_d))
        assert(fpa.children['preshift'].getOutPortByName('r').wire.get() == exp_m_b_shifted)

        significand_b = exp_m_b_shifted
        
        print('ma = ', hex(significand_a), '{:024b}'.format(significand_a))
        print('mb = ', hex(significand_b), '{:024b}'.format(significand_b))
        
        # 3. Significand addition: Perform addition or subtraction according to 
        # the effective operation, which is a function of the opcode and the signs 
        # of the operands.
        
        # a > b
        #  swapped | sa  | sb | operation | inversion | result
        #   no       +0   +0    |a| + |b|    no        |a| + |b|
        #   no       +0   -1    |a| - |b|    no        |a| - |b|
        #`  no       -1   +0    |a| - |b|    yes       -(|a| - |b|) 
        #   no       -1   -1    |a| + |b|    yes       -(|a| + |b|)
        exp_a_plus_b = significand_a + significand_b
        exp_a_minus_b = significand_a - significand_b
        assert(fpa.children['m_a_plus_b'].getOutPortByName('r').wire.get() == exp_a_plus_b)
        assert(fpa.children['m_a_minus_b'].getOutPortByName('r').wire.get() == exp_a_minus_b)
        
        print('ma + mb ', hex(exp_a_plus_b ), '{:025b}'.format(exp_a_plus_b))
        print('ma - mb ', hex(exp_a_minus_b ), '{:025b}'.format(exp_a_minus_b))
        
        exp_op_sub = (~sa & sb) | (sa & ~sb) 
        exp_inv_result = sa 
        assert(fpa.children['select_mr'].getInPortByName('sel').wire.get() == exp_op_sub)
        assert(fpa.children['sr'].getOutPortByName('r').wire.get() == exp_inv_result)
        
        print('Operation = ', 'sub' if (exp_op_sub == 1) else 'add')
        print('Final sign', -1*exp_inv_result)
        
        pre_shift_value = exp_a_minus_b if exp_op_sub == 1 else exp_a_plus_b
        
        assert(fpa.children['select_mr'].getOutPortByName('r').wire.get() == pre_shift_value )
               
        # 4. Conversion: Convert the significand result, when negative, to a sign-magnitude
        # representation. The conversion requires a two's complement operation, including 
        # an addition step.
        
        # this is not necessary as a > b , the swaping does not change anything,
        # as signs are maintained
        
        
        # 5. Leading-one detection: Determine the. amount of left shift needed in the case
        # of subtraction yielding cancellation. Priority encode (PENC) the result to
        # drive the normalizing shifter.
        
        assert(fpa.children['select_mr'].getOutPortByName('r').wire.getWidth() == 25) 
        clz = BitManipulation.countLeadingZeros(pre_shift_value, 25)
        print('CLZ({})={}'.format(hex(pre_shift_value), clz))
        
        assert(fpa.children['clz'].getOutPortByName('r').wire.get() == clz)
        
        # 6. Normalization: Normalize the significand and update Ef appropriately.
        after_shift_value = pre_shift_value << clz
        er = ea + 1 - clz

        print('After shift m:' , hex(after_shift_value), 'e:', er)
        assert(fpa.children['er'].getOutPortByName('r').wire.get() == er + 127)
        
        
        print('A: ', (ma + (1<<23)) / (1<<23) * math.pow(2, ea-127))
        print('B: ', (mb + (1<<23)) / (1<<23) * math.pow(2, eb-127))
        print('A+B:', pre_shift_value / (1<<23) * math.pow(2, ea-127))
        
        print('Before shift Floating point Value: ', pre_shift_value / (1<<23) * math.pow(2, ea-127),
              '{:025b}'.format(pre_shift_value))
        print('After  shift Floating point Value: ', after_shift_value / (1<<24) * math.pow(2, er-127),
              '{:025b}'.format(after_shift_value))

        assert(fpa.children['shift_left'].getOutPortByName('r').wire.get() == after_shift_value)
        
        
        # 7. Rounding: Round the final result by conditionally adding 1 unit in the last
        # place (ulp), as required by the IEEE standard [5]. If rounding causes an
        # overflow, perform a 1 bit right shift and increment Ef. 

        # now we have a 25 bits value, we should have 23, we have to remove 2 bits
        # if the higher bit of this 2 bits [1] is one, then add one to round up 
        round_up = BitManipulation.getBit(after_shift_value, 1) 
        print('round up bit:', round_up)
        assert(fpa.children['round_up'].getOutPortByName('r').wire.get() == round_up)
        
        round_result = after_shift_value + 1
        round_result_msb = BitManipulation.getBit(round_result, 25) 

        print('round result:', hex(round_result), '{:026b}'.format(round_result), 'msb:', round_result_msb)
        assert(fpa.children['round_result'].getOutPortByName('r').wire.get() == round_result)
        assert(fpa.children['round_result_msb'].getOutPortByName('r').wire.get() == round_result_msb)

        #assert (abs(err) < 1E-7)
        #after_shift_value
        #assert(fpa.children['mr3'].getOutPortByName('r').wire.get() == round_result)
        
        # final selection
        print('Final er: {:08b} mr: {:023b}'.format(
            fpa.children['er'].getOutPortByName('r').wire.get(),
            fpa.children['mr3'].getOutPortByName('r').wire.get()))
        
if __name__ == '__main__':
    #pytest.main(args=['-q', 'Test_FPAdder_SP.py'])
    pytest.main(args=['-s', 'Test_FPAdder_SP.py'])