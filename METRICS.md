# Hash Function Competition — Metrics & Scoring Reference

## Overview

Students submit a hash function (256-bit output) implemented in Python.
Each submission is evaluated on **6 axes** via automated tests, producing a composite score.

---

## 1. Avalanche Behavior (Strict Avalanche Criterion — SAC)

**What it measures:** When a single input bit is flipped, does each output bit flip with probability ≈ 0.5?

**How we test:**
- Take N random messages (default 1000).
- For each message, flip each bit position one at a time.
- Hash both original and flipped message.
- For each (input-bit, output-bit) pair, compute the flip probability across all N trials.
- Ideal flip probability = 0.5 for every pair.

**Metric:**
- Mean flip probability across all pairs (target: 0.50)
- Standard deviation of flip probabilities (target: as small as possible)
- SAC Score = 1 - 2 × |mean_flip - 0.5|, penalized by std dev

**Ideal:** SAC Score ≈ 1.0

**Reference (SHA-256):** mean ≈ 0.5000, std ≈ 0.002

---

## 2. Bit Independence Criterion (BIC)

**What it measures:** Are output bit flips independent of each other? When one input bit flips, are the resulting output bit changes uncorrelated?

**How we test:**
- From the SAC data, for each input bit flip, collect the output diff vector.
- Compute pairwise Pearson correlation between all output bit columns.
- Ideal: correlation ≈ 0 for all pairs.

**Metric:**
- Mean absolute correlation across all output bit pairs
- BIC Score = 1 - mean_abs_correlation

**Ideal:** BIC Score ≈ 1.0

---

## 3. Collision Resistance

**What it measures:** Does the hash behave like an ideal random function with respect to collisions?

**How we test:**
- Hash N random messages (default 100,000).
- Truncate outputs to T bits (default 32) to make birthday collisions tractable.
- Count actual collisions and compare to expected birthday bound: E[collisions] ≈ N² / (2^(T+1))
- Also test near-collisions (hamming distance ≤ threshold on full output).

**Metric:**
- Collision ratio = actual_collisions / expected_collisions (target: ≈ 1.0)
- Collision Score = 1 - |log2(collision_ratio)| / max_penalty, clamped to [0, 1]
- Too many collisions → bad. Suspiciously few → also flagged (may indicate pathological structure).

**Ideal:** Ratio ≈ 1.0, Score ≈ 1.0

**Note:** Full 256-bit collision search is infeasible.  We test on truncated outputs.

---

## 4. Statistical Randomness

**What it measures:** Do the hash outputs look indistinguishable from random bitstrings?

**Tests performed:**
1. **Frequency (monobit) test** — proportion of 1s vs 0s across all output bits
2. **Block frequency test** — uniformity within M-bit blocks
3. **Runs test** — number of uninterrupted runs of identical bits
4. **Longest run of ones** — in 8-bit blocks
5. **Chi-squared byte distribution** — all 256 byte values should appear uniformly

**Metric:**
- Each test returns a p-value. Pass if p ≥ 0.01.
- Randomness Score = fraction of tests passed

**Ideal:** All tests pass → Score = 1.0

---

## 5. Structural Weakness Detection

**What it measures:** Does the hash have exploitable algebraic or structural properties?

**Tests performed:**
1. **Zero-sensitivity:** Hash of all-zero vs all-one input. Outputs should have ~50% differing bits.
2. **Permutation sensitivity:** Swapping input halves should produce entirely different output.
3. **Linearity test:** H(A) XOR H(B) vs H(A XOR B). For a non-linear hash, these should be unrelated.
   Correlation between H(A)⊕H(B) and H(A⊕B) across many samples → should be ≈ 0.
4. **Symmetry test:** Related/mirrored inputs (e.g., abcd vs dcba) should hash to unrelated outputs.
5. **Sparse input sensitivity:** Inputs differing only in low-order bits should still produce high hamming distance.

**Metric:**
- Each sub-test scored 0 or 1 (pass/fail) with some returning a continuous score.
- Structure Score = mean of sub-test scores.

**Ideal:** Score ≈ 1.0

---

## 6. Speed / Throughput

**What it measures:** How fast is the hash function? A practical hash must be reasonably efficient.

**How we test:**
- Pre-generate 5,000 random 256-byte messages.
- Time the hashing of all messages (wall-clock).
- Compute throughput in bytes/second.

**Metric:**
- Uses a logistic scoring curve centered at a 500 KB/s baseline:
  $$\text{Speed Score} = \frac{1}{1 + e^{-k \cdot (\log_{10}(\text{throughput}) - \log_{10}(500{,}000))}}$$
  where $k = 3$.
- ~500 KB/s → score ≈ 0.5
- ~2 MB/s+ → score approaches 1.0
- Very slow → score approaches 0.0

**Ideal:** Score ≈ 1.0 (high throughput)

**Note:** Pure-Python implementations are inherently slower than C-backed ones (e.g., hashlib). Scoring is calibrated for pure Python.

---

## Composite Score

$$S = w_1 \cdot \text{SAC} + w_2 \cdot \text{BIC} + w_3 \cdot \text{Collision} + w_4 \cdot \text{Randomness} + w_5 \cdot \text{Structure} + w_6 \cdot \text{Speed}$$

**Default weights:**

| Component    | Weight | Rationale |
|-------------|--------|----------|
| SAC          | 0.20   | Core diffusion measure |
| BIC          | 0.15   | Deeper diffusion quality |
| Collision    | 0.20   | Primary hash security goal |
| Randomness   | 0.20   | Output quality |
| Structure    | 0.15   | Catches degenerate designs |
| Speed        | 0.10   | Practical efficiency |

All component scores are in [0, 1], so the composite score is also in [0, 1].

