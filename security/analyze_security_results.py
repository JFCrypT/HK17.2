import csv
import math
from collections import Counter
from pathlib import Path


# ============================================================================
# CONFIGURATION
# ============================================================================

P = 251

BASE_DIR = Path(__file__).resolve().parent

OB_CANDIDATES_CSV = BASE_DIR / "ob_candidates.csv"
MATRIX_DISTRIBUTION_CSV = BASE_DIR / "matrix_distribution.csv"
SECURITY_SUMMARY_CSV = BASE_DIR / "security_summary.csv"

NORM_DISTRIBUTION_CSV = BASE_DIR / "norm_distribution.csv"
NORM_CORRELATION_CSV = BASE_DIR / "norm_correlation.csv"
DERIVED_SUMMARY_CSV = BASE_DIR / "derived_security_summary.csv"


# ============================================================================
# AUXILIARY FUNCTIONS
# ============================================================================

def empirical_entropy(counter, total):
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
    if total == 0:
        return 0.0

    expected = total / alphabet_size
    statistic = 0.0

    for value in range(alphabet_size):
        observed = counter.get(value, 0)

        statistic += (
            (observed - expected) ** 2
            / expected
        )

    return statistic


def mean(values):
    if not values:
        return 0.0

    return sum(values) / len(values)


def pearson_correlation(x_values, y_values):
    if len(x_values) != len(y_values):
        raise ValueError(
            "Correlation vectors must have equal length"
        )

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

    denominator = math.sqrt(
        sum_square_x * sum_square_y
    )

    if denominator == 0:
        return 0.0

    return numerator / denominator


def boolean_from_csv(value):
    return str(value).strip().lower() == "true"


# ============================================================================
# LOAD DATA
# ============================================================================

rows = []

with open(
    OB_CANDIDATES_CSV,
    "r",
    encoding="utf-8",
    newline=""
) as csv_file:

    reader = csv.DictReader(csv_file)

    for row in reader:
        rows.append(row)


executions = len(rows)

print("=" * 100)
print("HK17.2 DERIVED SECURITY ANALYSIS")
print("=" * 100)
print("Input =", OB_CANDIDATES_CSV)
print("Executions =", executions)
print("=" * 100)


# ============================================================================
# EXTRACT CANDIDATE NORMS AND OCTONIONS
# ============================================================================

norm_values = [
    [],
    [],
    [],
    [],
]

norm_counts = [
    Counter(),
    Counter(),
    Counter(),
    Counter(),
]

candidate_values = [
    [],
    [],
    [],
    [],
]

invertibility_patterns = Counter()

same_candidate_pair_counts = Counter()
same_norm_pair_counts = Counter()

all_candidates_identical_count = 0
all_norms_identical_count = 0


for row in rows:

    execution_candidates = []
    execution_norms = []
    execution_invertibility = []

    for candidate_index in range(1, 5):

        norm = int(
            row[f"candidate_{candidate_index}_norm"]
        )

        invertible = boolean_from_csv(
            row[f"candidate_{candidate_index}_invertible"]
        )

        candidate = tuple(
            int(
                row[
                    f"candidate_{candidate_index}_a"
                    f"{component_index}"
                ]
            )
            for component_index in range(8)
        )

        norm_values[candidate_index - 1].append(
            norm
        )

        norm_counts[candidate_index - 1][norm] += 1

        candidate_values[candidate_index - 1].append(
            candidate
        )

        execution_candidates.append(
            candidate
        )

        execution_norms.append(
            norm
        )

        execution_invertibility.append(
            invertible
        )

    pattern = tuple(
        1 if value else 0
        for value in execution_invertibility
    )

    invertibility_patterns[pattern] += 1

    for i in range(4):
        for j in range(i + 1, 4):

            if (
                execution_candidates[i]
                == execution_candidates[j]
            ):
                same_candidate_pair_counts[
                    (i + 1, j + 1)
                ] += 1

            if (
                execution_norms[i]
                == execution_norms[j]
            ):
                same_norm_pair_counts[
                    (i + 1, j + 1)
                ] += 1

    if len(set(execution_candidates)) == 1:
        all_candidates_identical_count += 1

    if len(set(execution_norms)) == 1:
        all_norms_identical_count += 1


