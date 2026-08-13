"""HK17.2 mathematical core for the Raspberry Pi / Alice-KMS port.

This module is an independent port of the operations used by the frozen
`general/hk17_2-v2.py` and `general/octonions.py` reference implementation.
It intentionally preserves the same algebraic semantics while parameterizing
operations so every selectable HK17.2 system modulus is supported.
"""

from __future__ import annotations

from typing import Iterable, Sequence

Octonion = tuple[int, int, int, int, int, int, int, int]
Matrix = tuple[tuple[int, ...], ...]
Polynomial = tuple[tuple[int, int], ...]

O_NULL: Octonion = (0, 0, 0, 0, 0, 0, 0, 0)


# ============================================================
# OCTONION OPERATIONS
# ============================================================


def summ(o1: Sequence[int], o2: Sequence[int], modulo: int) -> Octonion:
    return tuple((int(o1[i]) + int(o2[i])) % modulo for i in range(8))  # type: ignore[return-value]


def scale(o: Sequence[int], scalar: int, modulo: int) -> Octonion:
    return tuple((int(scalar) * int(o[i])) % modulo for i in range(8))  # type: ignore[return-value]


def multiply(o1: Sequence[int], o2: Sequence[int], modulo: int) -> Octonion:
    """Multiply two octonions using exactly the reference sign convention."""

    a, b, c, d, e, f, g, h = (int(value) for value in o1)
    i, j, k, l, m, n, o, p = (int(value) for value in o2)

    t1 = (a * i - b * j - c * k - d * l - e * m - f * n - g * o - h * p) % modulo
    t2 = (a * j + b * i + c * m + d * p - e * k + f * o - g * n - h * l) % modulo
    t3 = (a * k - b * m + c * i + d * n + e * j - f * l + g * p - h * o) % modulo
    t4 = (a * l - b * p - c * n + d * i + e * o + f * k - g * m + h * j) % modulo
    t5 = (a * m + b * k - c * j - d * o + e * i + f * p + g * l - h * n) % modulo
    t6 = (a * n - b * o + c * l - d * k - e * p + f * i + g * j + h * m) % modulo
    t7 = (a * o + b * n - c * p + d * m - e * l - f * j + g * i + h * k) % modulo
    t8 = (a * p + b * l + c * o - d * j + e * n - f * m - g * k + h * i) % modulo

    return (t1, t2, t3, t4, t5, t6, t7, t8)


def power(octonion: Sequence[int], exponent: int, modulo: int) -> Octonion:
    """Reference-compatible iterative left-associated octonion power."""

    result: Octonion = O_NULL

    for index in range(1, exponent + 1):
        if index == 1:
            result = tuple(int(value) for value in octonion)  # type: ignore[assignment]
        else:
            result = multiply(result, octonion, modulo)

    if exponent == 0:
        result = (1, 0, 0, 0, 0, 0, 0, 0)

    return result


def obtain_polynomial(grade: int, modulo: int, rng) -> Polynomial:
    return tuple((rng.randrange(1, modulo), exponent) for exponent in range(grade - 1, -1, -1))


def calculate_f(octonion: Sequence[int], polynomial: Sequence[Sequence[int]], modulo: int) -> Octonion:
    result: Octonion = O_NULL
    polynomial_length = len(polynomial)

    for index in range(polynomial_length):
        coefficient = int(polynomial[index][0])
        exponent = int(polynomial[index][1])

        if index == polynomial_length - 1:
            result = summ(result, (coefficient, 0, 0, 0, 0, 0, 0, 0), modulo)
        else:
            powered = power(octonion, exponent, modulo)
            term = scale(powered, coefficient, modulo)
            result = summ(result, term, modulo)

    return result


def mod_reciprocal(value: int, modulo: int) -> int:
    value %= modulo

    if value == 0:
        raise ZeroDivisionError("Division by zero")

    return pow(value, modulo - 2, modulo)


def octonion_norm_squared(octonion: Sequence[int], modulo: int) -> int:
    return sum(int(value) * int(value) for value in octonion) % modulo


def is_invertible_octonion(octonion: Sequence[int], modulo: int) -> bool:
    return tuple(octonion) != O_NULL and octonion_norm_squared(octonion, modulo) != 0


def octonion_reciprocal(octonion: Sequence[int], modulo: int) -> Octonion:
    norm_squared = octonion_norm_squared(octonion, modulo)

    if norm_squared == 0:
        raise ValueError("The octonion is not invertible")

    conjugate = (
        int(octonion[0]),
        -int(octonion[1]),
        -int(octonion[2]),
        -int(octonion[3]),
        -int(octonion[4]),
        -int(octonion[5]),
        -int(octonion[6]),
        -int(octonion[7]),
    )

    return scale(conjugate, mod_reciprocal(norm_squared, modulo), modulo)


# ============================================================
# MATRIX OPERATIONS
# ============================================================


def matrix_null(dimension: int) -> Matrix:
    return tuple(tuple(0 for _ in range(dimension)) for _ in range(dimension))


def matrix_identity(dimension: int) -> Matrix:
    return tuple(tuple(1 if row == column else 0 for column in range(dimension)) for row in range(dimension))


def matrix_random(dimension: int, modulo: int, rng) -> Matrix:
    return tuple(tuple(rng.randrange(modulo) for _ in range(dimension)) for _ in range(dimension))


def matrix_add(matrix_1: Matrix, matrix_2: Matrix, dimension: int, modulo: int) -> Matrix:
    return tuple(
        tuple((matrix_1[row][column] + matrix_2[row][column]) % modulo for column in range(dimension))
        for row in range(dimension)
    )


