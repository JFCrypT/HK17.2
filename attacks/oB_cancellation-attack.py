# ===============================
# HK17.2 oB CANCELLATION ATTACK
# ===============================

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GENERAL_DIR = PROJECT_ROOT / "general"
PROTOCOL_FILE = PROJECT_ROOT / "old" / "hk17_2-v1.py"

sys.path.insert(0, str(GENERAL_DIR))

with open(PROTOCOL_FILE, "r", encoding="utf-8") as protocol_file:
    exec(
        compile(
            protocol_file.read(),
            str(PROTOCOL_FILE),
            "exec"
        ),
        globals()
    )

p = 251

print("=== HK17.2 oB CANCELLATION ATTACK ===")
print("oB =", oB)
print("rA =", rA)
print("rB =", rB)

# --- OCTONION INVERSE ---
def inv_oct(o):
    norm_sq = sum((x * x) % p for x in o) % p

    if norm_sq == 0:
        raise Exception("oB is not invertible")

    inv_norm = pow(norm_sq, p - 2, p)

    conj = (
        o[0],
        -o[1],
        -o[2],
        -o[3],
        -o[4],
        -o[5],
        -o[6],
        -o[7]
    )

    return tuple((conj[i] * inv_norm) % p for i in range(8))

# --- STEP 1: oB CANCELLATION ---
oB_inv = inv_oct(oB)

A = multiply(rA, oB_inv, p)
B = multiply(rB, oB_inv, p)

print("\nA (estimated) =", A)
print("B (estimated) =", B)

# --- STEP 2: KEY RECONSTRUCTION ---
C = multiply(A, B, p)
k_rec = multiply(C, oB, p)

print("\nReconstructed shared key =", k_rec)