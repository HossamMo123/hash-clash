#!/usr/bin/env python3
"""
Hash Competition Runner & Scorer.

Usage:
    python run_competition.py submissions/my_hash.py
    python run_competition.py submissions/       # run all submissions in folder

Each submission file must define a class that inherits from hash_base.HashFunction.
"""

import sys
import os
import json
import time
import importlib.util
import inspect

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hash_base import HashFunction
from tests.test_avalanche import test_avalanche, test_bit_independence
from tests.test_collision import test_collisions
from tests.test_randomness import test_randomness
from tests.test_structure import test_structure
from tests.test_speed import test_speed

# Default scoring weights
WEIGHTS = {
    "sac": 0.20,
    "bic": 0.15,
    "collision": 0.20,
    "randomness": 0.20,
    "structure": 0.15,
    "speed": 0.10,
}


def load_submission(filepath):
    """Dynamically load a .py file and find the HashFunction subclass in it."""
    spec = importlib.util.spec_from_file_location("submission", filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Find the first concrete HashFunction subclass
    for name, obj in inspect.getmembers(module, inspect.isclass):
        if issubclass(obj, HashFunction) and obj is not HashFunction:
            return obj()

    raise ValueError(f"No HashFunction subclass found in {filepath}")


def evaluate(hash_fn, verbose=True):
    """Run all test suites on a hash function and compute composite score."""
    results = {"name": hash_fn.name}

    def log(msg):
        if verbose:
            print(msg)

    # 1. Avalanche (SAC)
    log(f"  [1/6] Avalanche (SAC) test...")
    t0 = time.time()
    aval = test_avalanche(hash_fn, num_messages=500, message_len=32)
    results["avalanche"] = {
        "mean_flip": aval["mean_flip"],
        "std_flip": aval["std_flip"],
        "sac_score": aval["sac_score"],
        "time_sec": round(time.time() - t0, 2),
    }
    log(f"       SAC score: {aval['sac_score']}  (mean flip: {aval['mean_flip']:.4f})")

    # 2. Bit Independence (BIC)
    log(f"  [2/6] Bit Independence (BIC) test...")
    t0 = time.time()
    bic = test_bit_independence(aval["flip_matrix"])
    results["bit_independence"] = {
        "mean_abs_corr": bic["mean_abs_corr"],
        "bic_score": bic["bic_score"],
        "time_sec": round(time.time() - t0, 2),
    }
    log(f"       BIC score: {bic['bic_score']}  (mean |corr|: {bic['mean_abs_corr']:.4f})")

    # 3. Collision resistance
    log(f"  [3/6] Collision resistance test...")
    t0 = time.time()
    coll = test_collisions(hash_fn, num_messages=100_000, truncate_bits=24)
    results["collision"] = {
        "actual": coll["actual_collisions"],
        "expected": coll["expected_collisions"],
        "ratio": coll["collision_ratio"],
        "collision_score": coll["collision_score"],
        "time_sec": round(time.time() - t0, 2),
    }
    log(f"       Collision score: {coll['collision_score']}  "
        f"(actual: {coll['actual_collisions']}, expected: {coll['expected_collisions']:.1f})")

    # 4. Statistical randomness
    log(f"  [4/6] Statistical randomness tests...")
    t0 = time.time()
    rand = test_randomness(hash_fn, num_messages=1000)
    results["randomness"] = {
        "tests": rand["tests"],
        "pass_rate": rand["pass_rate"],
        "randomness_score": rand["randomness_score"],
        "time_sec": round(time.time() - t0, 2),
    }
    log(f"       Randomness score: {rand['randomness_score']}  "
        f"(passed {int(rand['pass_rate'] * 5)}/5 tests)")

    # 5. Structural weakness
    log(f"  [5/6] Structural weakness tests...")
    t0 = time.time()
    struct = test_structure(hash_fn)
    results["structure"] = {
        "subtests": struct["subtests"],
        "structure_score": struct["structure_score"],
        "time_sec": round(time.time() - t0, 2),
    }
    log(f"       Structure score: {struct['structure_score']}")

    # 6. Speed
    log(f"  [6/6] Speed test...")
    t0 = time.time()
    spd = test_speed(hash_fn)
    results["speed"] = {
        "throughput_bps": spd["throughput_bps"],
        "speed_score": spd["speed_score"],
        "time_sec": round(time.time() - t0, 2),
    }
    log(f"       Speed score: {spd['speed_score']}  "
        f"(throughput: {spd['throughput_bps'] / 1024:.1f} KB/s)")

    # Composite score
    composite = (
        WEIGHTS["sac"] * aval["sac_score"]
        + WEIGHTS["bic"] * bic["bic_score"]
        + WEIGHTS["collision"] * coll["collision_score"]
        + WEIGHTS["randomness"] * rand["randomness_score"]
        + WEIGHTS["structure"] * struct["structure_score"]
        + WEIGHTS["speed"] * spd["speed_score"]
    )
    results["composite_score"] = round(composite, 4)

    log(f"\n  === COMPOSITE SCORE: {results['composite_score']:.4f} / 1.0000 ===\n")

    return results


def main():
    if len(sys.argv) < 2:
        target = os.path.join(os.path.dirname(os.path.abspath(__file__)), "submissions", "my_hash.py")
    else:
        target = sys.argv[1]

    # Collect submission files
    if os.path.isdir(target):
        files = sorted(
            os.path.join(target, f)
            for f in os.listdir(target)
            if f.endswith(".py") and not f.startswith("_")
        )
    else:
        files = [target]

    all_results = []

    for filepath in files:
        print(f"\n{'='*60}")
        print(f" Evaluating: {filepath}")
        print(f"{'='*60}")
        try:
            hash_fn = load_submission(filepath)
            result = evaluate(hash_fn)
            all_results.append(result)
        except Exception as e:
            print(f"  ERROR: {e}")
            all_results.append({"file": filepath, "error": str(e)})

    # Leaderboard
    valid = [r for r in all_results if "composite_score" in r]
    if len(valid) > 1:
        print(f"\n{'='*60}")
        print(" LEADERBOARD")
        print(f"{'='*60}")
        valid.sort(key=lambda r: r["composite_score"], reverse=True)
        for rank, r in enumerate(valid, 1):
            print(f"  #{rank}  {r['name']:30s}  {r['composite_score']:.4f}")

    # Save results
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.json")
    with open(out_path, "w") as f:
        # Remove non-serializable items (numpy arrays)
        clean = []
        for r in all_results:
            cr = {}
            for k, v in r.items():
                if k == "flip_matrix":
                    continue
                cr[k] = v
            clean.append(cr)
        json.dump(clean, f, indent=2, default=str)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
