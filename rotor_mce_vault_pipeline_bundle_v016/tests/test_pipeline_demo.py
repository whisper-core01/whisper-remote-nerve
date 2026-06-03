# tests/test_pipeline_demo.py

import pytest

from pipeline_demo import fragment_payload, run_pipeline


def test_fragment_payload_splits_correctly():
    payload = b"abcdefghij"
    fragments = fragment_payload(payload, fragment_size=4)

    assert fragments == [b"abcd", b"efgh", b"ij"]


def test_fragment_payload_rejects_invalid_size():
    with pytest.raises(ValueError):
        fragment_payload(b"abc", fragment_size=0)


def test_run_pipeline_summary_basic():
    payload = b"hello whisper pipeline"
    summary = run_pipeline(payload, fragment_size=5, seed=b"test-seed")

    assert summary["pipeline"] == "RotorMachine -> MCE -> Vault"
    assert summary["input_size"] == len(payload)
    assert summary["output_size"] == len(payload)
    assert summary["fragment_count"] == 5
    assert summary["final_mce_counter"] == 5
    assert len(summary["vault_entries"]) == 5


def test_run_pipeline_deterministic_for_same_seed():
    payload = b"deterministic pipeline payload"

    a = run_pipeline(payload, fragment_size=4, seed=b"same-seed")
    b = run_pipeline(payload, fragment_size=4, seed=b"same-seed")

    assert a["final_mce_state_hex"] == b["final_mce_state_hex"]
    assert a["transformed_preview_hex"] == b["transformed_preview_hex"]


def test_run_pipeline_changes_with_seed():
    payload = b"seed changes pipeline output"

    a = run_pipeline(payload, fragment_size=4, seed=b"seed-a")
    b = run_pipeline(payload, fragment_size=4, seed=b"seed-b")

    assert a["final_mce_state_hex"] != b["final_mce_state_hex"]
