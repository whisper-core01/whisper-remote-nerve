# vault_v01.py
# Requires Python 3.8+

"""
Vault v0.1 — Minimal state persistence layer for Whisper MVP experiments.

Purpose:
    Store per-fragment MCE metadata snapshots.

Scope:
    RotorMachine = deterministic fragment transformation
    MCE          = state evolution
    Vault        = state persistence / metadata log

Security warning:
    This is NOT encrypted storage.
    This is NOT tamper-resistant storage.
    This is NOT secure audit logging.
    This is NOT a key vault.

    Vault stores metadata only. Do not store plaintext fragments, ciphertext
    fragments, raw seeds, or sensitive key material in this MVP implementation.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional

from mce_v01 import MCEState


__version__ = "0.1.0"
__all__ = ["Vault", "VaultEntry"]


@dataclass(frozen=True)
class VaultEntry:
    """Metadata snapshot for one processed fragment."""

    fragment_id: int
    input_size: int
    output_size: int
    mce_state_hex: str
    timestamp: float


class Vault:
    """
    Simple in-memory metadata store for MCE fragment processing.

    This MVP stores entries in a dictionary keyed by fragment_id.
    It does not persist to disk unless dump() output is written externally.
    """

    def __init__(self):
        self.entries: Dict[int, VaultEntry] = {}

    def store(
        self,
        fragment_id: int,
        input_size: int,
        output_size: int,
        mce_state: MCEState,
        timestamp: float,
    ) -> None:
        """Store or replace one fragment metadata entry."""
        self._validate_non_negative_int(fragment_id, "fragment_id")
        self._validate_non_negative_int(input_size, "input_size")
        self._validate_non_negative_int(output_size, "output_size")

        if not isinstance(timestamp, (int, float)):
            raise TypeError("timestamp must be int or float")

        entry = VaultEntry(
            fragment_id=fragment_id,
            input_size=input_size,
            output_size=output_size,
            mce_state_hex=mce_state.hex(8),
            timestamp=float(timestamp),
        )

        self.entries[fragment_id] = entry

    def get(self, fragment_id: int) -> Optional[VaultEntry]:
        """Return the VaultEntry for fragment_id, or None if absent."""
        return self.entries.get(fragment_id)

    def list_entries(self) -> List[VaultEntry]:
        """Return entries sorted by fragment_id."""
        return [self.entries[key] for key in sorted(self.entries)]

    def dump(self) -> str:
        """Dump entries to deterministic JSON sorted by fragment_id."""
        return json.dumps(
            [asdict(entry) for entry in self.list_entries()],
            indent=2,
            sort_keys=True,
        )

    def clear(self) -> None:
        """Remove all entries."""
        self.entries.clear()

    @staticmethod
    def _validate_non_negative_int(value: int, name: str) -> None:
        if not isinstance(value, int):
            raise TypeError(f"{name} must be an int")
        if value < 0:
            raise ValueError(f"{name} must be >= 0")


if __name__ == "__main__":
    import os
    import time

    from mce_v01 import MCE

    mce = MCE(b"whisper-vault-seed")
    vault = Vault()

    fragments = [os.urandom(256) for _ in range(100)]

    for i, frag in enumerate(fragments):
        t = time.time()
        transformed = mce.digest_fragment(frag)
        vault.store(i, len(frag), len(transformed), mce.snapshot(), t)

    print("=== Vault v0.1 Smoke Test ===")
    print(f"Stored {len(vault.entries)} fragments")
    print(f"First entry: {vault.get(0)}")
    print(f"Last entry:  {vault.get(99)}")
    print("JSON preview:")
    print(vault.dump()[:500] + "...")
