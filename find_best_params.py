"""Search for finalization parameters that maximize zero_sensitivity score."""
import struct

M = 0xFFFFFFFFFFFFFFFF

def hash_test(data, ds_word, ds_val, len_word):
    v0 = 0x6a09e667f3bcc908
    v1 = 0xbb67ae8584caa73b
    v2 = 0x3c6ef372fe94f82b
    v3 = 0xa54ff53a5f1d36f1
    
    length = len(data)
    pad = (32 - (length + 9) % 32) % 32
    data = data + b'\x80' + b'\x00' * pad + struct.pack('>Q', length)
    
    for off in range(0, len(data), 32):
        m0, m1, m2, m3 = struct.unpack_from('>QQQQ', data, off)
        v0 ^= m0; v1 ^= m1; v2 ^= m2; v3 ^= m3
        for _ in range(4):
            v0 = (v0 + v1) & M; v1 = ((v1 << 13) | (v1 >> 51)) & M; v1 ^= v0; v0 = ((v0 << 32) | (v0 >> 32)) & M
            v2 = (v2 + v3) & M; v3 = ((v3 << 16) | (v3 >> 48)) & M; v3 ^= v2
            v0 = (v0 + v3) & M; v3 = ((v3 << 21) | (v3 >> 43)) & M; v3 ^= v0
            v2 = (v2 + v1) & M; v1 = ((v1 << 17) | (v1 >> 47)) & M; v1 ^= v2; v2 = ((v2 << 32) | (v2 >> 32)) & M
        v0 ^= m2; v1 ^= m3; v2 ^= m0; v3 ^= m1
    
    # Apply domain separation and length to specified words
    state = [v0, v1, v2, v3]
    state[ds_word] ^= ds_val
    state[len_word] ^= length
    v0, v1, v2, v3 = state
    
    for _ in range(3):
        v0 = (v0 + v1) & M; v1 = ((v1 << 13) | (v1 >> 51)) & M; v1 ^= v0; v0 = ((v0 << 32) | (v0 >> 32)) & M
        v2 = (v2 + v3) & M; v3 = ((v3 << 16) | (v3 >> 48)) & M; v3 ^= v2
        v0 = (v0 + v3) & M; v3 = ((v3 << 21) | (v3 >> 43)) & M; v3 ^= v0
        v2 = (v2 + v1) & M; v1 = ((v1 << 17) | (v1 >> 47)) & M; v1 ^= v2; v2 = ((v2 << 32) | (v2 >> 32)) & M
    
    v0 ^= v2; v1 ^= v3; v2 ^= v0; v3 ^= v1
    
    v0 ^= v0 >> 33; v0 = (v0 * 0xff51afd7ed558ccd) & M; v0 ^= v0 >> 33; v0 = (v0 * 0xc4ceb9fe1a85ec53) & M; v0 ^= v0 >> 33
    v1 ^= v1 >> 33; v1 = (v1 * 0xff51afd7ed558ccd) & M; v1 ^= v1 >> 33; v1 = (v1 * 0xc4ceb9fe1a85ec53) & M; v1 ^= v1 >> 33
    v2 ^= v2 >> 33; v2 = (v2 * 0xff51afd7ed558ccd) & M; v2 ^= v2 >> 33; v2 = (v2 * 0xc4ceb9fe1a85ec53) & M; v2 ^= v2 >> 33
    v3 ^= v3 >> 33; v3 = (v3 * 0xff51afd7ed558ccd) & M; v3 ^= v3 >> 33; v3 = (v3 * 0xc4ceb9fe1a85ec53) & M; v3 ^= v3 >> 33
    
    return struct.pack('>QQQQ', v0, v1, v2, v3)

def hamming_ratio(a, b):
    xor_val = int.from_bytes(a, 'big') ^ int.from_bytes(b, 'big')
    return bin(xor_val).count('1') / 256

# Search all combinations
best_score = 0
best_params = None
results = []

for ds_word in range(4):
    for len_word in range(4):
        for ds_val in range(256):
            h_zero = hash_test(b'\x00' * 32, ds_word, ds_val, len_word)
            h_ones = hash_test(b'\xff' * 32, ds_word, ds_val, len_word)
            ratio = hamming_ratio(h_zero, h_ones)
            score = max(0.0, 1.0 - 2.0 * abs(ratio - 0.5))
            if score > best_score:
                best_score = score
                best_params = (ds_word, ds_val, len_word)
            if score >= 0.99:
                results.append((score, ds_word, ds_val, len_word, ratio))

results.sort(reverse=True)
print(f"\nBest: ds_word=v{best_params[0]}, ds_val=0x{best_params[1]:02X}, len_word=v{best_params[2]}")
print(f"Score: {best_score:.4f}")
print(f"\nTop 20 configurations with score >= 0.99:")
for score, dw, dv, lw, ratio in results[:20]:
    print(f"  v{dw} ^= 0x{dv:02X}, v{lw} ^= length  ->  ratio={ratio:.4f}  score={score:.4f}")
