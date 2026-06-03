# rotor_machine_v01.py
# Requires Python 3.8+

"""
RotorMachine v0.1.1

Purpose:
    Deterministic fragment representation mutation for Whisper experiments.

Security warning:
    This is NOT encryption.
    This is NOT a cryptographic primitive.
    This layer should only be used as symbolic / polymorphic transformation
    around already-encrypted fragments.

Recommended Whisper mode:
    transform_bytes() / inverse_transform_bytes()

Notes:
    - DeterministicStream instances are not thread-safe.
    - The implementation creates a fresh DeterministicStream per derivation, so
      normal RotorMachine usage is re-entrant as long as instances are not
      externally mutated.
    - Python does not guarantee secure zeroization of seed material.
      Do not use this implementation for production key handling.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Union

try:
    import blake3  # type: ignore

    def h32(data: bytes) -> bytes:
        """Return a 32-byte digest. Uses blake3 when installed."""
        return blake3.blake3(data).digest()

except ImportError:

    def h32(data: bytes) -> bytes:
        """Return a 32-byte digest. Portable fallback using hashlib.blake2b."""
        return hashlib.blake2b(data, digest_size=32).digest()


__version__ = "0.1.1"
__all__ = ["RotorMachine", "DeterministicStream"]

ROTORS = 3
MAX_RECOMMENDED_ROTORS = 8

ALPHABETS = {
    "greek": "αβγδεζηθικλμνξοπρστυφχψω",
    "cyrillic": "абвгдежзийклмнопрстуфхцчшщъыьэюя",
    "arabic": "ءابتثجحخدذرزسشصضطظعغفقكلمنهوي",
    "latin": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
}


def validate_fragment_id(fragment_id: int) -> None:
    """Validate that fragment_id can be encoded into the derivation context."""
    if not isinstance(fragment_id, int):
        raise TypeError("fragment_id must be an int")
    if fragment_id < 0:
        raise ValueError("fragment_id must be >= 0")
    if fragment_id >= 2**64:
        raise ValueError("fragment_id must fit in 64 bits")


@dataclass(frozen=True)
class Rotor:
    alphabet: List[str]
    permutation: List[str]
    index: Dict[str, int]
    inverse_index: Dict[str, str]


class DeterministicStream:
    """
    Deterministic byte stream derived from seed material.

    This is used to avoid random.Random while keeping reproducible shuffling.
    It is not thread-safe and is not intended as a cryptographic primitive.
    """

    def __init__(self, key: bytes):
        if not isinstance(key, (bytes, bytearray)):
            raise TypeError("key must be bytes")
        self.key = bytes(key)
        self.counter = 0
        self.buffer = b""

    def read(self, n: int) -> bytes:
        """Read n deterministic bytes from the stream."""
        if n < 0:
            raise ValueError("n must be >= 0")

        out = bytearray()

        while len(out) < n:
            if not self.buffer:
                block_input = self.key + b"|stream|" + self.counter.to_bytes(8, "big")
                self.buffer = h32(block_input)
                self.counter += 1

            take = min(n - len(out), len(self.buffer))
            out.extend(self.buffer[:take])
            self.buffer = self.buffer[take:]

        return bytes(out)

    def randbelow(self, upper: int) -> int:
        """
        Return a deterministic integer in [0, upper).

        Uses rejection sampling to avoid modulo bias.
        """
        if upper <= 0:
            raise ValueError("upper must be > 0")

        nbytes = max(1, (upper.bit_length() + 7) // 8)
        max_value = 1 << (8 * nbytes)
        limit = max_value - (max_value % upper)

        while True:
            candidate = int.from_bytes(self.read(nbytes), "big")
            if candidate < limit:
                return candidate % upper


class RotorMachine:
    """
    Deterministic rotor-style representation mutation.

    This class is intended for Whisper MVP experiments where fragments are
    already protected by real authenticated encryption. Use transform_bytes()
    for binary fragment mutation.
    """

    def __init__(
        self,
        seed: bytes,
        include_latin: bool = False,
        rotors: int = ROTORS,
    ):
        """
        Create a RotorMachine.

        Args:
            seed:
                Deterministic seed material. Python cannot securely zeroize it.
            include_latin:
                Enables Latin alphabet in text mode so ASCII strings are mutated.
            rotors:
                Number of rotor passes. Recommended range: 1..8 for MVP use.
        """
        if not isinstance(seed, (bytes, bytearray)):
            raise TypeError("seed must be bytes")

        if not isinstance(rotors, int) or rotors <= 0:
            raise ValueError("rotors must be a positive int")

        if rotors > MAX_RECOMMENDED_ROTORS:
            raise ValueError(
                f"rotors={rotors} is above the recommended maximum "
                f"({MAX_RECOMMENDED_ROTORS}) for this MVP implementation"
            )

        self.seed = bytes(seed)
        self.rotor_count = rotors

        self.alphabet_names = list(ALPHABETS.keys())
        if not include_latin:
            self.alphabet_names = [
                name for name in self.alphabet_names if name != "latin"
            ]

        if not self.alphabet_names:
            raise ValueError("at least one alphabet must be enabled")

    # ---------------------------------------------------------------------
    # Generic deterministic derivation
    # ---------------------------------------------------------------------

    def _ctx(
        self,
        label: bytes,
        fragment_id: int,
        rotor_id: Optional[int] = None,
    ) -> bytes:
        validate_fragment_id(fragment_id)

        data = self.seed + b"|" + label + b"|" + fragment_id.to_bytes(8, "big")

        if rotor_id is not None:
            if rotor_id < 0 or rotor_id >= 2**16:
                raise ValueError("rotor_id must fit in 16 bits")
            data += b"|" + rotor_id.to_bytes(2, "big")

        return data

    def _derive_rotor_order(self, fragment_id: int) -> List[int]:
        order = list(range(self.rotor_count))
        stream = DeterministicStream(self._ctx(b"order", fragment_id))

        for i in range(len(order) - 1, 0, -1):
            j = stream.randbelow(i + 1)
            order[i], order[j] = order[j], order[i]

        return order

    def _derive_alphabet_choice(self, rotor_id: int, fragment_id: int) -> int:
        raw = h32(self._ctx(b"alphabet", fragment_id, rotor_id))
        return raw[0] % len(self.alphabet_names)

    def _derive_permutation(
        self,
        alphabet: Sequence[str],
        rotor_id: int,
        fragment_id: int,
    ) -> List[str]:
        perm = list(alphabet)
        stream = DeterministicStream(self._ctx(b"perm", fragment_id, rotor_id))

        for i in range(len(perm) - 1, 0, -1):
            j = stream.randbelow(i + 1)
            perm[i], perm[j] = perm[j], perm[i]

        return perm

    @staticmethod
    def _make_rotor(alphabet: Sequence[str], permutation: Sequence[str]) -> Rotor:
        alphabet_list = list(alphabet)
        permutation_list = list(permutation)

        if len(alphabet_list) != len(permutation_list):
            raise ValueError("alphabet and permutation must have same length")
        if len(set(permutation_list)) != len(permutation_list):
            raise ValueError("permutation must contain unique symbols")

        index = {ch: i for i, ch in enumerate(alphabet_list)}
        inverse_index = {
            out_ch: in_ch
            for in_ch, out_ch in zip(alphabet_list, permutation_list)
        }

        return Rotor(
            alphabet=alphabet_list,
            permutation=permutation_list,
            index=index,
            inverse_index=inverse_index,
        )

    # ---------------------------------------------------------------------
    # Unicode mode
    # ---------------------------------------------------------------------

    def _build_unicode_rotors(self, fragment_id: int) -> List[Rotor]:
        rotors = []

        for rotor_id in range(self.rotor_count):
            alphabet_idx = self._derive_alphabet_choice(rotor_id, fragment_id)
            alphabet_name = self.alphabet_names[alphabet_idx]
            alphabet = list(ALPHABETS[alphabet_name])
            permutation = self._derive_permutation(alphabet, rotor_id, fragment_id)
            rotors.append(self._make_rotor(alphabet, permutation))

        order = self._derive_rotor_order(fragment_id)
        return [rotors[i] for i in order]

    def transform_text(self, input_text: str, fragment_id: int) -> str:
        """
        Transform Unicode text.

        Characters not present in a rotor alphabet pass through unchanged.
        Use include_latin=True to mutate ASCII letters in text mode.
        """
        if not isinstance(input_text, str):
            raise TypeError("input_text must be str")

        output = list(input_text)
        rotors = self._build_unicode_rotors(fragment_id)

        for rotor in rotors:
            output = self._pass_through_rotor(output, rotor)

        return "".join(output)

    def inverse_transform_text(self, transformed_text: str, fragment_id: int) -> str:
        """Reverse a Unicode text transformation made with transform_text()."""
        if not isinstance(transformed_text, str):
            raise TypeError("transformed_text must be str")

        output = list(transformed_text)
        rotors = self._build_unicode_rotors(fragment_id)

        for rotor in reversed(rotors):
            output = self._pass_back_through_rotor(output, rotor)

        return "".join(output)

    # ---------------------------------------------------------------------
    # Byte mode
    # ---------------------------------------------------------------------

    def _build_byte_rotors(self, fragment_id: int) -> List[Rotor]:
        alphabet = [f"{i:02x}" for i in range(256)]
        rotors = []

        for rotor_id in range(self.rotor_count):
            permutation = self._derive_permutation(alphabet, rotor_id, fragment_id)
            rotors.append(self._make_rotor(alphabet, permutation))

        order = self._derive_rotor_order(fragment_id)
        return [rotors[i] for i in order]

    def transform_bytes(self, data: Union[bytes, bytearray], fragment_id: int) -> bytes:
        """
        Transform raw bytes and return raw bytes.

        This is the recommended mode for Whisper fragment experiments.
        """
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes")

        tokens = [f"{b:02x}" for b in bytes(data)]
        rotors = self._build_byte_rotors(fragment_id)

        for rotor in rotors:
            tokens = self._pass_through_rotor(tokens, rotor)

        return bytes(int(tok, 16) for tok in tokens)

    def inverse_transform_bytes(
        self,
        transformed_data: Union[bytes, bytearray],
        fragment_id: int,
    ) -> bytes:
        """Reverse a byte transformation made with transform_bytes()."""
        if not isinstance(transformed_data, (bytes, bytearray)):
            raise TypeError("transformed_data must be bytes")

        tokens = [f"{b:02x}" for b in bytes(transformed_data)]
        rotors = self._build_byte_rotors(fragment_id)

        for rotor in reversed(rotors):
            tokens = self._pass_back_through_rotor(tokens, rotor)

        return bytes(int(tok, 16) for tok in tokens)

    def transform_bytes_hex(self, data: Union[bytes, bytearray], fragment_id: int) -> str:
        """Debug helper: transform bytes and return the result as hex."""
        return self.transform_bytes(data, fragment_id).hex()

    # ---------------------------------------------------------------------
    # Convenience wrappers
    # ---------------------------------------------------------------------

    def transform(
        self,
        input_data: Union[str, bytes, bytearray],
        fragment_id: int,
    ) -> Union[str, bytes]:
        """
        Transform text or bytes.

        str input returns str.
        bytes input returns bytes.
        """
        if isinstance(input_data, str):
            return self.transform_text(input_data, fragment_id)

        if isinstance(input_data, (bytes, bytearray)):
            return self.transform_bytes(input_data, fragment_id)

        raise TypeError("input_data must be str or bytes")

    def inverse_transform(
        self,
        input_data: Union[str, bytes, bytearray],
        fragment_id: int,
    ) -> Union[str, bytes]:
        """
        Reverse transform().

        str input returns str.
        bytes input returns bytes.
        """
        if isinstance(input_data, str):
            return self.inverse_transform_text(input_data, fragment_id)

        if isinstance(input_data, (bytes, bytearray)):
            return self.inverse_transform_bytes(input_data, fragment_id)

        raise TypeError("input_data must be str or bytes")

    # ---------------------------------------------------------------------
    # Rotor pass helpers
    # ---------------------------------------------------------------------

    @staticmethod
    def _pass_through_rotor(chars: List[str], rotor: Rotor) -> List[str]:
        output = []

        for char in chars:
            idx = rotor.index.get(char)
            if idx is None:
                output.append(char)
            else:
                output.append(rotor.permutation[idx])

        return output

    @staticmethod
    def _pass_back_through_rotor(chars: List[str], rotor: Rotor) -> List[str]:
        output = []

        for char in chars:
            original = rotor.inverse_index.get(char)
            if original is None:
                output.append(char)
            else:
                output.append(original)

        return output


if __name__ == "__main__":
    import os
    import time

    seed = b"whisper-test-seed-12345"

    print("=== Unicode Test ===")
    rm_unicode = RotorMachine(seed)
    sample_unicode = "αβγ абв ابت"

    encoded_u = rm_unicode.transform_text(sample_unicode, fragment_id=0)
    decoded_u = rm_unicode.inverse_transform_text(encoded_u, fragment_id=0)

    print("Input:    ", sample_unicode)
    print("Encoded:  ", encoded_u)
    print("Decoded:  ", decoded_u)
    print("Roundtrip:", decoded_u == sample_unicode)

    print("\n=== Latin Test ===")
    rm_latin = RotorMachine(seed, include_latin=True)
    sample_latin = "HELLO Whisper"

    encoded_l = rm_latin.transform_text(sample_latin, fragment_id=0)
    decoded_l = rm_latin.inverse_transform_text(encoded_l, fragment_id=0)

    print("Input:    ", sample_latin)
    print("Encoded:  ", encoded_l)
    print("Decoded:  ", decoded_l)
    print("Roundtrip:", decoded_l == sample_latin)

    print("\n=== Byte Mode Test ===")
    rm_bytes = RotorMachine(seed)
    sample_bytes = b"HELLO Whisper\x00\x01\x02"

    encoded_b = rm_bytes.transform_bytes(sample_bytes, fragment_id=0)
    decoded_b = rm_bytes.inverse_transform_bytes(encoded_b, fragment_id=0)

    print("Input bytes:  ", sample_bytes)
    print("Encoded hex:  ", encoded_b.hex())
    print("Decoded bytes:", decoded_b)
    print("Roundtrip:    ", decoded_b == sample_bytes)

    print("\n=== Byte Mode Determinism Test ===")
    rm_a = RotorMachine(seed)
    rm_b = RotorMachine(seed)

    out_a = rm_a.transform_bytes(sample_bytes, fragment_id=42)
    out_b = rm_b.transform_bytes(sample_bytes, fragment_id=42)

    print("Deterministic:", out_a == out_b)

    print("\n=== Fragment Mutation Test ===")
    out_1 = rm_bytes.transform_bytes(sample_bytes, fragment_id=1)
    out_2 = rm_bytes.transform_bytes(sample_bytes, fragment_id=2)

    print("Fragment 1 hex:", out_1.hex())
    print("Fragment 2 hex:", out_2.hex())
    print("Different:     ", out_1 != out_2)

    print("\n=== Random Payload Roundtrip Test ===")
    ok = True

    for fragment_id in range(100):
        payload = os.urandom(128)
        enc = rm_bytes.transform_bytes(payload, fragment_id)
        dec = rm_bytes.inverse_transform_bytes(enc, fragment_id)

        if dec != payload:
            ok = False
            print("Failed at fragment:", fragment_id)
            break

    print("100 random roundtrips:", ok)

    print("\n=== Output Diversity Test ===")
    outputs = set()

    for fragment_id in range(100):
        outputs.add(rm_bytes.transform_bytes(sample_bytes, fragment_id))

    print(f"100 fragments, {len(outputs)} unique outputs")

    print("\n=== Latency Test ===")
    start = time.time()

    for fragment_id in range(1000):
        rm_bytes.transform_bytes(sample_bytes, fragment_id)

    elapsed = time.time() - start

    print(f"1000 fragments: {elapsed:.3f}s")
    print(f"Per fragment:   {elapsed * 1000 / 1000:.3f} ms")
