# RotorMachine + MCE + Vault Bundle v0.1.4

Deterministic rotor-style representation mutation, experimental MCE state-feedback, and minimal Vault metadata persistence for Whisper MVP experiments.

## Status

This bundle contains:

```text
RotorMachine v0.1.1
MCE v0.1.0
Vault v0.1.0
Bundle README v0.1.4
```

System split:

```text
RotorMachine = deterministic fragment transformation
MCE          = state evolution
Vault        = state persistence / metadata log
```

These modules are **not encryption** and **not cryptographic primitives**.

They provide deterministic, reversible, symbolic transformation, state-evolution experiments, and metadata persistence for Whisper fragment polymorphism. They must only be used **around already-encrypted fragments** such as XChaCha20-Poly1305 or ChaCha20-Poly1305 ciphertexts.

## Cryptographic disclaimer

RotorMachine does **not** provide:

- confidentiality;
- integrity;
- authentication;
- indistinguishability;
- collision resistance;
- diffusion or avalanche properties;
- secure memory handling;
- metadata protection.

It is **not** a PRP, **not** a cipher, **not** a hash, and **not** a KDF.

RotorMachine is a deterministic bijective mapping parameterized by `(seed, fragment_id)`.

MCE is an experimental deterministic feedback engine. It is not a cryptographic key schedule and must not be treated as one.

Vault is an in-memory metadata store. It is not encrypted storage, not tamper-resistant storage, and not a key vault.

## Determinism and bijection

For a given `(seed, fragment_id)`:

- `transform_bytes()` is deterministic;
- `inverse_transform_bytes(transform_bytes(x, id), id) == x`;
- different `fragment_id` values produce different rotor configurations.

Important wording:

```text
RotorMachine is deterministic per (seed, fragment_id).
```

The transformation is a bijection for a given `(seed, fragment_id)`.

This property is essential for Whisper’s fragment polymorphism layer.

## Requirements

Python 3.8+

Optional:

```bash
pip install blake3
```

If `blake3` is not installed, the implementation falls back to `hashlib.blake2b`.

## Files

```text
rotor_machine_v01.py
mce_v01.py
vault_v01.py
tests/test_rotor_machine_v01.py
tests/test_mce_v01.py
tests/test_vault_v01.py
bench/bench_rotor.py
bench/bench_mce.py
bench/bench_vault.py
README.md
CHANGELOG.md
COMMIT_MESSAGE.txt
```

## Quick start

```python
from rotor_machine_v01 import RotorMachine

seed = b"whisper-test-seed-12345"
rm = RotorMachine(seed)

fragment_id = 42
fragment = b"HELLO Whisper"

encoded = rm.transform_bytes(fragment, fragment_id)
decoded = rm.inverse_transform_bytes(encoded, fragment_id)

assert decoded == fragment
```

## Recommended Whisper mode

Use bytes mode:

```python
encoded = rm.transform_bytes(fragment_bytes, fragment_id)
decoded = rm.inverse_transform_bytes(encoded, fragment_id)
```

Text mode exists only for visual experimentation:

```python
rm = RotorMachine(seed, include_latin=True)
encoded = rm.transform_text("HELLO Whisper", fragment_id=0)
decoded = rm.inverse_transform_text(encoded, fragment_id=0)
```

## Unicode behavior

In text mode:

- only characters present in the selected alphabets are transformed;
- all other characters pass through unchanged;
- roundtrip is guaranteed for any Unicode string.

## Byte mode behavior

In byte mode:

- all byte values `0x00` through `0xff` are transformable;
- output length equals input length;
- transformation is reversible for the same `(seed, fragment_id)`;
- output is returned as raw `bytes`.

Byte mode is the recommended mode for Whisper fragment experiments.

## MCE usage

```python
from mce_v01 import MCE

mce = MCE(b"whisper-mce-seed")

fragments = [b"fragment_0", b"fragment_1", b"fragment_2"]
outputs = mce.process_batch(fragments)

print(mce.snapshot().hex(8))
```

MCE behavior:

```text
1. derive rotor seed from current MCE state;
2. transform fragment through RotorMachine;
3. feed original fragment + transformed fragment back into state;
4. increment fragment counter;
5. produce deterministic state divergence across fragment sequences.
```

MCE is sequence-dependent: processing `[a, b, c]` is expected to produce a different final state than processing `[c, b, a]`.

## Vault usage

```python
import time

from mce_v01 import MCE
from vault_v01 import Vault

mce = MCE(b"whisper-vault-seed")
vault = Vault()

fragment = b"example-fragment"
transformed = mce.digest_fragment(fragment)

vault.store(
    fragment_id=0,
    input_size=len(fragment),
    output_size=len(transformed),
    mce_state=mce.snapshot(),
    timestamp=time.time(),
)

entry = vault.get(0)
print(entry)
print(vault.dump())
```

