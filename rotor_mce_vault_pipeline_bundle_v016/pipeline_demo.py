# pipeline_demo.py
# Requires Python 3.8+

"""
Whisper MVP Pipeline Demo v0.1

Flow:
    input payload
        -> fragmentation
        -> MCE digest_fragment()
             -> RotorMachine transform_bytes()
             -> MCE state evolution
        -> Vault metadata persistence
        -> JSON summary

Scope:
    This is a demo pipeline only.

Security warning:
    This is NOT encryption.
    This is NOT secure storage.
    This is NOT a production Whisper pipeline.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import asdict
from typing import List

from mce_v01 import MCE
from vault_v01 import Vault


DEFAULT_SEED = b"whisper-pipeline-demo-seed"


def fragment_payload(payload: bytes, fragment_size: int) -> List[bytes]:
    """Split payload into fixed-size fragments."""
    if not isinstance(payload, (bytes, bytearray)):
        raise TypeError("payload must be bytes")
    if not isinstance(fragment_size, int):
        raise TypeError("fragment_size must be an int")
    if fragment_size <= 0:
        raise ValueError("fragment_size must be > 0")

    payload = bytes(payload)

    return [
        payload[i : i + fragment_size]
        for i in range(0, len(payload), fragment_size)
    ]


def run_pipeline(payload: bytes, fragment_size: int, seed: bytes = DEFAULT_SEED) -> dict:
    """
    Run the demo pipeline.

    Returns a JSON-serializable summary containing:
        - fragment count
        - input/output sizes
        - transformed preview hashes/hex
        - vault entries
        - final MCE state
    """
    fragments = fragment_payload(payload, fragment_size)

    mce = MCE(seed)
    vault = Vault()

    transformed_fragments = []
    started = time.time()

    for fragment_id, fragment in enumerate(fragments):
        timestamp = time.time()
        transformed = mce.digest_fragment(fragment)

        vault.store(
            fragment_id=fragment_id,
            input_size=len(fragment),
            output_size=len(transformed),
            mce_state=mce.snapshot(),
            timestamp=timestamp,
        )

        transformed_fragments.append(transformed)

    elapsed = time.time() - started

    return {
        "pipeline": "RotorMachine -> MCE -> Vault",
        "fragment_size": fragment_size,
        "input_size": len(payload),
        "fragment_count": len(fragments),
        "output_size": sum(len(x) for x in transformed_fragments),
        "final_mce_counter": mce.fragment_counter,
        "final_mce_state_hex": mce.snapshot().hex(8),
        "elapsed_seconds": round(elapsed, 6),
        "unique_outputs": len(set(transformed_fragments)),
        "vault_entries": [asdict(entry) for entry in vault.list_entries()],
        "transformed_preview_hex": [
            fragment.hex()[:64]
            for fragment in transformed_fragments[:5]
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Whisper MVP pipeline demo")
    parser.add_argument(
        "--payload",
        type=str,
        default="Whisper pipeline demo payload. " * 20,
        help="Text payload to fragment and process",
    )
    parser.add_argument(
        "--random-bytes",
        type=int,
        default=0,
        help="Use N random bytes instead of --payload text",
    )
    parser.add_argument(
        "--fragment-size",
        type=int,
        default=64,
        help="Fragment size in bytes",
    )
    parser.add_argument(
        "--seed",
        type=str,
        default="whisper-pipeline-demo-seed",
        help="Demo seed string",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full JSON summary",
    )

    args = parser.parse_args()

    if args.random_bytes > 0:
        payload = os.urandom(args.random_bytes)
    else:
        payload = args.payload.encode("utf-8")

    summary = run_pipeline(
        payload=payload,
        fragment_size=args.fragment_size,
        seed=args.seed.encode("utf-8"),
    )

    print("=== Whisper MVP Pipeline Demo ===")
    print(f"Flow:             {summary['pipeline']}")
    print(f"Input size:       {summary['input_size']} bytes")
    print(f"Fragment size:    {summary['fragment_size']} bytes")
    print(f"Fragments:        {summary['fragment_count']}")
    print(f"Output size:      {summary['output_size']} bytes")
    print(f"Unique outputs:   {summary['unique_outputs']}")
    print(f"Final MCE count:  {summary['final_mce_counter']}")
    print(f"Final MCE state:  {summary['final_mce_state_hex']}")
    print(f"Elapsed:          {summary['elapsed_seconds']} s")

    print("\nFirst transformed fragments:")
    for i, preview in enumerate(summary["transformed_preview_hex"]):
        print(f"  [{i}] {preview}")

    print("\nFirst Vault entry:")
    if summary["vault_entries"]:
        print(json.dumps(summary["vault_entries"][0], indent=2, sort_keys=True))
    else:
        print("  <none>")

    if args.json:
        print("\nFull JSON summary:")
        print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
