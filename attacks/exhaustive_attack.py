# Eve's exhaustive attack - tries all combinations of public parameters
# This code should be run IMMEDIATELY AFTER the protocol execution

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GENERAL_DIR = PROJECT_ROOT / "general"
PROTOCOL_FILE = PROJECT_ROOT / "old" / "hk17_2-v1.py"

# The unique octonions.py implementation is located in general/
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

print("="*80)
print("EVE'S EXHAUSTIVE ATTACK")
print("="*80)

modulo = 251

print("\n[CAPTURED PUBLIC PARAMETERS]")
print("oA =", oA)
print("oB =", oB)
print("rA =", rA)
print("rB =", rB)
print("modulo =", modulo)

# Real shared key
print("\n[REAL SHARED KEY]")
print("k1 =", k1)
print("k2 =", k2)
print()

# List of public elements available to Eve
public_elements = [rA, rB, oA, oB]

print("[TRYING ALL COMBINATIONS OF PUBLIC ELEMENTS]")
print("(Products of length 2, 3, and 4)\n")

from itertools import product

attack_successful = False
successful_combo = None
attempts = 0

for length in [2, 3, 4]:
    for combo in product(public_elements, repeat=length):
        attempts += 1
        result = combo[0]
        for i in range(1, length):
            result = multiply(result, combo[i], modulo)
        
        if result == k1 and result == k2:
            attack_successful = True
            successful_combo = combo
            print(f"[FOUND] {combo} = {result}")
            break
        elif result == k1:
            print(f"[MATCHES k1] {combo} = {result}")
        elif result == k2:
            print(f"[MATCHES k2] {combo} = {result}")
    
    if attack_successful:
        break

print(f"\nTotal attempts: {attempts}")

if attack_successful:
    print(f"\n[ATTACK SUCCESSFUL]")
    print(f"Combination: {successful_combo}")
    print("Eve can recover the shared key using only public parameters.")
else:
    print("\n[ATTACK FAILED]")
    print("None of the combinations of public parameters produced the shared key.")

# Also check specific combinations with detailed output
print("\n" + "="*80)
print("CHECKING SPECIFIC COMBINATIONS WITH DETAILED OUTPUT")
print("="*80)

specific_combos = [
    ("rA * rB", multiply(rA, rB, modulo)),
    ("rB * rA", multiply(rB, rA, modulo)),
    ("rA * oB", multiply(rA, oB, modulo)),
    ("rB * oB", multiply(rB, oB, modulo)),
    ("rA * oB * rB", multiply(multiply(rA, oB, modulo), rB, modulo)),
    ("rB * oB * rA", multiply(multiply(rB, oB, modulo), rA, modulo)),
    ("rA * rB * oB", multiply(multiply(rA, rB, modulo), oB, modulo)),
    ("rB * rA * oB", multiply(multiply(rB, rA, modulo), oB, modulo)),
    ("rA * oB * rB * oB", multiply(multiply(multiply(rA, oB, modulo), rB, modulo), oB, modulo)),
    ("rB * oB * rA * oB", multiply(multiply(multiply(rB, oB, modulo), rA, modulo), oB, modulo)),
    ("rA * oB * rB * oA", multiply(multiply(multiply(rA, oB, modulo), rB, modulo), oA, modulo)),
    ("rB * oB * rA * oA", multiply(multiply(multiply(rB, oB, modulo), rA, modulo), oA, modulo)),
    ("oB * rA * rB", multiply(multiply(oB, rA, modulo), rB, modulo)),
    ("oB * rB * rA", multiply(multiply(oB, rB, modulo), rA, modulo)),
    ("rA * oB * rB * rA", multiply(multiply(multiply(rA, oB, modulo), rB, modulo), rA, modulo)),
    ("rB * oB * rA * rB", multiply(multiply(multiply(rB, oB, modulo), rA, modulo), rB, modulo)),
    ("(rA * oB) * (rB * oB)", multiply(multiply(rA, oB, modulo), multiply(rB, oB, modulo), modulo)),
    ("(rB * oB) * (rA * oB)", multiply(multiply(rB, oB, modulo), multiply(rA, oB, modulo), modulo)),
]

print(f"\n{'Combination':<35} {'Result':<60} {'Match?'}")
print("-" * 110)

for name, result in specific_combos:
    if result == k1 == k2:
        match = "YES (k1=k2)"
    elif result == k1:
        match = "YES (k1 only)"
    elif result == k2:
        match = "YES (k2 only)"
    else:
        match = "NO"
    print(f"{name:<35} {str(result):<60} {match}")

print("\n" + "="*80)
if attack_successful:
    print("CONCLUSION: The protocol is VULNERABLE to passive attack.")
else:
    print("CONCLUSION: The protocol appears SECURE against this exhaustive attack.")
print("="*80)