Vault behavior:

```text
1. stores fragment metadata keyed by fragment_id;
2. records input size and output size;
3. records truncated MCE state digest via mce_state.hex(8);
4. records timestamp;
5. dumps deterministic JSON sorted by fragment_id.
```

Vault does not store fragments, seeds, plaintext, ciphertext, or key material.

## Rotor count

Default: 3 rotors.

The implementation rejects `rotors > 8` because rotor permutations are rebuilt per fragment.

For high-throughput use:

- cache rotor derivations for repeated fragment IDs;
- optimize byte-token handling;
- move the hot path to Rust/WASM;
- handle seed material with native memory controls.

## Running tests

```bash
pip install pytest
pytest -q
```


## Running tests from subdirectories

The test suite includes `tests/conftest.py`, so tests can be run from either the project root or the `tests/` directory.

From project root:

```bash
pytest -q
```

From `tests/`:

```bash
cd tests
pytest -q test_vault_v01.py
```

## Benchmark

RotorMachine:

```bash
python bench/bench_rotor.py --fragments 10000 --payload-size 256
```

MCE:

```bash
python bench/bench_mce.py --fragments 10000 --payload-size 256
```

Vault:

```bash
python bench/bench_vault.py --fragments 10000 --payload-size 256
```

## Expected properties

For the same seed and fragment ID:

```text
transform_bytes(payload, id) is deterministic
inverse_transform_bytes(transform_bytes(payload, id), id) == payload
```

For different fragment IDs:

```text
transform_bytes(payload, id1) != transform_bytes(payload, id2)
```

This is usually true for non-trivial payloads, but not a cryptographic guarantee.

## Non-guarantees

RotorMachine does not guarantee:

```text
collision resistance
diffusion
avalanche effect
indistinguishability
pseudorandom permutation security
chosen-plaintext security
chosen-ciphertext security
metadata hiding
side-channel resistance
secure zeroization
```

MCE does not guarantee:

```text
secure key evolution
forward secrecy
backward secrecy
entropy extraction
cryptographic randomness
state compromise recovery
```

Vault does not guarantee:

```text
encrypted storage
tamper resistance
secure audit logging
anti-rollback protection
access control
confidentiality
integrity
secure deletion
```

These are experimental transformation / state / metadata layers, not security boundaries.

## Test Results (v0.1.4)

Example smoke results from local execution:

| Test | Result |
|------|--------|
| Determinism `(seed + fragment_id)` | ✓ deterministic |
| Roundtrip `100 random payloads` | ✓ 100/100 |
| Fragment mutation | ✓ different outputs across fragment IDs |
| Output diversity | ✓ 100 unique outputs over 100 fragments |
| Byte roundtrip | ✓ input recovered exactly |
| MCE deterministic batch | ✓ same seed + same sequence = same output |
| MCE sequence sensitivity | ✓ different order = different final state |
| Vault store/retrieve | ✓ entries recoverable by fragment ID |
| Vault JSON dump | ✓ deterministic JSON sorted by fragment ID |

Benchmark values depend on CPU, Python version, payload size, hash backend, and rotor count.

Run your own benchmark before claiming performance numbers:

```bash
python bench/bench_rotor.py --fragments 10000 --payload-size 256
python bench/bench_mce.py --fragments 10000 --payload-size 256
python bench/bench_vault.py --fragments 10000 --payload-size 256
```

## State Space

For the default 3-rotor symbolic configuration with 4 alphabets enabled:

- Rotor orderings: `3! = 6`
- Alphabet choices: `4^3 = 64`
- Per-fragment symbolic configurations: `6 × 64 = 384`
- Over 1000 fragments: `384^1000 ≈ 10^2584`

This is an approximate symbolic configuration count, not a cryptographic security claim.

In byte mode, each rotor operates over a 256-symbol alphabet, so the theoretical permutation space is vastly larger. However, this implementation derives permutations deterministically from seed material and fragment ID, so security must not be inferred from permutation counts.

Without the seed, output is computationally difficult to reproduce in practice, but this should not be treated as a confidentiality guarantee.

## Operational recommendation

MVP:

```text
Python implementation
pytest coverage
README clarity
benchmark scripts
use transform_bytes()
```

Hardening:

```text
Rust/WASM hot path
native memory handling
mlock where appropriate
explicit zeroization
larger benchmark suite
CI integration
```

Crypto:

```text
Keep RotorMachine, MCE and Vault as polymorphism/state/metadata experiment layers only.
Use authenticated encryption for confidentiality and authenticity.
```
