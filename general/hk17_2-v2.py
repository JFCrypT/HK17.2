import random as randomlib
from datetime import datetime
from octonions import summ, scale, multiply, power,obtainPolynomial, calculateF

random = randomlib.SystemRandom()

# Null octonion
o_null = (0, 0, 0, 0, 0, 0, 0, 0)

# ============================================================
# SYSTEM PARAMETERS
# ============================================================

modulo = 251  # 08 bits
# modulo = 13  # 04 bits
# modulo = 65521  # 16 bits
# modulo = 4294967279  # 32 bits
# modulo = 18446744073709551557  # 64 bits

powers = 257

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
    degree = 16
    component_bits = 8

# ============================================================
# MATRIX SYSTEM PARAMETERS
# ============================================================

matrix_dimension = 32
matrix_degree = 32
matrix_component_bits = component_bits // 2
matrix_modulo = 2 ** matrix_component_bits

submatrix_grid_dimension = 4
submatrix_dimension = matrix_dimension // submatrix_grid_dimension

u = random.randrange(2, powers)
v = random.randrange(2, powers)

k = 1


# ============================================================
# OCTONION AUXILIARY FUNCTIONS
# ============================================================

def modprecip(x):
    x %= modulo

    if x == 0:
        raise Exception("Division by zero")

    return pow(x, modulo - 2, modulo)


def octonionrecip(x):
    xnormsq = sum(xi ** 2 for xi in x) % modulo

    if xnormsq == 0:
        raise Exception("The octonion is not invertible")

    xconj = (x[0], -x[1], -x[2], -x[3], -x[4], -x[5], -x[6], -x[7])

    return scale(xconj, modprecip(xnormsq), modulo)


def octonion_norm_squared(x):
    return sum(xi * xi for xi in x) % modulo


def is_invertible_octonion(x):
    return x != o_null and octonion_norm_squared(x) != 0


# ============================================================
# MATRIX AUXILIARY FUNCTIONS
# ============================================================

def matrix_null():
    return tuple(tuple(0 for _ in range(matrix_dimension)) for _ in range(matrix_dimension))


def matrix_identity():
    return tuple(tuple(1 if i == j else 0 for j in range(matrix_dimension)) for i in range(matrix_dimension))


def matrix_random():
    return tuple(tuple(random.randrange(matrix_modulo) for _ in range(matrix_dimension)) for _ in range(matrix_dimension))


def matrix_add(matrix_1, matrix_2):
    return tuple(
        tuple((matrix_1[i][j] + matrix_2[i][j]) % matrix_modulo for j in range(matrix_dimension))
        for i in range(matrix_dimension)
    )


def matrix_scale(matrix, scalar):
    scalar %= matrix_modulo

    return tuple(
        tuple((matrix[i][j] * scalar) % matrix_modulo for j in range(matrix_dimension))
        for i in range(matrix_dimension)
    )


def matrix_multiply(matrix_1, matrix_2):
    result = []

    for i in range(matrix_dimension):
        row = []

        for j in range(matrix_dimension):
            value = 0

            for r in range(matrix_dimension):
                value += matrix_1[i][r] * matrix_2[r][j]

            row.append(value % matrix_modulo)

        result.append(tuple(row))

    return tuple(result)


def matrix_power(matrix, exponent):
    result = matrix_identity()
    base = matrix
    current_exponent = exponent

    while current_exponent > 0:
        if current_exponent % 2 == 1:
            result = matrix_multiply(result, base)

        base = matrix_multiply(base, base)
        current_exponent //= 2

    return result


def calculate_matrix_polynomial(matrix, polynomial):
    coefficients = {exponent: coefficient % matrix_modulo for coefficient, exponent in polynomial}
    maximum_exponent = max(coefficients.keys())
    result = matrix_scale(matrix_identity(), coefficients.get(maximum_exponent, 0))

    for exponent in range(maximum_exponent - 1, -1, -1):
        result = matrix_multiply(result, matrix)
        coefficient_matrix = matrix_scale(matrix_identity(), coefficients.get(exponent, 0))
        result = matrix_add(result, coefficient_matrix)

    return result


def print_matrix(name, matrix):
    print(name)

    for row in matrix:
        print("   ", row)


# ============================================================
# CONSTRUCTION OF oB
# ============================================================

