# bench/bench_vault.py

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mce_v01 import MCE  # noqa: E402
from vault_v01 import Vault  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fragments", type=int, default=10000)
    parser.add_argument("--payload-size", type=int, default=256)
    parser.add_argument("--seed", type=str, default="whisper-vault-seed")
    args = parser.parse_args()

    mce = MCE(args.seed.encode("utf-8"))
    vault = Vault()

    fragments = [os.urandom(args.payload_size) for _ in range(args.fragments)]

    start = time.perf_counter()

    for i, frag in enumerate(fragments):
        transformed = mce.digest_fragment(frag)
        vault.store(i, len(frag), len(transformed), mce.snapshot(), time.time())

    elapsed = time.perf_counter() - start

    dump_start = time.perf_counter()
    dumped = vault.dump()
    dump_elapsed = time.perf_counter() - dump_start

    print("Vault benchmark")
    print("---------------")
    print(f"fragments:       {args.fragments}")
    print(f"payload size:    {args.payload_size} bytes")
    print(f"stored entries:  {len(vault.entries)}")
    print(f"process+store:   {elapsed:.3f} s")
    print(f"ops/sec:         {args.fragments / elapsed:.2f}")
    print(f"dump time:       {dump_elapsed:.3f} s")
    print(f"dump size:       {len(dumped)} bytes")
    print(f"final state:     {mce.snapshot().hex(8)}")


if __name__ == "__main__":
    main()
