import csv
import io
import math
import os
import sys
import time
from collections import Counter
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


# ============================================================================
# CONFIGURATION
# ============================================================================

EXECUTIONS = 10_000
PROGRESS_INTERVAL = 100

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GENERAL_DIR = PROJECT_ROOT / "general"
PROTOCOL_FILE = GENERAL_DIR / "hk17_2-v2.py"

OUTPUT_DIR = Path(__file__).resolve().parent

MATRIX_DISTRIBUTION_CSV = OUTPUT_DIR / "matrix_distribution.csv"
OB_CANDIDATES_CSV = OUTPUT_DIR / "ob_candidates.csv"
SECURITY_SUMMARY_CSV = OUTPUT_DIR / "security_summary.csv"


# ============================================================================
# IMPORT PATH
#
# hk17_2-v2.py imports the unique octonions.py located in general/.
# The protocol itself is not modified.
# ============================================================================

if str(GENERAL_DIR) not in sys.path:
    sys.path.insert(0, str(GENERAL_DIR))


# ============================================================================
# LOAD AND COMPILE THE DEFINITIVE HK17.2 IMPLEMENTATION
#
# The source is compiled once. Each experimental execution receives a fresh
# global namespace, so every run is independent while avoiding reparsing the
# Python source 10,000 times.
# ============================================================================

with open(PROTOCOL_FILE, "r", encoding="utf-8") as protocol_file:
    PROTOCOL_CODE = compile(
        protocol_file.read(),
        str(PROTOCOL_FILE),
        "exec"
    )


# ============================================================================
# STATISTICAL AUXILIARY FUNCTIONS
# ============================================================================

def empirical_entropy(counter, total):
    """
    Shannon empirical entropy in bits.
    """
    if total == 0:
        return 0.0

    entropy = 0.0

    for count in counter.values():
        if count == 0:
            continue

        probability = count / total
        entropy -= probability * math.log2(probability)

    return entropy


def chi_square_uniform(counter, alphabet_size, total):
    """
    Pearson chi-square statistic against a discrete uniform distribution.

    This function returns the statistic only. Statistical interpretation of
    the resulting values will be performed after the experiment.
    """
    if total == 0:
        return 0.0

    expected = total / alphabet_size
    statistic = 0.0

    for value in range(alphabet_size):
        observed = counter.get(value, 0)
        statistic += ((observed - expected) ** 2) / expected

    return statistic


def mean(values):
    if not values:
        return 0.0

    return sum(values) / len(values)


def pearson_correlation(x_values, y_values):
    """
    Pearson sample correlation coefficient.
    """
    if len(x_values) != len(y_values):
        raise ValueError("Correlation vectors must have equal length")

    n = len(x_values)

    if n < 2:
        return 0.0

    mean_x = mean(x_values)
    mean_y = mean(y_values)

    numerator = 0.0
    sum_square_x = 0.0
    sum_square_y = 0.0

    for x, y in zip(x_values, y_values):
        dx = x - mean_x
        dy = y - mean_y

        numerator += dx * dy
        sum_square_x += dx * dx
        sum_square_y += dy * dy

    denominator = math.sqrt(sum_square_x * sum_square_y)

    if denominator == 0:
        return 0.0

    return numerator / denominator


# ============================================================================
# CSV HEADER FOR oB CANDIDATE DATA
# ============================================================================

candidate_fieldnames = [
    "execution",
    "protocol_success",
    "failure_reason",
    "matrix_equal",
    "key_equal",
    "selected_configuration",
]

for candidate_index in range(1, 5):
    candidate_fieldnames.extend(
        [
            f"candidate_{candidate_index}_norm",
            f"candidate_{candidate_index}_invertible",
        ]
    )

    for component_index in range(8):
        candidate_fieldnames.append(
            f"candidate_{candidate_index}_a{component_index}"
        )

for component_index in range(8):
    candidate_fieldnames.append(
        f"selected_oB_a{component_index}"
    )


# ============================================================================
# ACCUMULATORS
# ============================================================================

matrix_value_counts = Counter()

candidate_noninvertible_counts = [
    0,
    0,
    0,
    0,
]

selected_configuration_counts = Counter()

selected_ob_component_counts = [
    Counter()
    for _ in range(8)
]

selected_ob_component_values = [
    []
    for _ in range(8)
]

executions_completed = 0
successful_executions = 0
failed_executions = 0

matrix_agreement_count = 0
key_agreement_count = 0

all_four_noninvertible_count = 0

failure_reasons = Counter()

benchmark_start = time.perf_counter()


# ============================================================================
# EXPERIMENT
# ============================================================================