# ============================================================================
# NORM DISTRIBUTION CSV
# ============================================================================

with open(
    NORM_DISTRIBUTION_CSV,
    "w",
    encoding="utf-8",
    newline=""
) as csv_file:

    writer = csv.writer(csv_file)

    writer.writerow(
        [
            "candidate",
            "norm",
            "count",
            "relative_frequency",
            "expected_uniform_count",
        ]
    )

    expected_count = (
        executions / P
        if executions > 0
        else 0.0
    )

    for candidate_index in range(4):

        for norm in range(P):

            count = norm_counts[
                candidate_index
            ].get(norm, 0)

            relative_frequency = (
                count / executions
                if executions > 0
                else 0.0
            )

            writer.writerow(
                [
                    candidate_index + 1,
                    norm,
                    count,
                    relative_frequency,
                    expected_count,
                ]
            )


# ============================================================================
# NORM CORRELATION CSV
# ============================================================================

with open(
    NORM_CORRELATION_CSV,
    "w",
    encoding="utf-8",
    newline=""
) as csv_file:

    writer = csv.writer(csv_file)

    writer.writerow(
        [
            "candidate_i",
            "candidate_j",
            "pearson_correlation",
            "equal_norm_count",
            "equal_norm_rate",
            "identical_candidate_count",
            "identical_candidate_rate",
        ]
    )

    for i in range(4):
        for j in range(i + 1, 4):

            correlation = pearson_correlation(
                norm_values[i],
                norm_values[j]
            )

            equal_norm_count = (
                same_norm_pair_counts.get(
                    (i + 1, j + 1),
                    0
                )
            )

            identical_candidate_count = (
                same_candidate_pair_counts.get(
                    (i + 1, j + 1),
                    0
                )
            )

            writer.writerow(
                [
                    i + 1,
                    j + 1,
                    correlation,
                    equal_norm_count,
                    (
                        equal_norm_count / executions
                        if executions > 0
                        else 0.0
                    ),
                    identical_candidate_count,
                    (
                        identical_candidate_count
                        / executions
                        if executions > 0
                        else 0.0
                    ),
                ]
            )


# ============================================================================
# DERIVED SUMMARY
# ============================================================================

summary_rows = []


def add_summary(metric, value):
    summary_rows.append(
        (
            metric,
            value
        )
    )


add_summary(
    "executions",
    executions
)

add_summary(
    "norm_field_size",
    P
)

add_summary(
    "maximum_uniform_norm_entropy_bits",
    math.log2(P)
)


# --------------------------------------------------------------------------
# Per-candidate norm statistics
# --------------------------------------------------------------------------

for candidate_index in range(4):

    values = norm_values[
        candidate_index
    ]

    counts = norm_counts[
        candidate_index
    ]

    zero_count = counts.get(
        0,
        0
    )

    distinct_norms = len(
        counts
    )

    entropy = empirical_entropy(
        counts,
        executions
    )

    chi_square = chi_square_uniform(
        counts,
        P,
        executions
    )

    add_summary(
        f"candidate_{candidate_index + 1}_norm_distinct_values",
        distinct_norms
    )

    add_summary(
        f"candidate_{candidate_index + 1}_norm_zero_count",
        zero_count
    )

    add_summary(
        f"candidate_{candidate_index + 1}_norm_zero_rate",
        (
            zero_count / executions
            if executions > 0
            else 0.0
        )
    )

    add_summary(
        f"candidate_{candidate_index + 1}_norm_mean",
        mean(values)
    )

    add_summary(
        f"candidate_{candidate_index + 1}_norm_entropy_bits",
        entropy
    )

    add_summary(
        f"candidate_{candidate_index + 1}_norm_chi_square_uniform",
        chi_square
    )

    add_summary(
        f"candidate_{candidate_index + 1}_norm_chi_square_df",
        P - 1
    )


# --------------------------------------------------------------------------
# Pairwise norm/candidate relations
# --------------------------------------------------------------------------

