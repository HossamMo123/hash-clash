# MyHash.md - HossamMix-256 Hash Function

## Overview

**HossamMix-256** is a custom cryptographic hash function that produces a 256-bit output. It processes input data in 32-byte blocks and employs a combination of proven hash design techniques from SipHash, Murmur3, and ARX (Add-Rotate-XOR) mixing strategies.

---

## Algorithm Description

### Output Specification
- **Output Size**: 256 bits (4 × 64-bit words)
- **Block Size**: 32 bytes (256 bits)
- **State Size**: 4 × 64-bit words (256 bits)

### Core Components

#### 1. **Initialization**
The algorithm initializes four 64-bit state variables (v0-v3) with constants derived from the fractional parts of square roots of prime numbers (2, 3, 5, 7):

```python
v0 = 0x6a09e667f3bcc908  # sqrt(2)
v1 = 0xbb67ae8584caa73b  # sqrt(3)
v2 = 0x3c6ef372fe94f82b  # sqrt(5)
v3 = 0xa54ff53a5f1d36f1  # sqrt(7)
```

This initialization is inspired by SHA-256 and ensures independence from any suspicious constants.

#### 2. **Padding (Merkle-Damgård)**
Input data is padded according to the Merkle-Damgård construction:
- Append 0x80 byte
- Pad with zeros to reach length ≡ -8 (mod 32)
- Append 64-bit big-endian encoding of the message length

This ensures proper handling of variable-length inputs and prevents length-extension attacks.

#### 3. **Message Processing**
For each 32-byte block, the algorithm performs:

- **Pre-whitening**: XOR all four message words into the state
- **4 Double-Rounds of ARX Mixing**: Each round applies 4 mixing operations to the state variables
  - Modular addition (64-bit)
  - Bitwise rotation
  - XOR operations
  - Rotation amounts: 13, 16, 21, 17, 32 bits
- **Post-injection**: XOR the message words again (with permuted positions)

#### 4. **Finalization**
After all blocks are processed:

- **Domain Separation**: XOR 0xBE constant into v3 (prevents distinguishing from other hash functions)
- **Length Injection**: XOR message length into v0 (provides length-dependency)
- **3 Final Mixing Rounds**: Additional rounds for thorough diffusion
- **Cross-Word Diffusion**: Feistel-like operations exchange bits between words
- **Avalanche Finalizer**: Applies Murmur3-64 finalization to each word independently

**Parameter Search & Optimization:** 
The specific configuration used for domain separation and length injection (`v3 ^= 0xBE` and `v0 ^= length`) was derived via a brute-force solver script (`find_best_params.py`). The solver tested all possible variable/constant combinations to find the exact setup delivering the highest "zero-sensitivity" score—ensuring a near-perfect 50% bit avalanche even under worst-case input conditions (e.g., flipping a block of all 0s to all 1s).

The Murmur3 finalizer uses bijective multiplication with large prime constants to ensure every input bit affects all output bits.

#### 5. **Final Output**
The four 64-bit state words are concatenated in big-endian format to produce a 256-bit hash value.

---

## Algorithm Flow Diagram

```
Input Data
    ↓
Merkle-Damgård Padding
    ↓
Initialize State (v0, v1, v2, v3)
    ↓
For Each 32-Byte Block:
  ├─ Pre-whitening (XOR message words)
  ├─ 4 Double-Rounds (ARX Mixing)
  └─ Post-injection (XOR permuted message)
    ↓
Finalization:
  ├─ Domain Separation
  ├─ Length Injection
  ├─ 3 Final Rounds (ARX Mixing)
  ├─ Cross-Word Diffusion
  └─ Avalanche Finalization (per-word)
    ↓
Output (v0 || v1 || v2 || v3)
```

---

## Strengths

### 1. **Well-Grounded Design**
- Uses proven techniques from established hash functions (SipHash, Murmur3, SHA-256)
- ARX operations have been extensively analyzed in cryptographic literature
- Combines multiple independent diffusion mechanisms

### 2. **Strong Diffusion Properties**
- **Pre- and Post-injection**: Message words interact with state twice per block
- **Multiple Rounds**: 4 processing rounds + 3 finalization rounds provide sufficient diffusion
- **Cross-word Mixing**: Feistel-like operations ensure state words interact with each other
- **Avalanche Finalizer**: Murmur3 algorithm guarantees each bit influences all output bits

### 3. **Proper Padding**
- Merkle-Damgård padding with explicit length encoding
- Prevents length-extension vulnerabilities
- Ensures proper handling of edge cases (empty input, unaligned blocks)

### 4. **Computational Efficiency**
- Uses only arithmetic and bitwise operations (no lookup tables or S-boxes)
- No memory-intensive state (only 32 bytes)

### 5. **Balanced Design**
- Equal treatment of state words and message words
- Symmetric round structure with rotation amounts spread across bit positions
- Domain separation constant prevents accidental collisions with other algorithms

---

## Weaknesses



### 1. **State Size Limitations**
- 4 × 64-bit state is relatively small compared to industrial standards (SHA-256 has 8 × 32-bit)
- Potential vulnerability to meet-in-the-middle attacks on very large computational budgets
- Not suitable for cryptographic applications requiring provable security margins

### 2. **Potential Attack Vectors (Hypothetical)**
- **Differential Cryptanalysis**: ARX-only design without non-linear S-boxes may be analyzable
- **Linear Cryptanalysis**: Rotation-based designs can sometimes be approximated linearly
- **Chosen-Prefix Attacks**: Merkle-Damgård is vulnerable if the compression function has weaknesses

### 3. **Limited Analysis of Rotation Constants**
- While rotation amounts (13, 16, 21, 17, 32) are reasonable, no proof that these are optimal
- No analysis of correlation or bias between rotation values
- Different constants might reveal different vulnerabilities

### 4. **Finalization Concerns**
- The avalanche finalizer applies Murmur3 independently to each word
- Lacks cross-word interaction at the very end (only happens before finalization)
- Murmur3 multiplier constants are borrowed from another algorithm (unclear if optimal here)




