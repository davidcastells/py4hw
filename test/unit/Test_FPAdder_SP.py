# -*- coding: utf-8 -*-
"""
Extended tests for FPAdder_SP.
"""
import struct
import py4hw
import pytest


# ---------------------------------------------------------------------------
# bit-level helpers
# ---------------------------------------------------------------------------

def f32_to_bits(x):
    return struct.unpack('<I', struct.pack('<f', x))[0]


def bits_to_f32(b):
    return struct.unpack('<f', struct.pack('<I', b & 0xFFFFFFFF))[0]


def make_bits(sign, exp, frac):
    """sign: 0/1, exp: 8-bit raw (biased) exponent field, frac: 23-bit fraction."""
    return ((sign & 1) << 31) | ((exp & 0xFF) << 23) | (frac & 0x7FFFFF)



def expected_sum_bits(a_bits, b_bits):
    av = bits_to_f32(a_bits)
    bv = bits_to_f32(b_bits)
    try:
        return f32_to_bits(av + bv)
    except OverflowError:
        # Determine sign of infinity based on the result sign
        sign = 1 if (av + bv) < 0 else 0
        # Exponent = 0xFF (255), Mantissa = 0 for Infinity
        return make_bits(sign, 0xFF, 0)
    
# ---------------------------------------------------------------------------
# Shared Circuit Fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def shared_adder_circuit():
    """
    Instantiates the HWSystem and FPAdder_SP once per test module execution.
    Returns a dictionary containing references to input drivers, output wire,
    and simulator.
    """
    sys = py4hw.HWSystem()
    r = sys.wire('r', 32)
    a = sys.wire('a', 32)
    b = sys.wire('b', 32)

    ca = py4hw.Constant(sys, 'a', 0, a)
    cb = py4hw.Constant(sys, 'b', 0, b)
    
    py4hw.FPAdder_SP(sys, 'fpa', a, b, r)
    sim = sys.getSimulator()

    return {
        'ca': ca,
        'cb': cb,
        'r': r,
        'sim': sim
    }


