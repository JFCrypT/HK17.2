import argparse
import json
import random as randomlib
from pathlib import Path

# This generator is retained only for provenance/reconstruction.
# The five canonical JSON vectors in this repository are frozen and must not be
# regenerated during normal validation. Use --force only if intentionally
# establishing a new canonical vector set.

from vector_core import (
    O_NULL,
    calculate_f,
    calculate_matrix_polynomial,
    generate_octonion_candidates,
    matrix_multiply,
    matrix_power,
    octonionrecip,
    power,
    multiply,
    scale,
    summ,
    jsonable,
)

MODULI_AND_START_SEEDS = (
    (13, 130013),
    (251, 251251),
    (65521, 6552165521),
    (4294967279, 4294967279),
    (18446744073709551557, 18446744073709551557),
)


def parameters_for(modulo):
    if modulo == 13:
        degree, component_bits = 8, 4
    elif modulo == 251:
        degree, component_bits = 16, 8
    elif modulo == 65521:
        degree, component_bits = 32, 16
    elif modulo == 4294967279:
        degree, component_bits = 64, 32
    elif modulo == 18446744073709551557:
        degree, component_bits = 128, 64
    else:
        raise ValueError('Unsupported canonical modulus')

    matrix_dimension = 32
    matrix_degree = 32
    matrix_component_bits = component_bits // 2
    matrix_modulo = 2 ** matrix_component_bits
    return {
        'modulo': modulo,
        'powers': 257,
        'degree': degree,
        'component_bits': component_bits,
        'matrix_dimension': matrix_dimension,
        'matrix_degree': matrix_degree,
        'matrix_component_bits': matrix_component_bits,
        'matrix_modulo': matrix_modulo,
        'submatrix_grid_dimension': 4,
        'submatrix_dimension': 8,
    }


def obtain_polynomial(grade, modulo, rng):
    return tuple((rng.randrange(1, modulo), exponent) for exponent in range(grade - 1, -1, -1))


def matrix_random(dimension, modulo, rng):
    return tuple(tuple(rng.randrange(modulo) for _ in range(dimension)) for _ in range(dimension))


def build(modulo, seed):
    p = parameters_for(modulo)
    rng = randomlib.Random(seed)
    powers = p['powers']
    dim = p['matrix_dimension']
    q = p['matrix_modulo']

    u = rng.randrange(2, powers)
    v = rng.randrange(2, powers)
    oA = O_NULL
    while oA == O_NULL:
        oA = tuple(rng.randrange(modulo) for _ in range(8))
    m = rng.randrange(2, powers)
    n = rng.randrange(2, powers)
    f = obtain_polynomial(p['degree'], modulo, rng)
    h = obtain_polynomial(p['degree'], modulo, rng)
    g = obtain_polynomial(p['matrix_degree'], q, rng)
    j = obtain_polynomial(p['matrix_degree'], q, rng)
    A = matrix_random(dim, q, rng)
    B = matrix_random(dim, q, rng)

    G = calculate_matrix_polynomial(A, g, dim, q)
    J = calculate_matrix_polynomial(A, j, dim, q)
    G_u = matrix_power(G, u, dim, q)
    G_v = matrix_power(G, v, dim, q)
    J_u = matrix_power(J, u, dim, q)
    J_v = matrix_power(J, v, dim, q)
    TA = matrix_multiply(matrix_multiply(G_u, B, dim, q), G_v, dim, q)
    TB = matrix_multiply(matrix_multiply(J_u, B, dim, q), J_v, dim, q)
    MA = matrix_multiply(matrix_multiply(G_u, TB, dim, q), G_v, dim, q)
    MB = matrix_multiply(matrix_multiply(J_u, TA, dim, q), J_v, dim, q)
    if MA != MB:
        raise ValueError('Matrix exchange failure')

    sums, candidates = generate_octonion_candidates(MA, modulo, 4, 8)
    selected = next((idx for idx, c in enumerate(candidates, 1) if c['invertible']), None)
    if selected is None:
        raise ValueError('No invertible oB candidate')
    oB = candidates[selected - 1]['octonion']
    oB_inverse = octonionrecip(oB, modulo)

    oS1 = tuple(rng.randrange(modulo) for _ in range(8))
    neg1 = summ(scale(oA, -1, modulo), oS1, modulo)
    f_oA = calculate_f(oA, f, modulo)
    f_neg = calculate_f(neg1, f, modulo)
    f1 = power(f_oA, m, modulo)
    f2 = power(f_neg, m, modulo)
    f_auto = multiply(f1, f2, modulo)
    rA = multiply(f_auto, oB, modulo)

    oS2 = tuple(rng.randrange(modulo) for _ in range(8))
    neg2 = summ(scale(oA, -1, modulo), oS2, modulo)
    h_oA = calculate_f(oA, h, modulo)
    h_neg = calculate_f(neg2, h, modulo)
    h1 = power(h_oA, n, modulo)
    h2 = power(h_neg, n, modulo)
    h_auto = multiply(h1, h2, modulo)
    rB = multiply(h_auto, oB, modulo)
    kA = multiply(f_auto, rB, modulo)
    recovered = multiply(rA, oB_inverse, modulo)
    kB = multiply(recovered, rB, modulo)
    if kA != kB:
        raise ValueError('Key mismatch')

    return jsonable({
        'metadata': {
            'name': f'test_vector_p{modulo}',
            'seed': seed,
            'source': 'deterministic reconstruction of frozen HK17.2 semantics',
            'note': 'Seed is generation provenance only and is not used by normal validation.',
            'format': 'HK17.2 canonical test vector JSON v1',
            'status': 'candidate-regenerated',
            'seed_role': 'generation provenance only; not used by normal validation',
        },
        'parameters': p,
        'inputs': {
            'u': u, 'v': v, 'oA': oA, 'm': m, 'n': n,
            'f': f, 'h': h, 'g': g, 'j': j, 'A': A, 'B': B,
            'oS1': oS1, 'oS2': oS2,
        },
        'expected': {
            'G': G, 'J': J, 'G_u': G_u, 'G_v': G_v, 'J_u': J_u, 'J_v': J_v,
            'TA': TA, 'TB': TB, 'MA': MA, 'MB': MB, 'M': MA,
            'submatrix_sums': sums, 'oB_candidates': candidates,
            'selected_oB_configuration': selected, 'oB': oB, 'oB_inverse': oB_inverse,
            'negative_oA_plus_oS1': neg1, 'negative_oA_plus_oS2': neg2,
            'f_oA': f_oA, 'f_negative_oA_plus_oS1': f_neg,
            'h_oA': h_oA, 'h_negative_oA_plus_oS2': h_neg,
            'f1': f1, 'f2': f2, 'h1': h1, 'h2': h2,
            'f_autoconvolution': f_auto, 'h_autoconvolution': h_auto,
            'rA': rA, 'rB': rB, 'recovered_f_autoconvolution': recovered,
            'kA': kA, 'kB': kB, 'session_key': kA,
        },
    })


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--force', action='store_true', help='overwrite canonical vector JSON files')
    args = parser.parse_args()
    if not args.force:
        raise SystemExit('Refusing to overwrite canonical vectors. Use --force only when intentionally establishing a new canonical set.')

    base = Path(__file__).resolve().parent
    for modulo, seed in MODULI_AND_START_SEEDS:
        vector = build(modulo, seed)
        path = base / f'test_vector_p{modulo}.json'
        path.write_text(json.dumps(vector, indent=2) + '\n', encoding='utf-8')
        print(f'generated {path.name}')


if __name__ == '__main__':
    main()
