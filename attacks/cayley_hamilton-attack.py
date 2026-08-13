import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GENERAL_DIR = PROJECT_ROOT / "general"
PROTOCOL_FILE = GENERAL_DIR / "hk17_2-v2.py"

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

from datetime import datetime
import time


def attack_coefficients_from_index(index, base, length):
    coefficients = [0] * length

    for position in range(length - 1, -1, -1):
        coefficients[position] = index % base
        index //= base

    return tuple(coefficients)


def attack_matrix_linear_combination(coefficients, basis):
    result = matrix_null()

    for coefficient, basis_matrix in zip(coefficients, basis):
        if coefficient != 0:
            result = matrix_add(result, matrix_scale(basis_matrix, coefficient))

    return result


def attack_format_duration(seconds):
    if seconds == float("inf"):
        return "infinite"

    years = seconds / (365.25 * 24 * 60 * 60)

    if years >= 1:
        return "{:.6e} years".format(years)

    days = seconds / (24 * 60 * 60)

    if days >= 1:
        return "{:.6f} days".format(days)

    hours = seconds / 3600

    if hours >= 1:
        return "{:.6f} hours".format(hours)

    minutes = seconds / 60

    if minutes >= 1:
        return "{:.6f} minutes".format(minutes)

    return "{:.6f} seconds".format(seconds)


def attack_print_status(tested_candidates, total_candidates, elapsed_seconds, start_index):
    speed = tested_candidates / elapsed_seconds if elapsed_seconds > 0 else 0
    current_index = start_index + tested_candidates
    percentage = current_index * 100 / total_candidates
    remaining_candidates = total_candidates - current_index

    if speed == 0:
        remaining_seconds = float("inf")
        total_seconds = float("inf")
        expected_seconds = float("inf")
    else:
        remaining_seconds = remaining_candidates / speed
        total_seconds = total_candidates / speed
        expected_seconds = (total_candidates / 2) / speed

    print("\n" + "-" * 100)
    print("ATTACK PROGRESS")
    print("-" * 100)
    print("Current candidate index =", current_index)
    print("Candidates tested in this run =", tested_candidates)
    print("Total candidate space =", total_candidates)
    print("Progress = {:.30f}%".format(percentage))
    print("Measured speed = {:.6f} candidates/second".format(speed))
    print("Elapsed time =", attack_format_duration(elapsed_seconds))
    print("Estimated remaining time =", attack_format_duration(remaining_seconds))
    print("Estimated complete-space time =", attack_format_duration(total_seconds))
    print("Estimated average recovery time =", attack_format_duration(expected_seconds))
    print("Resume index if interrupted =", current_index)


attack_start_index = 0
attack_status_interval_seconds = 30

attack_start_datetime = datetime.now()
attack_start_time = time.perf_counter()
attack_last_status_time = attack_start_time

attack_basis = []
attack_current_power = matrix_identity()

for attack_exponent in range(matrix_degree):
    attack_basis.append(attack_current_power)
    attack_current_power = matrix_multiply(attack_current_power, A)

attack_total_candidates = matrix_modulo ** matrix_degree
attack_tested_candidates = 0
attack_valid_factor_candidates = 0
attack_success = False

print("\n" + "=" * 100)
print("UNRESTRICTED CAYLEY-HAMILTON EXHAUSTIVE ATTACK")
print("=" * 100)

print("\nPUBLIC INFORMATION AVAILABLE TO EVE")
print("-" * 100)
print("Matrix dimension =", matrix_dimension)
print("Matrix polynomial degree =", matrix_degree)
print("Matrix modulus =", matrix_modulo)
print("Public exponent u =", u)
print("Public exponent v =", v)
print("Total candidate space =", attack_total_candidates)
print("Equivalent binary complexity = 2^{}".format(matrix_degree * matrix_component_bits))
print("Starting candidate index =", attack_start_index)
print("Status interval =", attack_status_interval_seconds, "seconds")

print("\nPUBLIC MATRICES")
print("-" * 100)
print_matrix("Public matrix A =", A)
print_matrix("Public matrix B =", B)

print("\nPUBLIC MATRIX TOKENS")
print("-" * 100)
print_matrix("Alice public matrix token TA =", TA)
print_matrix("Bob public matrix token TB =", TB)

print("\nPUBLIC HK17.2 TOKENS")
print("-" * 100)
print("Alice public octonion token rA =", rA)
print("Bob public octonion token rB =", rB)

print("\nSEARCHING FOR X SUCH THAT")
print("-" * 100)
print("X^u · B · X^v = TA")
print("\nThe attack will continue until:")
print("1. The actual oB and session key are recovered.")
print("2. The complete space is exhausted.")
print("3. The user interrupts execution with Ctrl+C.")

