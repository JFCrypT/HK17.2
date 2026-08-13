import csv
import math
import os
import sys
import time
from collections import Counter, defaultdict
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


# ============================================================================
# CONFIGURATION
# ============================================================================

EXECUTIONS = 10_000
PROGRESS_INTERVAL = 100

P = 251
P_MINUS_1 = P - 1

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GENERAL_DIR = PROJECT_ROOT / "general"
PROTOCOL_FILE = GENERAL_DIR / "hk17_2-v2.py"

OUTPUT_DIR = Path(__file__).resolve().parent

RAW_CSV = OUTPUT_DIR / "octonion_layer_full.csv"
SUMMARY_CSV = OUTPUT_DIR / "octonion_layer_full_summary.csv"
POWER_CLASSES_CSV = OUTPUT_DIR / "octonion_power_classes.csv"


# ============================================================================
# IMPORT PATH
# ============================================================================

if str(GENERAL_DIR) not in sys.path:
    sys.path.insert(0, str(GENERAL_DIR))


# ============================================================================
# LOAD DEFINITIVE HK17.2 WITHOUT MODIFYING IT
# ============================================================================

with open(PROTOCOL_FILE, "r", encoding="utf-8") as protocol_file:
    PROTOCOL_CODE = compile(
        protocol_file.read(),
        str(PROTOCOL_FILE),
        "exec"
    )


# ============================================================================
# OCTONION VARIABLES
# ============================================================================

OCTONION_VARIABLES = [
    ("oA", "public_oA"),
    ("oB", "shared_oB"),

    ("oS1", "alice_secret_displacement"),
    ("oS2", "bob_secret_displacement"),

    ("negative_oA_plus_oS1", "alice_shifted_argument"),
    ("negative_oA_plus_oS2", "bob_shifted_argument"),

    ("f_oA", "alice_polynomial_public_input"),
    (
        "f_negative_oA_plus_oS1",
        "alice_polynomial_shifted_input"
    ),

    ("h_oA", "bob_polynomial_public_input"),
    (
        "h_negative_oA_plus_oS2",
        "bob_polynomial_shifted_input"
    ),

    ("f1", "alice_power_public_input"),
    ("f2", "alice_power_shifted_input"),

    ("h1", "bob_power_public_input"),
    ("h2", "bob_power_shifted_input"),

    ("f_autoconvolution", "alice_autoconvolution"),
    ("h_autoconvolution", "bob_autoconvolution"),

    ("recovered_f_autoconvolution", "bob_recovered_alice_autoconvolution"),

    ("rA", "alice_public_token"),
    ("rB", "bob_public_token"),

    ("kA", "alice_session_key"),
    ("kB", "bob_session_key"),
]


# Variables specifically related by exponentiation.
POWER_RELATIONS = [
    (
        "alice_polynomial_public_input",
        "alice_power_public_input",
        "m"
    ),
    (
        "alice_polynomial_shifted_input",
        "alice_power_shifted_input",
        "m"
    ),
    (
        "bob_polynomial_public_input",
        "bob_power_public_input",
        "n"
    ),
    (
        "bob_polynomial_shifted_input",
        "bob_power_shifted_input",
        "n"
    ),
]


# ============================================================================
# AUXILIARY FUNCTIONS
# ============================================================================

def mean(values):
    if not values:
        return 0.0
    return sum(values) / len(values)


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


def pearson_correlation(x_values, y_values):
    if len(x_values) != len(y_values):
        raise ValueError(
            "Correlation vectors must have equal length"
        )

    if len(x_values) < 2:
        return 0.0

    mean_x = mean(x_values)
    mean_y = mean(y_values)

    numerator = 0.0
    square_x = 0.0
    square_y = 0.0

    for x, y in zip(x_values, y_values):
        dx = x - mean_x
        dy = y - mean_y

        numerator += dx * dy
        square_x += dx * dx
        square_y += dy * dy

    denominator = math.sqrt(
        square_x * square_y
    )

    if denominator == 0:
        return 0.0

    return numerator / denominator


