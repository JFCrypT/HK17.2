"""Raspberry Pi 3 Alice/KMS port of the frozen HK17.2 protocol.

This module implements the cryptographic Alice role and the in-memory KMS
session manager used by the operational MQTT service. Network transport is
implemented separately in `kms_server.py`; the protocol sequence is kept
unchanged:

1. Alice prepares A, B, q, u, v and TA.
2. Alice receives TB, derives MA -> oB, and prepares p, oA and rA.
3. Alice receives rB and computes kA.

The implementation supports every selectable system modulus from the frozen
reference implementation.
"""

from __future__ import annotations

import random as randomlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence

from hk17_math import (
    Matrix,
    Octonion,
    Polynomial,
    O_NULL,
    calculate_f,
    calculate_matrix_polynomial,
    generate_octonion_candidates,
    matrix_multiply,
    matrix_null,
    matrix_power,
    matrix_random,
    multiply,
    obtain_polynomial,
    octonion_reciprocal,
    power,
    scale,
    select_first_invertible_octonion,
    summ,
)


# ============================================================
# SELECTABLE SYSTEM PARAMETER
# Same selectable values as general/hk17_2-v2.py.
# ============================================================

DEFAULT_MODULO = 251  # 08 bits
# DEFAULT_MODULO = 13  # 04 bits
# DEFAULT_MODULO = 65521  # 16 bits
# DEFAULT_MODULO = 4294967279  # 32 bits
# DEFAULT_MODULO = 18446744073709551557  # 64 bits

POWERS = 257
MATRIX_DIMENSION = 32
MATRIX_DEGREE = 32
SUBMATRIX_GRID_DIMENSION = 4

SUPPORTED_MODULI = (
    13,
    251,
    65521,
    4294967279,
    18446744073709551557,
)


@dataclass(frozen=True)
class SystemParameters:
    modulo: int
    powers: int
    degree: int
    component_bits: int
    matrix_dimension: int
    matrix_degree: int
    matrix_component_bits: int
    matrix_modulo: int
    submatrix_grid_dimension: int
    submatrix_dimension: int


def derive_system_parameters(modulo: int = DEFAULT_MODULO) -> SystemParameters:
    if modulo == 13:
        degree = 8
        component_bits = 4
    elif modulo == 251:
        degree = 16
        component_bits = 8
    elif modulo == 65521:
        degree = 32
        component_bits = 16
    elif modulo == 4294967279:
        degree = 64
        component_bits = 32
    elif modulo == 18446744073709551557:
        degree = 128
        component_bits = 64
    else:
        raise ValueError(f"Unsupported HK17.2 modulus: {modulo}")

    matrix_component_bits = component_bits // 2
    matrix_modulo = 2 ** matrix_component_bits
    submatrix_dimension = MATRIX_DIMENSION // SUBMATRIX_GRID_DIMENSION

    return SystemParameters(
        modulo=modulo,
        powers=POWERS,
        degree=degree,
        component_bits=component_bits,
        matrix_dimension=MATRIX_DIMENSION,
        matrix_degree=MATRIX_DEGREE,
        matrix_component_bits=matrix_component_bits,
        matrix_modulo=matrix_modulo,
        submatrix_grid_dimension=SUBMATRIX_GRID_DIMENSION,
        submatrix_dimension=submatrix_dimension,
    )


class SessionState(str, Enum):
    MATRIX_READY = "matrix_ready"
    OCTONION_READY = "octonion_ready"
    KEY_ESTABLISHED = "key_established"


