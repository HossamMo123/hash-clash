"""
Structural weakness detection tests.

Checks for zero-sensitivity, permutation sensitivity, linearity,
symmetry, and sparse-input sensitivity.
"""

import os
import numpy as np


def _hamming_distance(a: bytes, b: bytes) -> int:
    xor_val = int.from_bytes(a, "big") ^ int.from_bytes(b, "big")
    return bin(xor_val).count("1")


def _hamming_ratio(a: bytes, b: bytes, total_bits=256) -> float:
    """Hamming distance as a fraction of total bits. Ideal ≈ 0.5 for unrelated inputs."""
    return _hamming_distance(a, b) / total_bits


def test_zero_sensitivity(hash_fn, message_len=32):
    """Hash of all-zeros vs all-ones should differ by ~50% of bits."""
    h_zero = hash_fn.hash(b"\x00" * message_len)
    h_ones = hash_fn.hash(b"\xff" * message_len)
    ratio = _hamming_ratio(h_zero, h_ones)
    # Score: how close to 0.5
    score = max(0.0, 1.0 - 2.0 * abs(ratio - 0.5))
    return {"hamming_ratio": round(ratio, 4), "score": round(score, 4)}


def test_permutation_sensitivity(hash_fn, num_trials=200, message_len=32):
    """Swapping input halves should produce very different outputs."""
    total_ratio = 0.0
    for _ in range(num_trials):
        msg = os.urandom(message_len)
        half = message_len // 2
        swapped = msg[half:] + msg[:half]
        h1 = hash_fn.hash(msg)
        h2 = hash_fn.hash(swapped)
        total_ratio += _hamming_ratio(h1, h2)

    mean_ratio = total_ratio / num_trials
    score = max(0.0, 1.0 - 2.0 * abs(mean_ratio - 0.5))
    return {"mean_hamming_ratio": round(mean_ratio, 4), "score": round(score, 4)}


def test_linearity(hash_fn, num_trials=500, message_len=32):
    """
    Check H(A) XOR H(B) vs H(A XOR B).
    For a non-linear hash these should be unrelated (hamming ≈ 50%).
    For a linear hash they'd be identical (hamming = 0).
    """
    total_ratio = 0.0
    for _ in range(num_trials):
        a = os.urandom(message_len)
        b = os.urandom(message_len)
        a_xor_b = bytes(x ^ y for x, y in zip(a, b))

        ha = hash_fn.hash(a)
        hb = hash_fn.hash(b)
        ha_xor_hb = bytes(x ^ y for x, y in zip(ha, hb))
        h_axb = hash_fn.hash(a_xor_b)

        total_ratio += _hamming_ratio(ha_xor_hb, h_axb)

    mean_ratio = total_ratio / num_trials
    # If linear, ratio ≈ 0. If non-linear (good), ratio ≈ 0.5
    score = max(0.0, 1.0 - 2.0 * abs(mean_ratio - 0.5))
    return {"mean_hamming_ratio": round(mean_ratio, 4), "score": round(score, 4)}


def test_symmetry(hash_fn, num_trials=300, message_len=32):
    """Reversed inputs should produce entirely different outputs."""
    total_ratio = 0.0
    for _ in range(num_trials):
        msg = os.urandom(message_len)
        rev = bytes(reversed(msg))
        h1 = hash_fn.hash(msg)
        h2 = hash_fn.hash(rev)
        total_ratio += _hamming_ratio(h1, h2)

    mean_ratio = total_ratio / num_trials
    score = max(0.0, 1.0 - 2.0 * abs(mean_ratio - 0.5))
    return {"mean_hamming_ratio": round(mean_ratio, 4), "score": round(score, 4)}


def test_sparse_sensitivity(hash_fn, num_trials=300, message_len=32):
    """Inputs differing only in the last byte should still produce ~50% output difference."""
    total_ratio = 0.0
    for _ in range(num_trials):
        msg = os.urandom(message_len)
        # Flip only the last byte
        modified = msg[:-1] + bytes([(msg[-1] ^ 0x01)])
        h1 = hash_fn.hash(msg)
        h2 = hash_fn.hash(modified)
        total_ratio += _hamming_ratio(h1, h2)

    mean_ratio = total_ratio / num_trials
    score = max(0.0, 1.0 - 2.0 * abs(mean_ratio - 0.5))
    return {"mean_hamming_ratio": round(mean_ratio, 4), "score": round(score, 4)}


def test_structure(hash_fn, message_len=32):
    """
    Run all structural weakness tests.

    Returns dict with:
        subtests:        dict of subtest_name -> {hamming_ratio, score}
        structure_score:  mean of all sub-scores
    """
    subtests = {
        "zero_sensitivity": test_zero_sensitivity(hash_fn, message_len),
        "permutation_sensitivity": test_permutation_sensitivity(hash_fn, message_len=message_len),
        "linearity": test_linearity(hash_fn, message_len=message_len),
        "symmetry": test_symmetry(hash_fn, message_len=message_len),
        "sparse_sensitivity": test_sparse_sensitivity(hash_fn, message_len=message_len),
    }

    scores = [v["score"] for v in subtests.values()]
    structure_score = sum(scores) / len(scores)

    return {
        "subtests": subtests,
        "structure_score": round(structure_score, 4),
    }
