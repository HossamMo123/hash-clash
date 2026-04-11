"""
Statistical randomness tests on hash outputs.

Implements a subset of NIST SP 800-22 tests plus byte distribution chi-squared.
"""

import os
import math
import numpy as np
from scipy import stats as sp_stats


def _collect_bitstream(hash_fn, num_messages=2000, message_len=32):
    """Hash many random messages and concatenate output bits into one bitstream."""
    all_bytes = bytearray()
    for i in range(num_messages):
        # Use sequential + random to avoid degenerate inputs
        msg = i.to_bytes(4, "big") + os.urandom(message_len - 4)
        all_bytes.extend(hash_fn.hash(msg))
    return bytes(all_bytes)


def _bytes_to_bits(data: bytes) -> np.ndarray:
    return np.unpackbits(np.frombuffer(data, dtype=np.uint8)).astype(np.int8)


def frequency_test(bits: np.ndarray) -> float:
    """NIST SP 800-22 Test 1: Monobit frequency test. Returns p-value."""
    n = len(bits)
    s = np.sum(2 * bits - 1)  # map 0->-1, 1->+1
    s_obs = abs(s) / math.sqrt(n)
    p_value = math.erfc(s_obs / math.sqrt(2))
    return p_value


def block_frequency_test(bits: np.ndarray, block_size=128) -> float:
    """NIST SP 800-22 Test 2: Block frequency test. Returns p-value."""
    n = len(bits)
    num_blocks = n // block_size
    if num_blocks == 0:
        return 0.0

    proportions = np.array([
        np.mean(bits[i * block_size:(i + 1) * block_size])
        for i in range(num_blocks)
    ])
    chi_sq = 4.0 * block_size * np.sum((proportions - 0.5) ** 2)
    p_value = 1.0 - float(sp_stats.chi2.cdf(chi_sq, num_blocks))
    return p_value


def runs_test(bits: np.ndarray) -> float:
    """NIST SP 800-22 Test 3: Runs test. Returns p-value."""
    n = len(bits)
    pi = np.mean(bits)

    # Pre-test: if proportion is too far from 0.5, skip
    if abs(pi - 0.5) >= (2.0 / math.sqrt(n)):
        return 0.0

    # Count runs (transitions + 1)
    transitions = np.sum(bits[:-1] != bits[1:])
    v_obs = transitions + 1

    p_value = math.erfc(
        abs(v_obs - 2.0 * n * pi * (1 - pi))
        / (2.0 * math.sqrt(2.0 * n) * pi * (1 - pi))
    )
    return p_value


def longest_run_test(bits: np.ndarray) -> float:
    """
    NIST SP 800-22 Test 4: Longest run of ones in 8-bit blocks.
    Simplified version — returns p-value from chi-squared comparison.
    """
    block_size = 8
    n = len(bits)
    num_blocks = n // block_size
    if num_blocks < 16:
        return 0.0

    longest_runs = []
    for i in range(num_blocks):
        block = bits[i * block_size:(i + 1) * block_size]
        max_run = 0
        current_run = 0
        for b in block:
            if b == 1:
                current_run += 1
                max_run = max(max_run, current_run)
            else:
                current_run = 0
        longest_runs.append(max_run)

    longest_runs = np.array(longest_runs)

    # Bin into categories: 0-1, 2, 3, 4+
    bins = [0, 0, 0, 0]
    for lr in longest_runs:
        if lr <= 1:
            bins[0] += 1
        elif lr == 2:
            bins[1] += 1
        elif lr == 3:
            bins[2] += 1
        else:
            bins[3] += 1

    # Expected proportions for 8-bit blocks
    expected_props = [0.2148, 0.3672, 0.2305, 0.1875]
    expected = [p * num_blocks for p in expected_props]

    chi_sq = sum((bins[i] - expected[i]) ** 2 / expected[i] for i in range(4) if expected[i] > 0)
    p_value = 1.0 - float(sp_stats.chi2.cdf(chi_sq, 3))
    return p_value


def byte_distribution_test(data: bytes) -> float:
    """Chi-squared test on byte value distribution (all 256 values should be uniform)."""
    counts = np.zeros(256, dtype=np.int64)
    for b in data:
        counts[b] += 1

    n = len(data)
    expected = n / 256.0
    chi_sq = float(np.sum((counts - expected) ** 2 / expected))
    p_value = 1.0 - float(sp_stats.chi2.cdf(chi_sq, 255))
    return p_value


def test_randomness(hash_fn, num_messages=2000, message_len=32):
    """
    Run all statistical randomness tests.

    Returns dict with:
        tests:           dict of test_name -> {p_value, passed}
        pass_rate:       fraction of tests passed
        randomness_score: same as pass_rate
    """
    alpha = 0.01  # significance level

    raw_output = _collect_bitstream(hash_fn, num_messages, message_len)
    bits = _bytes_to_bits(raw_output)

    test_suite = {
        "frequency": frequency_test(bits),
        "block_frequency": block_frequency_test(bits),
        "runs": runs_test(bits),
        "longest_run": longest_run_test(bits),
        "byte_distribution": byte_distribution_test(raw_output),
    }

    results = {}
    passed = 0
    for name, p_value in test_suite.items():
        ok = p_value >= alpha
        results[name] = {"p_value": round(p_value, 6), "passed": ok}
        if ok:
            passed += 1

    pass_rate = passed / len(test_suite)

    return {
        "tests": results,
        "pass_rate": round(pass_rate, 4),
        "randomness_score": round(pass_rate, 4),
    }