class Test_FPAdder_SP:

    # -- Helper to run a test case using the pre-built shared circuit --
    def _run_case(self, hw, a_bits, b_bits, label='', rel_tol=1e-6):
        hw['ca'].value = a_bits
        hw['cb'].value = b_bits
        hw['sim'].clk(1)

        actual_bits = hw['r'].get()
        exp_bits = expected_sum_bits(a_bits, b_bits)

        if actual_bits != exp_bits:
            av, bv = bits_to_f32(a_bits), bits_to_f32(b_bits)
            actual, expected = bits_to_f32(actual_bits), bits_to_f32(exp_bits)
            abs_err = abs(actual - expected)
            rel_err = abs_err / abs(expected) if expected != 0.0 else abs_err
            print(f"FAIL [{label}]: {av!r} + {bv!r}")
            print(f"  a_bits=0x{a_bits:08X} b_bits=0x{b_bits:08X}")
            print(f"  expected={hex(exp_bits)} ({expected!r})  actual={hex(actual_bits)} ({actual!r})")
            assert rel_err < rel_tol, f"[{label}] mismatch: {av!r} + {bv!r}: expected {expected!r} got {actual!r}"

        return actual_bits

    # =====================================================================
    # A. Trivial / identity values
    # =====================================================================

    def test_zero_plus_zero(self, shared_adder_circuit):
        self._run_case(shared_adder_circuit, make_bits(0, 0, 0), make_bits(0, 0, 0), 'zero+zero')

    def test_negzero_plus_zero(self, shared_adder_circuit):
        self._run_case(shared_adder_circuit, make_bits(1, 0, 0), make_bits(0, 0, 0), '-0+0')

    def test_a_plus_zero(self, shared_adder_circuit):
        self._run_case(shared_adder_circuit, f32_to_bits(3.75), make_bits(0, 0, 0), 'a+0')

    def test_zero_plus_b(self, shared_adder_circuit):
        self._run_case(shared_adder_circuit, make_bits(0, 0, 0), f32_to_bits(-2.5), '0+b')

    def test_identity_a_plus_a(self, shared_adder_circuit):
        self._run_case(shared_adder_circuit, f32_to_bits(0.1), f32_to_bits(0.1), 'a+a')

    # =====================================================================
    # B. Same exponent, no alignment shift needed (ediff == 0)
    # =====================================================================

    def test_same_exponent_add(self, shared_adder_circuit):
        self._run_case(shared_adder_circuit, f32_to_bits(1.25), f32_to_bits(1.75), 'same-exp add')

    def test_same_exponent_subtract_nonzero(self, shared_adder_circuit):
        self._run_case(shared_adder_circuit, f32_to_bits(1.75), f32_to_bits(-1.25), 'same-exp sub')

    def test_same_exponent_exact_cancellation(self, shared_adder_circuit):
        r = self._run_case(shared_adder_circuit, f32_to_bits(5.5), f32_to_bits(-5.5), 'exact cancellation')
        assert r == make_bits(0, 0, 0), f"expected +0.0, got {hex(r)}"

    # =====================================================================
    # C. Catastrophic cancellation
    # =====================================================================

    def test_massive_cancellation_one_ulp(self, shared_adder_circuit):
        a = make_bits(0, 127, 1)
        b = make_bits(1, 127, 0)
        r = self._run_case(shared_adder_circuit, a, b, 'cancellation 1ulp')
        assert bits_to_f32(r) == pytest.approx(2 ** -23, rel=0, abs=0)

    def test_near_total_cancellation(self, shared_adder_circuit):
        a = f32_to_bits(1.0000002384185791)
        b = f32_to_bits(-1.0)
        self._run_case(shared_adder_circuit, a, b, 'near-total cancellation')

    # =====================================================================
    # D. Mantissa carry-out on addition
    # =====================================================================

    def test_carry_out_simple(self, shared_adder_circuit):
        self._run_case(shared_adder_circuit, f32_to_bits(1.5), f32_to_bits(1.5), 'carry-out simple')

    def test_carry_out_near_max_mantissa(self, shared_adder_circuit):
        a = make_bits(0, 127, 0x7FFFFF)
        r = self._run_case(shared_adder_circuit, a, a, 'carry-out near-max mantissa')
        assert bits_to_f32(r) == pytest.approx(2 * bits_to_f32(a))

    # =====================================================================
    # E. Moderate alignment shift
    # =====================================================================

    @pytest.mark.parametrize("ediff", [1, 2, 3, 7, 15, 23])
    @pytest.mark.parametrize("sign_b", [0, 1])
    def test_moderate_alignment_shift(self, shared_adder_circuit, ediff, sign_b):
        a = make_bits(0, 150, 0x123456)
        b = make_bits(sign_b, 150 - ediff, 0x654321)
        self._run_case(shared_adder_circuit, a, b, f'moderate shift ediff={ediff} sign_b={sign_b}')

    # =====================================================================
    # F. Large alignment shift
    # =====================================================================

    def test_bug_reported_case_ediff_37(self, shared_adder_circuit):
        a = make_bits(0, 145, 0)
        b = make_bits(0, 108, 0)
        self._run_case(shared_adder_circuit, a, b, 'reported bug: ediff=37')

    def test_bug_reported_case_ediff_37_with_nonzero_mantissas(self, shared_adder_circuit):
        a = make_bits(0, 145, 0x2A2A2A >> 1)
        b = make_bits(1, 108, 0x555555 >> 1)
        self._run_case(shared_adder_circuit, a, b, 'reported bug: ediff=37, nonzero mantissas, mixed sign')

    @pytest.mark.parametrize("ediff", [
        24, 25, 31, 32, 33, 37, 40, 63, 64, 65, 96, 100, 150, 200,
    ])
    @pytest.mark.parametrize("sign_combo", [(0, 0), (0, 1), (1, 0), (1, 1)])
    def test_large_alignment_shift_sweep(self, shared_adder_circuit, ediff, sign_combo):
        exp_a = 220
        exp_b = exp_a - ediff
        if exp_b < 1:
            pytest.skip("exponent would underflow the field for this base")
        sign_a, sign_b = sign_combo
        a = make_bits(sign_a, exp_a, 0x3A5A5A)
        b = make_bits(sign_b, exp_b, 0x1E1E1E)
        self._run_case(shared_adder_circuit, a, b, f'large shift ediff={ediff} signs={sign_combo}')

    # =====================================================================
    # G. Rounding stress
    # =====================================================================

    @pytest.mark.parametrize("k", [1, 2, 3, 4])
    @pytest.mark.parametrize("sign_b", [0, 1])
    def test_rounding_ulp_boundary(self, shared_adder_circuit, k, sign_b):
        a = make_bits(0, 127, 0)
        b_val = k * (2.0 ** -24)
        b = f32_to_bits(-b_val if sign_b else b_val)
        self._run_case(shared_adder_circuit, a, b, f'rounding ULP boundary k={k} sign_b={sign_b}')

    def test_rounding_overflow_into_next_exponent(self, shared_adder_circuit):
        a = make_bits(0, 127, 0x7FFFFF)
        b = make_bits(0, 100, 0x7FFFFF)
        self._run_case(shared_adder_circuit, a, b, 'rounding overflow into next exponent')

    def test_tie_to_even_classic(self, shared_adder_circuit):
        a = make_bits(0, 127, 0)
        b = make_bits(0, 103, 0)
        self._run_case(shared_adder_circuit, a, b, 'tie-to-even classic (1.0 + 2^-24)')

    # =====================================================================
    # H. Denormalized operands
    # =====================================================================

    def test_denormal_plus_normal(self, shared_adder_circuit):
        self._run_case(shared_adder_circuit, f32_to_bits(1e-40), f32_to_bits(1.0), 'denormal + normal')

    def test_denormal_plus_denormal(self, shared_adder_circuit):
        self._run_case(shared_adder_circuit, f32_to_bits(1e-40), f32_to_bits(1e-40), 'denormal + denormal')

    # =====================================================================
    # I. Sign combinations at large magnitude ratios
    # =====================================================================

    def test_neg_large_plus_small(self, shared_adder_circuit):
        self._run_case(shared_adder_circuit, f32_to_bits(-1.2), f32_to_bits(0.0000002), '-large + small')

    def test_neg_large_plus_neg_small(self, shared_adder_circuit):
        self._run_case(shared_adder_circuit, f32_to_bits(-1.2), f32_to_bits(-0.0000002), '-large + -small')

    # =====================================================================
    # J. Parametrized sweep across ediff = 0..48
    # =====================================================================

    def test_ediff_sweep_shared_circuit(self, shared_adder_circuit, is_deep_random):
        if not is_deep_random:
            pytest.skip("Skipping deep random sweep. Pass --deep_random to run.")

        exp_a = 200
        failures = []

        for ediff in range(0, 49):
            exp_b = exp_a - ediff
            for sign_b in (0, 1):
                a_bits = make_bits(0, exp_a, 0x4B4B4B)
                b_bits = make_bits(sign_b, exp_b, 0x2D2D2D)
                
                shared_adder_circuit['ca'].value = a_bits
                shared_adder_circuit['cb'].value = b_bits
                shared_adder_circuit['sim'].clk(1)

                actual_bits = shared_adder_circuit['r'].get()
                exp_bits = expected_sum_bits(a_bits, b_bits)
                if actual_bits != exp_bits:
                    av, bv = bits_to_f32(a_bits), bits_to_f32(b_bits)
                    actual, expected = bits_to_f32(actual_bits), bits_to_f32(exp_bits)
                    rel_err = abs(actual - expected) / abs(expected) if expected != 0.0 else abs(actual - expected)
                    if rel_err >= 1e-6:
                        failures.append((ediff, sign_b, hex(a_bits), hex(b_bits),
                                         hex(exp_bits), hex(actual_bits)))

        if failures:
            print("Sweep failures (ediff, sign_b, a_bits, b_bits, expected, actual):")
            for f in failures:
                print(" ", f)
        assert not failures, f"{len(failures)} ediff sweep case(s) failed: {failures[:5]}..."



    def test_random_float_additions(self, shared_adder_circuit, is_deep_random):
        """
        Tests random IEEE-754 single-precision float additions.
        Runs fewer iterations by default for fast CI, and deep iterations
        when --deep_random is passed.
        """
        import random

        # Set a deterministic seed so failures are reproducible
        random.seed(0xDEADBEEF)

        # Scale iterations depending on whether --deep_random was passed
        num_iterations = 5000 if is_deep_random else 50

        failures = []

        for _ in range(num_iterations):
            # Generate random 32-bit representations
            # (Filters out NaNs and Infs for standard addition checks)
            a_bits = random.getrandbits(32)
            b_bits = random.getrandbits(32)

            # Skip NaNs / Infs (exponent field == 0xFF)
            if ((a_bits >> 23) & 0xFF) == 0xFF or ((b_bits >> 23) & 0xFF) == 0xFF:
                continue

            shared_adder_circuit['ca'].value = a_bits
            shared_adder_circuit['cb'].value = b_bits
            shared_adder_circuit['sim'].clk(1)

            actual_bits = shared_adder_circuit['r'].get()
            exp_bits = expected_sum_bits(a_bits, b_bits)

            # Ignore sign differences on zero results (+0 vs -0)
            if actual_bits != exp_bits:
                actual = bits_to_f32(actual_bits)
                expected = bits_to_f32(exp_bits)

                # Skip if both are zero (IEEE 754 sign rules on zero can vary depending on mode)
                if actual == 0.0 and expected == 0.0:
                    continue

                abs_err = abs(actual - expected)
                rel_err = abs_err / abs(expected) if expected != 0.0 else abs_err

                if rel_err >= 1e-6:
                    failures.append((
                        f"a_bits=0x{a_bits:08X} ({bits_to_f32(a_bits)})",
                        f"b_bits=0x{b_bits:08X} ({bits_to_f32(b_bits)})",
                        f"expected=0x{exp_bits:08X} ({expected})",
                        f"actual=0x{actual_bits:08X} ({actual})"
                    ))
                    if len(failures) >= 10:  # Cap logged failures
                        break

        assert not failures, f"Random test failures encountered:\n" + "\n".join(str(f) for f in failures)
        
if __name__ == '__main__':
    pytest.main(args=['-q', 'Test_FPAdder_SP.py', '--deep_random', '-s'])