def matrix_scale(matrix: Matrix, scalar: int, dimension: int, modulo: int) -> Matrix:
    scalar %= modulo
    return tuple(
        tuple((matrix[row][column] * scalar) % modulo for column in range(dimension))
        for row in range(dimension)
    )


def matrix_multiply(matrix_1: Matrix, matrix_2: Matrix, dimension: int, modulo: int) -> Matrix:
    result: list[tuple[int, ...]] = []

    for row in range(dimension):
        result_row: list[int] = []

        for column in range(dimension):
            value = 0

            for index in range(dimension):
                value += matrix_1[row][index] * matrix_2[index][column]

            result_row.append(value % modulo)

        result.append(tuple(result_row))

    return tuple(result)


def matrix_power(matrix: Matrix, exponent: int, dimension: int, modulo: int) -> Matrix:
    result = matrix_identity(dimension)
    base = matrix
    current_exponent = exponent

    while current_exponent > 0:
        if current_exponent % 2 == 1:
            result = matrix_multiply(result, base, dimension, modulo)

        base = matrix_multiply(base, base, dimension, modulo)
        current_exponent //= 2

    return result


def calculate_matrix_polynomial(
    matrix: Matrix,
    polynomial: Sequence[Sequence[int]],
    dimension: int,
    modulo: int,
) -> Matrix:
    coefficients = {int(exponent): int(coefficient) % modulo for coefficient, exponent in polynomial}
    maximum_exponent = max(coefficients.keys())

    result = matrix_scale(
        matrix_identity(dimension),
        coefficients.get(maximum_exponent, 0),
        dimension,
        modulo,
    )

    for exponent in range(maximum_exponent - 1, -1, -1):
        result = matrix_multiply(result, matrix, dimension, modulo)
        coefficient_matrix = matrix_scale(
            matrix_identity(dimension),
            coefficients.get(exponent, 0),
            dimension,
            modulo,
        )
        result = matrix_add(result, coefficient_matrix, dimension, modulo)

    return result


# ============================================================
# DETERMINISTIC CONSTRUCTION OF oB
# ============================================================


def decimal_concatenate(value_1: int, value_2: int) -> int:
    return int(str(value_1) + str(value_2))


def calculate_submatrix_sums(
    matrix: Matrix,
    grid_dimension: int,
    submatrix_dimension: int,
) -> tuple[tuple[int, ...], ...]:
    sums: list[tuple[int, ...]] = []

    for block_row in range(grid_dimension):
        row: list[int] = []

        for block_column in range(grid_dimension):
            total = 0
            start_row = block_row * submatrix_dimension
            start_column = block_column * submatrix_dimension

            for matrix_row in range(start_row, start_row + submatrix_dimension):
                for matrix_column in range(start_column, start_column + submatrix_dimension):
                    total += matrix[matrix_row][matrix_column]

            row.append(total)

        sums.append(tuple(row))

    return tuple(sums)


def get_submatrix_traversals() -> tuple[tuple[str, tuple[tuple[int, int], ...]], ...]:
    return (
        (
            "1. Rows left-to-right, top-to-bottom",
            tuple((row, column) for row in range(4) for column in range(4)),
        ),
        (
            "2. Rows right-to-left, top-to-bottom",
            tuple((row, column) for row in range(4) for column in range(3, -1, -1)),
        ),
        (
            "3. Columns top-to-bottom, left-to-right",
            tuple((row, column) for column in range(4) for row in range(4)),
        ),
        (
            "4. Columns bottom-to-top, left-to-right",
            tuple((row, column) for column in range(4) for row in range(3, -1, -1)),
        ),
    )


def construct_octonion_from_sums(
    submatrix_sums: tuple[tuple[int, ...], ...],
    traversal: Sequence[Sequence[int]],
    modulo: int,
) -> tuple[tuple[int, ...], Octonion]:
    ordered_sums = tuple(submatrix_sums[int(row)][int(column)] for row, column in traversal)
    octonion = tuple(
        decimal_concatenate(ordered_sums[2 * index], ordered_sums[2 * index + 1]) % modulo
        for index in range(8)
    )

    return ordered_sums, octonion  # type: ignore[return-value]


def generate_octonion_candidates(
    shared_matrix: Matrix,
    modulo: int,
    grid_dimension: int,
    submatrix_dimension: int,
) -> tuple[tuple[tuple[int, ...], ...], tuple[dict, ...]]:
    submatrix_sums = calculate_submatrix_sums(shared_matrix, grid_dimension, submatrix_dimension)
    candidates: list[dict] = []

    for name, traversal in get_submatrix_traversals():
        ordered_sums, candidate = construct_octonion_from_sums(submatrix_sums, traversal, modulo)
        norm_squared = octonion_norm_squared(candidate, modulo)

        candidates.append(
            {
                "name": name,
                "traversal": traversal,
                "ordered_sums": ordered_sums,
                "octonion": candidate,
                "norm_squared": norm_squared,
                "invertible": candidate != O_NULL and norm_squared != 0,
            }
        )

    return submatrix_sums, tuple(candidates)


def select_first_invertible_octonion(candidates: Sequence[dict]) -> tuple[int | None, Octonion | None]:
    for index, candidate in enumerate(candidates, start=1):
        if candidate["invertible"]:
            return index, tuple(candidate["octonion"])  # type: ignore[return-value]

    return None, None
