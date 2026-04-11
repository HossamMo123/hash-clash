"""
Avalanche & Bit Independence Criterion tests.

SAC: For each input bit flip, each output bit should flip with P ≈ 0.5.
BIC: Output bit flips should be pairwise uncorrelated.
"""

import os
import numpy as np

OUTPUT_BITS = 256  # 32 bytes


def _bytes_to_bitarray(b: bytes) -> np.ndarray:
    """Convert bytes to a numpy array of 0/1 ints."""
    return np.unpackbits(np.frombuffer(b, dtype=np.uint8))


def _flip_bit(data: bytes, bit_index: int) -> bytes:
    """Return a copy of data with the given bit flipped."""
    arr = bytearray(data)
    byte_idx = bit_index // 8
    bit_offset = 7 - (bit_index % 8)
    arr[byte_idx] ^= (1 << bit_offset)
    return bytes(arr)


def test_avalanche(hash_fn, num_messages=500, message_len=32):
    """
    Run the Strict Avalanche Criterion test.

    Returns dict with:
        mean_flip:  average flip probability (ideal 0.5)
        std_flip:   std dev of flip probabilities
        sac_score:  composite SAC score in [0, 1]
        flip_matrix: (input_bits x output_bits) matrix of flip probabilities
    """
    input_bits = message_len * 8
    # Accumulator: for each (input_bit, output_bit), count how many times it flipped
    flip_counts = np.zeros((input_bits, OUTPUT_BITS), dtype=np.int64)

    for _ in range(num_messages):
        msg = os.urandom(message_len)
        original_hash = hash_fn.hash(msg)
        original_bits = _bytes_to_bitarray(original_hash)

        for bit_i in range(input_bits):
            flipped_msg = _flip_bit(msg, bit_i)
            flipped_hash = hash_fn.hash(flipped_msg)
            flipped_bits = _bytes_to_bitarray(flipped_hash)
            diff = original_bits ^ flipped_bits  # 1 where bits differ
            flip_counts[bit_i] += diff

    flip_probs = flip_counts / num_messages  # each entry in [0, 1]
    mean_flip = float(np.mean(flip_probs))
    std_flip = float(np.std(flip_probs))

    # Expected std for an ideal hash due to sampling noise: sqrt(0.25 / N)
    expected_std = (0.25 / num_messages) ** 0.5

    # Score: penalize deviation from 0.5 mean AND excess variance beyond sampling noise
    deviation_penalty = min(2.0 * abs(mean_flip - 0.5) / 0.05, 1.0)
    excess_std = max(0.0, std_flip - expected_std)
    variance_penalty = min(excess_std / 0.05, 1.0)  # 0.05 excess std → full penalty
    sac_score = max(0.0, 1.0 - 0.5 * deviation_penalty - 0.5 * variance_penalty)

    return {
        "mean_flip": mean_flip,
        "std_flip": std_flip,
        "sac_score": round(sac_score, 4),
        "flip_matrix": flip_probs,
    }


def test_bit_independence(flip_matrix):
    """
    Bit Independence Criterion from an existing flip_matrix (from SAC test).

    Computes pairwise Pearson correlation between output bit columns.

    Returns dict with:
        mean_abs_corr:  mean |correlation| across all output bit pairs
        bic_score:      1 - mean_abs_corr, in [0, 1]
    """
    # flip_matrix shape: (input_bits, output_bits)
    # Compute correlation between output bit columns (across input bit variations)
    # Use numpy corrcoef on transposed matrix
    # Each column = one output bit's flip behavior across all input bit flips
    n_output = flip_matrix.shape[1]

    # corrcoef expects each row to be a variable
    corr_matrix = np.corrcoef(flip_matrix.T)  # (output_bits x output_bits)

    # Extract upper triangle (exclude diagonal)
    upper_indices = np.triu_indices(n_output, k=1)
    pairwise_corrs = corr_matrix[upper_indices]

    # Handle NaN (can happen if an output bit never flips)
    pairwise_corrs = np.nan_to_num(pairwise_corrs, nan=1.0)

    mean_abs_corr = float(np.mean(np.abs(pairwise_corrs)))

    # Expected baseline |corr| from sampling noise ≈ sqrt(2/π) / sqrt(N_input_bits)
    n_input = flip_matrix.shape[0]
    expected_abs_corr = (2.0 / 3.14159) ** 0.5 / max(n_input, 1) ** 0.5
    excess_corr = max(0.0, mean_abs_corr - expected_abs_corr)
    bic_score = max(0.0, 1.0 - excess_corr / 0.1)  # 0.1 excess → score 0

    return {
        "mean_abs_corr": round(mean_abs_corr, 4),
        "bic_score": round(bic_score, 4),
    }