def octonion_norm_squared(octonion):
    if octonion is None:
        return None

    return sum(
        (component * component) % P
        for component in octonion
    ) % P


def is_null_octonion(octonion):
    return (
        octonion is not None
        and all(component == 0 for component in octonion)
    )


def quadratic_character(value):
    """
    Legendre quadratic character over F_p.

    Returns:
        0  if value == 0
        1  if value is a non-zero quadratic residue
       -1  otherwise
    """
    value %= P

    if value == 0:
        return 0

    result = pow(
        value,
        (P - 1) // 2,
        P
    )

    if result == 1:
        return 1

    if result == P - 1:
        return -1

    raise RuntimeError(
        "Unexpected quadratic-character result"
    )


def extract_polynomial_coefficients(polynomial):
    """
    HK17.2 stores a polynomial as a list of (coefficient, exponent) pairs.

    Returns coefficients ordered from exponent 0 upward.
    """
    coefficient_by_exponent = {
        int(exponent): int(coefficient)
        for coefficient, exponent in polynomial
    }

    if not coefficient_by_exponent:
        return []

    maximum_exponent = max(
        coefficient_by_exponent
    )

    return [
        coefficient_by_exponent.get(
            exponent,
            0
        )
        for exponent in range(
            maximum_exponent + 1
        )
    ]


# ============================================================================
# CSV FIELD DEFINITIONS
# ============================================================================

fieldnames = [
    "execution",
    "protocol_success",
    "failure_reason",

    "m",
    "n",

    "m_mod_250",
    "n_mod_250",

    "gcd_m_250",
    "gcd_n_250",

    "key_equal",
    "recovered_autoconvolution_equal",
]

# f(x) and h(x) each have 16 coefficients in the definitive configuration.
for i in range(16):
    fieldnames.append(f"f_coefficient_{i}")

for i in range(16):
    fieldnames.append(f"h_coefficient_{i}")


for _, output_name in OCTONION_VARIABLES:

    for component_index in range(8):
        fieldnames.append(
            f"{output_name}_a{component_index}"
        )

    fieldnames.extend(
        [
            f"{output_name}_norm",
            f"{output_name}_invertible",
            f"{output_name}_quadratic_character_norm",
        ]
    )


# Explicit checks for norm behavior under exponentiation.
for relation_index in range(1, 5):

    fieldnames.extend(
        [
            f"power_relation_{relation_index}_input_norm",
            f"power_relation_{relation_index}_exponent",
            f"power_relation_{relation_index}_predicted_output_norm",
            f"power_relation_{relation_index}_actual_output_norm",
            f"power_relation_{relation_index}_norm_identity_holds",
        ]
    )


# ============================================================================
# STATISTICAL ACCUMULATORS
# ============================================================================

component_counts = {
    output_name: [
        Counter()
        for _ in range(8)
    ]
    for _, output_name in OCTONION_VARIABLES
}

component_values = {
    output_name: [
        []
        for _ in range(8)
    ]
    for _, output_name in OCTONION_VARIABLES
}

norm_counts = {
    output_name: Counter()
    for _, output_name in OCTONION_VARIABLES
}

norm_values = {
    output_name: []
    for _, output_name in OCTONION_VARIABLES
}

quadratic_character_counts = {
    output_name: Counter()
    for _, output_name in OCTONION_VARIABLES
}

null_counts = Counter()
noninvertible_counts = Counter()

m_counts = Counter()
n_counts = Counter()

m_mod_counts = Counter()
n_mod_counts = Counter()

gcd_m_counts = Counter()
gcd_n_counts = Counter()

power_norm_identity_failures = [
    0,
    0,
    0,
    0,
]

successful_executions = 0
failed_executions = 0

key_agreement_count = 0
recovered_autoconvolution_agreement_count = 0

failure_reasons = Counter()


