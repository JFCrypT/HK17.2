import sys
from pathlib import Path
import random

GENERAL_DIR = Path(__file__).resolve().parent.parent / "general"
sys.path.insert(0, str(GENERAL_DIR))

from octonions import summ, scale, multiply, power, obtainPolynomial, calculateF

# Modular field
modulo = 251

# Randomly generate nonzero octonions for the test
def rand_octonion():
    o = (0,)*8
    while o == (0,)*8:
        o = tuple(random.randint(1, modulo - 1) for _ in range(8))
    return o

# Define parameters
oA = rand_octonion()
oS1 = rand_octonion()
oS2 = rand_octonion()
oB = rand_octonion()

# Degrees and exponents
degree = 4
m = random.randint(2, 7)
n = random.randint(2, 7)

# Define two random polynomials for f and h
f = obtainPolynomial(degree, modulo)
h = obtainPolynomial(degree, modulo)

# Evaluate F and H as per protocol (autoconvolution-like blocks)
f1 = power(calculateF(oA, f, modulo), m, modulo)
f2 = power(calculateF(summ(scale(oA, -1, modulo), oS1, modulo), f, modulo), m, modulo)
F = multiply(f1, f2, modulo)

h1 = power(calculateF(oA, h, modulo), n, modulo)
h2 = power(calculateF(summ(scale(oA, -1, modulo), oS2, modulo), h, modulo), n, modulo)
H = multiply(h1, h2, modulo)

# Compute products in both orders
F_H_oB = multiply(multiply(F, H, modulo), oB, modulo)
H_F_oB = multiply(multiply(H, F, modulo), oB, modulo)

# Print results
print("F * H * oB =", F_H_oB)
print("H * F * oB =", H_F_oB)
print("Are they equal?", "YES" if F_H_oB == H_F_oB else "NO (Noncommutative)")

# For reference, print arguments:
print("\noA =", oA)
print("oS1 =", oS1)
print("oS2 =", oS2)
print("oB  =", oB)
print("Polynomial f =", f)
print("Polynomial h =", h)
print("Exponent m =", m)
print("Exponent n =", n)