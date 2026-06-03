# mce_v01.py
# Requires Python 3.8+

"""
MCE v0.1 — Metabolic Correlation Engine

Purpose:
    Experimental state-feedback layer for Whisper MVP experiments.

Security warning:
    This is NOT encryption.
    This is NOT authentication.
    This is NOT a cryptographic key schedule.
    It is an experimental deterministic state-evolution mechanism designed
    to study fragment divergence and feedback amplification.

Recommended use:
    Apply MCE only around fragments already protected by authenticated
    encryption, such as XChaCha20-Poly1305 / ChaCha20-Poly1305.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence

from rotor_machine_v01 import RotorMachine


__version__ = "0.1.0"
__all__ = ["MCE", "MCEState"]


def h32(data: bytes) -> bytes:
    """Portable 32-byte hash helper."""
    return hashlib.blake2b(data, digest_size=32).digest()


@dataclass(frozen=True)
class MCEState:
    fragment_counter: int
    state_digest: bytes

    def hex(self, n: Optional[int] = None) -> str:
        if n is None:
            return self.state_digest.hex()
        return self.state_digest[:n].hex()


class MCE:
    """
    Metabolic Correlation Engine.

    Each processed fragment:
        1. derives a RotorMachine from the current state;
        2. transforms the fragment using the current fragment counter;
        3. feeds transformed bytes back into the state;
        4. increments the fragment counter.

    This creates deterministic state divergence across fragment sequences.
    """

    def __init__(self, seed: bytes, rotors: int = 3):
        if not isinstance(seed, (bytes, bytearray)):
            raise TypeError("seed must be bytes")

        if not isinstance(rotors, int) or rotors <= 0:
            raise ValueError("rotors must be a positive int")

        self.initial_seed = bytes(seed)
        self.state = h32(b"mce:init|" + bytes(seed))
        self.fragment_counter = 0
        self.rotors = rotors

    def snapshot(self) -> MCEState:
        """Return an immutable snapshot of the current MCE state."""
        return MCEState(
            fragment_counter=self.fragment_counter,
            state_digest=self.state,
        )

    def reset(self) -> None:
        """Reset the engine to the original initial seed."""
        self.state = h32(b"mce:init|" + self.initial_seed)
        self.fragment_counter = 0

    def _derive_rotor_seed(self, fragment_id: int) -> bytes:
        return h32(
            b"mce:rotor-seed|"
            + self.state
            + b"|"
            + fragment_id.to_bytes(8, "big")
        )

    def _update_state(self, fragment: bytes, transformed: bytes, fragment_id: int) -> None:
        self.state = h32(
            b"mce:update|"
            + self.state
            + b"|fid|"
            + fragment_id.to_bytes(8, "big")
            + b"|in|"
            + len(fragment).to_bytes(8, "big")
            + fragment
            + b"|out|"
            + len(transformed).to_bytes(8, "big")
            + transformed
        )

    def digest_fragment(self, fragment: bytes) -> bytes:
        """
        Transform one fragment and evolve internal state.

        Args:
            fragment:
                Raw fragment bytes.

        Returns:
            Transformed fragment bytes.
        """
        if not isinstance(fragment, (bytes, bytearray)):
            raise TypeError("fragment must be bytes")

        fragment = bytes(fragment)
        fragment_id = self.fragment_counter

        rotor_seed = self._derive_rotor_seed(fragment_id)
        rm = RotorMachine(rotor_seed, rotors=self.rotors)

        transformed = rm.transform_bytes(fragment, fragment_id)
        self._update_state(fragment, transformed, fragment_id)

        self.fragment_counter += 1
        return transformed

    def process_batch(self, fragments: Sequence[bytes]) -> List[bytes]:
        """Transform a sequence of fragments and evolve state after each one."""
        return [self.digest_fragment(fragment) for fragment in fragments]

    def process_iterable(self, fragments: Iterable[bytes]) -> Iterable[bytes]:
        """Lazy iterable interface."""
        for fragment in fragments:
            yield self.digest_fragment(fragment)


if __name__ == "__main__":
    import time

    seed = b"whisper-mce-seed"
    fragments = [b"fragment_%d" % i for i in range(100)]

    mce = MCE(seed)

    start = time.time()
    results = mce.process_batch(fragments)
    elapsed = time.time() - start

    print("=== MCE v0.1 Smoke Test ===")
    print(f"Processed 100 fragments in {elapsed:.3f}s")
    print(f"Outputs: {len(results)}")
    print(f"Unique outputs: {len(set(results))}")
    print(f"Final counter: {mce.fragment_counter}")
    print(f"Final state: {mce.snapshot().hex(8)}")

    states = []
    mce2 = MCE(seed)

    for fragment in fragments:
        mce2.digest_fragment(fragment)
        states.append(mce2.snapshot().hex(8))

    print(f"First 5 states: {states[:5]}")
    print(f"All states different: {len(set(states)) == len(states)}")

    mce_a = MCE(seed)
    mce_b = MCE(seed)

    out_a = mce_a.process_batch(fragments)
    out_b = mce_b.process_batch(fragments)

    print(f"Deterministic batch: {out_a == out_b}")
    print(f"Deterministic final state: {mce_a.snapshot() == mce_b.snapshot()}")
