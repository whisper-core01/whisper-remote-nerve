# bench/bench_vaultdisk.py

import argparse
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mce_v01 import MCE  # noqa: E402
from vault_v01 import Vault  # noqa: E402
from vault_disk_v01 import VaultDisk  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--entries", type=int, default=10000)
    parser.add_argument("--seed", type=str, default="whisper-vaultdisk-seed")
    args = parser.parse_args()

    mce = MCE(args.seed.encode("utf-8"))
    vault = Vault()

    for i in range(args.entries):
        fragment = b"fragment_%d" % i
        transformed = mce.digest_fragment(fragment)
        vault.store(i, len(fragment), len(transformed), mce.snapshot(), time.time())

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "vault.json"
        disk = VaultDisk(path)

        save_start = time.perf_counter()
        disk.save(vault)
        save_elapsed = time.perf_counter() - save_start

        load_start = time.perf_counter()
        loaded = disk.load()
        load_elapsed = time.perf_counter() - load_start

        print("VaultDisk benchmark")
        print("-------------------")
        print(f"entries:       {args.entries}")
        print(f"file size:     {path.stat().st_size} bytes")
        print(f"save time:     {save_elapsed:.3f} s")
        print(f"load time:     {load_elapsed:.3f} s")
        print(f"loaded:        {len(loaded.entries)}")
        print(f"roundtrip:     {loaded.dump() == vault.dump()}")


if __name__ == "__main__":
    main()
