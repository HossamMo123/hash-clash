# Hash Function Competition

## What is this?

You're going to design your own cryptographic hash function from scratch.

No libraries. No shortcuts. Just you, some bit operations, and whatever clever ideas you can come up with.

Your submission will go head-to-head against your classmates' designs on an automated test suite. May the best hash win.

## Why hash functions matter

Hash functions are everywhere. Every time you download a file and verify its checksum, every time you log into a website that stores your password (properly)— there's a hash function doing the heavy lifting behind the scenes.

A good hash function takes arbitrary input and produces a fixed-size fingerprint. Sounds simple enough. But the hard part is making that fingerprint behave *well*:

- **Change one bit** of the input and the output should look completely different (avalanche effect).
- **Two different inputs** should (almost) never produce the same output (collision resistance).
- **The output** should look indistinguishable from random noise (statistical randomness).
- **No structural shortcuts** — an attacker shouldn't be able to predict or manipulate the output by exploiting algebraic patterns.
- **It has to be fast enough** to actually be usable in practice.

Getting all of these right at the same time is genuinely difficult. That's the challenge.

## How we evaluate your hash

Your submission is scored on **6 axes**, each probing a different property of a good hash function:

| # | Test | Weight | What it checks |
|---|------|--------|----------------|
| 1 | **Avalanche (SAC)** | 20% | Flip one input bit → does each output bit flip ~50% of the time? |
| 2 | **Bit Independence (BIC)** | 15% | Are output bit changes uncorrelated with each other? |
| 3 | **Collision Resistance** | 20% | Does the number of collisions match what you'd expect from a random function? |
| 4 | **Statistical Randomness** | 20% | Do outputs pass standard NIST-style randomness tests? |
| 5 | **Structural Weakness** | 15% | Can we find algebraic shortcuts, symmetry, or linearity in your design? |
| 6 | **Speed** | 10% | How fast is it? A hash that takes forever isn't very useful. |

Each axis gives a score between 0 and 1. Your **composite score** is the weighted sum — also between 0 and 1.

For the full details on every test and how scores are computed, see [METRICS.md](METRICS.md).

## How to submit

1. **Edit `submissions/my_hash.py`** — this is the only file you need to modify.

2. **Subclass `HashFunction`** from `hash_base.py` and implement three things:

   - `name` — a display name for the leaderboard (be creative)
   - `digest_size` — must be `32` (256-bit output)
   - `_compress(data: bytes) -> bytes` — your actual hash logic

3. That's it. Here's the minimal skeleton:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from hash_base import HashFunction

class MyHash(HashFunction):

    @property
    def name(self) -> str:
        return "MyHash-256"

    def _compress(self, data: bytes) -> bytes:
        # Your hash logic here.
        # Must return exactly 32 bytes.
        ...
```

## Rules

- **No `hashlib`**, no calling out to OpenSSL, no importing someone else's hash implementation. The point is to build your own.
- **Pure Python only.** You can use the standard library (e.g., `struct`, `math`, `os` for nothing hash-related), but no C extensions or Cython.
- Your `_compress` method must be **deterministic** — same input, same output, every time.
- Output must be exactly **32 bytes** (256 bits).
- Don't modify `hash_base.py` or anything in `tests/`.

## Running it locally

Make sure you have the dependencies installed (numpy, scipy):

```bash
pip install numpy scipy
```

Then run your submission through the test suite:

```bash
python run_competition.py
```

This evaluates `submissions/my_hash.py` by default. You can also pass the path explicitly:

```bash
python run_competition.py submissions/my_hash.py
```

You'll see scores for each axis and a composite score.

## Grading

Your grade is based on your **composite score**.

You don't need to beat SHA-256. But you should aim to understand *why* your score is what it is. If your avalanche score is low, what does that tell you about your design? If collisions are too frequent, where is the mixing falling short?

The goal isn't perfection — it's understanding.

## Tips

- **Start simple.** Get something that runs, then iterate. A working hash that scores 0.5 is better than an elegant design that crashes.
- **Think in rounds.** Most good hash functions apply a mixing step repeatedly. More rounds = better diffusion, but slower.
- **Test early, test often.** Run the suite on your hash after every change. Watch which scores go up and which go down.
- **Read METRICS.md.** Seriously. Understanding what each test is looking for will tell you exactly what properties your hash needs.

Good luck. Make something interesting.
