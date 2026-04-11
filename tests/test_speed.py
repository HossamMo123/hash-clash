"""
Speed / throughput test for hash functions.

Measures how many bytes per second a hash function can process,
then scores relative to a baseline throughput.
"""

import os
import time


def test_speed(hash_fn, num_messages=5000, message_len=256):
    """
    Benchmark the hash function on many random messages.

    Returns dict with:
        total_bytes:     total input bytes hashed
        elapsed_sec:     wall-clock time
        throughput_bps:  bytes per second
        speed_score:     score in [0, 1]
    """
    # Pre-generate messages so generation time isn't measured
    messages = [os.urandom(message_len) for _ in range(num_messages)]

    start = time.perf_counter()
    for msg in messages:
        hash_fn.hash(msg)
    elapsed = time.perf_counter() - start

    total_bytes = num_messages * message_len
    throughput = total_bytes / elapsed if elapsed > 0 else 0

    # Scoring: logistic curve centered at a baseline throughput.
    # ~500 KB/s  -> score ≈ 0.5  (baseline)
    # ~2 MB/s+   -> score approaches 1.0
    # Very slow   -> score approaches 0.0
    #
    # score = 1 / (1 + exp(-k * (log10(throughput) - log10(baseline))))
    import math

    baseline_bps = 500_000  # 500 KB/s
    k = 3.0  # steepness

    if throughput > 0:
        log_ratio = math.log10(throughput) - math.log10(baseline_bps)
        speed_score = 1.0 / (1.0 + math.exp(-k * log_ratio))
    else:
        speed_score = 0.0

    return {
        "total_bytes": total_bytes,
        "elapsed_sec": round(elapsed, 4),
        "throughput_bps": round(throughput, 1),
        "speed_score": round(speed_score, 4),
    }