# ============================================================================
# POWER-CLASS ACCUMULATORS
#
# We group output components according to gcd(exponent, p-1).
# This will let us test whether the observed power bias depends on the
# algebraic class of the exponent.
# ============================================================================

power_class_component_counts = {
    "alice_power_public_input": defaultdict(
        lambda: [
            Counter()
            for _ in range(8)
        ]
    ),
    "alice_power_shifted_input": defaultdict(
        lambda: [
            Counter()
            for _ in range(8)
        ]
    ),
    "bob_power_public_input": defaultdict(
        lambda: [
            Counter()
            for _ in range(8)
        ]
    ),
    "bob_power_shifted_input": defaultdict(
        lambda: [
            Counter()
            for _ in range(8)
        ]
    ),
}

power_class_sample_counts = {
    key: Counter()
    for key in power_class_component_counts
}


analysis_start = time.perf_counter()


# ============================================================================
# EXPERIMENT
# ============================================================================

print("=" * 100)
print("HK17.2 COMPLETE OCTONION-LAYER SECURITY ANALYSIS")
print("=" * 100)
print("Protocol =", PROTOCOL_FILE)
print("Executions =", EXECUTIONS)
print("Raw CSV =", RAW_CSV)
print("Summary CSV =", SUMMARY_CSV)
print("Power classes CSV =", POWER_CLASSES_CSV)
print("=" * 100)
print()


