"""Validate the binary transport representation against all canonical vectors."""

from __future__ import annotations

import json
from pathlib import Path

from wire import (
    decode_matrix,
    decode_matrix_parameters,
    decode_octonion,
    decode_octonion_parameters,
    encode_matrix,
    encode_matrix_parameters,
    encode_octonion,
    encode_octonion_parameters,
)

VECTOR_NAMES = (
    "test_vector_p13.json",
    "test_vector_p251.json",
    "test_vector_p65521.json",
    "test_vector_p4294967279.json",
    "test_vector_p18446744073709551557.json",
)


def locate_vector_directory() -> Path:
    return Path(__file__).resolve().parent.parent / "general" / "test_vectors"


def load(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def as_matrix(value):
    return tuple(tuple(int(item) for item in row) for row in value)


def as_octonion(value):
    return tuple(int(item) for item in value)


def validate(path: Path) -> None:
    vector = load(path)
    params = vector["parameters"]
    inputs = vector["inputs"]
    expected = vector["expected"]

    p = int(params["modulo"])
    q = int(params["matrix_modulo"])
    u = int(inputs["u"])
    v = int(inputs["v"])
    A = as_matrix(inputs["A"])
    B = as_matrix(inputs["B"])
    oA = as_octonion(inputs["oA"])

    matrix_params_payload = encode_matrix_parameters(A, B, q, u, v)
    decoded_matrix_params = decode_matrix_parameters(matrix_params_payload)
    assert decoded_matrix_params["A"] == A
    assert decoded_matrix_params["B"] == B
    assert decoded_matrix_params["q"] == q
    assert decoded_matrix_params["u"] == u
    assert decoded_matrix_params["v"] == v

    for field in ("TA", "TB", "MA", "MB", "M"):
        matrix = as_matrix(expected[field])
        assert decode_matrix(encode_matrix(matrix, q), q) == matrix

    oct_params_payload = encode_octonion_parameters(p, oA)
    decoded_oct_params = decode_octonion_parameters(oct_params_payload)
    assert decoded_oct_params["p"] == p
    assert decoded_oct_params["oA"] == oA

    for field in ("oB", "rA", "rB", "kA", "kB", "session_key"):
        octonion = as_octonion(expected[field])
        assert decode_octonion(encode_octonion(octonion, p), p) == octonion


def main() -> int:
    vector_dir = locate_vector_directory()
    print("=" * 100)
    print("HK17.2 RASPBERRY PI / ESP32 BINARY WIRE CONFORMANCE TEST")
    print("=" * 100)

    failures = 0
    for name in VECTOR_NAMES:
        try:
            validate(vector_dir / name)
            print(f"[PASS] {name}")
        except Exception as exc:
            failures += 1
            print(f"[FAIL] {name}: {exc}")

    print("=" * 100)
    if failures:
        print(f"FAILURE: {failures} canonical vector(s) failed binary wire validation.")
        return 1

    print("SUCCESS: the binary wire representation preserves all five canonical HK17.2 vectors.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