@dataclass
class AliceSession:
    parameters: SystemParameters
    u: int
    v: int
    oA: Octonion
    m: int
    f: Polynomial
    g: Polynomial
    A: Matrix
    B: Matrix
    G: Matrix
    G_u: Matrix
    G_v: Matrix
    TA: Matrix
    oS1: Octonion | None = None
    TB: Matrix | None = None
    MA: Matrix | None = None
    M: Matrix | None = None
    submatrix_sums: tuple[tuple[int, ...], ...] | None = None
    oB_candidates: tuple[dict, ...] | None = None
    selected_oB_configuration: int | None = None
    oB: Octonion | None = None
    oB_inverse: Octonion | None = None
    negative_oA_plus_oS1: Octonion | None = None
    f_oA: Octonion | None = None
    f_negative_oA_plus_oS1: Octonion | None = None
    f1: Octonion | None = None
    f2: Octonion | None = None
    f_autoconvolution: Octonion | None = None
    rA: Octonion | None = None
    rB: Octonion | None = None
    kA: Octonion | None = None
    session_key: Octonion | None = None
    state: SessionState = SessionState.MATRIX_READY

    @classmethod
    def create_random(cls, modulo: int = DEFAULT_MODULO, rng=None) -> "AliceSession":
        parameters = derive_system_parameters(modulo)
        rng = rng if rng is not None else randomlib.SystemRandom()

        u = rng.randrange(2, parameters.powers)
        v = rng.randrange(2, parameters.powers)

        oA = O_NULL
        while oA == O_NULL:
            oA = tuple(rng.randrange(parameters.modulo) for _ in range(8))  # type: ignore[assignment]

        m = rng.randrange(2, parameters.powers)
        f = obtain_polynomial(parameters.degree, parameters.modulo, rng)
        g = obtain_polynomial(parameters.matrix_degree, parameters.matrix_modulo, rng)

        null_matrix = matrix_null(parameters.matrix_dimension)

        A = null_matrix
        while A == null_matrix:
            A = matrix_random(parameters.matrix_dimension, parameters.matrix_modulo, rng)

        B = null_matrix
        while B == null_matrix:
            B = matrix_random(parameters.matrix_dimension, parameters.matrix_modulo, rng)

        return cls._build_matrix_stage(
            parameters=parameters,
            u=u,
            v=v,
            oA=oA,
            m=m,
            f=f,
            g=g,
            A=A,
            B=B,
        )

    @classmethod
    def from_fixed_inputs(
        cls,
        parameters: SystemParameters,
        *,
        u: int,
        v: int,
        oA: Sequence[int],
        m: int,
        f: Sequence[Sequence[int]],
        g: Sequence[Sequence[int]],
        A: Sequence[Sequence[int]],
        B: Sequence[Sequence[int]],
        oS1: Sequence[int],
    ) -> "AliceSession":
        """Construct Alice from canonical fixed inputs for conformance testing."""

        session = cls._build_matrix_stage(
            parameters=parameters,
            u=int(u),
            v=int(v),
            oA=tuple(int(value) for value in oA),  # type: ignore[arg-type]
            m=int(m),
            f=tuple((int(term[0]), int(term[1])) for term in f),
            g=tuple((int(term[0]), int(term[1])) for term in g),
            A=tuple(tuple(int(value) for value in row) for row in A),
            B=tuple(tuple(int(value) for value in row) for row in B),
        )
        session.oS1 = tuple(int(value) for value in oS1)  # type: ignore[assignment]
        return session

    @classmethod
    def _build_matrix_stage(
        cls,
        *,
        parameters: SystemParameters,
        u: int,
        v: int,
        oA: Octonion,
        m: int,
        f: Polynomial,
        g: Polynomial,
        A: Matrix,
        B: Matrix,
    ) -> "AliceSession":
        G = calculate_matrix_polynomial(
            A,
            g,
            parameters.matrix_dimension,
            parameters.matrix_modulo,
        )

        null_matrix = matrix_null(parameters.matrix_dimension)
        if G == null_matrix:
            raise ValueError("G = g(A) is the null matrix")

        G_u = matrix_power(G, u, parameters.matrix_dimension, parameters.matrix_modulo)
        G_v = matrix_power(G, v, parameters.matrix_dimension, parameters.matrix_modulo)

        TA = matrix_multiply(
            matrix_multiply(G_u, B, parameters.matrix_dimension, parameters.matrix_modulo),
            G_v,
            parameters.matrix_dimension,
            parameters.matrix_modulo,
        )

        return cls(
            parameters=parameters,
            u=u,
            v=v,
            oA=oA,
            m=m,
            f=f,
            g=g,
            A=A,
            B=B,
            G=G,
            G_u=G_u,
            G_v=G_v,
            TA=TA,
        )

    def matrix_parameters(self) -> dict[str, Any]:
        """Values sent by Alice before TA in the frozen protocol."""

        return {
            "A": self.A,
            "B": self.B,
            "q": self.parameters.matrix_modulo,
            "u": self.u,
            "v": self.v,
        }

    def matrix_token(self) -> Matrix:
        return self.TA

    def receive_tb(self, TB: Sequence[Sequence[int]], rng=None) -> None:
        if self.state != SessionState.MATRIX_READY:
            raise RuntimeError(f"TB cannot be processed in state {self.state.value}")

        p = self.parameters
        self.TB = tuple(tuple(int(value) for value in row) for row in TB)

        self.MA = matrix_multiply(
            matrix_multiply(self.G_u, self.TB, p.matrix_dimension, p.matrix_modulo),
            self.G_v,
            p.matrix_dimension,
            p.matrix_modulo,
        )
        self.M = self.MA

        if self.M == matrix_null(p.matrix_dimension):
            raise ValueError("The shared matrix M is null")

        self.submatrix_sums, self.oB_candidates = generate_octonion_candidates(
            self.M,
            p.modulo,
            p.submatrix_grid_dimension,
            p.submatrix_dimension,
        )

        self.selected_oB_configuration, self.oB = select_first_invertible_octonion(self.oB_candidates)

        if self.oB is None:
            raise ValueError("None of the four oB candidates is invertible")

        self.oB_inverse = octonion_reciprocal(self.oB, p.modulo)

        if self.oS1 is None:
            rng = rng if rng is not None else randomlib.SystemRandom()
            self.oS1 = tuple(rng.randrange(p.modulo) for _ in range(8))  # type: ignore[assignment]

        self.f_oA = calculate_f(self.oA, self.f, p.modulo)
        self.negative_oA_plus_oS1 = summ(scale(self.oA, -1, p.modulo), self.oS1, p.modulo)
        self.f_negative_oA_plus_oS1 = calculate_f(self.negative_oA_plus_oS1, self.f, p.modulo)
        self.f1 = power(self.f_oA, self.m, p.modulo)
        self.f2 = power(self.f_negative_oA_plus_oS1, self.m, p.modulo)
        self.f_autoconvolution = multiply(self.f1, self.f2, p.modulo)
        self.rA = multiply(self.f_autoconvolution, self.oB, p.modulo)

        self.state = SessionState.OCTONION_READY

    def octonion_parameters(self) -> dict[str, Any]:
        if self.state == SessionState.MATRIX_READY:
            raise RuntimeError("TB must be processed before the octonion phase")

        return {
            "p": self.parameters.modulo,
            "oA": self.oA,
        }

    def octonion_token(self) -> Octonion:
        if self.rA is None:
            raise RuntimeError("TB must be processed before rA is available")
        return self.rA

    def receive_rb(self, rB: Sequence[int]) -> Octonion:
        if self.state != SessionState.OCTONION_READY:
            raise RuntimeError(f"rB cannot be processed in state {self.state.value}")

        if self.f_autoconvolution is None:
            raise RuntimeError("Alice autoconvolution is unavailable")

        self.rB = tuple(int(value) for value in rB)  # type: ignore[assignment]
        self.kA = multiply(self.f_autoconvolution, self.rB, self.parameters.modulo)

        if self.kA == O_NULL:
            raise ValueError("The generated session key is null")

        self.session_key = self.kA
        self.state = SessionState.KEY_ESTABLISHED
        return self.session_key


@dataclass
class HK17KMS:
    """Minimal in-memory session manager for multiple future ESP32 nodes."""

    modulo: int = DEFAULT_MODULO
    sessions: dict[str, AliceSession] = field(default_factory=dict)

    def create_session(self, device_id: str) -> AliceSession:
        if not device_id:
            raise ValueError("device_id must not be empty")
        if device_id in self.sessions:
            raise ValueError(f"A session already exists for device_id={device_id!r}")

        session = AliceSession.create_random(self.modulo)
        self.sessions[device_id] = session
        return session

    def get_session(self, device_id: str) -> AliceSession:
        try:
            return self.sessions[device_id]
        except KeyError as exc:
            raise KeyError(f"Unknown device_id={device_id!r}") from exc

    def remove_session(self, device_id: str) -> None:
        self.sessions.pop(device_id, None)
