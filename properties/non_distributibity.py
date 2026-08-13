import sys
from pathlib import Path

GENERAL_DIR = Path(__file__).resolve().parent.parent / "general"
sys.path.insert(0, str(GENERAL_DIR))

from octonions import multiply, power

# Non-distributivity property of octonion exponentiation

modulo = 251  # Zp
n = 3          # Exponent

# Define two octonions O1 and O2, all components nonzero
O1 = (3, 5, 7, 11, 13, 17, 19, 23)
O2 = (2, 4, 6, 8, 10, 12, 14, 16)

# Product O1 * O2
P = multiply(O1, O2, modulo)

# Power of the product: (O1 * O2)^n
lhs = power(P, n, modulo)  # left-hand side

# Separate powers: O1^n and O2^n
O1_n = power(O1, n, modulo)
O2_n = power(O2, n, modulo)

# Product of powers: O1^n * O2^n
rhs = multiply(O1_n, O2_n, modulo)  # right-hand side

# Compare both sides
print("Is (O1 * O2)^n == O1^n * O2^n ?")
print("LHS =", lhs)
print("RHS =", rhs)
print("Result:", "EQUAL" if lhs == rhs else "DIFFERENT")