print("=" * 100)
print("HK17.2 PROTOCOL SECURITY ANALYSIS")
print("=" * 100)
print("Protocol =", PROTOCOL_FILE)
print("Executions =", EXECUTIONS)
print("Matrix distribution CSV =", MATRIX_DISTRIBUTION_CSV)
print("oB candidates CSV =", OB_CANDIDATES_CSV)
print("Summary CSV =", SECURITY_SUMMARY_CSV)
print("=" * 100)
print()

with open(
    OB_CANDIDATES_CSV,
    "w",
    newline="",
    encoding="utf-8"
) as candidate_csv_file:

    candidate_writer = csv.DictWriter(
        candidate_csv_file,
        fieldnames=candidate_fieldnames
    )

    candidate_writer.writeheader()

    # Suppress the very large normal output produced by hk17_2-v2.py.
    with open(os.devnull, "w", encoding="utf-8") as devnull:

        for execution in range(1, EXECUTIONS + 1):

            namespace = {
                "__builtins__": __builtins__,
                "__name__": "__main__",
                "__file__": str(PROTOCOL_FILE),
            }

            protocol_success = True
            failure_reason = ""

            try:
                with redirect_stdout(devnull), redirect_stderr(devnull):
                    exec(
                        PROTOCOL_CODE,
                        namespace
                    )

            except Exception as exc:
                protocol_success = False
                failure_reason = f"{type(exc).__name__}: {exc}"

            executions_completed += 1

            if protocol_success:
                successful_executions += 1
            else:
                failed_executions += 1
                failure_reasons[failure_reason] += 1

            # ================================================================
            # MATRIX LAYER
            # ================================================================

            MA = namespace.get("MA")
            MB = namespace.get("MB")
            M = namespace.get("M")

            matrix_equal = (
                MA is not None
                and MB is not None
                and MA == MB
            )

            if matrix_equal:
                matrix_agreement_count += 1

            if M is not None:
                for row in M:
                    matrix_value_counts.update(row)

            # ================================================================
            # oB CANDIDATES
            # ================================================================

            candidates = namespace.get(
                "oB_candidates_alice",
                []
            )

            row_data = {
                "execution": execution,
                "protocol_success": protocol_success,
                "failure_reason": failure_reason,
                "matrix_equal": matrix_equal,
                "key_equal": False,
                "selected_configuration": "",
            }

            candidate_invertibility = []

            for candidate_index in range(4):

                if candidate_index < len(candidates):
                    candidate = candidates[candidate_index]

                    norm = candidate["norm_squared"]
                    invertible = candidate["invertible"]
                    octonion = candidate["octonion"]

                    row_data[
                        f"candidate_{candidate_index + 1}_norm"
                    ] = norm

                    row_data[
                        f"candidate_{candidate_index + 1}_invertible"
                    ] = invertible

                    candidate_invertibility.append(invertible)

                    if not invertible:
                        candidate_noninvertible_counts[
                            candidate_index
                        ] += 1

                    for component_index in range(8):
                        row_data[
                            f"candidate_{candidate_index + 1}_a"
                            f"{component_index}"
                        ] = octonion[component_index]

                else:
                    row_data[
                        f"candidate_{candidate_index + 1}_norm"
                    ] = ""

                    row_data[
                        f"candidate_{candidate_index + 1}_invertible"
                    ] = ""

                    for component_index in range(8):
                        row_data[
                            f"candidate_{candidate_index + 1}_a"
                            f"{component_index}"
                        ] = ""

            if (
                len(candidate_invertibility) == 4
                and not any(candidate_invertibility)
            ):
                all_four_noninvertible_count += 1

            # ================================================================
            # SELECTED oB
            # ================================================================

            selected_configuration = namespace.get(
                "selected_oB_configuration"
            )

            selected_ob = namespace.get("oB")

            if (
                selected_configuration is not None
                and selected_ob is not None
            ):
                row_data[
                    "selected_configuration"
                ] = selected_configuration

                selected_configuration_counts[
                    selected_configuration
                ] += 1

                for component_index in range(8):

                    component_value = selected_ob[
                        component_index
                    ]

                    row_data[
                        f"selected_oB_a{component_index}"
                    ] = component_value

                    selected_ob_component_counts[
                        component_index
                    ][component_value] += 1

                    selected_ob_component_values[
                        component_index
                    ].append(component_value)

            else:
                for component_index in range(8):
                    row_data[
                        f"selected_oB_a{component_index}"
                    ] = ""

            # ================================================================
            # SESSION KEY AGREEMENT
            # ================================================================

            kA = namespace.get("kA")
            kB = namespace.get("kB")

            key_equal = (
                kA is not None
                and kB is not None
                and kA == kB
            )

            row_data["key_equal"] = key_equal

            if key_equal:
                key_agreement_count += 1

            candidate_writer.writerow(
                row_data
            )

            if execution % PROGRESS_INTERVAL == 0:
                candidate_csv_file.flush()

                elapsed = (
                    time.perf_counter()
                    - benchmark_start
                )

                print(
                    f"[{execution:05d}/{EXECUTIONS}] "
                    f"protocol_success={successful_executions} "
                    f"failures={failed_executions} "
                    f"matrix_agreements={matrix_agreement_count} "
                    f"key_agreements={key_agreement_count} "
                    f"four_candidate_failures="
                    f"{all_four_noninvertible_count} "
                    f"elapsed={elapsed:.2f}s"
                )


