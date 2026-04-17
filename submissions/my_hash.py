import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from hash_base import HashFunction


class MyHash(HashFunction):

    @property
    def name(self) -> str:
        return "HossamMix-256"

    # --- Helper: rotate left ---
    def _rotl(self, x, n):
        return ((x << n) | (x >> (64 - n))) & 0xFFFFFFFFFFFFFFFF

    def _compress(self, data: bytes) -> bytes:


        # ---- Initial state ----
        h = [
            0x6a09e667f3bcc908,
            0xbb67ae8584caa73b,
            0x3c6ef372fe94f82b,
            0xa54ff53a5f1d36f1,
        ]

        # ---- Padding ----
        length = len(data)
        data += b'\x80'
        while (len(data) % 32) != 24:
            data += b'\x00'
        data += length.to_bytes(8, 'big')

        # ---- Process blocks ----
        for i in range(0, len(data), 32):
            block = data[i:i+32]

            m = [
                int.from_bytes(block[j:j+8], 'big')
                for j in range(0, 32, 8)
            ]
            h[0] ^= m[0]

            # ---- MORE ROUNDS (important) ----
            for r in range(9):

                # Mix state with message
                h[0] = (h[0] + m[0]) & 0xFFFFFFFFFFFFFFFF
                h[1] ^= h[0]
                h[1] = self._rotl(h[1], 13)

                h[2] = (h[2] + m[1]) & 0xFFFFFFFFFFFFFFFF
                h[3] ^= h[2]
                h[3] = self._rotl(h[3], 17)

                # Cross mixing
                h[0] ^= h[3]
                h[2] ^= h[1]

                # Strong nonlinear mixing
                h[0] = (h[0] * 0x9E3779B185EBCA87) & 0xFFFFFFFFFFFFFFFF
                h[1] = (h[1] * 0xC2B2AE3D27D4EB4F) & 0xFFFFFFFFFFFFFFFF
                h[2] = (h[2] * 0x165667B19E3779F9) & 0xFFFFFFFFFFFFFFFF
                h[3] = (h[3] * 0x85EBCA77C2B2AE63) & 0xFFFFFFFFFFFFFFFF

                h[1] ^= h[2]
                h[3] ^= h[0]

                # Rotate everything differently (important for BIC)
                h = [
                    self._rotl(h[0], 7),
                    self._rotl(h[1], 11),
                    self._rotl(h[2], 19),
                    self._rotl(h[3], 23),
                ]

                # Rotate message (prevents structure patterns)
                m = m[1:] + m[:1]


        # ---- Strong finalization ----
        for i in range(4):
            h[i] ^= (h[(i+1) % 4] >> 29)
            h[i] = (h[i] * 0xff51afd7ed558ccd) & 0xFFFFFFFFFFFFFFFF
            h[i] ^= (h[i] >> 33)
            h[i] = (h[i] * 0xc4ceb9fe1a85ec53) & 0xFFFFFFFFFFFFFFFF
            h[i] ^= (h[i] >> 33)

        return b''.join(x.to_bytes(8, 'big') for x in h)