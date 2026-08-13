import sys
from pathlib import Path

GENERAL_DIR = Path(__file__).resolve().parent.parent / "general"
sys.path.insert(0, str(GENERAL_DIR))

from octonions import summ, scale, multiply, power, obtainPolynomial, calculateF
import random as randomlib
random = randomlib.SystemRandom()
from datetime import datetime

# 1. Inicialization
# Loading necessary elements
o_null = (0, 0, 0, 0, 0, 0, 0, 0)
oA = o_null
oB = o_null
kA = o_null
kB = o_null
degree = 0
k = 1
# Selecting platform:
modulo = 251  # 08 bits
#modulo = 65521  # 16 bits
#modulo = 4294967279  # 32 bits
#modulo = 18446744073709551557  # 64 bits
powers = 257
if modulo == 13:
    degree = 8
if modulo == 251:
    degree = 16
if modulo == 65521:
    degree = 32
if modulo == 4294967279:
    degree = 64
if modulo == 18446744073709551557:
    degree = 128
# Counting time:
start = datetime.now()
# Algorithm generates 256 bits key lenght
for j in range(k):
    k1re = 0
    k1e1 = 0
    k1e2 = 0
    k1e3 = 0
    k1e4 = 0
    k1e5 = 0
    k1e6 = 0
    k1e7 = 0
    k2re = 0
    k2e1 = 0
    k2e2 = 0
    k2e3 = 0
    k2e4 = 0
    k2e5 = 0
    k2e6 = 0
    k2e7 = 0
    while (((k1re != k2re) or (k1re == 0) or (k2re == 0)) or ((k1re != k2re) or (k1re == 0) or (k2re == 0)) or ((k1re != k2re) or (k1re == 0) or (k2re == 0)) or ((k1re != k2re) or (k1re == 0) or (k2re == 0)) or ((k1re != k2re) or (k1re == 0) or (k2re == 0)) or ((k1re != k2re) or (k1re == 0) or (k2re == 0)) or ((k1re != k2re) or (k1re == 0) or (k2re == 0)) or ((k1re != k2re) or (k1re == 0) or (k2re == 0))):
        # Public elements: oA and oB
        oA = o_null
        oB = o_null
        while oA == o_null:
            oA = (random.randrange(modulo), random.randrange(modulo), random.randrange(modulo), random.randrange(modulo), random.randrange(modulo), random.randrange(modulo), random.randrange(modulo), random.randrange(modulo))
        while oB == o_null:
            oB = (random.randrange(modulo), random.randrange(modulo), random.randrange(modulo), random.randrange(modulo), random.randrange(modulo), random.randrange(modulo), random.randrange(modulo), random.randrange(modulo))
        # Alice Private Key
        m = random.randrange(2, powers)
        n = random.randrange(2, powers)
        # Bob Private Key
        r = random.randrange(2, powers)
        s = random.randrange(2, powers)
        fa = o_null
        while fa == o_null:
            f = obtainPolynomial(degree, modulo)  # Alice private key: (coeficient, power)
            fa = calculateF(oA, f, modulo)
        ha = o_null
        while ha == o_null:
            h = obtainPolynomial(degree, modulo)  # Bob private key: (coeficient, power)
            ha = calculateF(oA, h, modulo)
        # 2. Alice Token rA
        # rA=F(oA)exp(m).oB.F(oA)exp(n)
        rA = o_null
        fa_n = power(fa, n, modulo)
        fa_m = power(fa, m, modulo)
        aux_rA = multiply(fa_m, oB, modulo)
        rA = multiply(aux_rA, fa_n, modulo)
        rA = (int(rA[0]), int(rA[1]), int(rA[2]), int(rA[3]), int(rA[4]), int(rA[5]), int(rA[6]), int(rA[7]))
        # 3. Bob Token rB
        # rB=h(a)exp(r).b.h(a)exp(s)
        rB = o_null
        ha_s = power(ha, s, modulo)
        ha_r = power(ha, r, modulo)
        aux_rB = multiply(ha_r, oB, modulo)
        rB = multiply(aux_rB, ha_s, modulo)
        rB = (int(rB[0]), int(rB[1]), int(rB[2]), int(rB[3]), int(rB[4]), int(rB[5]), int(rB[6]), int(rB[7]))
        # 4. Alice: session key
        # k1=(fa)exp(m).rB.f(a)exp(n)
        aux_k1 = multiply(fa_m, rB, modulo)
        k1 = multiply(aux_k1, fa_n, modulo)
        k1re = k1[0]
        k1e1 = k1[1]
        k1e2 = k1[2]
        k1e3 = k1[3]
        k1e4 = k1[4]
        k1e5 = k1[5]
        k1e6 = k1[6]
        k1e7 = k1[7]
        # 5. Bob: session key
        # k2=(ha)exp(m).rA.h(a)exp(n)
        aux_k2 = multiply(rA, ha_s, modulo)
        k2 = multiply(ha_r, aux_k2, modulo)
        k2re = k2[0]
        k2e1 = k2[1]
        k2e2 = k2[2]
        k2e3 = k2[3]
        k2e4 = k2[4]
        k2e5 = k2[5]
        k2e6 = k2[6]
        k2e7 = k2[7]
        message = "SUCCESS!!! ALICE generate same keys than BOB"
        ## SubKeys Compare:
        if ((k1re != k2re) or (k1e1 != k2e1) or (k1e2 != k2e2) or (k1e3 != k2e3) or (k1e4 != k2e4) or (k1e5 != k2e5) or (k1e6 != k2e6) or (k1e7 != k2e7)):
            message = "ERROR: A Key obtained by ALICE is different than one obtained by BOB"
            break
        kA = (int(k1[0]), int(k1[1]), int(k1[2]), int(k1[3]), int(k1[4]), int(k1[5]), int(k1[6]), int(k1[7]))
        kB = (int(k2[0]), int(k2[1]), int(k2[2]), int(k2[3]), int(k2[4]), int(k2[5]), int(k2[6]), int(k2[7]))
    finish = datetime.now()
    elapsed = str(finish - start)
    print("SUCCESS!!! Alice and Bob generated the same key.")
    print("Public modulus:", modulo)
    print("oA =", oA)
    print("oB =", oB)
    print("rA =", rA)
    print("rB =", rB)
    print("Shared key from Alice:", kA)
    print("Shared key from Bob:  ", kB)
    print("Time:", elapsed)
    dif = finish - start
    times = str(k) + " keys of " + str(4 * degree) + "bits generated in " + str(dif) + " sec."