# ============================================================================
# MATRIX DISTRIBUTION
# ============================================================================

total_matrix_entries = sum(
    matrix_value_counts.values()
)

matrix_alphabet_size = 16

expected_matrix_count = (
    total_matrix_entries / matrix_alphabet_size
    if total_matrix_entries > 0
    else 0.0
)

with open(
    MATRIX_DISTRIBUTION_CSV,
    "w",
    newline="",
    encoding="utf-8"
) as matrix_csv_file:

    writer = csv.writer(matrix_csv_file)

    writer.writerow(
        [
            "value",
            "count",
            "relative_frequency",
            "expected_uniform_count",
        ]
    )

    for value in range(matrix_alphabet_size):

        count = matrix_value_counts.get(
            value,
            0
        )

        relative_frequency = (
            count / total_matrix_entries
            if total_matrix_entries > 0
            else 0.0
        )

        writer.writerow(
            [
                value,
                count,
                relative_frequency,
                expected_matrix_count,
            ]
        )


# ============================================================================
# SUMMARY
# ============================================================================

total_time = (
    time.perf_counter()
    - benchmark_start
)

summary_rows = []


def add_summary(metric, value):
    summary_rows.append(
        (
            metric,
            value
        )
    )


# --------------------------------------------------------------------------
# General execution results
# --------------------------------------------------------------------------

add_summary(
    "executions_requested",
    EXECUTIONS
)

add_summary(
    "executions_completed",
    executions_completed
)

add_summary(
    "successful_executions",
    successful_executions
)

add_summary(
    "failed_executions",
    failed_executions
)

add_summary(
    "success_rate",
    (
        successful_executions
        / executions_completed
        if executions_completed
        else 0.0
    )
)

add_summary(
    "matrix_agreement_count",
    matrix_agreement_count
)

add_summary(
    "matrix_agreement_rate",
    (
        matrix_agreement_count
        / executions_completed
        if executions_completed
        else 0.0
    )
)

add_summary(
    "key_agreement_count",
    key_agreement_count
)

add_summary(
    "key_agreement_rate",
    (
        key_agreement_count
        / executions_completed
        if executions_completed
        else 0.0
    )
)

add_summary(
    "total_analysis_time_s",
    total_time
)


# --------------------------------------------------------------------------
# Failure reasons
# --------------------------------------------------------------------------

for failure_reason, count in sorted(
    failure_reasons.items()
):
    add_summary(
        f"failure_reason::{failure_reason}",
        count
    )


# --------------------------------------------------------------------------
# Matrix distribution
# --------------------------------------------------------------------------

matrix_entropy = empirical_entropy(
    matrix_value_counts,
    total_matrix_entries
)

matrix_chi_square = chi_square_uniform(
    matrix_value_counts,
    matrix_alphabet_size,
    total_matrix_entries
)

add_summary(
    "matrix_total_entries",
    total_matrix_entries
)

add_summary(
    "matrix_empirical_entropy_bits",
    matrix_entropy
)

add_summary(
    "matrix_maximum_uniform_entropy_bits",
    math.log2(matrix_alphabet_size)
)

add_summary(
    "matrix_chi_square_uniform",
    matrix_chi_square
)

add_summary(
    "matrix_chi_square_degrees_of_freedom",
    matrix_alphabet_size - 1
)


# --------------------------------------------------------------------------
# Candidate invertibility
# --------------------------------------------------------------------------

for candidate_index in range(4):

    count = candidate_noninvertible_counts[
        candidate_index
    ]

    add_summary(
        f"candidate_{candidate_index + 1}_noninvertible_count",
        count
    )

    add_summary(
        f"candidate_{candidate_index + 1}_noninvertible_rate",
        (
            count / executions_completed
            if executions_completed
            else 0.0
        )
    )


# --------------------------------------------------------------------------
# Simultaneous failure of the four candidates
# --------------------------------------------------------------------------

