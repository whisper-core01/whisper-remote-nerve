# bench/bench_mce.py

import argparse
import os
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mce_v01 import MCE  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fragments", type=int, default=10000)
    parser.add_argument("--payload-size", type=int, default=256)
    parser.add_argument("--rotors", type=int, default=3)
    parser.add_argument("--seed", type=str, default="whisper-mce-seed")
    args = parser.parse_args()

    mce = MCE(args.seed.encode("utf-8"), rotors=args.rotors)
    fragments = [os.urandom(args.payload_size) for _ in range(args.fragments)]

    timings = []

    start_total = time.perf_counter()

    for fragment in fragments:
        start = time.perf_counter()
        mce.digest_fragment(fragment)
        end = time.perf_counter()
        timings.append((end - start) * 1000.0)

    elapsed = time.perf_counter() - start_total

    print("MCE benchmark")
    print("-------------")
    print(f"fragments:       {args.fragments}")
    print(f"payload size:    {args.payload_size} bytes")
    print(f"rotors:          {args.rotors}")
    print(f"total time:      {elapsed:.3f} s")
    print(f"ops/sec:         {args.fragments / elapsed:.2f}")
    print(f"mean ms/op:      {statistics.mean(timings):.4f}")
    print(f"median ms/op:    {statistics.median(timings):.4f}")
    print(f"p95 ms/op:       {statistics.quantiles(timings, n=20)[18]:.4f}")
    print(f"final counter:   {mce.fragment_counter}")
    print(f"final state:     {mce.snapshot().hex(8)}")


if __name__ == "__main__":
    main()