with open(
    RAW_CSV,
    "w",
    newline="",
    encoding="utf-8"
) as raw_file:

    writer = csv.DictWriter(
        raw_file,
        fieldnames=fieldnames
    )

    writer.writeheader()

    with open(
        os.devnull,
        "w",
        encoding="utf-8"
    ) as devnull:

        for execution in range(
            1,
            EXECUTIONS + 1
        ):

            namespace = {
                "__builtins__": __builtins__,
                "__name__": "__main__",
                "__file__": str(PROTOCOL_FILE),
            }

            protocol_success = True
            failure_reason = ""

            try:

                with (
                    redirect_stdout(devnull),
                    redirect_stderr(devnull)
                ):
                    exec(
                        PROTOCOL_CODE,
                        namespace
                    )

            except Exception as exc:

                protocol_success = False
                failure_reason = (
                    f"{type(exc).__name__}: {exc}"
                )

            if protocol_success:
                successful_executions += 1

            else:
                failed_executions += 1
                failure_reasons[
                    failure_reason
                ] += 1


            row = {
                "execution": execution,
                "protocol_success": protocol_success,
                "failure_reason": failure_reason,
            }


            # ================================================================
            # EXPONENTS
            # ================================================================

            m = namespace.get("m")
            n = namespace.get("n")

            row["m"] = (
                m if m is not None else ""
            )

            row["n"] = (
                n if n is not None else ""
            )

            if m is not None:

                row["m_mod_250"] = (
                    m % P_MINUS_1
                )

                row["gcd_m_250"] = math.gcd(
                    m,
                    P_MINUS_1
                )

                m_counts[m] += 1
                m_mod_counts[
                    m % P_MINUS_1
                ] += 1

                gcd_m_counts[
                    math.gcd(
                        m,
                        P_MINUS_1
                    )
                ] += 1

            else:

                row["m_mod_250"] = ""
                row["gcd_m_250"] = ""


            if n is not None:

                row["n_mod_250"] = (
                    n % P_MINUS_1
                )

                row["gcd_n_250"] = math.gcd(
                    n,
                    P_MINUS_1
                )

                n_counts[n] += 1
                n_mod_counts[
                    n % P_MINUS_1
                ] += 1

                gcd_n_counts[
                    math.gcd(
                        n,
                        P_MINUS_1
                    )
                ] += 1

            else:

                row["n_mod_250"] = ""
                row["gcd_n_250"] = ""


            # ================================================================
            # POLYNOMIAL COEFFICIENTS
            # ================================================================

            f = namespace.get("f")
            h = namespace.get("h")

            f_coefficients = (
                extract_polynomial_coefficients(f)
                if f is not None
                else []
            )

            h_coefficients = (
                extract_polynomial_coefficients(h)
                if h is not None
                else []
            )

            for i in range(16):

                row[f"f_coefficient_{i}"] = (
                    f_coefficients[i]
                    if i < len(f_coefficients)
                    else ""
                )

                row[f"h_coefficient_{i}"] = (
                    h_coefficients[i]
                    if i < len(h_coefficients)
                    else ""
                )


            # ================================================================
            # CORRECTNESS
            # ================================================================

            kA = namespace.get("kA")
            kB = namespace.get("kB")

            key_equal = (
                kA is not None
                and kB is not None
                and kA == kB
            )

            row["key_equal"] = key_equal

            if key_equal:
                key_agreement_count += 1


            f_autoconvolution = namespace.get(
                "f_autoconvolution"
            )

            recovered_f_autoconvolution = namespace.get(
                "recovered_f_autoconvolution"
            )

            recovered_equal = (
                f_autoconvolution is not None
                and
                recovered_f_autoconvolution is not None
                and
                f_autoconvolution
                == recovered_f_autoconvolution
            )

            row[
                "recovered_autoconvolution_equal"
            ] = recovered_equal

            if recovered_equal:
                recovered_autoconvolution_agreement_count += 1


            # ================================================================
            # OCTONION VALUES AND NORMS
            # ================================================================

            values_by_output_name = {}

            for (
                protocol_variable,
                output_name
            ) in OCTONION_VARIABLES:

                octonion = namespace.get(
                    protocol_variable
                )

                values_by_output_name[
                    output_name
                ] = octonion

                if octonion is None:

                    for component_index in range(8):

                        row[
                            f"{output_name}_a"
                            f"{component_index}"
                        ] = ""

                    row[
                        f"{output_name}_norm"
                    ] = ""

                    row[
                        f"{output_name}_invertible"
                    ] = ""

                    row[
                        f"{output_name}_quadratic_character_norm"
                    ] = ""

                    continue


                for component_index in range(8):

                    value = octonion[
                        component_index
                    ]

                    row[
                        f"{output_name}_a"
                        f"{component_index}"
                    ] = value

                    component_counts[
                        output_name
                    ][component_index][value] += 1

                    component_values[
                        output_name
                    ][component_index].append(
                        value
                    )


                norm = octonion_norm_squared(
                    octonion
                )

                invertible = (
                    not is_null_octonion(octonion)
                    and norm != 0
                )

                character = quadratic_character(
                    norm
                )

                row[
                    f"{output_name}_norm"
                ] = norm

                row[
                    f"{output_name}_invertible"
                ] = invertible

                row[
                    f"{output_name}_quadratic_character_norm"
                ] = character


                norm_counts[
                    output_name
                ][norm] += 1

                norm_values[
                    output_name
                ].append(
                    norm
                )

                quadratic_character_counts[
                    output_name
                ][character] += 1


                if is_null_octonion(
                    octonion
                ):
                    null_counts[
                        output_name
                    ] += 1


                if not invertible:

                    noninvertible_counts[
                        output_name
                    ] += 1


            # ================================================================
            # POWER-NORM IDENTITIES
            # ================================================================

            for relation_index, (
                input_name,
                output_name,
                exponent_name
            ) in enumerate(
                POWER_RELATIONS,
                start=1
            ):

                input_octonion = (
                    values_by_output_name.get(
                        input_name
                    )
                )

                output_octonion = (
                    values_by_output_name.get(
                        output_name
                    )
                )

                exponent = namespace.get(
                    exponent_name
                )

                if (
                    input_octonion is None
                    or output_octonion is None
                    or exponent is None
                ):

                    row[
                        f"power_relation_{relation_index}_input_norm"
                    ] = ""

                    row[
                        f"power_relation_{relation_index}_exponent"
                    ] = ""

                    row[
                        f"power_relation_{relation_index}_predicted_output_norm"
                    ] = ""

                    row[
                        f"power_relation_{relation_index}_actual_output_norm"
                    ] = ""

                    row[
                        f"power_relation_{relation_index}_norm_identity_holds"
                    ] = ""

                    continue


                input_norm = (
                    octonion_norm_squared(
                        input_octonion
                    )
                )

                output_norm = (
                    octonion_norm_squared(
                        output_octonion
                    )
                )

                predicted_output_norm = pow(
                    input_norm,
                    exponent,
                    P
                )

                identity_holds = (
                    predicted_output_norm
                    == output_norm
                )

                row[
                    f"power_relation_{relation_index}_input_norm"
                ] = input_norm

                row[
                    f"power_relation_{relation_index}_exponent"
                ] = exponent

                row[
                    f"power_relation_{relation_index}_predicted_output_norm"
                ] = predicted_output_norm

                row[
                    f"power_relation_{relation_index}_actual_output_norm"
                ] = output_norm

                row[
                    f"power_relation_{relation_index}_norm_identity_holds"
                ] = identity_holds


                if not identity_holds:

                    power_norm_identity_failures[
                        relation_index - 1
                    ] += 1


            # ================================================================
            # POWER CLASSES BY gcd(exponent, p-1)
            # ================================================================

            if m is not None:

                gcd_m = math.gcd(
                    m,
                    P_MINUS_1
                )

                for output_name in [
                    "alice_power_public_input",
                    "alice_power_shifted_input",
                ]:

                    octonion = (
                        values_by_output_name.get(
                            output_name
                        )
                    )

                    if octonion is not None:

                        power_class_sample_counts[
                            output_name
                        ][gcd_m] += 1

                        for component_index in range(8):

                            power_class_component_counts[
                                output_name
                            ][gcd_m][
                                component_index
                            ][
                                octonion[
                                    component_index
                                ]
                            ] += 1


            if n is not None:

                gcd_n = math.gcd(
                    n,
                    P_MINUS_1
                )

                for output_name in [
                    "bob_power_public_input",
                    "bob_power_shifted_input",
                ]:

                    octonion = (
                        values_by_output_name.get(
                            output_name
                        )
                    )

                    if octonion is not None:

                        power_class_sample_counts[
                            output_name
                        ][gcd_n] += 1

                        for component_index in range(8):

                            power_class_component_counts[
                                output_name
                            ][gcd_n][
                                component_index
                            ][
                                octonion[
                                    component_index
                                ]
                            ] += 1


            writer.writerow(row)


            # ================================================================
            # PROGRESS
            # ================================================================

            if (
                execution
                % PROGRESS_INTERVAL
                == 0
            ):

                raw_file.flush()

                elapsed = (
                    time.perf_counter()
                    - analysis_start
                )

                print(
                    f"[{execution:05d}/{EXECUTIONS}] "
                    f"success={successful_executions} "
                    f"failures={failed_executions} "
                    f"key_agreements="
                    f"{key_agreement_count} "
                    f"recovered_F="
                    f"{recovered_autoconvolution_agreement_count} "
                    f"elapsed={elapsed:.2f}s"
                )


