# tests/test_vault_disk_v01.py

import json
import time

import pytest

from mce_v01 import MCE
from vault_v01 import Vault
from vault_disk_v01 import VaultDisk


SEED = b"whisper-vaultdisk-seed"


def build_vault(count=10):
    mce = MCE(SEED)
    vault = Vault()

    for i in range(count):
        fragment = b"fragment_%d" % i
        transformed = mce.digest_fragment(fragment)
        vault.store(i, len(fragment), len(transformed), mce.snapshot(), time.time())

    return vault


def test_vaultdisk_save_and_load(tmp_path):
    vault = build_vault(10)
    path = tmp_path / "vault.json"
    disk = VaultDisk(path)

    disk.save(vault)
    loaded = disk.load()

    assert disk.exists()
    assert len(loaded.entries) == 10
    assert loaded.dump() == vault.dump()


def test_vaultdisk_save_creates_parent_dirs(tmp_path):
    vault = build_vault(3)
    path = tmp_path / "nested" / "dir" / "vault.json"
    disk = VaultDisk(path)

    disk.save(vault)

    assert path.exists()
    assert disk.load().dump() == vault.dump()


def test_vaultdisk_delete(tmp_path):
    vault = build_vault(1)
    path = tmp_path / "vault.json"
    disk = VaultDisk(path)

    disk.save(vault)
    assert disk.exists()

    disk.delete()
    assert not disk.exists()

    disk.delete()
    assert not disk.exists()


def test_vaultdisk_load_missing_file(tmp_path):
    disk = VaultDisk(tmp_path / "missing.json")

    with pytest.raises(FileNotFoundError):
        disk.load()


def test_vaultdisk_rejects_invalid_format(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"format": "wrong", "version": 1, "entries": []}))

    with pytest.raises(ValueError):
        VaultDisk(path).load()


def test_vaultdisk_rejects_invalid_version(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"format": "whisper-vaultdisk", "version": 999, "entries": []}))

    with pytest.raises(ValueError):
        VaultDisk(path).load()


def test_vaultdisk_rejects_missing_entry_fields(tmp_path):
    path = tmp_path / "bad.json"
    payload = {
        "format": "whisper-vaultdisk",
        "version": 1,
        "entries": [{"fragment_id": 0}],
    }
    path.write_text(json.dumps(payload))

    with pytest.raises(ValueError):
        VaultDisk(path).load()


def test_vaultdisk_deterministic_file_order(tmp_path):
    vault = Vault()
    mce = MCE(SEED)

    for i in [9, 2, 5, 1]:
        fragment = b"fragment_%d" % i
        transformed = mce.digest_fragment(fragment)
        vault.store(i, len(fragment), len(transformed), mce.snapshot(), time.time())

    path = tmp_path / "vault.json"
    disk = VaultDisk(path)
    disk.save(vault)

    loaded_json = json.loads(path.read_text())
    ids = [entry["fragment_id"] for entry in loaded_json["entries"]]

    assert ids == [1, 2, 5, 9]


def test_vaultdisk_rejects_non_vault(tmp_path):
    disk = VaultDisk(tmp_path / "vault.json")

    with pytest.raises(TypeError):
        disk.save(object())  # type: ignore[arg-type]
