# tests/test_vault_v01.py

import json
import os
import time

import pytest

from mce_v01 import MCE
from vault_v01 import Vault


SEED = b"whisper-vault-seed"


def test_vault_store_and_retrieve():
    vault = Vault()
    mce = MCE(SEED)

    frag = b"test"
    transformed = mce.digest_fragment(frag)

    vault.store(0, len(frag), len(transformed), mce.snapshot(), time.time())

    entry = vault.get(0)

    assert entry is not None
    assert entry.fragment_id == 0
    assert entry.input_size == 4
    assert entry.output_size == 4
    assert isinstance(entry.mce_state_hex, str)
    assert len(entry.mce_state_hex) == 16


def test_vault_multiple_entries():
    vault = Vault()
    mce = MCE(SEED)

    for i in range(50):
        frag = os.urandom(128)
        transformed = mce.digest_fragment(frag)
        vault.store(i, len(frag), len(transformed), mce.snapshot(), time.time())

    assert len(vault.entries) == 50
    assert vault.get(0) is not None
    assert vault.get(49) is not None
    assert vault.get(100) is None


def test_vault_dump_json():
    vault = Vault()
    mce = MCE(SEED)

    for i in range(10):
        frag = b"frag_%d" % i
        transformed = mce.digest_fragment(frag)
        vault.store(i, len(frag), len(transformed), mce.snapshot(), time.time())

    dump = vault.dump()
    parsed = json.loads(dump)

    assert isinstance(dump, str)
    assert "fragment_id" in dump
    assert len(vault.entries) == 10
    assert isinstance(parsed, list)
    assert len(parsed) == 10
    assert parsed[0]["fragment_id"] == 0


def test_vault_dump_is_sorted_by_fragment_id():
    vault = Vault()
    mce = MCE(SEED)

    for i in [5, 2, 9, 1]:
        frag = b"frag_%d" % i
        transformed = mce.digest_fragment(frag)
        vault.store(i, len(frag), len(transformed), mce.snapshot(), time.time())

    parsed = json.loads(vault.dump())
    ids = [entry["fragment_id"] for entry in parsed]

    assert ids == [1, 2, 5, 9]


def test_vault_replaces_existing_fragment_id():
    vault = Vault()
    mce = MCE(SEED)

    frag1 = b"first"
    transformed1 = mce.digest_fragment(frag1)
    vault.store(7, len(frag1), len(transformed1), mce.snapshot(), time.time())

    frag2 = b"second-longer"
    transformed2 = mce.digest_fragment(frag2)
    vault.store(7, len(frag2), len(transformed2), mce.snapshot(), time.time())

    assert len(vault.entries) == 1

    entry = vault.get(7)
    assert entry is not None
    assert entry.input_size == len(frag2)
    assert entry.output_size == len(transformed2)


def test_vault_clear():
    vault = Vault()
    mce = MCE(SEED)

    frag = b"test"
    transformed = mce.digest_fragment(frag)
    vault.store(0, len(frag), len(transformed), mce.snapshot(), time.time())

    assert len(vault.entries) == 1

    vault.clear()

    assert len(vault.entries) == 0


def test_vault_rejects_negative_fragment_id():
    vault = Vault()
    mce = MCE(SEED)

    with pytest.raises(ValueError):
        vault.store(-1, 1, 1, mce.snapshot(), time.time())


def test_vault_rejects_negative_sizes():
    vault = Vault()
    mce = MCE(SEED)

    with pytest.raises(ValueError):
        vault.store(0, -1, 1, mce.snapshot(), time.time())

    with pytest.raises(ValueError):
        vault.store(0, 1, -1, mce.snapshot(), time.time())


def test_vault_rejects_invalid_timestamp():
    vault = Vault()
    mce = MCE(SEED)

    with pytest.raises(TypeError):
        vault.store(0, 1, 1, mce.snapshot(), "not-a-timestamp")  # type: ignore[arg-type]