# ============================================================================
# SUMMARY CSV
# ============================================================================

summary_rows = []


def add_summary(
    category,
    variable,
    component,
    metric,
    value
):

    summary_rows.append(
        {
            "category": category,
            "variable": variable,
            "component": component,
            "metric": metric,
            "value": value,
        }
    )


# ============================================================================
# GENERAL
# ============================================================================

add_summary(
    "general",
    "",
    "",
    "executions_requested",
    EXECUTIONS
)

add_summary(
    "general",
    "",
    "",
    "successful_executions",
    successful_executions
)

add_summary(
    "general",
    "",
    "",
    "failed_executions",
    failed_executions
)

add_summary(
    "general",
    "",
    "",
    "key_agreement_count",
    key_agreement_count
)

add_summary(
    "general",
    "",
    "",
    "key_agreement_rate",
    key_agreement_count / EXECUTIONS
)

add_summary(
    "general",
    "",
    "",
    "recovered_autoconvolution_agreement_count",
    recovered_autoconvolution_agreement_count
)

add_summary(
    "general",
    "",
    "",
    "recovered_autoconvolution_agreement_rate",
    recovered_autoconvolution_agreement_count
    / EXECUTIONS
)


# ============================================================================
# EXPONENT STATISTICS
# ============================================================================

