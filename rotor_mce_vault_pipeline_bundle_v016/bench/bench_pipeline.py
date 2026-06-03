# bench/bench_pipeline.py

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline_demo import run_pipeline  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload-size", type=int, default=1024 * 1024)
    parser.add_argument("--fragment-size", type=int, default=256)
    parser.add_argument("--seed", type=str, default="whisper-pipeline-demo-seed")
    args = parser.parse_args()

    payload = os.urandom(args.payload_size)

    start = time.perf_counter()
    summary = run_pipeline(
        payload=payload,
        fragment_size=args.fragment_size,
        seed=args.seed.encode("utf-8"),
    )
    elapsed = time.perf_counter() - start

    print("Pipeline benchmark")
    print("------------------")
    print(f"payload size:      {args.payload_size} bytes")
    print(f"fragment size:     {args.fragment_size} bytes")
    print(f"fragments:         {summary['fragment_count']}")
    print(f"elapsed:           {elapsed:.3f} s")
    print(f"fragments/sec:     {summary['fragment_count'] / elapsed:.2f}")
    print(f"throughput MB/sec: {(args.payload_size / (1024 * 1024)) / elapsed:.3f}")
    print(f"final state:       {summary['final_mce_state_hex']}")


if __name__ == "__main__":
    main()
