import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from hash_base import HashFunction


class MyHash(HashFunction):

    @property
    def name(self) -> str:
        return "HossamMix-256"

    def _compress(self, data: bytes) -> bytes:
        M = 0xFFFFFFFFFFFFFFFF

        # Initial state: first 64 bits of fractional parts of sqrt(2,3,5,7)
        v0 = 0x6a09e667f3bcc908
        v1 = 0xbb67ae8584caa73b
        v2 = 0x3c6ef372fe94f82b
        v3 = 0xa54ff53a5f1d36f1

        # Merkle-Damgard padding: 0x80 || zeros || 64-bit big-endian length
        length = len(data)
        pad = (32 - (length + 9) % 32) % 32
        data = data + b'\x80' + b'\x00' * pad + struct.pack('>Q', length)

        # Process 32-byte blocks
        for m0, m1, m2, m3 in struct.iter_unpack('>QQQQ', data):
            # Pre-whitening: inject all message words into state
            v0 ^= m0; v1 ^= m1; v2 ^= m2; v3 ^= m3

            # 4 double-rounds of SipHash-style ARX mixing 
            # Round 1
            v0 = (v0 + v1) & M; v1 = ((v1 << 13) | (v1 >> 51)) & M; v1 ^= v0; v0 = ((v0 << 32) | (v0 >> 32)) & M
            v2 = (v2 + v3) & M; v3 = ((v3 << 16) | (v3 >> 48)) & M; v3 ^= v2
            v0 = (v0 + v3) & M; v3 = ((v3 << 21) | (v3 >> 43)) & M; v3 ^= v0
            v2 = (v2 + v1) & M; v1 = ((v1 << 17) | (v1 >> 47)) & M; v1 ^= v2; v2 = ((v2 << 32) | (v2 >> 32)) & M
            # Round 2
            v0 = (v0 + v1) & M; v1 = ((v1 << 13) | (v1 >> 51)) & M; v1 ^= v0; v0 = ((v0 << 32) | (v0 >> 32)) & M
            v2 = (v2 + v3) & M; v3 = ((v3 << 16) | (v3 >> 48)) & M; v3 ^= v2
            v0 = (v0 + v3) & M; v3 = ((v3 << 21) | (v3 >> 43)) & M; v3 ^= v0
            v2 = (v2 + v1) & M; v1 = ((v1 << 17) | (v1 >> 47)) & M; v1 ^= v2; v2 = ((v2 << 32) | (v2 >> 32)) & M
            # Round 3
            v0 = (v0 + v1) & M; v1 = ((v1 << 13) | (v1 >> 51)) & M; v1 ^= v0; v0 = ((v0 << 32) | (v0 >> 32)) & M
            v2 = (v2 + v3) & M; v3 = ((v3 << 16) | (v3 >> 48)) & M; v3 ^= v2
            v0 = (v0 + v3) & M; v3 = ((v3 << 21) | (v3 >> 43)) & M; v3 ^= v0
            v2 = (v2 + v1) & M; v1 = ((v1 << 17) | (v1 >> 47)) & M; v1 ^= v2; v2 = ((v2 << 32) | (v2 >> 32)) & M
            # Round 4
            v0 = (v0 + v1) & M; v1 = ((v1 << 13) | (v1 >> 51)) & M; v1 ^= v0; v0 = ((v0 << 32) | (v0 >> 32)) & M
            v2 = (v2 + v3) & M; v3 = ((v3 << 16) | (v3 >> 48)) & M; v3 ^= v2
            v0 = (v0 + v3) & M; v3 = ((v3 << 21) | (v3 >> 43)) & M; v3 ^= v0
            v2 = (v2 + v1) & M; v1 = ((v1 << 17) | (v1 >> 47)) & M; v1 ^= v2; v2 = ((v2 << 32) | (v2 >> 32)) & M

            # Post-injection with permuted message words 
            v0 ^= m2; v1 ^= m3; v2 ^= m0; v3 ^= m1

        # Finalization: domain separation + length mixing
        # Constants tuned for optimal zero-sensitivity 
        v3 ^= 0xBE
        v0 ^= length

        # 3 finalization rounds for extra diffusion 
        # Final Round 1
        v0 = (v0 + v1) & M; v1 = ((v1 << 13) | (v1 >> 51)) & M; v1 ^= v0; v0 = ((v0 << 32) | (v0 >> 32)) & M
        v2 = (v2 + v3) & M; v3 = ((v3 << 16) | (v3 >> 48)) & M; v3 ^= v2
        v0 = (v0 + v3) & M; v3 = ((v3 << 21) | (v3 >> 43)) & M; v3 ^= v0
        v2 = (v2 + v1) & M; v1 = ((v1 << 17) | (v1 >> 47)) & M; v1 ^= v2; v2 = ((v2 << 32) | (v2 >> 32)) & M
        # Final Round 2
        v0 = (v0 + v1) & M; v1 = ((v1 << 13) | (v1 >> 51)) & M; v1 ^= v0; v0 = ((v0 << 32) | (v0 >> 32)) & M
        v2 = (v2 + v3) & M; v3 = ((v3 << 16) | (v3 >> 48)) & M; v3 ^= v2
        v0 = (v0 + v3) & M; v3 = ((v3 << 21) | (v3 >> 43)) & M; v3 ^= v0
        v2 = (v2 + v1) & M; v1 = ((v1 << 17) | (v1 >> 47)) & M; v1 ^= v2; v2 = ((v2 << 32) | (v2 >> 32)) & M
        # Final Round 3
        v0 = (v0 + v1) & M; v1 = ((v1 << 13) | (v1 >> 51)) & M; v1 ^= v0; v0 = ((v0 << 32) | (v0 >> 32)) & M
        v2 = (v2 + v3) & M; v3 = ((v3 << 16) | (v3 >> 48)) & M; v3 ^= v2
        v0 = (v0 + v3) & M; v3 = ((v3 << 21) | (v3 >> 43)) & M; v3 ^= v0
        v2 = (v2 + v1) & M; v1 = ((v1 << 17) | (v1 >> 47)) & M; v1 ^= v2; v2 = ((v2 << 32) | (v2 >> 32)) & M

        # Cross-word diffusion (Feistel-like)
        v0 ^= v2; v1 ^= v3
        v2 ^= v0; v3 ^= v1

        # Murmur3-64 avalanche finalizer on each word (bijective)
        v0 ^= v0 >> 33; v0 = (v0 * 0xff51afd7ed558ccd) & M
        v0 ^= v0 >> 33; v0 = (v0 * 0xc4ceb9fe1a85ec53) & M
        v0 ^= v0 >> 33

        v1 ^= v1 >> 33; v1 = (v1 * 0xff51afd7ed558ccd) & M
        v1 ^= v1 >> 33; v1 = (v1 * 0xc4ceb9fe1a85ec53) & M
        v1 ^= v1 >> 33

        v2 ^= v2 >> 33; v2 = (v2 * 0xff51afd7ed558ccd) & M
        v2 ^= v2 >> 33; v2 = (v2 * 0xc4ceb9fe1a85ec53) & M
        v2 ^= v2 >> 33

        v3 ^= v3 >> 33; v3 = (v3 * 0xff51afd7ed558ccd) & M
        v3 ^= v3 >> 33; v3 = (v3 * 0xc4ceb9fe1a85ec53) & M
        v3 ^= v3 >> 33

        return struct.pack('>QQQQ', v0, v1, v2, v3)