def decimal_concatenate(value_1, value_2):
    return int(str(value_1) + str(value_2))


def calculate_submatrix_sums(matrix):
    sums = []

    for block_row in range(submatrix_grid_dimension):
        row = []

        for block_column in range(submatrix_grid_dimension):
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
        (
            "1. Rows left-to-right, top-to-bottom",
            tuple((row, column) for row in range(4) for column in range(4))
        ),
        (
            "2. Rows right-to-left, top-to-bottom",
            tuple((row, column) for row in range(4) for column in range(3, -1, -1))
        ),
        (
            "3. Columns top-to-bottom, left-to-right",
            tuple((row, column) for column in range(4) for row in range(4))
        ),
        (
            "4. Columns bottom-to-top, left-to-right",
            tuple((row, column) for column in range(4) for row in range(3, -1, -1))
        )
    )


def construct_octonion_from_sums(submatrix_sums, traversal):
    ordered_sums = tuple(submatrix_sums[row][column] for row, column in traversal)
    octonion = tuple(
        decimal_concatenate(ordered_sums[2 * index], ordered_sums[2 * index + 1]) % modulo
        for index in range(8)
    )

    return ordered_sums, octonion


def generate_octonion_candidates(shared_matrix):
    submatrix_sums = calculate_submatrix_sums(shared_matrix)
    candidates = []

    for name, traversal in get_submatrix_traversals():
        ordered_sums, candidate = construct_octonion_from_sums(submatrix_sums, traversal)
        norm_squared = octonion_norm_squared(candidate)

        candidates.append(
            {
                "name": name,
                "traversal": traversal,
                "ordered_sums": ordered_sums,
                "octonion": candidate,
                "norm_squared": norm_squared,
                "invertible": candidate != o_null and norm_squared != 0
            }
        )

    return submatrix_sums, candidates


def select_first_invertible_octonion(candidates):
    for index, candidate in enumerate(candidates, start=1):
        if candidate["invertible"]:
            return index, candidate["octonion"]

    return None, None


# ============================================================
# PROTOCOL
# ============================================================

start = datetime.now()

