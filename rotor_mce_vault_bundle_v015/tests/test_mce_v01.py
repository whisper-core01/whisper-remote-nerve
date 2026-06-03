# tests/test_mce_v01.py

from mce_v01 import MCE


SEED = b"whisper-mce-seed"


def test_mce_deterministic_batch():
    fragments = [b"fragment_%d" % i for i in range(100)]

    mce_a = MCE(SEED)
    mce_b = MCE(SEED)

    out_a = mce_a.process_batch(fragments)
    out_b = mce_b.process_batch(fragments)

    assert out_a == out_b
    assert mce_a.snapshot() == mce_b.snapshot()


def test_mce_state_changes_per_fragment():
    fragments = [b"fragment_%d" % i for i in range(50)]
    mce = MCE(SEED)

    states = []

    for fragment in fragments:
        mce.digest_fragment(fragment)
        states.append(mce.snapshot().state_digest)

    assert len(set(states)) == len(states)


def test_mce_output_diversity():
    fragments = [b"fragment_%d" % i for i in range(100)]
    mce = MCE(SEED)

    outputs = mce.process_batch(fragments)

    assert len(set(outputs)) == len(outputs)


def test_mce_counter_updates():
    mce = MCE(SEED)

    assert mce.fragment_counter == 0

    mce.digest_fragment(b"one")
    assert mce.fragment_counter == 1

    mce.digest_fragment(b"two")
    assert mce.fragment_counter == 2


def test_mce_reset():
    fragments = [b"a", b"b", b"c"]

    mce = MCE(SEED)
    out_1 = mce.process_batch(fragments)
    snap_1 = mce.snapshot()

    mce.reset()
    out_2 = mce.process_batch(fragments)
    snap_2 = mce.snapshot()

    assert out_1 == out_2
    assert snap_1 == snap_2


def test_mce_sequence_order_matters():
    mce_a = MCE(SEED)
    mce_b = MCE(SEED)

    out_a = mce_a.process_batch([b"a", b"b", b"c"])
    out_b = mce_b.process_batch([b"c", b"b", b"a"])

    assert out_a != out_b
    assert mce_a.snapshot() != mce_b.snapshot()
