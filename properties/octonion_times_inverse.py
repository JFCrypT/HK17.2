# Octonion times its inverse → octonion unit

def octonion_conjugate(o):
    # Octonion conjugate
    return (o[0], -o[1], -o[2], -o[3], -o[4], -o[5], -o[6], -o[7])

def octonion_norm_squared(o, p):
    # Squared norm (modulo p)
    return sum((x * x) % p for x in o) % p

def modinv(a, p):
    # Modular inverse (a^{-1} mod p)
    return pow(a, p - 2, p)

def octonion_scalar_mul(o, s, p):
    # Multiply octonion by scalar mod p
    return tuple((xi * s) % p for xi in o)

def octonion_mult(a, b, p):
    # Octonion product (Cayley-Dickson)
    a0, a1, a2, a3, a4, a5, a6, a7 = a
    b0, b1, b2, b3, b4, b5, b6, b7 = b
    c0 = (a0*b0 - a1*b1 - a2*b2 - a3*b3 - a4*b4 - a5*b5 - a6*b6 - a7*b7) % p
    c1 = (a0*b1 + a1*b0 + a2*b3 - a3*b2 + a4*b5 - a5*b4 - a6*b7 + a7*b6) % p
    c2 = (a0*b2 - a1*b3 + a2*b0 + a3*b1 + a4*b6 + a5*b7 - a6*b4 - a7*b5) % p
    c3 = (a0*b3 + a1*b2 - a2*b1 + a3*b0 + a4*b7 - a5*b6 + a6*b5 - a7*b4) % p
    c4 = (a0*b4 - a1*b5 - a2*b6 - a3*b7 + a4*b0 + a5*b1 + a6*b2 + a7*b3) % p
    c5 = (a0*b5 + a1*b4 - a2*b7 + a3*b6 - a4*b1 + a5*b0 - a6*b3 + a7*b2) % p
    c6 = (a0*b6 + a1*b7 + a2*b4 - a3*b5 - a4*b2 + a5*b3 + a6*b0 - a7*b1) % p
    c7 = (a0*b7 - a1*b6 + a2*b5 + a3*b4 - a4*b3 - a5*b2 + a6*b1 + a7*b0) % p
    return (c0, c1, c2, c3, c4, c5, c6, c7)

def octonion_inverse(o, p):
    # Octonion inverse
    norm2 = octonion_norm_squared(o, p)
    if norm2 == 0:
        raise ValueError("Octonion is not invertible (zero squared norm).")
    norm2_inv = modinv(norm2, p)
    return octonion_scalar_mul(octonion_conjugate(o), norm2_inv, p)

# --- USAGE EXAMPLE ---

p = 251
O = (7, 2, 3, 5, 1, 0, 4, 6)
O_inv = octonion_inverse(O, p)
unit1 = octonion_mult(O, O_inv, p)
unit2 = octonion_mult(O_inv, O, p)

print("Octonion:", O)
print("Inverse:", O_inv)
print("Product O * O^{-1}:", unit1)
print("Product O^{-1} * o:", unit2)