try:
    for attack_candidate_index in range(attack_start_index, attack_total_candidates):
        attack_coefficients = attack_coefficients_from_index(attack_candidate_index, matrix_modulo, matrix_degree)
        attack_matrix_X = attack_matrix_linear_combination(attack_coefficients, attack_basis)
        attack_matrix_X_u = matrix_power(attack_matrix_X, u)
        attack_matrix_X_v = matrix_power(attack_matrix_X, v)
        attack_candidate_TA = matrix_multiply(matrix_multiply(attack_matrix_X_u, B), attack_matrix_X_v)

        attack_tested_candidates += 1

        if attack_candidate_TA == TA:
            attack_valid_factor_candidates += 1
            attack_recovered_shared_matrix = matrix_multiply(matrix_multiply(attack_matrix_X_u, TB), attack_matrix_X_v)
            attack_submatrix_sums, attack_oB_candidates = generate_octonion_candidates(attack_recovered_shared_matrix)
            attack_selected_oB_configuration, attack_candidate_oB = select_first_invertible_octonion(attack_oB_candidates)

            print("\n" + "=" * 100)
            print("VALID MATRIX FACTOR FOUND")
            print("=" * 100)
            print("Candidate index =", attack_candidate_index)
            print("Coefficients =", attack_coefficients)
            print_matrix("Recovered matrix factor X =", attack_matrix_X)
            print_matrix("Recovered shared matrix =", attack_recovered_shared_matrix)

            print("\nRECOVERED SUBMATRIX SUMS")
            print("-" * 100)

            for row in attack_submatrix_sums:
                print("   ", row)

            print("\nRECOVERED oB CANDIDATES")
            print("-" * 100)

            for index, candidate in enumerate(attack_oB_candidates, start=1):
                print("\nConfiguration", index)
                print("Traversal =", candidate["name"])
                print("Ordered sums =", candidate["ordered_sums"])
                print("oB =", candidate["octonion"])
                print("Quadratic norm =", candidate["norm_squared"])
                print("Invertible =", candidate["invertible"])

            print("\nSelected oB configuration =", attack_selected_oB_configuration)
            print("Recovered oB candidate =", attack_candidate_oB)

            if attack_candidate_oB is not None:
                attack_candidate_oB_inverse = octonionrecip(attack_candidate_oB)
                attack_candidate_alice_autoconvolution = multiply(rA, attack_candidate_oB_inverse, modulo)
                attack_candidate_bob_autoconvolution = multiply(rB, attack_candidate_oB_inverse, modulo)

                # kE = (rA · oB^(-1)) · rB
                # This preserves the definitive association:
                # kE = CA · (CB · oB)
                attack_candidate_session_key = multiply(attack_candidate_alice_autoconvolution, rB, modulo)

                print("Recovered oB^(-1) =", attack_candidate_oB_inverse)
                print("Recovered Alice autoconvolution =", attack_candidate_alice_autoconvolution)
                print("Recovered Bob autoconvolution =", attack_candidate_bob_autoconvolution)
                print("Recovered session-key candidate =", attack_candidate_session_key)

                print("\nEXPERIMENTAL VALIDATION")
                print("-" * 100)
                print("Matches actual shared matrix =", attack_recovered_shared_matrix == M)
                print("Matches actual oB =", attack_candidate_oB == oB)
                print("Matches actual session key =", attack_candidate_session_key == session_key)

                if attack_candidate_oB == oB and attack_candidate_session_key == session_key:
                    attack_success = True

                    print("\n" + "=" * 100)
                    print("ATTACK SUCCESSFUL!!!")
                    print("Eve recovered the actual oB and the actual session key.")
                    print("=" * 100)

                    break
            else:
                print("None of the four recovered oB candidates is invertible.")

        attack_current_time = time.perf_counter()

        if attack_current_time - attack_last_status_time >= attack_status_interval_seconds:
            attack_elapsed_seconds = attack_current_time - attack_start_time
            attack_print_status(attack_tested_candidates, attack_total_candidates, attack_elapsed_seconds, attack_start_index)
            attack_last_status_time = attack_current_time

except KeyboardInterrupt:
    attack_finish_time = time.perf_counter()
    attack_elapsed_seconds = attack_finish_time - attack_start_time

    print("\n\n" + "=" * 100)
    print("ATTACK INTERRUPTED BY USER")
    print("=" * 100)

    attack_print_status(attack_tested_candidates, attack_total_candidates, attack_elapsed_seconds, attack_start_index)

    print("\nTo resume the attack, set:")
    print("attack_start_index =", attack_start_index + attack_tested_candidates)

attack_finish_datetime = datetime.now()
attack_finish_time = time.perf_counter()
attack_total_elapsed_seconds = attack_finish_time - attack_start_time

print("\n" + "=" * 100)
print("ATTACK EXECUTION SUMMARY")
print("=" * 100)
print("Started at =", attack_start_datetime)
print("Finished at =", attack_finish_datetime)
print("Candidates tested =", attack_tested_candidates)
print("Valid factor candidates =", attack_valid_factor_candidates)
print("Final candidate index =", attack_start_index + attack_tested_candidates)
print("Execution time =", attack_format_duration(attack_total_elapsed_seconds))

attack_final_speed = attack_tested_candidates / attack_total_elapsed_seconds if attack_total_elapsed_seconds > 0 else 0

print("Average speed = {:.6f} candidates/second".format(attack_final_speed))

if attack_final_speed > 0:
    print("Estimated complete-space time =", attack_format_duration(attack_total_candidates / attack_final_speed))
    print("Estimated average recovery time =", attack_format_duration((attack_total_candidates / 2) / attack_final_speed))

if attack_success:
    print("Result = ATTACK SUCCESSFUL")
elif attack_start_index + attack_tested_candidates >= attack_total_candidates:
    print("Result = COMPLETE SPACE EXHAUSTED WITHOUT SUCCESS")
else:
    print("Result = ATTACK IN PROGRESS OR INTERRUPTED")