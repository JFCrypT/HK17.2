import random
from math import gcd


# ============================================================
# PARAMETERS
# ============================================================

P = 251
GROUP_ORDER = P - 1  # |F_251^*| = 250

# CHANGE ONLY THIS VALUE:
TARGET_GCD = 1      # Try: 250, 125, 50, 25

SAMPLES = 10000

# For these values:
# gcd(250,250) = 250
# gcd(125,250) = 125
# gcd(50,250)  = 50
# gcd(25,250)  = 25
EXPONENT = TARGET_GCD


# ============================================================
# OCTONION ARITHMETIC
# ============================================================

def multiply(a, b, modulo):
    a0, a1, a2, a3, a4, a5, a6, a7 = a
    b0, b1, b2, b3, b4, b5, b6, b7 = b

    return (
        (
            a0 * b0
            - a1 * b1
            - a2 * b2
            - a3 * b3
            - a4 * b4
            - a5 * b5
            - a6 * b6
            - a7 * b7
        ) % modulo,

        (
            a0 * b1
            + a1 * b0
            + a2 * b4
            + a3 * b7
            - a4 * b2
            + a5 * b6
            - a6 * b5
            - a7 * b3
        ) % modulo,

        (
            a0 * b2
            - a1 * b4
            + a2 * b0
            + a3 * b5
            + a4 * b1
            - a5 * b3
            + a6 * b7
            - a7 * b6
        ) % modulo,

        (
            a0 * b3
            - a1 * b7
            - a2 * b5
            + a3 * b0
            + a4 * b6
            + a5 * b2
            - a6 * b4
            + a7 * b1
        ) % modulo,

        (
            a0 * b4
            + a1 * b2
            - a2 * b1
            - a3 * b6
            + a4 * b0
            + a5 * b7
            + a6 * b3
            - a7 * b5
        ) % modulo,

        (
            a0 * b5
            - a1 * b6
            + a2 * b3
            - a3 * b2
            - a4 * b7
            + a5 * b0
            + a6 * b1
            + a7 * b4
        ) % modulo,

        (
            a0 * b6
            + a1 * b5
            - a2 * b7
            + a3 * b4
            - a4 * b3
            - a5 * b1
            + a6 * b0
            + a7 * b2
        ) % modulo,

        (
            a0 * b7
            + a1 * b3
            + a2 * b6
            - a3 * b1
            + a4 * b5
            - a5 * b4
            - a6 * b2
            + a7 * b0
        ) % modulo,
    )


def power(octonion, exponent, modulo):
    """
    Same left-associated power convention used by HK17.2:

    o^1 = o
    o^(k+1) = o^k * o
    """

    if exponent == 0:
        return (1, 0, 0, 0, 0, 0, 0, 0)

    result = octonion

    for _ in range(1, exponent):
        result = multiply(result, octonion, modulo)

    return result


def quadratic_norm(octonion, modulo):
    return sum(
        component * component
        for component in octonion
    ) % modulo


def random_octonion():
    return tuple(
        random.randrange(P)
        for _ in range(8)
    )


# ============================================================
# MAIN EXPERIMENT
# ============================================================

def main():
    actual_gcd = gcd(EXPONENT, GROUP_ORDER)

    if actual_gcd != TARGET_GCD:
        raise ValueError(
            f"gcd({EXPONENT}, {GROUP_ORDER}) = {actual_gcd}, "
            f"not {TARGET_GCD}"
        )

    theoretical_values = GROUP_ORDER // TARGET_GCD

    print("=" * 80)
    print("QUADRATIC-NORM POWER-MAP EXPERIMENT")
    print("=" * 80)

    print(f"p                        = {P}")
    print(f"|F_p^*|                  = {GROUP_ORDER}")
    print(f"Exponent e               = {EXPONENT}")
    print(f"gcd(e, 250)              = {actual_gcd}")
    print(
        f"Theoretical image size   = "
        f"250 / {actual_gcd} = {theoretical_values}"
    )

    observed_norms = set()
    valid_samples = 0

    print()
    print("First examples:")
    print("-" * 80)

    while valid_samples < SAMPLES:
        o = random_octonion()

        norm_o = quadratic_norm(o, P)

        # We study F_251^*, so exclude zero quadratic norm.
        if norm_o == 0:
            continue

        powered = power(o, EXPONENT, P)

        norm_powered = quadratic_norm(powered, P)

        # Theoretical identity:
        expected_norm = pow(norm_o, EXPONENT, P)

        if norm_powered != expected_norm:
            raise RuntimeError(
                "Norm identity failed: "
                "N(o^e) != N(o)^e mod p"
            )

        observed_norms.add(norm_powered)

        if valid_samples < 25:
            print(
                f"{valid_samples + 1:2d}: "
                f"N(o) = {norm_o:3d}  ->  "
                f"N(o^{EXPONENT}) = {norm_powered:3d}"
            )

        valid_samples += 1

    print()
    print("=" * 80)
    print("RESULT")
    print("=" * 80)

    print(f"Valid octonions tested   = {valid_samples}")
    print(f"Observed quadratic norms = {sorted(observed_norms)}")
    print(f"Number observed          = {len(observed_norms)}")
    print(f"Theoretical maximum      = {theoretical_values}")

    print()

    if len(observed_norms) == theoretical_values:
        print("SUCCESS: all theoretically possible powered norms were observed.")
    else:
        print(
            "The sample did not yet cover the complete theoretical image. "
            "Increase SAMPLES."
        )


if __name__ == "__main__":
    main()