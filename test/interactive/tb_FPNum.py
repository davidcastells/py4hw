# -*- coding: utf-8 -*-
"""
Created on Tue Jun  4 11:22:48 2024

@author: 2016570
"""

from py4hw.helper import *

a = FPNum(0x7C00, 'hp')
b = FPNum(0x7C00, 'hp')

print('computing', a.to_float(), '+', b.to_float(), end=' ')

r = a.add(b)

print('=', r.to_float())


print('computing', a.to_float(), '-', b.to_float(), end=' ')

r = a.sub(b)

print('=', r.to_float(), hex(r.convert('hp')))

a = FPNum(0xFFFFFFFF40200000, 'sp')
b = FPNum(0xFFFFFFFF3F800000, 'sp')
e = FPNum(0x0000000040200000, 'sp')

r = a.mul(b)

print('computing', a.to_float(), '*', b.to_float(), end=' ')
print('=', r.to_float(), hex(r.convert('sp')), 'expected:', hex(e.convert('sp')))


a = FPNum(0x400921FB53C8D4F1, 'dp')
b = FPNum(0x4005BF0A89F1B0DD, 'dp')
e = FPNum(0x3FF27DDBF6C383EC, 'dp')
r = a.div(b)


print('Computing SQRT')
a = FPNum(0x40490FDB, 'sp')
a.increase_precision(23)
print('a=', a.to_float(), a.s, a.e, hex(a.m), hex(a.p), math.log2(a.p), a.inexact)

r = a.sqrt()
print('r=', r.to_float(), r.s, r.e, hex(r.m), hex(r.p), math.log2(r.p), r.inexact)
r.reducePrecisionWithRounding(23)
print('r=', r.to_float(), r.s, r.e, hex(r.m), hex(r.p), math.log2(r.p), r.inexact)

print('Checking Square')
a = FPNum(0x3FE2DFC5, 'sp')
r = a.mul(a)
r.reducePrecisionWithRounding(23)
print('r=', r.to_float(), r.s, r.e, hex(r.m), hex(r.p), math.log2(r.p), r.inexact)


print()
print('Computing SQRT')
a = FPNum(10000)
a.increase_precision(23)
print('a=', a.to_float(), a.s, a.e, hex(a.m), hex(a.p), math.log2(a.p), a.inexact)

r = a.sqrt(50)
print('r=', r.to_float(), r.s, r.e, hex(r.m), hex(r.p), math.log2(r.p), r.inexact)
r.reducePrecisionWithRounding(23)
print('r=', r.to_float(), r.s, r.e, hex(r.m), hex(r.p), math.log2(r.p), r.inexact)

print()
print('Computing SQRT')
a = FPNum(0xFFFFFFFFBF800000, 'sp')
a.increase_precision(23)
print('a=', a.to_float(), a.s, a.e, hex(a.m), hex(a.p), math.log2(a.p), a.inexact)

e = FPNum(0x000000007FC00000, 'sp')
print('e=', e.to_float()) #, e.s, e.e, hex(e.m), hex(e.p), math.log2(e.p), e.inexact)

r = a.sqrt(50)
print('r=', r.to_float(), hex(r.convert('sp')))
#r.reducePrecisionWithRounding(23)
#print('r=', r.to_float(), r.s, r.e, hex(r.m), hex(r.p), math.log2(r.p), r.inexact)

print()
print('Computing SQRT')

a = FPNum(0x400921FB53C8D4F1, 'dp')
print('a=', a.to_float(), a.s, a.e, hex(a.m), hex(a.p), math.log2(a.p), a.inexact)

r = a.sqrt()
print('r=', r.to_float(), hex(r.convert('dp')))
'''
80000240: E2450513     ADDI r10 = r10 + -476 -> 0000000080002060
80000244: 00053007     FLD fr0 = [r2 + 0] -> 400921FB53C8D4F1
80000248: 00853087     FLD fr1 = [r2 + 8] -> 0000000000000000
8000024C: 01053107     FLD fr2 = [r2 + 16] -> 0000000000000000
80000250: 01853683     LD r13 = [r10 + 24] -> [0000000080002078]=3FFC5BF8916F587B
80000254: 5A0071D3     FSQRT.D fr3 = sqrt(fr0) -> 3FFC5BF8916F587B
80000258: E2018553     FMV.X.D r10 = fr3 -> 3FFC5BF8916F587B
8000025C: 001015F3     CSRRW r11 = fflags, fflags = r0 -> 0000000000000000,0000000000000000
80000260: 00100613     ADDI r12 = r0 + 1 -> 0000000000000001
80000264: 0CD51E63     BNE r10 != r13 ? False 0000000080000340
'''

