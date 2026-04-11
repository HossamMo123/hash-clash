"""
Collision resistance test.

Hashes many random messages, truncates outputs to T bits,
and compares observed collisions to birthday-bound expectation.
"""

import os
import math


def test_collisions(hash_fn, num_messages=100_000, truncate_bits=32, message_len=32):
    """
    Birthday collision test on truncated outputs.

    Returns dict with:
        total_hashes:      number of messages hashed
        truncate_bits:     how many bits we kept
        actual_collisions: observed collisions
        expected_collisions: birthday-bound expectation
        collision_ratio:   actual / expected (ideal ≈ 1.0)
        collision_score:   score in [0, 1]
    """
    truncate_bytes = (truncate_bits + 7) // 8
    mask = (1 << truncate_bits) - 1

    seen = {}
    collisions = 0

    for _ in range(num_messages):
        msg = os.urandom(message_len)
        digest = hash_fn.hash(msg)
        # Truncate to T bits
        truncated = int.from_bytes(digest[:truncate_bytes], "big") & mask
        if truncated in seen:
            collisions += 1
        else:
            seen[truncated] = True

    # Expected collisions via birthday approximation:
    # E[C] ≈ N^2 / (2 * 2^T)
    space = 2 ** truncate_bits
    expected = (num_messages * (num_messages - 1)) / (2.0 * space)

    if expected < 1.0:
        expected = max(expected, 0.001)

    if expected > 0:
        ratio = collisions / expected
    else:
        ratio = 0.0

    # Score: penalize deviation from ratio=1.0 on a log scale
    if ratio > 0:
        log_dev = abs(math.log2(max(ratio, 0.001)))
    else:
        # Zero collisions when many expected → suspicious but give some credit
        log_dev = 5.0

    max_penalty = 5.0  # log2 deviation that maps to score=0
    collision_score = max(0.0, 1.0 - log_dev / max_penalty)

    return {
        "total_hashes": num_messages,
        "truncate_bits": truncate_bits,
        "actual_collisions": collisions,
        "expected_collisions": round(expected, 2),
        "collision_ratio": round(ratio, 4),
        "collision_score": round(collision_score, 4),
    }