for exponent_name, counts in [
    ("m", m_counts),
    ("n", n_counts),
]:

    add_summary(
        "exponent",
        exponent_name,
        "",
        "distinct_values",
        len(counts)
    )

    add_summary(
        "exponent",
        exponent_name,
        "",
        "entropy_bits",
        empirical_entropy(
            counts,
            sum(counts.values())
        )
    )


for exponent_name, counts in [
    ("m_mod_250", m_mod_counts),
    ("n_mod_250", n_mod_counts),
]:

    add_summary(
        "exponent",
        exponent_name,
        "",
        "distinct_values",
        len(counts)
    )

    add_summary(
        "exponent",
        exponent_name,
        "",
        "entropy_bits",
        empirical_entropy(
            counts,
            sum(counts.values())
        )
    )


for gcd_value, count in sorted(
    gcd_m_counts.items()
):

    add_summary(
        "exponent_gcd",
        "m",
        gcd_value,
        "count",
        count
    )

    add_summary(
        "exponent_gcd",
        "m",
        gcd_value,
        "rate",
        count / EXECUTIONS
    )


for gcd_value, count in sorted(
    gcd_n_counts.items()
):

    add_summary(
        "exponent_gcd",
        "n",
        gcd_value,
        "count",
        count
    )

    add_summary(
        "exponent_gcd",
        "n",
        gcd_value,
        "rate",
        count / EXECUTIONS
    )


# ============================================================================
# OCTONION STATISTICS
# ============================================================================

maximum_component_entropy = math.log2(
    P
)

