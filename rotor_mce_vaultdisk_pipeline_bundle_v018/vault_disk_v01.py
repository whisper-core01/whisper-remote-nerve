# vault_disk_v01.py
# Requires Python 3.8+

"""
VaultDisk v0.1 — Minimal JSON disk persistence for Vault entries.

Purpose:
    Persist Vault metadata entries to disk and reload them later.

Scope:
    RotorMachine = deterministic fragment transformation
    MCE          = state evolution
    Vault        = in-memory state persistence / metadata log
    VaultDisk    = JSON disk persistence for Vault metadata

Security warning:
    This is NOT encrypted storage.
    This is NOT tamper-resistant storage.
    This is NOT secure audit logging.
    This is NOT a key vault.
    This does NOT provide rollback protection.

    VaultDisk stores metadata only. Do not store plaintext fragments, ciphertext
    fragments, raw seeds, or sensitive key material in this MVP implementation.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Union

from vault_v01 import Vault, VaultEntry


__version__ = "0.1.0"
__all__ = ["VaultDisk"]


class VaultDisk:
    """
    Minimal JSON persistence layer for Vault.

    Writes are atomic-ish on POSIX through temp-file + os.replace().
    This protects against partially written JSON files in simple cases, but it
    is not an integrity or tamper-resistance guarantee.
    """

    FORMAT_VERSION = 1

    def __init__(self, path: Union[str, Path]):
        self.path = Path(path)

    def save(self, vault: Vault) -> None:
        """
        Save Vault entries to disk as deterministic JSON.

        Args:
            vault:
                Vault instance to persist.
        """
        if not isinstance(vault, Vault):
            raise TypeError("vault must be a Vault instance")

        self.path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "format": "whisper-vaultdisk",
            "version": self.FORMAT_VERSION,
            "entries": [
                {
                    "fragment_id": entry.fragment_id,
                    "input_size": entry.input_size,
                    "output_size": entry.output_size,
                    "mce_state_hex": entry.mce_state_hex,
                    "timestamp": entry.timestamp,
                }
                for entry in vault.list_entries()
            ],
        }

        tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")

        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())

        os.replace(tmp_path, self.path)

    def load(self) -> Vault:
        """
        Load Vault entries from disk.

        Returns:
            A new Vault instance populated from disk.

        Raises:
            FileNotFoundError:
                If the path does not exist.
            ValueError:
                If the file is malformed or has unsupported format/version.
        """
        if not self.path.exists():
            raise FileNotFoundError(str(self.path))

        with self.path.open("r", encoding="utf-8") as f:
            payload = json.load(f)

        self._validate_payload(payload)

        vault = Vault()

        for raw_entry in payload["entries"]:
            entry = self._entry_from_dict(raw_entry)
            vault.entries[entry.fragment_id] = entry

        return vault

    def exists(self) -> bool:
        """Return True if the vault file exists."""
        return self.path.exists()

    def delete(self) -> None:
        """
        Delete the vault file if it exists.

        This is normal filesystem deletion, not secure deletion.
        """
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass

    @classmethod
    def _validate_payload(cls, payload: Any) -> None:
        if not isinstance(payload, dict):
            raise ValueError("vault file must contain a JSON object")

        if payload.get("format") != "whisper-vaultdisk":
            raise ValueError("unsupported vault format")

        if payload.get("version") != cls.FORMAT_VERSION:
            raise ValueError("unsupported vault version")

        entries = payload.get("entries")
        if not isinstance(entries, list):
            raise ValueError("vault entries must be a list")

    @staticmethod
    def _entry_from_dict(raw: Dict[str, Any]) -> VaultEntry:
        required = {
            "fragment_id",
            "input_size",
            "output_size",
            "mce_state_hex",
            "timestamp",
        }

        missing = required - set(raw)
        if missing:
            raise ValueError(f"missing vault entry fields: {sorted(missing)}")

        fragment_id = raw["fragment_id"]
        input_size = raw["input_size"]
        output_size = raw["output_size"]
        mce_state_hex = raw["mce_state_hex"]
        timestamp = raw["timestamp"]

        if not isinstance(fragment_id, int) or fragment_id < 0:
            raise ValueError("fragment_id must be a non-negative int")
        if not isinstance(input_size, int) or input_size < 0:
            raise ValueError("input_size must be a non-negative int")
        if not isinstance(output_size, int) or output_size < 0:
            raise ValueError("output_size must be a non-negative int")
        if not isinstance(mce_state_hex, str):
            raise ValueError("mce_state_hex must be a str")
        if not isinstance(timestamp, (int, float)):
            raise ValueError("timestamp must be numeric")

        return VaultEntry(
            fragment_id=fragment_id,
            input_size=input_size,
            output_size=output_size,
            mce_state_hex=mce_state_hex,
            timestamp=float(timestamp),
        )


if __name__ == "__main__":
    import tempfile
    import time

    from mce_v01 import MCE

    print("=== VaultDisk v0.1 Smoke Test ===")

    mce = MCE(b"whisper-vaultdisk-seed")
    vault = Vault()

    for i in range(10):
        fragment = b"fragment_%d" % i
        transformed = mce.digest_fragment(fragment)
        vault.store(i, len(fragment), len(transformed), mce.snapshot(), time.time())

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "vault.json"
        disk = VaultDisk(path)

        disk.save(vault)
        loaded = disk.load()

        print(f"Saved to:        {path}")
        print(f"Exists:          {disk.exists()}")
        print(f"Stored entries:  {len(vault.entries)}")
        print(f"Loaded entries:  {len(loaded.entries)}")
        print(f"First entry:     {loaded.get(0)}")
        print(f"Roundtrip OK:    {vault.dump() == loaded.dump()}")