add_summary(
    "all_four_candidates_noninvertible_count",
    all_four_noninvertible_count
)

add_summary(
    "all_four_candidates_noninvertible_rate",
    (
        all_four_noninvertible_count
        / executions_completed
        if executions_completed
        else 0.0
    )
)


# Idealized independent-candidate reference probability
p = 251

single_candidate_noninvertibility_probability = (
    1 / p
    + (p - 1) / (p ** 5)
)

idealized_four_candidate_failure_probability = (
    single_candidate_noninvertibility_probability ** 4
)

add_summary(
    "idealized_single_candidate_noninvertibility_probability",
    single_candidate_noninvertibility_probability
)

add_summary(
    "idealized_four_candidate_failure_probability",
    idealized_four_candidate_failure_probability
)


# --------------------------------------------------------------------------
# Selected configuration frequencies
# --------------------------------------------------------------------------

selected_total = sum(
    selected_configuration_counts.values()
)

for configuration in range(1, 5):

    count = selected_configuration_counts.get(
        configuration,
        0
    )

    add_summary(
        f"selected_configuration_{configuration}_count",
        count
    )

    add_summary(
        f"selected_configuration_{configuration}_rate",
        (
            count / selected_total
            if selected_total
            else 0.0
        )
    )


# --------------------------------------------------------------------------
# Selected oB component statistics
# --------------------------------------------------------------------------

for component_index in range(8):

    values = selected_ob_component_values[
        component_index
    ]

    counts = selected_ob_component_counts[
        component_index
    ]

    total = len(values)

    add_summary(
        f"selected_oB_a{component_index}_samples",
        total
    )

    add_summary(
        f"selected_oB_a{component_index}_mean",
        mean(values)
    )

    add_summary(
        f"selected_oB_a{component_index}_empirical_entropy_bits",
        empirical_entropy(
            counts,
            total
        )
    )

    add_summary(
        f"selected_oB_a{component_index}_maximum_uniform_entropy_bits",
        math.log2(p)
    )

    add_summary(
        f"selected_oB_a{component_index}_chi_square_uniform",
        chi_square_uniform(
            counts,
            p,
            total
        )
    )

    add_summary(
        f"selected_oB_a{component_index}_chi_square_degrees_of_freedom",
        p - 1
    )


# --------------------------------------------------------------------------
# Correlation matrix among selected oB components
# --------------------------------------------------------------------------

for i in range(8):
    for j in range(i, 8):

        correlation = pearson_correlation(
            selected_ob_component_values[i],
            selected_ob_component_values[j]
        )

        add_summary(
            f"selected_oB_correlation_a{i}_a{j}",
            correlation
        )


# ============================================================================
# WRITE SUMMARY CSV
# ============================================================================

with open(
    SECURITY_SUMMARY_CSV,
    "w",
    newline="",
    encoding="utf-8"
) as summary_csv_file:

    writer = csv.writer(
        summary_csv_file
    )

    writer.writerow(
        [
            "metric",
            "value",
        ]
    )

    writer.writerows(
        summary_rows
    )


# ============================================================================
# TERMINAL SUMMARY
# ============================================================================

print()
print("=" * 100)
print("SECURITY ANALYSIS COMPLETED")
print("=" * 100)

print(
    "Executions requested =",
    EXECUTIONS
)

print(
    "Executions completed =",
    executions_completed
)

print(
    "Successful protocol executions =",
    successful_executions
)

print(
    "Failed protocol executions =",
    failed_executions
)

print(
    "Matrix agreements =",
    matrix_agreement_count
)

print(
    "Key agreements =",
    key_agreement_count
)

print(
    "All four candidates non-invertible =",
    all_four_noninvertible_count
)

print()

for candidate_index in range(4):
    print(
        f"Candidate {candidate_index + 1} "
        f"non-invertible = "
        f"{candidate_noninvertible_counts[candidate_index]}"
    )

print()

for configuration in range(1, 5):
    print(
        f"Selected configuration {configuration} = "
        f"{selected_configuration_counts.get(configuration, 0)}"
    )

print()

print(
    "Matrix empirical entropy =",
    matrix_entropy,
    "bits"
)

print(
    "Matrix chi-square statistic =",
    matrix_chi_square
)

print(
    "Idealized single-candidate "
    "non-invertibility probability =",
    single_candidate_noninvertibility_probability
)

print(
    "Idealized four-candidate failure probability =",
    idealized_four_candidate_failure_probability
)

print(
    "Total analysis time =",
    f"{total_time:.3f} s"
)

print()
print("Generated files:")
print(MATRIX_DISTRIBUTION_CSV)
print(OB_CANDIDATES_CSV)
print(SECURITY_SUMMARY_CSV)