for _, output_name in OCTONION_VARIABLES:

    add_summary(
        "octonion",
        output_name,
        "",
        "null_octonion_count",
        null_counts.get(
            output_name,
            0
        )
    )

    add_summary(
        "octonion",
        output_name,
        "",
        "noninvertible_count",
        noninvertible_counts.get(
            output_name,
            0
        )
    )

    add_summary(
        "octonion",
        output_name,
        "",
        "noninvertible_rate",
        noninvertible_counts.get(
            output_name,
            0
        ) / EXECUTIONS
    )


    entropies = []
    chi_squares = []


    for component_index in range(8):

        values = component_values[
            output_name
        ][component_index]

        counts = component_counts[
            output_name
        ][component_index]

        total = len(values)

        entropy = empirical_entropy(
            counts,
            total
        )

        chi_square = chi_square_uniform(
            counts,
            P,
            total
        )

        entropies.append(
            entropy
        )

        chi_squares.append(
            chi_square
        )


        add_summary(
            "component",
            output_name,
            component_index,
            "samples",
            total
        )

        add_summary(
            "component",
            output_name,
            component_index,
            "mean",
            mean(values)
        )

        add_summary(
            "component",
            output_name,
            component_index,
            "distinct_values",
            len(counts)
        )

        add_summary(
            "component",
            output_name,
            component_index,
            "entropy_bits",
            entropy
        )

        add_summary(
            "component",
            output_name,
            component_index,
            "maximum_uniform_entropy_bits",
            maximum_component_entropy
        )

        add_summary(
            "component",
            output_name,
            component_index,
            "chi_square_uniform",
            chi_square
        )

        add_summary(
            "component",
            output_name,
            component_index,
            "chi_square_df",
            P - 1
        )


    add_summary(
        "octonion",
        output_name,
        "",
        "mean_component_entropy_bits",
        mean(entropies)
    )

    add_summary(
        "octonion",
        output_name,
        "",
        "minimum_component_entropy_bits",
        min(entropies)
    )

    add_summary(
        "octonion",
        output_name,
        "",
        "maximum_component_entropy_bits",
        max(entropies)
    )

    add_summary(
        "octonion",
        output_name,
        "",
        "mean_component_chi_square",
        mean(chi_squares)
    )


    # ------------------------------------------------------------------------
    # NORM
    # ------------------------------------------------------------------------

    norms = norm_values[
        output_name
    ]

    norm_counter = norm_counts[
        output_name
    ]

    add_summary(
        "norm",
        output_name,
        "",
        "distinct_norm_values",
        len(norm_counter)
    )

    add_summary(
        "norm",
        output_name,
        "",
        "mean",
        mean(norms)
    )

    add_summary(
        "norm",
        output_name,
        "",
        "entropy_bits",
        empirical_entropy(
            norm_counter,
            len(norms)
        )
    )

    add_summary(
        "norm",
        output_name,
        "",
        "chi_square_uniform",
        chi_square_uniform(
            norm_counter,
            P,
            len(norms)
        )
    )

    add_summary(
        "norm",
        output_name,
        "",
        "chi_square_df",
        P - 1
    )


    for character in [
        -1,
        0,
        1
    ]:

        count = (
            quadratic_character_counts[
                output_name
            ].get(
                character,
                0
            )
        )

        add_summary(
            "quadratic_character",
            output_name,
            character,
            "count",
            count
        )

        add_summary(
            "quadratic_character",
            output_name,
            character,
            "rate",
            count / EXECUTIONS
        )


    # ------------------------------------------------------------------------
    # COMPONENT CORRELATIONS
    # ------------------------------------------------------------------------

    correlations = []

    for i in range(8):
        for j in range(
            i + 1,
            8
        ):

            rho = pearson_correlation(
                component_values[
                    output_name
                ][i],
                component_values[
                    output_name
                ][j]
            )

            correlations.append(
                (
                    abs(rho),
                    rho,
                    i,
                    j
                )
            )

            add_summary(
                "correlation",
                output_name,
                f"{i}-{j}",
                "pearson_correlation",
                rho
            )


    correlations.sort(
        reverse=True
    )

    if correlations:

        absolute_rho, rho, i, j = (
            correlations[0]
        )

        add_summary(
            "octonion",
            output_name,
            "",
            "maximum_absolute_pairwise_correlation",
            absolute_rho
        )

        add_summary(
            "octonion",
            output_name,
            "",
            "maximum_correlation_pair",
            f"a{i}-a{j}"
        )

        add_summary(
            "octonion",
            output_name,
            "",
            "maximum_correlation_signed_value",
            rho
        )


# ============================================================================
# POWER NORM IDENTITIES
# ============================================================================

for relation_index, failures in enumerate(
    power_norm_identity_failures,
    start=1
):

    add_summary(
        "power_norm_identity",
        f"relation_{relation_index}",
        "",
        "failure_count",
        failures
    )

    add_summary(
        "power_norm_identity",
        f"relation_{relation_index}",
        "",
        "success_rate",
        (
            EXECUTIONS - failures
        ) / EXECUTIONS
    )


# ============================================================================
# FAILURE REASONS
# ============================================================================

for failure_reason, count in sorted(
    failure_reasons.items()
):

    add_summary(
        "failure",
        "",
        "",
        failure_reason,
        count
    )


# ============================================================================
# TOTAL TIME
# ============================================================================

analysis_time = (
    time.perf_counter()
    - analysis_start
)

add_summary(
    "general",
    "",
    "",
    "total_analysis_time_s",
    analysis_time
)


# ============================================================================
# WRITE SUMMARY CSV
# ============================================================================

with open(
    SUMMARY_CSV,
    "w",
    newline="",
    encoding="utf-8"
) as summary_file:

    writer = csv.DictWriter(
        summary_file,
        fieldnames=[
            "category",
            "variable",
            "component",
            "metric",
            "value",
        ]
    )

    writer.writeheader()
    writer.writerows(
        summary_rows
    )


