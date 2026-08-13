import sys
from pathlib import Path


# ============================================================================
# PATHS
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GENERAL_DIR = PROJECT_ROOT / "general"

HK17_FILE = PROJECT_ROOT / "old" / "hk17.py"
HK17_2_V2_FILE = GENERAL_DIR / "hk17_2-v2.py"

# The unique octonions.py implementation is located in general/
sys.path.insert(0, str(GENERAL_DIR))


# ============================================================================
# PROTOCOL LOADER
# ============================================================================

def load_protocol(protocol_file):
    protocol_globals = {
        "__builtins__": __builtins__,
        "__name__": "__main__",
        "__file__": str(protocol_file),
    }

    with open(protocol_file, "r", encoding="utf-8") as file:
        exec(
            compile(
                file.read(),
                str(protocol_file),
                "exec"
            ),
            protocol_globals
        )

    return protocol_globals


# ============================================================================
# BERNSTEIN-LI ATTACK
# ============================================================================

def run_bernstein_li_attack(protocol_globals, protocol_name):

    modulo = protocol_globals["modulo"]
    oA = protocol_globals["oA"]
    oB = protocol_globals["oB"]
    rA = protocol_globals["rA"]
    rB = protocol_globals["rB"]

    summ = protocol_globals["summ"]
    scale = protocol_globals["scale"]
    multiply = protocol_globals["multiply"]

    kA = protocol_globals.get("kA")
    kB = protocol_globals.get("kB")

    # HK17.2 V2 also exposes session_key for experimental validation
    session_key = protocol_globals.get("session_key")

    print("\n" + "#" * 80)
    print("TARGET PROTOCOL:", protocol_name)
    print("#" * 80)

    print("=" * 80)
    print("NEW BERNSTEIN-LI STYLE LINEARIZATION ATTACK")
    print("=" * 80)

    o_null = (0, 0, 0, 0, 0, 0, 0, 0)
    one = (1, 0, 0, 0, 0, 0, 0, 0)

    print("\n[PROTOCOL DATA]")
    print("modulo =", modulo)
    print("oA =", oA)
    print("oB =", oB)
    print("rA =", rA)
    print("rB =", rB)

    def modprecip(x):
        x %= modulo

        if x == 0:
            raise Exception("Division by zero")

        return pow(x, modulo - 2, modulo)

    def lincomb_1_oA(a, b):
        return summ(
            scale(oA, a, modulo),
            scale(one, b, modulo),
            modulo
        )

    def solve_linear_8x4(cols, target):
        """
        Solves M x = target over F_p.

        cols:
            List of 4 octonions used as columns.

        target:
            Target octonion.

        Returns:
            One solution [A, B, C, D], or None.
        """

        M = []

        for i in range(8):
            row = [
                cols[j][i] % modulo
                for j in range(4)
            ]

            row.append(target[i] % modulo)
            M.append(row)

        rows = 8
        cols_n = 4

        pivot_cols = []
        r = 0

        for c in range(cols_n):
            pivot = None

            for i in range(r, rows):
                if M[i][c] % modulo != 0:
                    pivot = i
                    break

            if pivot is None:
                continue

            M[r], M[pivot] = M[pivot], M[r]

            inv = modprecip(M[r][c])

            M[r] = [
                (v * inv) % modulo
                for v in M[r]
            ]

            for i in range(rows):
                if (
                    i != r
                    and M[i][c] % modulo != 0
                ):
                    factor = M[i][c] % modulo

                    M[i] = [
                        (
                            M[i][j]
                            - factor * M[r][j]
                        )
                        % modulo
                        for j in range(cols_n + 1)
                    ]

            pivot_cols.append(c)
            r += 1

        for i in range(rows):
            if (
                all(
                    M[i][j] % modulo == 0
                    for j in range(cols_n)
                )
                and M[i][cols_n] % modulo != 0
            ):
                return None

        sol = [0] * cols_n

        for row_idx, c in enumerate(pivot_cols):
            sol[c] = M[row_idx][cols_n] % modulo

        return sol

    def factor_bilinear_coeffs(A, B, C, D):
        """
        Finds a,b,c,d such that:

            a*c = A
            a*d = B
            b*c = C
            b*d = D

        over F_p.

        Returns a list of candidates.
        """

        candidates = []

        for a in range(modulo):

            if a != 0:
                c = (A * modprecip(a)) % modulo
                d = (B * modprecip(a)) % modulo

                possible_b = []

                if c != 0:
                    possible_b.append(
                        (C * modprecip(c)) % modulo
                    )

                elif C == 0:
                    possible_b.extend(range(modulo))

                if d != 0:
                    bd = (
                        D * modprecip(d)
                    ) % modulo

                    if possible_b:
                        possible_b = [
                            x
                            for x in possible_b
                            if x == bd
                        ]

                    else:
                        possible_b.append(bd)

                elif D != 0:
                    possible_b = []

                for b in possible_b:
                    if (
                        (a * c) % modulo == A
                        and (a * d) % modulo == B
                        and (b * c) % modulo == C
                        and (b * d) % modulo == D
                    ):
                        candidates.append(
                            (a, b, c, d)
                        )

            else:

                if A != 0 or B != 0:
                    continue

                for b in range(modulo):

                    if b == 0:
                        if C == 0 and D == 0:
                            candidates.append(
                                (0, 0, 0, 0)
                            )

                        continue

                    c = (
                        C * modprecip(b)
                    ) % modulo

                    d = (
                        D * modprecip(b)
                    ) % modulo

                    if (
                        (b * c) % modulo == C
                        and
                        (b * d) % modulo == D
                    ):
                        candidates.append(
                            (0, b, c, d)
                        )

        return candidates

    def verify_key(kE):

        print("\n[EXPERIMENTAL VALIDATION]")

        if kA is not None:
            print("kA =", kA)

        if kB is not None:
            print("kB =", kB)

        if session_key is not None:
            print("session_key =", session_key)

        if (
            kA is not None
            and kB is not None
            and kE == kA == kB
        ):
            print(
                "\n[SUCCESS] Eve recovered "
                "the shared key."
            )

            return True

        if (
            session_key is not None
            and kE == session_key
        ):
            print(
                "\n[SUCCESS] Eve recovered "
                "the shared key."
            )

            return True

        print(
            "\n[FAIL] Candidate key "
            "does not match."
        )

        return False

    # ------------------------------------------------------------------------
    # Bernstein-Li linear span:
    #
    # rA = (a*oA + b) * oB * (c*oA + d)
    #
    # Expands as:
    #
    # rA =
    #   ac * (oA * oB * oA)
    # + ad * (oA * oB)
    # + bc * (oB * oA)
    # + bd * oB
    # ------------------------------------------------------------------------

    basis1 = multiply(
        multiply(oA, oB, modulo),
        oA,
        modulo
    )

    basis2 = multiply(
        oA,
        oB,
        modulo
    )

    basis3 = multiply(
        oB,
        oA,
        modulo
    )

    basis4 = oB

    solution = solve_linear_8x4(
        [
            basis1,
            basis2,
            basis3,
            basis4
        ],
        rA
    )

    if solution is None:

        print(
            "\n[BLOCKED] rA is not in "
            "the Bernstein-Li linear span."
        )

        return False

    A, B, C, D = solution

    print("\n[LINEAR REPRESENTATION FOUND]")
    print("A = ac =", A)
    print("B = ad =", B)
    print("C = bc =", C)
    print("D = bd =", D)

    candidates = factor_bilinear_coeffs(
        A,
        B,
        C,
        D
    )

    print(
        "\nNumber of (a,b,c,d) candidates:",
        len(candidates)
    )

    recovered = False

    for a, b, c, d in candidates:

        g1 = lincomb_1_oA(a, b)
        g2 = lincomb_1_oA(c, d)

        test_rA = multiply(
            multiply(
                g1,
                oB,
                modulo
            ),
            g2,
            modulo
        )

        if test_rA != rA:
            continue

        print("\n[VALID FACTORIZATION FOUND]")
        print("a =", a)
        print("b =", b)
        print("c =", c)
        print("d =", d)
        print("g1 = a*oA + b =", g1)
        print("g2 = c*oA + d =", g2)

        kE = multiply(
            multiply(
                g1,
                rB,
                modulo
            ),
            g2,
            modulo
        )

        print("\n[EVE'S RECONSTRUCTED KEY]")
        print("kE =", kE)

        result = verify_key(kE)

        if result:
            recovered = True
            break

    if not recovered:
        print(
            "\n[FAILED] Linear form exists, "
            "but no candidate recovered the key."
        )

    return recovered


# ============================================================================
# RUN AGAINST ORIGINAL HK17
# ============================================================================

print("\n" + "=" * 80)
print("LOADING ORIGINAL HK17")
print("=" * 80)

hk17_globals = load_protocol(
    HK17_FILE
)

run_bernstein_li_attack(
    hk17_globals,
    "HK17 ORIGINAL"
)


# ============================================================================
# RUN AGAINST HK17.2 V2
# ============================================================================

print("\n" + "=" * 80)
print("LOADING HK17.2 V2")
print("=" * 80)

hk17_2_v2_globals = load_protocol(
    HK17_2_V2_FILE
)

run_bernstein_li_attack(
    hk17_2_v2_globals,
    "HK17.2 V2"
)