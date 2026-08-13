"""Deterministic HK17.2 test-vector evaluator.

This module reimplements the operations required to validate the canonical
vectors. It does not import or modify general/hk17_2-v2.py or general/octonions.py.
Normal validation uses only the hardcoded inputs and expected values stored in
JSON vector files.
"""

O_NULL = (0, 0, 0, 0, 0, 0, 0, 0)


def as_tuple(value):
    if isinstance(value, list):
        return tuple(as_tuple(item) for item in value)
    if isinstance(value, dict):
        return {key: as_tuple(item) for key, item in value.items()}
    return value


def jsonable(value):
    if isinstance(value, dict):
        return {key: jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [jsonable(item) for item in value]
    return value


# ============================================================
# OCTONION FUNCTIONS
# ============================================================

def summ(o1, o2, modulo):
    return tuple((int(o1[i]) + int(o2[i])) % modulo for i in range(8))


def scale(o, sca, modulo):
    sca = int(sca)
    return tuple((sca * int(o[i])) % modulo for i in range(8))


def multiply(o1, o2, modulo):
    a, b, c, d, e, f, g, h = (int(x) for x in o1)
    i, j, k, l, m, n, o, p = (int(x) for x in o2)

    t1 = (a * i - b * j - c * k - d * l - e * m - f * n - g * o - h * p) % modulo
    t2 = (a * j + b * i + c * m + d * p - e * k + f * o - g * n - h * l) % modulo
    t3 = (a * k - b * m + c * i + d * n + e * j - f * l + g * p - h * o) % modulo
    t4 = (a * l - b * p - c * n + d * i + e * o + f * k - g * m + h * j) % modulo
    t5 = (a * m + b * k - c * j - d * o + e * i + f * p + g * l - h * n) % modulo
    t6 = (a * n - b * o + c * l - d * k - e * p + f * i + g * j + h * m) % modulo
    t7 = (a * o + b * n - c * p + d * m - e * l - f * j + g * i + h * k) % modulo
    t8 = (a * p + b * l + c * o - d * j + e * n - f * m - g * k + h * i) % modulo

    return (t1, t2, t3, t4, t5, t6, t7, t8)


def power(oc, potency, modulo):
    res = O_NULL
    for index in range(1, potency + 1):
        if index == 1:
            res = oc
        else:
            res = multiply(res, oc, modulo)
    if potency == 0:
        res = (1, 0, 0, 0, 0, 0, 0, 0)
    return res


def calculate_f(oa, polynomial, modulo):
    fa = O_NULL
    length = len(polynomial)
    for index in range(length):
        coefficient, exponent = polynomial[index]
        if index == length - 1:
            fa = summ(fa, (coefficient, 0, 0, 0, 0, 0, 0, 0), modulo)
        else:
            on = power(oa, exponent, modulo)
            ox = scale(on, coefficient, modulo)
            fa = summ(fa, ox, modulo)
    return fa


def modprecip(x, modulo):
    x %= modulo
    if x == 0:
        raise ValueError('Division by zero')
    return pow(x, modulo - 2, modulo)


def octonion_norm_squared(x, modulo):
    return sum(xi * xi for xi in x) % modulo


def octonionrecip(x, modulo):
    norm = octonion_norm_squared(x, modulo)
    if norm == 0:
        raise ValueError('The octonion is not invertible')
    conjugate = (x[0], -x[1], -x[2], -x[3], -x[4], -x[5], -x[6], -x[7])
    return scale(conjugate, modprecip(norm, modulo), modulo)


# ============================================================
# MATRIX FUNCTIONS
# ============================================================

def matrix_identity(dimension):
    return tuple(tuple(1 if i == j else 0 for j in range(dimension)) for i in range(dimension))


def matrix_add(a, b, dimension, modulo):
    return tuple(
        tuple((a[i][j] + b[i][j]) % modulo for j in range(dimension))
        for i in range(dimension)
    )


def matrix_scale(matrix, scalar, dimension, modulo):
    scalar %= modulo
    return tuple(
        tuple((matrix[i][j] * scalar) % modulo for j in range(dimension))
        for i in range(dimension)
    )


def matrix_multiply(a, b, dimension, modulo):
    result = []
    for i in range(dimension):
        row = []
        for j in range(dimension):
            value = 0
            for r in range(dimension):
                value += a[i][r] * b[r][j]
            row.append(value % modulo)
        result.append(tuple(row))
    return tuple(result)


def matrix_power(matrix, exponent, dimension, modulo):
    result = matrix_identity(dimension)
    base = matrix
    current = exponent
    while current > 0:
        if current % 2 == 1:
            result = matrix_multiply(result, base, dimension, modulo)
        base = matrix_multiply(base, base, dimension, modulo)
        current //= 2
    return result


def calculate_matrix_polynomial(matrix, polynomial, dimension, modulo):
    coefficients = {exponent: coefficient % modulo for coefficient, exponent in polynomial}
    maximum_exponent = max(coefficients.keys())
    result = matrix_scale(matrix_identity(dimension), coefficients.get(maximum_exponent, 0), dimension, modulo)
    for exponent in range(maximum_exponent - 1, -1, -1):
        result = matrix_multiply(result, matrix, dimension, modulo)
        coefficient_matrix = matrix_scale(matrix_identity(dimension), coefficients.get(exponent, 0), dimension, modulo)
        result = matrix_add(result, coefficient_matrix, dimension, modulo)
    return result


# ============================================================
# oB CONSTRUCTION
# ============================================================

def decimal_concatenate(value_1, value_2):
    return int(str(value_1) + str(value_2))


def calculate_submatrix_sums(matrix, grid_dimension, submatrix_dimension):
    sums = []
    for block_row in range(grid_dimension):
        row = []
        for block_column in range(grid_dimension):
            total = 0
            start_row = block_row * submatrix_dimension
            start_column = block_column * submatrix_dimension
            for i in range(start_row, start_row + submatrix_dimension):
                for j in range(start_column, start_column + submatrix_dimension):
                    total += matrix[i][j]
            row.append(total)
        sums.append(tuple(row))
    return tuple(sums)


def get_submatrix_traversals():
    return (
        ('1. Rows left-to-right, top-to-bottom', tuple((row, column) for row in range(4) for column in range(4))),
        ('2. Rows right-to-left, top-to-bottom', tuple((row, column) for row in range(4) for column in range(3, -1, -1))),
        ('3. Columns top-to-bottom, left-to-right', tuple((row, column) for column in range(4) for row in range(4))),
        ('4. Columns bottom-to-top, left-to-right', tuple((row, column) for column in range(4) for row in range(3, -1, -1))),
    )


def generate_octonion_candidates(shared_matrix, modulo, grid_dimension, submatrix_dimension):
    submatrix_sums = calculate_submatrix_sums(shared_matrix, grid_dimension, submatrix_dimension)
    candidates = []
    for name, traversal in get_submatrix_traversals():
        ordered_sums = tuple(submatrix_sums[row][column] for row, column in traversal)
        candidate = tuple(
            decimal_concatenate(ordered_sums[2 * index], ordered_sums[2 * index + 1]) % modulo
            for index in range(8)
        )
        norm_squared = octonion_norm_squared(candidate, modulo)
        candidates.append({
            'name': name,
            'traversal': traversal,
            'ordered_sums': ordered_sums,
            'octonion': candidate,
            'norm_squared': norm_squared,
            'invertible': candidate != O_NULL and norm_squared != 0,
        })
    return submatrix_sums, tuple(candidates)


def select_first_invertible_octonion(candidates):
    for index, candidate in enumerate(candidates, start=1):
        if candidate['invertible']:
            return index, candidate['octonion']
    return None, None


# ============================================================
# FULL RECOMPUTATION FROM HARDCODED VECTOR INPUTS
# ============================================================

def recompute_from_vector(vector):
    params = vector['parameters']
    inputs = as_tuple(vector['inputs'])

    modulo = params['modulo']
    dimension = params['matrix_dimension']
    matrix_modulo = params['matrix_modulo']
    grid_dimension = params['submatrix_grid_dimension']
    submatrix_dimension = params['submatrix_dimension']

    A = inputs['A']
    B = inputs['B']
    g = inputs['g']
    j = inputs['j']
    u = inputs['u']
    v = inputs['v']
    oA = inputs['oA']
    m = inputs['m']
    n = inputs['n']
    f = inputs['f']
    h = inputs['h']
    oS1 = inputs['oS1']
    oS2 = inputs['oS2']

    G = calculate_matrix_polynomial(A, g, dimension, matrix_modulo)
    J = calculate_matrix_polynomial(A, j, dimension, matrix_modulo)
    G_u = matrix_power(G, u, dimension, matrix_modulo)
    G_v = matrix_power(G, v, dimension, matrix_modulo)
    J_u = matrix_power(J, u, dimension, matrix_modulo)
    J_v = matrix_power(J, v, dimension, matrix_modulo)

    TA = matrix_multiply(matrix_multiply(G_u, B, dimension, matrix_modulo), G_v, dimension, matrix_modulo)
    TB = matrix_multiply(matrix_multiply(J_u, B, dimension, matrix_modulo), J_v, dimension, matrix_modulo)
    MA = matrix_multiply(matrix_multiply(G_u, TB, dimension, matrix_modulo), G_v, dimension, matrix_modulo)
    MB = matrix_multiply(matrix_multiply(J_u, TA, dimension, matrix_modulo), J_v, dimension, matrix_modulo)
    if MA != MB:
        raise ValueError('Matrix exchange failure: MA != MB')
    M = MA

    submatrix_sums, candidates = generate_octonion_candidates(M, modulo, grid_dimension, submatrix_dimension)
    selected_configuration, oB = select_first_invertible_octonion(candidates)
    if oB is None:
        raise ValueError('None of the four oB candidates is invertible')
    oB_inverse = octonionrecip(oB, modulo)

    negative_oA_plus_oS1 = summ(scale(oA, -1, modulo), oS1, modulo)
    negative_oA_plus_oS2 = summ(scale(oA, -1, modulo), oS2, modulo)

    f_oA = calculate_f(oA, f, modulo)
    f_negative = calculate_f(negative_oA_plus_oS1, f, modulo)
    h_oA = calculate_f(oA, h, modulo)
    h_negative = calculate_f(negative_oA_plus_oS2, h, modulo)

    f1 = power(f_oA, m, modulo)
    f2 = power(f_negative, m, modulo)
    h1 = power(h_oA, n, modulo)
    h2 = power(h_negative, n, modulo)

    f_autoconvolution = multiply(f1, f2, modulo)
    h_autoconvolution = multiply(h1, h2, modulo)
    rA = multiply(f_autoconvolution, oB, modulo)
    rB = multiply(h_autoconvolution, oB, modulo)
    kA = multiply(f_autoconvolution, rB, modulo)
    recovered = multiply(rA, oB_inverse, modulo)
    if recovered != f_autoconvolution:
        raise ValueError("Bob could not recover Alice's autoconvolution")
    kB = multiply(recovered, rB, modulo)
    if kA != kB:
        raise ValueError('HK17.2 failure: kA != kB')

    return jsonable({
        'G': G,
        'J': J,
        'G_u': G_u,
        'G_v': G_v,
        'J_u': J_u,
        'J_v': J_v,
        'TA': TA,
        'TB': TB,
        'MA': MA,
        'MB': MB,
        'M': M,
        'submatrix_sums': submatrix_sums,
        'oB_candidates': candidates,
        'selected_oB_configuration': selected_configuration,
        'oB': oB,
        'oB_inverse': oB_inverse,
        'negative_oA_plus_oS1': negative_oA_plus_oS1,
        'negative_oA_plus_oS2': negative_oA_plus_oS2,
        'f_oA': f_oA,
        'f_negative_oA_plus_oS1': f_negative,
        'h_oA': h_oA,
        'h_negative_oA_plus_oS2': h_negative,
        'f1': f1,
        'f2': f2,
        'h1': h1,
        'h2': h2,
        'f_autoconvolution': f_autoconvolution,
        'h_autoconvolution': h_autoconvolution,
        'rA': rA,
        'rB': rB,
        'recovered_f_autoconvolution': recovered,
        'kA': kA,
        'kB': kB,
        'session_key': kA,
    })