# ============================================================================
# POWER CLASS ANALYSIS
# ============================================================================

with open(
    POWER_CLASSES_CSV,
    "w",
    newline="",
    encoding="utf-8"
) as power_file:

    writer = csv.writer(
        power_file
    )

    writer.writerow(
        [
            "variable",
            "gcd_exponent_250",
            "samples",
            "component",
            "distinct_values",
            "entropy_bits",
            "chi_square_uniform",
            "chi_square_df",
        ]
    )


    for output_name in (
        power_class_component_counts
    ):

        gcd_classes = sorted(
            power_class_component_counts[
                output_name
            ].keys()
        )

        for gcd_value in gcd_classes:

            samples = (
                power_class_sample_counts[
                    output_name
                ][gcd_value]
            )

            for component_index in range(8):

                counts = (
                    power_class_component_counts[
                        output_name
                    ][gcd_value][
                        component_index
                    ]
                )

                writer.writerow(
                    [
                        output_name,
                        gcd_value,
                        samples,
                        component_index,
                        len(counts),
                        empirical_entropy(
                            counts,
                            samples
                        ),
                        chi_square_uniform(
                            counts,
                            P,
                            samples
                        ),
                        P - 1,
                    ]
                )


# ============================================================================
# TERMINAL SUMMARY
# ============================================================================

print()
print("=" * 100)
print("COMPLETE OCTONION-LAYER ANALYSIS FINISHED")
print("=" * 100)

print(
    "Successful executions =",
    successful_executions
)

print(
    "Failed executions =",
    failed_executions
)

print(
    "Key agreements =",
    key_agreement_count
)

print(
    "Recovered Alice autoconvolutions =",
    recovered_autoconvolution_agreement_count
)

print()

print("Exponent gcd classes for m:")
for gcd_value, count in sorted(
    gcd_m_counts.items()
):
    print(
        f"  gcd(m, 250) = {gcd_value}: "
        f"{count}"
    )

print()

print("Exponent gcd classes for n:")
for gcd_value, count in sorted(
    gcd_n_counts.items()
):
    print(
        f"  gcd(n, 250) = {gcd_value}: "
        f"{count}"
    )

print()

print(
    f"{'Variable':<44}"
    f"{'Entropy':>12}"
    f"{'Norm H':>12}"
    f"{'Noninv':>10}"
    f"{'Max |rho|':>14}"
)

print("-" * 95)


for _, output_name in OCTONION_VARIABLES:

    entropies = []

    for component_index in range(8):

        counts = component_counts[
            output_name
        ][component_index]

        entropies.append(
            empirical_entropy(
                counts,
                sum(counts.values())
            )
        )


    norm_entropy = empirical_entropy(
        norm_counts[
            output_name
        ],
        len(
            norm_values[
                output_name
            ]
        )
    )


    correlations = []

    for i in range(8):
        for j in range(
            i + 1,
            8
        ):

            rho = pearson_correlation(
                component_values[
                    output_name
                ][i],
                component_values[
                    output_name
                ][j]
            )

            correlations.append(
                abs(rho)
            )


    max_rho = (
        max(correlations)
        if correlations
        else 0.0
    )


    print(
        f"{output_name:<44}"
        f"{mean(entropies):>12.6f}"
        f"{norm_entropy:>12.6f}"
        f"{noninvertible_counts.get(output_name, 0):>10}"
        f"{max_rho:>14.6f}"
    )


print()

for relation_index, failures in enumerate(
    power_norm_identity_failures,
    start=1
):

    print(
        f"Power norm relation {relation_index}: "
        f"{EXECUTIONS - failures}/{EXECUTIONS} "
        f"verified"
    )


print()

print(
    "Maximum theoretical component entropy =",
    math.log2(P)
)

print(
    "Total analysis time =",
    f"{analysis_time:.3f} s"
)

print()

print("Generated files:")
print(RAW_CSV)
print(SUMMARY_CSV)
print(POWER_CLASSES_CSV)