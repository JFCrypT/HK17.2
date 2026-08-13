"""HK17.2 Raspberry Pi / Alice-KMS canonical conformance test.

The test consumes the official JSON vectors from `general/test_vectors/`.
It never regenerates or modifies those vectors.

Only Alice/KMS inputs are injected. Bob is represented exclusively by the
values Alice receives in the frozen protocol: TB and rB.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from kms import AliceSession, derive_system_parameters


VECTOR_NAMES = (
    "test_vector_p13.json",
    "test_vector_p251.json",
    "test_vector_p65521.json",
    "test_vector_p4294967279.json",
    "test_vector_p18446744073709551557.json",
)

ALICE_EXPECTED_FIELDS = (
    "G",
    "G_u",
    "G_v",
    "TA",
    "MA",
    "M",
    "submatrix_sums",
    "oB_candidates",
    "selected_oB_configuration",
    "oB",
    "oB_inverse",
    "negative_oA_plus_oS1",
    "f_oA",
    "f_negative_oA_plus_oS1",
    "f1",
    "f2",
    "f_autoconvolution",
    "rA",
    "kA",
    "session_key",
)


def normalize(value: Any) -> Any:
    if isinstance(value, tuple):
        return [normalize(item) for item in value]
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if isinstance(value, dict):
        return {key: normalize(item) for key, item in value.items()}
    return value


def first_difference(expected: Any, actual: Any, path: str = "value") -> str | None:
    expected = normalize(expected)
    actual = normalize(actual)

    if type(expected) is not type(actual):
        return f"{path}: type mismatch: {type(expected).__name__} != {type(actual).__name__}"

    if isinstance(expected, dict):
        if expected.keys() != actual.keys():
            return f"{path}: keys differ: {expected.keys()} != {actual.keys()}"
        for key in expected:
            difference = first_difference(expected[key], actual[key], f"{path}.{key}")
            if difference is not None:
                return difference
        return None

    if isinstance(expected, list):
        if len(expected) != len(actual):
            return f"{path}: length mismatch: {len(expected)} != {len(actual)}"
        for index, (expected_item, actual_item) in enumerate(zip(expected, actual)):
            difference = first_difference(expected_item, actual_item, f"{path}[{index}]")
            if difference is not None:
                return difference
        return None

    if expected != actual:
        return f"{path}: {expected!r} != {actual!r}"

    return None


def locate_vector_directory() -> Path:
    script_path = Path(__file__).resolve()
    repository_root = script_path.parent.parent
    vector_directory = repository_root / "general" / "test_vectors"

    if not vector_directory.is_dir():
        raise FileNotFoundError(
            "Canonical vector directory not found: "
            f"{vector_directory}\n"
            "Run this test from the HK17.2 repository with raspberry/ and general/ as sibling directories."
        )

    return vector_directory


def load_vector(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def build_alice_from_vector(vector: dict[str, Any]) -> AliceSession:
    parameters = vector["parameters"]
    inputs = vector["inputs"]

    derived = derive_system_parameters(int(parameters["modulo"]))

    # Verify that the KMS parameter derivation itself matches the canonical vector.
    canonical_parameters = {
        "modulo": derived.modulo,
        "powers": derived.powers,
        "degree": derived.degree,
        "component_bits": derived.component_bits,
        "matrix_dimension": derived.matrix_dimension,
        "matrix_degree": derived.matrix_degree,
        "matrix_component_bits": derived.matrix_component_bits,
        "matrix_modulo": derived.matrix_modulo,
        "submatrix_grid_dimension": derived.submatrix_grid_dimension,
        "submatrix_dimension": derived.submatrix_dimension,
    }

    difference = first_difference(parameters, canonical_parameters, "parameters")
    if difference is not None:
        raise AssertionError(difference)

    return AliceSession.from_fixed_inputs(
        derived,
        u=inputs["u"],
        v=inputs["v"],
        oA=inputs["oA"],
        m=inputs["m"],
        f=inputs["f"],
        g=inputs["g"],
        A=inputs["A"],
        B=inputs["B"],
        oS1=inputs["oS1"],
    )


def actual_alice_values(session: AliceSession) -> dict[str, Any]:
    return {
        "G": session.G,
        "G_u": session.G_u,
        "G_v": session.G_v,
        "TA": session.TA,
        "MA": session.MA,
        "M": session.M,
        "submatrix_sums": session.submatrix_sums,
        "oB_candidates": session.oB_candidates,
        "selected_oB_configuration": session.selected_oB_configuration,
        "oB": session.oB,
        "oB_inverse": session.oB_inverse,
        "negative_oA_plus_oS1": session.negative_oA_plus_oS1,
        "f_oA": session.f_oA,
        "f_negative_oA_plus_oS1": session.f_negative_oA_plus_oS1,
        "f1": session.f1,
        "f2": session.f2,
        "f_autoconvolution": session.f_autoconvolution,
        "rA": session.rA,
        "kA": session.kA,
        "session_key": session.session_key,
    }


def validate_vector(path: Path) -> tuple[bool, str | None]:
    vector = load_vector(path)
    expected = vector["expected"]

    session = build_alice_from_vector(vector)

    # Initial outbound values must match the canonical reference.
    matrix_payload = session.matrix_parameters()
    inputs = vector["inputs"]

    initial_checks = {
        "A": matrix_payload["A"],
        "B": matrix_payload["B"],
        "q": matrix_payload["q"],
        "u": matrix_payload["u"],
        "v": matrix_payload["v"],
        "TA": session.matrix_token(),
        "p": session.parameters.modulo,
        "oA": session.oA,
    }

    initial_expected = {
        "A": inputs["A"],
        "B": inputs["B"],
        "q": vector["parameters"]["matrix_modulo"],
        "u": inputs["u"],
        "v": inputs["v"],
        "TA": expected["TA"],
        "p": vector["parameters"]["modulo"],
        "oA": inputs["oA"],
    }

    difference = first_difference(initial_expected, initial_checks, "alice.outbound.matrix_stage")
    if difference is not None:
        return False, difference

    # Bob is represented only by TB, which is what Alice receives at this stage.
    session.receive_tb(expected["TB"])

    octonion_payload = session.octonion_parameters()
    octonion_outbound = {
        "p": octonion_payload["p"],
        "oA": octonion_payload["oA"],
        "rA": session.octonion_token(),
    }
    octonion_expected = {
        "p": vector["parameters"]["modulo"],
        "oA": inputs["oA"],
        "rA": expected["rA"],
    }

    difference = first_difference(octonion_expected, octonion_outbound, "alice.outbound.octonion_stage")
    if difference is not None:
        return False, difference

    # Bob is represented only by rB, which is what Alice receives at the final stage.
    session.receive_rb(expected["rB"])

    actual = actual_alice_values(session)
    expected_alice = {field: expected[field] for field in ALICE_EXPECTED_FIELDS}

    difference = first_difference(expected_alice, actual, "alice")
    if difference is not None:
        return False, difference

    return True, None


def main() -> int:
    vector_directory = locate_vector_directory()
    failures = 0

    print("=" * 100)
    print("HK17.2 RASPBERRY PI / ALICE-KMS CANONICAL CONFORMANCE TEST")
    print("=" * 100)

    for vector_name in VECTOR_NAMES:
        path = vector_directory / vector_name

        if not path.is_file():
            failures += 1
            print(f"[FAIL] {vector_name}")
            print(f"       Missing canonical vector: {path}")
            continue

        try:
            success, difference = validate_vector(path)
        except Exception as exc:  # Continue to report every vector.
            failures += 1
            print(f"[FAIL] {vector_name}")
            print(f"       {type(exc).__name__}: {exc}")
            continue

        if success:
            print(f"[PASS] {vector_name}")
        else:
            failures += 1
            print(f"[FAIL] {vector_name}")
            print(f"       {difference}")

    print("=" * 100)

    if failures == 0:
        print("SUCCESS: the Raspberry Pi / Alice-KMS port matches all five canonical HK17.2 vectors.")
        return 0

    print(f"FAILURE: {failures} canonical vector(s) failed Alice-KMS conformance.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
