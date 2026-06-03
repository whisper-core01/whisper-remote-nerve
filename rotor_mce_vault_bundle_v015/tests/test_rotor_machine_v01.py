# tests/test_rotor_machine_v01.py

import os
import pytest

from rotor_machine_v01 import RotorMachine, DeterministicStream


SEED = b"whisper-test-seed-12345"


def test_roundtrip_bytes_100_random_payloads():
    rm = RotorMachine(SEED)

    for fragment_id in range(100):
        payload = os.urandom(128)
        encoded = rm.transform_bytes(payload, fragment_id)
        decoded = rm.inverse_transform_bytes(encoded, fragment_id)

        assert decoded == payload


def test_roundtrip_text_unicode():
    rm = RotorMachine(SEED)
    sample = "αβγ абв ابت"

    encoded = rm.transform_text(sample, fragment_id=0)
    decoded = rm.inverse_transform_text(encoded, fragment_id=0)

    assert decoded == sample


def test_roundtrip_text_latin():
    rm = RotorMachine(SEED, include_latin=True)
    sample = "HELLO Whisper"

    encoded = rm.transform_text(sample, fragment_id=0)
    decoded = rm.inverse_transform_text(encoded, fragment_id=0)

    assert decoded == sample
    assert encoded != sample


def test_latin_not_transformed_without_include_latin():
    rm = RotorMachine(SEED)
    sample = "HELLO"

    encoded = rm.transform_text(sample, fragment_id=0)

    assert encoded == sample


def test_fragment_variation_bytes():
    rm = RotorMachine(SEED)
    payload = b"HELLO Whisper\x00\x01\x02"

    out_1 = rm.transform_bytes(payload, fragment_id=1)
    out_2 = rm.transform_bytes(payload, fragment_id=2)

    assert out_1 != out_2


def test_determinism_bytes_same_seed_same_fragment():
    rm_a = RotorMachine(SEED)
    rm_b = RotorMachine(SEED)
    payload = b"deterministic-test"

    out_a = rm_a.transform_bytes(payload, fragment_id=42)
    out_b = rm_b.transform_bytes(payload, fragment_id=42)

    assert out_a == out_b


def test_different_seed_changes_output():
    rm_a = RotorMachine(b"seed-A")
    rm_b = RotorMachine(b"seed-B")
    payload = b"seed-test"

    out_a = rm_a.transform_bytes(payload, fragment_id=0)
    out_b = rm_b.transform_bytes(payload, fragment_id=0)

    assert out_a != out_b


def test_output_diversity_smoke():
    rm = RotorMachine(SEED)
    payload = b"HELLO Whisper"

    outputs = {
        rm.transform_bytes(payload, fragment_id=i)
        for i in range(100)
    }

    assert len(outputs) >= 95


def test_transform_wrapper_bytes():
    rm = RotorMachine(SEED)
    payload = b"wrapper-test"

    encoded = rm.transform(payload, fragment_id=0)
    decoded = rm.inverse_transform(encoded, fragment_id=0)

    assert isinstance(encoded, bytes)
    assert decoded == payload


def test_transform_wrapper_text():
    rm = RotorMachine(SEED, include_latin=True)
    payload = "WrapperTest"

    encoded = rm.transform(payload, fragment_id=0)
    decoded = rm.inverse_transform(encoded, fragment_id=0)

    assert isinstance(encoded, str)
    assert decoded == payload


def test_invalid_seed_type():
    with pytest.raises(TypeError):
        RotorMachine("not-bytes")  # type: ignore[arg-type]


def test_invalid_fragment_id_negative():
    rm = RotorMachine(SEED)

    with pytest.raises(ValueError):
        rm.transform_bytes(b"x", fragment_id=-1)


def test_invalid_fragment_id_too_large():
    rm = RotorMachine(SEED)

    with pytest.raises(ValueError):
        rm.transform_bytes(b"x", fragment_id=2**64)


def test_invalid_rotor_count_zero():
    with pytest.raises(ValueError):
        RotorMachine(SEED, rotors=0)


def test_invalid_rotor_count_too_large():
    with pytest.raises(ValueError):
        RotorMachine(SEED, rotors=99)


def test_deterministic_stream_randbelow_bounds():
    stream = DeterministicStream(b"test")

    for upper in [1, 2, 3, 7, 255, 256, 257, 1000]:
        for _ in range(50):
            value = stream.randbelow(upper)
            assert 0 <= value < upper


def test_performance_smoke():
    rm = RotorMachine(SEED)
    payload = os.urandom(256)

    for fragment_id in range(200):
        rm.transform_bytes(payload, fragment_id)