for i in range(4):
    for j in range(i + 1, 4):

        correlation = pearson_correlation(
            norm_values[i],
            norm_values[j]
        )

        equal_norm_count = (
            same_norm_pair_counts.get(
                (i + 1, j + 1),
                0
            )
        )

        identical_candidate_count = (
            same_candidate_pair_counts.get(
                (i + 1, j + 1),
                0
            )
        )

        add_summary(
            f"norm_correlation_candidate_{i + 1}_candidate_{j + 1}",
            correlation
        )

        add_summary(
            f"equal_norm_count_candidate_{i + 1}_candidate_{j + 1}",
            equal_norm_count
        )

        add_summary(
            f"equal_norm_rate_candidate_{i + 1}_candidate_{j + 1}",
            (
                equal_norm_count / executions
                if executions > 0
                else 0.0
            )
        )

        add_summary(
            f"identical_candidate_count_{i + 1}_{j + 1}",
            identical_candidate_count
        )

        add_summary(
            f"identical_candidate_rate_{i + 1}_{j + 1}",
            (
                identical_candidate_count
                / executions
                if executions > 0
                else 0.0
            )
        )


add_summary(
    "all_four_candidates_identical_count",
    all_candidates_identical_count
)

add_summary(
    "all_four_candidates_identical_rate",
    (
        all_candidates_identical_count / executions
        if executions > 0
        else 0.0
    )
)

add_summary(
    "all_four_norms_identical_count",
    all_norms_identical_count
)

add_summary(
    "all_four_norms_identical_rate",
    (
        all_norms_identical_count / executions
        if executions > 0
        else 0.0
    )
)


# --------------------------------------------------------------------------
# Invertibility joint patterns
# --------------------------------------------------------------------------

for pattern, count in sorted(
    invertibility_patterns.items()
):

    pattern_string = "".join(
        str(bit)
        for bit in pattern
    )

    add_summary(
        f"invertibility_pattern_{pattern_string}_count",
        count
    )

    add_summary(
        f"invertibility_pattern_{pattern_string}_rate",
        (
            count / executions
            if executions > 0
            else 0.0
        )
    )


# --------------------------------------------------------------------------
# Idealized reference
# --------------------------------------------------------------------------

single_candidate_noninvertibility_probability = (
    1 / P
    + (P - 1) / (P ** 5)
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


# ============================================================================
# WRITE DERIVED SUMMARY
# ============================================================================

with open(
    DERIVED_SUMMARY_CSV,
    "w",
    encoding="utf-8",
    newline=""
) as csv_file:

    writer = csv.writer(csv_file)

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
# TERMINAL OUTPUT
# ============================================================================

print()
print("PER-CANDIDATE NORM STATISTICS")
print("-" * 100)

for candidate_index in range(4):

    counts = norm_counts[
        candidate_index
    ]

    entropy = empirical_entropy(
        counts,
        executions
    )

    chi_square = chi_square_uniform(
        counts,
        P,
        executions
    )

    print(
        f"Candidate {candidate_index + 1}: "
        f"distinct_norms={len(counts)}, "
        f"zero_count={counts.get(0, 0)}, "
        f"entropy={entropy:.9f}, "
        f"chi_square={chi_square:.6f}"
    )


print()
print("PAIRWISE NORM RELATIONS")
print("-" * 100)

for i in range(4):
    for j in range(i + 1, 4):

        correlation = pearson_correlation(
            norm_values[i],
            norm_values[j]
        )

        equal_norm_count = (
            same_norm_pair_counts.get(
                (i + 1, j + 1),
                0
            )
        )

        identical_candidate_count = (
            same_candidate_pair_counts.get(
                (i + 1, j + 1),
                0
            )
        )

        print(
            f"Candidate {i + 1} vs {j + 1}: "
            f"rho={correlation:.9f}, "
            f"equal_norms={equal_norm_count}, "
            f"identical_candidates="
            f"{identical_candidate_count}"
        )


print()
print("JOINT INVERTIBILITY PATTERNS")
print("-" * 100)

for pattern, count in sorted(
    invertibility_patterns.items()
):

    pattern_string = "".join(
        str(bit)
        for bit in pattern
    )

    print(
        f"{pattern_string}: "
        f"{count} "
        f"({count / executions:.8f})"
    )


print()
print("Generated files:")
print(NORM_DISTRIBUTION_CSV)
print(NORM_CORRELATION_CSV)
print(DERIVED_SUMMARY_CSV)