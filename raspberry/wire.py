"""Binary transport encoding for the distributed HK17.2 implementation.

This module does not alter the HK17.2 cryptographic protocol. It only defines
how the values already present in the frozen protocol are serialized for MQTT
transport between the Raspberry Pi 3 (Alice/KMS) and ESP32 nodes (Bob).

All integers are encoded unsigned, big-endian. Matrix and octonion component
widths are derived from q and p respectively.
"""

from __future__ import annotations

from typing import Sequence

from hk17_math import Matrix, Octonion

MATRIX_DIMENSION = 32
OCTONION_COMPONENTS = 8


def matrix_component_width(q: int) -> int:
    if q <= 1:
        raise ValueError("Matrix modulus q must be greater than 1")
    return max(1, ((q - 1).bit_length() + 7) // 8)


def octonion_component_width(p: int) -> int:
    if p <= 1:
        raise ValueError("Octonion modulus p must be greater than 1")
    return max(1, ((p - 1).bit_length() + 7) // 8)


def _encode_uint(value: int, width: int) -> bytes:
    value = int(value)
    if value < 0 or value >= (1 << (8 * width)):
        raise ValueError(f"Integer {value} does not fit in {width} byte(s)")
    return value.to_bytes(width, byteorder="big", signed=False)


def _decode_uint(data: bytes, offset: int, width: int) -> tuple[int, int]:
    end = offset + width
    if end > len(data):
        raise ValueError("Truncated binary payload")
    return int.from_bytes(data[offset:end], byteorder="big", signed=False), end


def encode_matrix(matrix: Sequence[Sequence[int]], q: int) -> bytes:
    width = matrix_component_width(q)
    if len(matrix) != MATRIX_DIMENSION:
        raise ValueError(f"Expected {MATRIX_DIMENSION} matrix rows")

    output = bytearray()
    for row in matrix:
        if len(row) != MATRIX_DIMENSION:
            raise ValueError(f"Expected {MATRIX_DIMENSION} matrix columns")
        for value in row:
            value = int(value)
            if not 0 <= value < q:
                raise ValueError(f"Matrix component {value} is outside Z_{q}")
            output.extend(_encode_uint(value, width))

    return bytes(output)


def decode_matrix(payload: bytes, q: int) -> Matrix:
    width = matrix_component_width(q)
    expected = MATRIX_DIMENSION * MATRIX_DIMENSION * width
    if len(payload) != expected:
        raise ValueError(f"Invalid matrix payload length: expected {expected}, got {len(payload)}")

    offset = 0
    rows: list[tuple[int, ...]] = []
    for _ in range(MATRIX_DIMENSION):
        row: list[int] = []
        for _ in range(MATRIX_DIMENSION):
            value, offset = _decode_uint(payload, offset, width)
            if value >= q:
                raise ValueError(f"Decoded matrix component {value} is outside Z_{q}")
            row.append(value)
        rows.append(tuple(row))

    return tuple(rows)


def encode_octonion(octonion: Sequence[int], p: int) -> bytes:
    width = octonion_component_width(p)
    if len(octonion) != OCTONION_COMPONENTS:
        raise ValueError("An octonion must contain exactly 8 components")

    output = bytearray()
    for value in octonion:
        value = int(value)
        if not 0 <= value < p:
            raise ValueError(f"Octonion component {value} is outside Z_{p}")
        output.extend(_encode_uint(value, width))
    return bytes(output)


def decode_octonion(payload: bytes, p: int) -> Octonion:
    width = octonion_component_width(p)
    expected = OCTONION_COMPONENTS * width
    if len(payload) != expected:
        raise ValueError(f"Invalid octonion payload length: expected {expected}, got {len(payload)}")

    offset = 0
    values: list[int] = []
    for _ in range(OCTONION_COMPONENTS):
        value, offset = _decode_uint(payload, offset, width)
        if value >= p:
            raise ValueError(f"Decoded octonion component {value} is outside Z_{p}")
        values.append(value)

    return tuple(values)  # type: ignore[return-value]


def encode_matrix_parameters(A: Matrix, B: Matrix, q: int, u: int, v: int) -> bytes:
    if not 0 <= q < (1 << 64):
        raise ValueError("q must fit in uint64")
    if not 0 <= u < (1 << 16) or not 0 <= v < (1 << 16):
        raise ValueError("u and v must fit in uint16")

    return b"".join(
        (
            _encode_uint(q, 8),
            _encode_uint(u, 2),
            _encode_uint(v, 2),
            encode_matrix(A, q),
            encode_matrix(B, q),
        )
    )


def decode_matrix_parameters(payload: bytes) -> dict[str, object]:
    if len(payload) < 12:
        raise ValueError("Truncated matrix-parameter payload")

    q, offset = _decode_uint(payload, 0, 8)
    u, offset = _decode_uint(payload, offset, 2)
    v, offset = _decode_uint(payload, offset, 2)

    width = matrix_component_width(q)
    matrix_length = MATRIX_DIMENSION * MATRIX_DIMENSION * width
    expected = 12 + 2 * matrix_length
    if len(payload) != expected:
        raise ValueError(
            f"Invalid matrix-parameter payload length: expected {expected}, got {len(payload)}"
        )

    A = decode_matrix(payload[offset : offset + matrix_length], q)
    offset += matrix_length
    B = decode_matrix(payload[offset : offset + matrix_length], q)

    return {"A": A, "B": B, "q": q, "u": u, "v": v}


def encode_octonion_parameters(p: int, oA: Octonion) -> bytes:
    if not 0 <= p < (1 << 64):
        raise ValueError("p must fit in uint64")
    return _encode_uint(p, 8) + encode_octonion(oA, p)


def decode_octonion_parameters(payload: bytes) -> dict[str, object]:
    if len(payload) < 8:
        raise ValueError("Truncated octonion-parameter payload")

    p, offset = _decode_uint(payload, 0, 8)
    width = octonion_component_width(p)
    expected = 8 + OCTONION_COMPONENTS * width
    if len(payload) != expected:
        raise ValueError(
            f"Invalid octonion-parameter payload length: expected {expected}, got {len(payload)}"
        )

    oA = decode_octonion(payload[offset:], p)
    return {"p": p, "oA": oA}
