import sys
from pathlib import Path

GENERAL_DIR = Path(__file__).resolve().parent.parent / "general"
sys.path.insert(0, str(GENERAL_DIR))

from octonions import summ, scale, multiply, power, obtainPolynomial, calculateF
import random as randomlib
from datetime import datetime

random = randomlib.SystemRandom()

# Null octonion
o_null = (0, 0, 0, 0, 0, 0, 0, 0)

# System parameters
modulo = 251  # 08 bits
# modulo = 65521  # 16 bits
# modulo = 4294967279  # 32 bits
# modulo = 18446744073709551557  # 64 bits

powers = 257

if modulo == 13:
    degree = 8
elif modulo == 251:
    degree = 16
elif modulo == 65521:
    degree = 32
elif modulo == 4294967279:
    degree = 64
elif modulo == 18446744073709551557:
    degree = 128
else:
    degree = 16  # Default value

k = 1

def modprecip(x):
    x %= modulo
    if x == 0:
        raise Exception("Division by zero")
    return pow(x, modulo - 2, modulo)

def octonionrecip(x):
    xnormsq = sum(xi**2 for xi in x) % modulo
    xconj = (x[0], -x[1], -x[2], -x[3], -x[4], -x[5], -x[6], -x[7])
    return scale(xconj, modprecip(xnormsq), modulo)

def is_invertible_octonion(x):
    # Norma cuadrada N(x) = sum(x_i^2) mod p
    return (sum(xi*xi for xi in x) % modulo) != 0

start = datetime.now()

for _ in range(k):
    k1 = o_null
    k2 = o_null

    while k1 == o_null or k1 != k2:
        iterations = 1
        # print("Iteration: {}\nk1 = {}\nk2 = {}".format(iterations, k1, k2))
        iterations += 1
        # Public parameters
        oA = o_null
        oB = o_null
        while oA == o_null:
            oA = tuple(random.randrange(modulo) for _ in range(8))
        while oB == o_null or not is_invertible_octonion(oB):
            oB = tuple(random.randrange(modulo) for _ in range(8))

        # Secret keys
        m = random.randrange(2, powers)
        n = random.randrange(2, powers)

        # ALICE
        f = obtainPolynomial(degree, modulo)
        fa = calculateF(oA, f, modulo)
        o_S1 = tuple(random.randrange(modulo) for _ in range(8))
        oA_s1 = summ(scale(oA, -1, modulo), o_S1, modulo)
        f1 = power(fa, m, modulo)
        f2 = power(calculateF(oA_s1, f, modulo), m, modulo)
        rA = multiply(multiply(f1, f2, modulo), oB, modulo)

        # BOB
        h = obtainPolynomial(degree, modulo)
        ha = calculateF(oA, h, modulo)
        o_S2 = tuple(random.randrange(modulo) for _ in range(8))
        oA_s2 = summ(scale(oA, -1, modulo), o_S2, modulo)
        h1 = power(ha, n, modulo)
        h2 = power(calculateF(oA_s2, h, modulo), n, modulo)
        rB = multiply(multiply(h1, h2, modulo), oB, modulo)

        # ALICE'S KEY
        k1 = multiply(multiply(f1, f2, modulo),
                                multiply(h1, h2, modulo), modulo)
        k1 = multiply(k1, oB, modulo)

        # BOB'S KEY
        oB_inv = octonionrecip(oB)
        k2_intermediate = multiply(rA, oB_inv, modulo)
        k2_intermediate = multiply(k2_intermediate, multiply(h1, h2, modulo), modulo)
        k2 = multiply(k2_intermediate, oB, modulo)

    finish = datetime.now()
    elapsed = str(finish - start)

    print("SUCCESS!!! Alice and Bob generated the same key.")
    print("Public modulus:", modulo)
    print("oA =", oA)
    print("oB =", oB)
    print("o_S1 =", o_S1)
    print("o_S2 =", o_S2)
    print("rA =", rA)
    print("rB =", rB)
    print("Shared key from Alice:", k1)
    print("Shared key from Bob:  ", k2)
    print("Time:", elapsed)