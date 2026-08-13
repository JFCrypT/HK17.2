# HK17.2 Canonical Test Vectors

This directory contains the **official canonical conformance vectors for the frozen HK17.2 implementation in this repository**.

The five vectors were generated and validated against the final PC reference implementation before being frozen. They must **not** be regenerated during normal development or validation.

## Canonical vectors

| File | Public modulus `p` | Octonion component bits | Octonion polynomial degree | Matrix modulus `q` |
|---|---:|---:|---:|---:|
| `test_vector_p13.json` | 13 | 4 | 8 | 4 |
| `test_vector_p251.json` | 251 | 8 | 16 | 16 |
| `test_vector_p65521.json` | 65521 | 16 | 32 | 256 |
| `test_vector_p4294967279.json` | 4294967279 | 32 | 64 | 65536 |
| `test_vector_p18446744073709551557.json` | 18446744073709551557 | 64 | 128 | 4294967296 |

Each JSON file stores:

- system parameters;
- fixed protocol inputs;
- matrix polynomial evaluations;
- matrix powers;
- matrix tokens `TA` and `TB`;
- shared matrices `MA`, `MB`, and `M`;
- submatrix sums;
- all four deterministic `oB` candidates, their quadratic norms, and invertibility flags;
- selected `oB` and its inverse;
- octonion polynomial evaluations;
- powered polynomial evaluations;
- both autoconvolutions;
- `rA` and `rB`;
- the recovered Alice autoconvolution;
- `kA`, `kB`, and the final session key.

## Normal validation

Normal validation does **not** use the stored generation seed. It reads the hardcoded `inputs` from each canonical JSON file, recomputes HK17.2 with `vector_core.py`, and compares every recomputed value against the hardcoded `expected` section.

It also verifies the SHA-256 digest of every canonical JSON vector before running the conformance test.

```bash
cd general/test_vectors
python3 validate_test_vectors.py
```

Expected result:

```text
[PASS] test_vector_p13.json
[PASS] test_vector_p251.json
[PASS] test_vector_p65521.json
[PASS] test_vector_p4294967279.json
[PASS] test_vector_p18446744073709551557.json
```

## Integrity

`SHA256SUMS` contains the frozen SHA-256 digest of every canonical JSON vector. Any modification to a canonical vector causes normal validation to fail before protocol recomputation.

## Regeneration policy

`generate_test_vectors.py` is retained only for provenance and deliberate reconstruction. It refuses to overwrite canonical vectors unless invoked with `--force`.

**Do not run it during normal validation.** Regenerating the vectors establishes a new reference set and therefore requires an explicit project decision and subsequent re-freezing of the SHA-256 digests.

## Ports

These JSON files are the single canonical data source for conformance testing of:

- the final Python PC implementation;
- the Raspberry Pi 3 KMS port;
- the ESP32 C++/PlatformIO port;
- any future HK17.2 port or optimization intended to preserve protocol semantics.

A platform-specific representation, such as a generated C++ header for ESP32, is a derived artifact and must reproduce these canonical JSON values exactly.
