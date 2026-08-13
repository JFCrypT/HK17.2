import csv
import math
from collections import Counter
from pathlib import Path
from statistics import mean, median
import sys


# ============================================================================
# CONFIGURATION
# ============================================================================

P = 251
Q = 16

OCTONION_DIMENSION = 8
OCTONION_POLYNOMIAL_COEFFICIENTS = 16
MATRIX_POLYNOMIAL_COEFFICIENTS = 32

MIN_PRIVATE_EXPONENT = 2
MAX_PRIVATE_EXPONENT = 256

EXPONENT_CHOICES = (
    MAX_PRIVATE_EXPONENT
    - MIN_PRIVATE_EXPONENT
    + 1
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GENERAL_DIR = PROJECT_ROOT / "general"
SECURITY_DIR = Path(__file__).resolve().parent

INPUT_CSV = (
    SECURITY_DIR
    / "octonion_layer_full.csv"
)

EXPONENT_DIVERSITY_CSV = (
    SECURITY_DIR
    / "exponent_diversity.csv"
)

KEYSPACE_SUMMARY_CSV = (
    SECURITY_DIR
    / "keyspace_summary.csv"
)


# ============================================================================
# IMPORT UNIQUE OCTONION IMPLEMENTATION
# ============================================================================

if str(GENERAL_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(GENERAL_DIR)
    )

from octonions import multiply


# ============================================================================
# CONSTANTS
# ============================================================================

UNIT_OCTONION = (
    1, 0, 0, 0,
    0, 0, 0, 0
)

NULL_OCTONION = (
    0, 0, 0, 0,
    0, 0, 0, 0
)


# ============================================================================
# VARIABLES WHOSE POWERS ARE USED BY HK17.2
# ============================================================================

POWER_BASES = [
    {
        "name": "alice_public_input",
        "prefix": "alice_polynomial_public_input",
        "powered_prefix": "alice_power_public_input",
        "exponent": "m",
    },
    {
        "name": "alice_shifted_input",
        "prefix": "alice_polynomial_shifted_input",
        "powered_prefix": "alice_power_shifted_input",
        "exponent": "m",
    },
    {
        "name": "bob_public_input",
        "prefix": "bob_polynomial_public_input",
        "powered_prefix": "bob_power_public_input",
        "exponent": "n",
    },
    {
        "name": "bob_shifted_input",
        "prefix": "bob_polynomial_shifted_input",
        "powered_prefix": "bob_power_shifted_input",
        "exponent": "n",
    },
]


# ============================================================================
# AUXILIARY FUNCTIONS
# ============================================================================

def read_octonion(row, prefix):
    return tuple(
        int(
            row[
                f"{prefix}_a{i}"
            ]
        )
        for i in range(8)
    )


def log2_integer(value):
    return math.log2(value)


def power_diversity(base):
    """
    Computes exactly the powers used by the protocol:

        base^2, base^3, ..., base^256

    with the same left-associated multiplication used by
    general/octonions.py.

    Returns:
        powers_by_exponent
        first_repeat_exponent
    """

    current = base

    powers_by_exponent = {}

    seen = {}

    first_repeat_exponent = None

    for exponent in range(
        2,
        MAX_PRIVATE_EXPONENT + 1
    ):

        current = multiply(
            current,
            base,
            P
        )

        powers_by_exponent[
            exponent
        ] = current

        if (
            current in seen
            and
            first_repeat_exponent
            is None
        ):
            first_repeat_exponent = (
                exponent
            )

        if current not in seen:
            seen[current] = exponent

    return (
        powers_by_exponent,
        first_repeat_exponent
    )


# ============================================================================
# LOAD DATA
# ============================================================================

rows = []

with open(
    INPUT_CSV,
    "r",
    encoding="utf-8",
    newline=""
) as input_file:

    reader = csv.DictReader(
        input_file
    )

    for row in reader:
        rows.append(row)


executions = len(rows)


# ============================================================================
# EXPONENT-DIVERSITY ACCUMULATORS
# ============================================================================

distinct_counts = {
    item["name"]: []
    for item in POWER_BASES
}

collision_counts = {
    item["name"]: []
    for item in POWER_BASES
}

chosen_multiplicities = {
    item["name"]: []
    for item in POWER_BASES
}

unit_counts = Counter()
null_counts = Counter()

first_repeat_counts = Counter()

validation_failures = Counter()

full_distinct_count = Counter()

session_keys = Counter()


# ============================================================================
# OUTPUT HEADER
# ============================================================================

fieldnames = [
    "execution",
    "base",
    "private_exponent",
    "gcd_exponent_250",
    "distinct_power_outputs",
    "collision_count",
    "effective_exponent_bits",
    "first_repeat_exponent",
    "unit_power_count",
    "null_power_count",
    "chosen_output_multiplicity",
    "chosen_output_unique",
    "stored_power_validation",
]


# ============================================================================
# ANALYSIS
# ============================================================================

print("=" * 100)
print("HK17.2 KEY-SPACE AND EXPONENT-DIVERSITY ANALYSIS")
print("=" * 100)
print("Input =", INPUT_CSV)
print("Executions =", executions)
print(
    "Exponent range =",
    f"{MIN_PRIVATE_EXPONENT}..{MAX_PRIVATE_EXPONENT}"
)
print(
    "Exponent choices =",
    EXPONENT_CHOICES
)
print("=" * 100)
print()


with open(
    EXPONENT_DIVERSITY_CSV,
    "w",
    encoding="utf-8",
    newline=""
) as output_file:

    writer = csv.DictWriter(
        output_file,
        fieldnames=fieldnames
    )

    writer.writeheader()


    for execution_index, row in enumerate(
        rows,
        start=1
    ):

        # ================================================================
        # SESSION KEY COLLISION ANALYSIS
        # ================================================================

        session_key = read_octonion(
            row,
            "alice_session_key"
        )

        session_keys[
            session_key
        ] += 1


        # ================================================================
        # FOUR POWER BASES
        # ================================================================

        for item in POWER_BASES:

            name = item["name"]

            base = read_octonion(
                row,
                item["prefix"]
            )

            stored_power = read_octonion(
                row,
                item["powered_prefix"]
            )

            private_exponent = int(
                row[
                    item["exponent"]
                ]
            )

            (
                powers_by_exponent,
                first_repeat_exponent
            ) = power_diversity(
                base
            )

            outputs = list(
                powers_by_exponent.values()
            )

            output_counter = Counter(
                outputs
            )

            distinct = len(
                output_counter
            )

            collisions = (
                EXPONENT_CHOICES
                - distinct
            )

            chosen_output = (
                powers_by_exponent[
                    private_exponent
                ]
            )

            chosen_multiplicity = (
                output_counter[
                    chosen_output
                ]
            )

            unit_power_count = (
                output_counter.get(
                    UNIT_OCTONION,
                    0
                )
            )

            null_power_count = (
                output_counter.get(
                    NULL_OCTONION,
                    0
                )
            )

            validation = (
                chosen_output
                == stored_power
            )

            if not validation:
                validation_failures[
                    name
                ] += 1


            distinct_counts[
                name
            ].append(
                distinct
            )

            collision_counts[
                name
            ].append(
                collisions
            )

            chosen_multiplicities[
                name
            ].append(
                chosen_multiplicity
            )

            unit_counts[
                name
            ] += unit_power_count

            null_counts[
                name
            ] += null_power_count

            if first_repeat_exponent is not None:

                first_repeat_counts[
                    name
                ] += 1


            if distinct == EXPONENT_CHOICES:

                full_distinct_count[
                    name
                ] += 1


            writer.writerow(
                {
                    "execution":
                        execution_index,

                    "base":
                        name,

                    "private_exponent":
                        private_exponent,

                    "gcd_exponent_250":
                        math.gcd(
                            private_exponent,
                            P - 1
                        ),

                    "distinct_power_outputs":
                        distinct,

                    "collision_count":
                        collisions,

                    "effective_exponent_bits":
                        math.log2(
                            distinct
                        ),

                    "first_repeat_exponent":
                        (
                            first_repeat_exponent
                            if
                            first_repeat_exponent
                            is not None
                            else ""
                        ),

                    "unit_power_count":
                        unit_power_count,

                    "null_power_count":
                        null_power_count,

                    "chosen_output_multiplicity":
                        chosen_multiplicity,

                    "chosen_output_unique":
                        (
                            chosen_multiplicity
                            == 1
                        ),

                    "stored_power_validation":
                        validation,
                }
            )


        if execution_index % 100 == 0:

            print(
                f"[{execution_index:05d}/"
                f"{executions}]"
            )


# ============================================================================
# EXACT NOMINAL CARDINALITIES OF THE CURRENT IMPLEMENTATION
# ============================================================================

# obtainPolynomial() draws every coefficient from 1,...,modulus-1.

octonion_polynomial_space = (
    (P - 1)
    ** OCTONION_POLYNOMIAL_COEFFICIENTS
)

matrix_polynomial_space = (
    (Q - 1)
    ** MATRIX_POLYNOMIAL_COEFFICIENTS
)

secret_displacement_space = (
    P
    ** OCTONION_DIMENSION
)

private_exponent_space = (
    EXPONENT_CHOICES
)

# Nominal private configuration space for one participant:
#
# matrix polynomial
# octonion polynomial
# secret displacement
# private exponent

per_party_private_configuration_space = (
    matrix_polynomial_space
    * octonion_polynomial_space
    * secret_displacement_space
    * private_exponent_space
)

joint_private_configuration_space = (
    per_party_private_configuration_space
    ** 2
)


# ============================================================================
# ATTACK-RELEVANT UPPER / NOMINAL SPACES
# ============================================================================

cayley_hamilton_coefficient_space = (
    Q
    ** MATRIX_POLYNOMIAL_COEFFICIENTS
)

maximum_session_key_space = (
    P
    ** OCTONION_DIMENSION
    - 1
)


# ============================================================================
# SESSION-KEY EMPIRICAL COLLISIONS
# ============================================================================

distinct_session_keys = len(
    session_keys
)

session_key_collision_samples = (
    executions
    - distinct_session_keys
)

maximum_session_key_multiplicity = (
    max(
        session_keys.values()
    )
    if session_keys
    else 0
)


# ============================================================================
# SUMMARY
# ============================================================================

summary = []


def add(metric, value):
    summary.append(
        (
            metric,
            value
        )
    )


add(
    "executions",
    executions
)

add(
    "p",
    P
)

add(
    "q",
    Q
)

add(
    "private_exponent_min",
    MIN_PRIVATE_EXPONENT
)

add(
    "private_exponent_max",
    MAX_PRIVATE_EXPONENT
)

add(
    "private_exponent_choices",
    private_exponent_space
)

add(
    "private_exponent_nominal_bits",
    log2_integer(
        private_exponent_space
    )
)


# --------------------------------------------------------------------------
# OCTONION POLYNOMIAL SPACE
# --------------------------------------------------------------------------

add(
    "octonion_polynomial_space",
    octonion_polynomial_space
)

add(
    "octonion_polynomial_space_bits",
    log2_integer(
        octonion_polynomial_space
    )
)


# --------------------------------------------------------------------------
# MATRIX POLYNOMIAL SPACE
# --------------------------------------------------------------------------

add(
    "matrix_polynomial_space",
    matrix_polynomial_space
)

add(
    "matrix_polynomial_space_bits",
    log2_integer(
        matrix_polynomial_space
    )
)


# --------------------------------------------------------------------------
# SECRET DISPLACEMENT
# --------------------------------------------------------------------------

add(
    "secret_displacement_space",
    secret_displacement_space
)

add(
    "secret_displacement_space_bits",
    log2_integer(
        secret_displacement_space
    )
)


# --------------------------------------------------------------------------
# NOMINAL PRIVATE CONFIGURATION
# --------------------------------------------------------------------------

add(
    "per_party_nominal_private_configuration_space",
    per_party_private_configuration_space
)

add(
    "per_party_nominal_private_configuration_bits",
    log2_integer(
        per_party_private_configuration_space
    )
)

add(
    "joint_nominal_private_configuration_space",
    joint_private_configuration_space
)

add(
    "joint_nominal_private_configuration_bits",
    log2_integer(
        joint_private_configuration_space
    )
)


# --------------------------------------------------------------------------
# MATRIX RECOVERY SPACES
# --------------------------------------------------------------------------

add(
    "cayley_hamilton_coefficient_space",
    cayley_hamilton_coefficient_space
)

add(
    "cayley_hamilton_coefficient_space_bits",
    log2_integer(
        cayley_hamilton_coefficient_space
    )
)


# --------------------------------------------------------------------------
# SESSION KEY
# --------------------------------------------------------------------------

add(
    "maximum_session_key_space",
    maximum_session_key_space
)

add(
    "maximum_session_key_space_bits",
    log2_integer(
        maximum_session_key_space
    )
)

add(
    "empirical_distinct_session_keys",
    distinct_session_keys
)

add(
    "empirical_session_key_collision_samples",
    session_key_collision_samples
)

add(
    "maximum_empirical_session_key_multiplicity",
    maximum_session_key_multiplicity
)


# --------------------------------------------------------------------------
# EXPONENT DIVERSITY
# --------------------------------------------------------------------------

for item in POWER_BASES:

    name = item["name"]

    values = distinct_counts[
        name
    ]

    collisions = collision_counts[
        name
    ]

    multiplicities = (
        chosen_multiplicities[
            name
        ]
    )


    add(
        f"{name}_mean_distinct_power_outputs",
        mean(values)
    )

    add(
        f"{name}_median_distinct_power_outputs",
        median(values)
    )

    add(
        f"{name}_minimum_distinct_power_outputs",
        min(values)
    )

    add(
        f"{name}_maximum_distinct_power_outputs",
        max(values)
    )

    add(
        f"{name}_mean_effective_exponent_bits",
        mean(
            math.log2(value)
            for value in values
        )
    )

    add(
        f"{name}_full_255_distinct_count",
        full_distinct_count[
            name
        ]
    )

    add(
        f"{name}_full_255_distinct_rate",
        (
            full_distinct_count[
                name
            ]
            / executions
        )
    )

    add(
        f"{name}_mean_collision_count",
        mean(collisions)
    )

    add(
        f"{name}_executions_with_repeat",
        first_repeat_counts[
            name
        ]
    )

    add(
        f"{name}_executions_with_repeat_rate",
        (
            first_repeat_counts[
                name
            ]
            / executions
        )
    )

    add(
        f"{name}_mean_chosen_output_multiplicity",
        mean(multiplicities)
    )

    add(
        f"{name}_maximum_chosen_output_multiplicity",
        max(multiplicities)
    )

    add(
        f"{name}_unit_occurrences_in_allowed_power_range",
        unit_counts[
            name
        ]
    )

    add(
        f"{name}_null_occurrences_in_allowed_power_range",
        null_counts[
            name
        ]
    )

    add(
        f"{name}_stored_power_validation_failures",
        validation_failures[
            name
        ]
    )


# ============================================================================
# WRITE SUMMARY CSV
# ============================================================================

with open(
    KEYSPACE_SUMMARY_CSV,
    "w",
    encoding="utf-8",
    newline=""
) as output_file:

    writer = csv.writer(
        output_file
    )

    writer.writerow(
        [
            "metric",
            "value",
        ]
    )

    writer.writerows(
        summary
    )


# ============================================================================
# TERMINAL OUTPUT
# ============================================================================

print()
print("=" * 100)
print("ANALYSIS COMPLETED")
print("=" * 100)

print()
print("NOMINAL SPACES")
print("-" * 100)

print(
    "Octonion polynomial space bits =",
    log2_integer(
        octonion_polynomial_space
    )
)

print(
    "Matrix polynomial space bits =",
    log2_integer(
        matrix_polynomial_space
    )
)

print(
    "Secret displacement space bits =",
    log2_integer(
        secret_displacement_space
    )
)

print(
    "Private exponent space bits =",
    log2_integer(
        private_exponent_space
    )
)

print(
    "Per-party nominal private configuration bits =",
    log2_integer(
        per_party_private_configuration_space
    )
)

print(
    "Joint nominal private configuration bits =",
    log2_integer(
        joint_private_configuration_space
    )
)


print()
print("ATTACK-RELEVANT SPACES")
print("-" * 100)

print(
    "Cayley-Hamilton coefficient space bits =",
    log2_integer(
        cayley_hamilton_coefficient_space
    )
)

print(
    "Maximum session-key space bits =",
    log2_integer(
        maximum_session_key_space
    )
)


print()
print("EMPIRICAL SESSION KEYS")
print("-" * 100)

print(
    "Distinct session keys =",
    distinct_session_keys,
    "/",
    executions
)

print(
    "Collision samples =",
    session_key_collision_samples
)


print()
print("EXPONENT DIVERSITY")
print("-" * 100)

for item in POWER_BASES:

    name = item["name"]

    values = distinct_counts[
        name
    ]

    print()
    print(name)

    print(
        "  mean distinct outputs =",
        mean(values)
    )

    print(
        "  median distinct outputs =",
        median(values)
    )

    print(
        "  min/max =",
        min(values),
        "/",
        max(values)
    )

    print(
        "  mean effective exponent bits =",
        mean(
            math.log2(value)
            for value in values
        )
    )

    print(
        "  full 255 distinct =",
        full_distinct_count[
            name
        ],
        "/",
        executions
    )


print()
print("Generated files:")
print(EXPONENT_DIVERSITY_CSV)
print(KEYSPACE_SUMMARY_CSV)