for execution in range(1, k + 1):
    # ========================================================
    # PUBLIC HK17.2 OCTONION
    # ========================================================

    oA = o_null

    while oA == o_null:
        oA = tuple(random.randrange(modulo) for _ in range(8))

    # ========================================================
    # PRIVATE HK17.2 PARAMETERS
    # ========================================================

    m = random.randrange(2, powers)
    n = random.randrange(2, powers)

    f = obtainPolynomial(degree, modulo)
    h = obtainPolynomial(degree, modulo)

    # ========================================================
    # PRIVATE MATRIX POLYNOMIALS
    # ========================================================

    g = obtainPolynomial(matrix_degree, matrix_modulo)
    j = obtainPolynomial(matrix_degree, matrix_modulo)

    # ========================================================
    # PUBLIC MATRICES
    # ========================================================

    null_matrix = matrix_null()

    A = null_matrix

    while A == null_matrix:
        A = matrix_random()

    B = null_matrix

    while B == null_matrix:
        B = matrix_random()

    # ========================================================
    # MATRIX POLYNOMIAL EVALUATIONS
    # ========================================================

    G = calculate_matrix_polynomial(A, g)
    J = calculate_matrix_polynomial(A, j)

    if G == null_matrix:
        raise Exception("G = g(A) is the null matrix")

    if J == null_matrix:
        raise Exception("J = j(A) is the null matrix")

    # ========================================================
    # MATRIX POWERS
    # ========================================================

    G_u = matrix_power(G, u)
    G_v = matrix_power(G, v)
    J_u = matrix_power(J, u)
    J_v = matrix_power(J, v)

    # ========================================================
    # MATRIX TOKENS
    # ========================================================

    TA = matrix_multiply(matrix_multiply(G_u, B), G_v)
    TB = matrix_multiply(matrix_multiply(J_u, B), J_v)

    # ========================================================
    # SHARED MATRICES
    # ========================================================

    MA = matrix_multiply(matrix_multiply(G_u, TB), G_v)
    MB = matrix_multiply(matrix_multiply(J_u, TA), J_v)

    if MA != MB:
        raise Exception("Matrix exchange failure: MA != MB")

    M = MA

    if M == null_matrix:
        raise Exception("The shared matrix M is null")

    # ========================================================
    # CONSTRUCTION OF oB
    # ========================================================

    submatrix_sums_alice, oB_candidates_alice = generate_octonion_candidates(MA)
    submatrix_sums_bob, oB_candidates_bob = generate_octonion_candidates(MB)

    if submatrix_sums_alice != submatrix_sums_bob:
        raise Exception("Submatrix sums are different")

    if oB_candidates_alice != oB_candidates_bob:
        raise Exception("Alice and Bob generated different oB candidates")

    selected_oB_configuration_alice, oB_alice = select_first_invertible_octonion(oB_candidates_alice)
    selected_oB_configuration_bob, oB_bob = select_first_invertible_octonion(oB_candidates_bob)

    if selected_oB_configuration_alice != selected_oB_configuration_bob:
        raise Exception("Alice and Bob selected different oB configurations")

    if oB_alice != oB_bob:
        raise Exception("Alice and Bob generated different oB values")

    if oB_alice is None:
        raise Exception("None of the four oB candidates is invertible")

    selected_oB_configuration = selected_oB_configuration_alice
    oB = oB_alice

    # ========================================================
    # ALICE: HK17.2
    # ========================================================

    f_oA = calculateF(oA, f, modulo)
    oS1 = tuple(random.randrange(modulo) for _ in range(8))
    negative_oA_plus_oS1 = summ(scale(oA, -1, modulo), oS1, modulo)
    f_negative_oA_plus_oS1 = calculateF(negative_oA_plus_oS1, f, modulo)
    f1 = power(f_oA, m, modulo)
    f2 = power(f_negative_oA_plus_oS1, m, modulo)
    f_autoconvolution = multiply(f1, f2, modulo)
    rA = multiply(f_autoconvolution, oB, modulo)

    # ========================================================
    # BOB: HK17.2
    # ========================================================

    h_oA = calculateF(oA, h, modulo)
    oS2 = tuple(random.randrange(modulo) for _ in range(8))
    negative_oA_plus_oS2 = summ(scale(oA, -1, modulo), oS2, modulo)
    h_negative_oA_plus_oS2 = calculateF(negative_oA_plus_oS2, h, modulo)
    h1 = power(h_oA, n, modulo)
    h2 = power(h_negative_oA_plus_oS2, n, modulo)
    h_autoconvolution = multiply(h1, h2, modulo)
    rB = multiply(h_autoconvolution, oB, modulo)

    # ========================================================
    # SESSION KEY CALCULATED BY ALICE
    #
    # kA = (f * f)(oA, oS1, m) · rB
    # ========================================================

    kA = multiply(f_autoconvolution, rB, modulo)

    # ========================================================
    # SESSION KEY CALCULATED BY BOB
    #
    # recovered_f_autoconvolution = rA · oB^(-1)
    # kB = recovered_f_autoconvolution · rB
    # ========================================================

    oB_inverse = octonionrecip(oB)
    recovered_f_autoconvolution = multiply(rA, oB_inverse, modulo)

    if recovered_f_autoconvolution != f_autoconvolution:
        raise Exception("Bob could not recover Alice's autoconvolution")

    kB = multiply(recovered_f_autoconvolution, rB, modulo)

    # ========================================================
    # SESSION KEY VERIFICATION
    # ========================================================

    if kA == o_null:
        raise Exception("The generated session key is null")

    if kA != kB:
        raise Exception("HK17.2 failure: kA != kB")

    session_key = kA

    finish = datetime.now()
    elapsed = str(finish - start)

    # ========================================================
    # OUTPUT
    # ========================================================

    print("\n" + "=" * 100)
    print("SUCCESS!!! Alice and Bob generated the same key.")
    print("=" * 100)

    print("\nSYSTEM PARAMETERS")
    print("-" * 100)
    print("Public modulus p =", modulo)
    print("Powers =", powers)
    print("Octonion polynomial degree =", degree)
    print("Octonion component bits =", component_bits)
    print("Matrix dimension =", matrix_dimension)
    print("Matrix polynomial degree =", matrix_degree)
    print("Matrix component bits =", matrix_component_bits)
    print("Matrix modulus q =", matrix_modulo)
    print("Submatrix grid =", "4 x 4")
    print("Submatrix dimension =", "8 x 8")
    print("Execution =", execution)

    print("\nPUBLIC MATRIX EXPONENTS")
    print("-" * 100)
    print("Public exponent u =", u)
    print("Public exponent v =", v)

    print("\nPRIVATE HK17.2 EXPONENTS")
    print("-" * 100)
    print("Alice private exponent m =", m)
    print("Bob private exponent n =", n)

    print("\nPRIVATE OCTONION POLYNOMIALS")
    print("-" * 100)
    print("Alice octonion polynomial f(x) =", f)
    print("Bob octonion polynomial h(x) =", h)

    print("\nPRIVATE MATRIX POLYNOMIALS")
    print("-" * 100)
    print("Alice matrix polynomial g(x) =", g)
    print("Bob matrix polynomial j(x) =", j)

    print("\nPUBLIC MATRICES")
    print("-" * 100)
    print_matrix("A =", A)
    print_matrix("B =", B)

    print("\nMATRIX POLYNOMIAL EVALUATIONS")
    print("-" * 100)
    print_matrix("G = g(A) =", G)
    print_matrix("J = j(A) =", J)

    print("\nMATRIX TOKENS")
    print("-" * 100)
    print_matrix("TA =", TA)
    print_matrix("TB =", TB)

    print("\nSHARED MATRICES")
    print("-" * 100)
    print_matrix("MA =", MA)
    print_matrix("MB =", MB)
    print_matrix("M =", M)

    print("\nSUBMATRIX SUMS")
    print("-" * 100)

    for row in submatrix_sums_alice:
        print("   ", row)

    print("\nFOUR oB CANDIDATES")
    print("-" * 100)

    for index, candidate in enumerate(oB_candidates_alice, start=1):
        print("\nConfiguration", index)
        print("Traversal =", candidate["name"])
        print("Ordered sums =", candidate["ordered_sums"])
        print("oB =", candidate["octonion"])
        print("Quadratic norm =", candidate["norm_squared"])
        print("Invertible =", candidate["invertible"])

    print("\nSELECTED oB")
    print("-" * 100)
    print("Selected configuration =", selected_oB_configuration)
    print("oB obtained by Alice =", oB_alice)
    print("oB obtained by Bob =", oB_bob)
    print("N(oB) =", octonion_norm_squared(oB))
    print("oB^(-1) =", oB_inverse)

    print("\nHK17.2 PUBLIC AND PRIVATE OCTONIONS")
    print("-" * 100)
    print("Public octonion oA =", oA)
    print("Shared secret octonion oB =", oB)
    print("Alice secret displacement oS1 =", oS1)
    print("Bob secret displacement oS2 =", oS2)
    print("-oA + oS1 =", negative_oA_plus_oS1)
    print("-oA + oS2 =", negative_oA_plus_oS2)

    print("\nHK17.2 POLYNOMIAL EVALUATIONS")
    print("-" * 100)
    print("f(oA) =", f_oA)
    print("f(-oA + oS1) =", f_negative_oA_plus_oS1)
    print("h(oA) =", h_oA)
    print("h(-oA + oS2) =", h_negative_oA_plus_oS2)

    print("\nHK17.2 POWERED POLYNOMIAL EVALUATIONS")
    print("-" * 100)
    print("f1 = f(oA)^m =", f1)
    print("f2 = f(-oA + oS1)^m =", f2)
    print("h1 = h(oA)^n =", h1)
    print("h2 = h(-oA + oS2)^n =", h2)

    print("\nAUTOCONVOLUTIONS")
    print("-" * 100)
    print("(f * f)(oA, oS1, m) =", f_autoconvolution)
    print("(h * h)(oA, oS2, n) =", h_autoconvolution)
    print("Alice autoconvolution recovered by Bob =", recovered_f_autoconvolution)

    print("\nHK17.2 OCTONION TOKENS")
    print("-" * 100)
    print("rA =", rA)
    print("rB =", rB)

    print("\nSESSION KEYS")
    print("-" * 100)
    print("kA =", kA)
    print("kB =", kB)
    print("Session key k =", session_key)

    print("\nEXECUTION")
    print("-" * 100)
    print("Time =", elapsed)