# Changelog

## v0.1.5

Test runner import-path fix.

### Added

- `tests/conftest.py`

### Fixed

- Allows pytest to be run from the `tests/` directory without `ModuleNotFoundError` for project-level modules such as `mce_v01`, `rotor_machine_v01`, and `vault_v01`.

## v0.1.4

Added Vault v0.1 minimal metadata persistence.

### Added

- `vault_v01.py`
- `tests/test_vault_v01.py`
- `bench/bench_vault.py`
- Vault usage section in README.
- Vault non-guarantees section.
- Explicit system split:
  - RotorMachine = transformation;
  - MCE = state evolution;
  - Vault = state persistence.

### Security notes

Vault v0.1 is an in-memory metadata store only. It is not encrypted storage, not tamper-resistant storage, and not a key vault.

## v0.1.3

README and documentation hardening.

### Added

- Explicit statement: `RotorMachine is deterministic per (seed, fragment_id)`.
- Explicit bijection statement for a given `(seed, fragment_id)`.
- Unicode behavior section.
- Byte mode behavior section.
- Non-guarantees section.
- MCE usage section.
- MCE non-guarantees.
- Operational recommendation section.

## v0.1.2

Added MCE integration bundle.

## v0.1.1

RotorMachine MVP hardening.

## v0.1.0

Initial RotorMachine MVP.
