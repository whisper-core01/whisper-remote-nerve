# bench/bench_rotor.py

import argparse
import os
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rotor_machine_v01 import RotorMachine  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fragments", type=int, default=10000)
    parser.add_argument("--payload-size", type=int, default=256)
    parser.add_argument("--rotors", type=int, default=3)
    parser.add_argument("--seed", type=str, default="whisper-test-seed-12345")
    args = parser.parse_args()

    rm = RotorMachine(args.seed.encode("utf-8"), rotors=args.rotors)
    payload = os.urandom(args.payload_size)

    timings = []

    start_total = time.perf_counter()

    for fragment_id in range(args.fragments):
        start = time.perf_counter()
        encoded = rm.transform_bytes(payload, fragment_id)
        decoded = rm.inverse_transform_bytes(encoded, fragment_id)
        end = time.perf_counter()

        if decoded != payload:
            raise RuntimeError(f"roundtrip failed at fragment {fragment_id}")

        timings.append((end - start) * 1000.0)

    elapsed = time.perf_counter() - start_total

    print("RotorMachine benchmark")
    print("----------------------")
    print(f"fragments:       {args.fragments}")
    print(f"payload size:    {args.payload_size} bytes")
    print(f"rotors:          {args.rotors}")
    print(f"total time:      {elapsed:.3f} s")
    print(f"ops/sec:         {args.fragments / elapsed:.2f}")
    print(f"mean ms/op:      {statistics.mean(timings):.4f}")
    print(f"median ms/op:    {statistics.median(timings):.4f}")
    print(f"p95 ms/op:       {statistics.quantiles(timings, n=20)[18]:.4f}")


if __name__ == "__main__":
    main()
