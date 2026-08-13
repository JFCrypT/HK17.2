#include "hk17_math.hpp"

#include <algorithm>
#include <stdexcept>
#include <string>

#ifdef ESP_PLATFORM
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#endif

namespace hk17 {

namespace {

constexpr Octonion O_NULL{0, 0, 0, 0, 0, 0, 0, 0};

inline std::size_t idx(std::size_t row, std::size_t col) {
    return row * MATRIX_DIMENSION + col;
}

inline void cooperative_yield() {
#ifdef ESP_PLATFORM
    // HK17.2 is CPU-intensive. Yield one RTOS tick at controlled points so
    // the ESP-IDF idle/system tasks can run and the Task Watchdog is not
    // starved. This does not alter any algebraic operation or result.
    vTaskDelay(1);
#endif
}

u64 decimal_concatenate_mod(u64 a, u64 b, u64 modulus) {
    // Python uses arbitrary-precision decimal concatenation before reducing modulo p.
    // For the 64-bit parameter set the full concatenated integer can exceed uint64_t,
    // so compute the same value directly modulo p.
    std::size_t digits = 1;
    for (u64 temp = b; temp >= 10; temp /= 10) {
        ++digits;
    }

    u64 power10 = 1 % modulus;
    for (std::size_t i = 0; i < digits; ++i) {
        power10 = mod_mul(power10, 10, modulus);
    }
    return mod_add(mod_mul(a % modulus, power10, modulus), b % modulus, modulus);
}

}  // namespace

u64 mod_add(u64 a, u64 b, u64 modulus) {
    a %= modulus;
    b %= modulus;
    if (a >= modulus - b) {
        return a - (modulus - b);
    }
    return a + b;
}

u64 mod_sub(u64 a, u64 b, u64 modulus) {
    a %= modulus;
    b %= modulus;
    if (a >= b) {
        return a - b;
    }
    return modulus - (b - a);
}

u64 mod_mul(u64 a, u64 b, u64 modulus) {
    if (modulus == 0) {
        throw std::invalid_argument("modulus must be non-zero");
    }

    a %= modulus;
    b %= modulus;

    // Fast path for products that fit safely in uint64_t.
    if (a == 0 || b == 0) {
        return 0;
    }
    if (a <= UINT64_MAX / b) {
        return (a * b) % modulus;
    }

    // Overflow-safe double-and-add for the 64-bit HK17.2 modulus.
    u64 result = 0;
    while (b != 0) {
        if (b & 1ULL) {
            result = mod_add(result, a, modulus);
        }
        b >>= 1U;
        if (b != 0) {
            a = mod_add(a, a, modulus);
        }
    }
    return result;
}

u64 mod_pow(u64 base, u64 exponent, u64 modulus) {
    u64 result = 1 % modulus;
    base %= modulus;
    while (exponent > 0) {
        if (exponent & 1ULL) {
            result = mod_mul(result, base, modulus);
        }
        exponent >>= 1U;
        if (exponent != 0) {
            base = mod_mul(base, base, modulus);
        }
    }
    return result;
}

Octonion oct_sum(const Octonion& a, const Octonion& b, u64 modulus) {
    Octonion out{};
    for (std::size_t i = 0; i < OCTONION_COMPONENTS; ++i) {
        out[i] = mod_add(a[i], b[i], modulus);
    }
    return out;
}

Octonion oct_scale(const Octonion& a, u64 scalar, u64 modulus) {
    Octonion out{};
    scalar %= modulus;
    for (std::size_t i = 0; i < OCTONION_COMPONENTS; ++i) {
        out[i] = mod_mul(a[i], scalar, modulus);
    }
    return out;
}

Octonion oct_multiply(const Octonion& x, const Octonion& y, u64 m) {
    const u64 a = x[0], b = x[1], c = x[2], d = x[3];
    const u64 e = x[4], f = x[5], g = x[6], h = x[7];
    const u64 i = y[0], j = y[1], k = y[2], l = y[3];
    const u64 mm = y[4], n = y[5], o = y[6], p = y[7];

    auto add = [m](u64 lhs, u64 rhs) { return mod_add(lhs, rhs, m); };
    auto sub = [m](u64 lhs, u64 rhs) { return mod_sub(lhs, rhs, m); };
    auto mul = [m](u64 lhs, u64 rhs) { return mod_mul(lhs, rhs, m); };

    Octonion t{};

    t[0] = mul(a, i);
    t[0] = sub(t[0], mul(b, j));
    t[0] = sub(t[0], mul(c, k));
    t[0] = sub(t[0], mul(d, l));
    t[0] = sub(t[0], mul(e, mm));
    t[0] = sub(t[0], mul(f, n));
    t[0] = sub(t[0], mul(g, o));
    t[0] = sub(t[0], mul(h, p));

    t[1] = mul(a, j);
    t[1] = add(t[1], mul(b, i));
    t[1] = add(t[1], mul(c, mm));
    t[1] = add(t[1], mul(d, p));
    t[1] = sub(t[1], mul(e, k));
    t[1] = add(t[1], mul(f, o));
    t[1] = sub(t[1], mul(g, n));
    t[1] = sub(t[1], mul(h, l));

    t[2] = mul(a, k);
    t[2] = sub(t[2], mul(b, mm));
    t[2] = add(t[2], mul(c, i));
    t[2] = add(t[2], mul(d, n));
    t[2] = add(t[2], mul(e, j));
    t[2] = sub(t[2], mul(f, l));
    t[2] = add(t[2], mul(g, p));
    t[2] = sub(t[2], mul(h, o));

    t[3] = mul(a, l);
    t[3] = sub(t[3], mul(b, p));
    t[3] = sub(t[3], mul(c, n));
    t[3] = add(t[3], mul(d, i));
    t[3] = add(t[3], mul(e, o));
    t[3] = add(t[3], mul(f, k));
    t[3] = sub(t[3], mul(g, mm));
    t[3] = add(t[3], mul(h, j));

    t[4] = mul(a, mm);
    t[4] = add(t[4], mul(b, k));
    t[4] = sub(t[4], mul(c, j));
    t[4] = sub(t[4], mul(d, o));
    t[4] = add(t[4], mul(e, i));
    t[4] = add(t[4], mul(f, p));
    t[4] = add(t[4], mul(g, l));
    t[4] = sub(t[4], mul(h, n));

    t[5] = mul(a, n);
    t[5] = sub(t[5], mul(b, o));
    t[5] = add(t[5], mul(c, l));
    t[5] = sub(t[5], mul(d, k));
    t[5] = sub(t[5], mul(e, p));
    t[5] = add(t[5], mul(f, i));
    t[5] = add(t[5], mul(g, j));
    t[5] = add(t[5], mul(h, mm));

    t[6] = mul(a, o);
    t[6] = add(t[6], mul(b, n));
    t[6] = sub(t[6], mul(c, p));
    t[6] = add(t[6], mul(d, mm));
    t[6] = sub(t[6], mul(e, l));
    t[6] = sub(t[6], mul(f, j));
    t[6] = add(t[6], mul(g, i));
    t[6] = add(t[6], mul(h, k));

    t[7] = mul(a, p);
    t[7] = add(t[7], mul(b, l));
    t[7] = add(t[7], mul(c, o));
    t[7] = sub(t[7], mul(d, j));
    t[7] = add(t[7], mul(e, n));
    t[7] = sub(t[7], mul(f, mm));
    t[7] = sub(t[7], mul(g, k));
    t[7] = add(t[7], mul(h, i));

    return t;
}

Octonion oct_power(const Octonion& a, u64 potency, u64 modulus) {
    if (potency == 0) {
        return Octonion{1, 0, 0, 0, 0, 0, 0, 0};
    }

    Octonion result = a;
    for (u64 current = 2; current <= potency; ++current) {
        result = oct_multiply(result, a, modulus);
        // The 64-bit parameter set makes each octonion multiplication
        // substantially more expensive because modular products must be
        // overflow-safe. Block the current task for one RTOS tick at short,
        // deterministic intervals so IDLE0 and system tasks can run.
        // This is scheduling only and does not alter HK17.2 arithmetic.
        if ((current & 7ULL) == 0ULL) {
            cooperative_yield();
        }
    }
    return result;
}

Octonion calculate_f(const Octonion& oa, const u64* coefficients, std::size_t coefficient_count, u64 modulus) {
    Octonion fa = O_NULL;
    for (std::size_t index = 0; index < coefficient_count; ++index) {
        const std::size_t exponent = coefficient_count - 1 - index;
        if (exponent == 0) {
            Octonion constant{coefficients[index] % modulus, 0, 0, 0, 0, 0, 0, 0};
            fa = oct_sum(fa, constant, modulus);
        } else {
            const Octonion powered = oct_power(oa, exponent, modulus);
            const Octonion scaled = oct_scale(powered, coefficients[index], modulus);
            fa = oct_sum(fa, scaled, modulus);
        }
        // A polynomial evaluation consists of many independent left-associated
        // powers. Yield between terms as an additional scheduling boundary,
        // especially for the 64-bit / 128-coefficient parameter set.
        cooperative_yield();
    }
    return fa;
}

u64 octonion_norm_squared(const Octonion& a, u64 modulus) {
    u64 result = 0;
    for (u64 value : a) {
        result = mod_add(result, mod_mul(value, value, modulus), modulus);
    }
    return result;
}

Octonion octonion_reciprocal(const Octonion& a, u64 modulus) {
    const u64 norm = octonion_norm_squared(a, modulus);
    if (norm == 0) {
        throw std::runtime_error("octonion is not invertible");
    }
    const u64 inverse_norm = mod_pow(norm, modulus - 2, modulus);
    Octonion conjugate{};
    conjugate[0] = a[0] % modulus;
    for (std::size_t i = 1; i < OCTONION_COMPONENTS; ++i) {
        conjugate[i] = (a[i] == 0) ? 0 : modulus - (a[i] % modulus);
    }
    return oct_scale(conjugate, inverse_norm, modulus);
}

Matrix matrix_identity() {
    Matrix result(MATRIX_ELEMENTS, 0);
    for (std::size_t i = 0; i < MATRIX_DIMENSION; ++i) {
        result[idx(i, i)] = 1;
    }
    return result;
}

Matrix matrix_multiply(const Matrix& a, const Matrix& b, u64 modulus) {
    if (a.size() != MATRIX_ELEMENTS || b.size() != MATRIX_ELEMENTS) {
        throw std::invalid_argument("invalid matrix size");
    }

    Matrix result(MATRIX_ELEMENTS, 0);
    for (std::size_t row = 0; row < MATRIX_DIMENSION; ++row) {
        for (std::size_t col = 0; col < MATRIX_DIMENSION; ++col) {
            u64 value = 0;
            for (std::size_t r = 0; r < MATRIX_DIMENSION; ++r) {
                // q <= 2^32 in the frozen protocol, so each product fits uint64_t.
                const u64 product = a[idx(row, r)] * b[idx(r, col)];
                value = mod_add(value, product % modulus, modulus);
            }
            result[idx(row, col)] = value;
        }
    }
    cooperative_yield();
    return result;
}

Matrix matrix_power(const Matrix& a, u64 exponent, u64 modulus) {
    Matrix result = matrix_identity();
    Matrix base = a;
    u64 current = exponent;

    while (current > 0) {
        if (current & 1ULL) {
            result = matrix_multiply(result, base, modulus);
        }
        base = matrix_multiply(base, base, modulus);
        current >>= 1U;
    }
    return result;
}

Matrix calculate_matrix_polynomial(const Matrix& a, const u64* coefficients, std::size_t coefficient_count, u64 modulus) {
    if (coefficient_count == 0) {
        return Matrix(MATRIX_ELEMENTS, 0);
    }

    Matrix result = matrix_identity();
    for (u64& value : result) {
        value = mod_mul(value, coefficients[0], modulus);
    }

    for (std::size_t coefficient_index = 1; coefficient_index < coefficient_count; ++coefficient_index) {
        result = matrix_multiply(result, a, modulus);
        const u64 coefficient = coefficients[coefficient_index] % modulus;
        for (std::size_t diagonal = 0; diagonal < MATRIX_DIMENSION; ++diagonal) {
            const std::size_t position = idx(diagonal, diagonal);
            result[position] = mod_add(result[position], coefficient, modulus);
        }
    }
    return result;
}

ObDerivation derive_ob(const Matrix& shared_matrix, u64 p) {
    if (shared_matrix.size() != MATRIX_ELEMENTS) {
        throw std::invalid_argument("invalid matrix size");
    }

    ObDerivation out{};

    for (std::size_t block_row = 0; block_row < SUBMATRIX_GRID_DIMENSION; ++block_row) {
        for (std::size_t block_col = 0; block_col < SUBMATRIX_GRID_DIMENSION; ++block_col) {
            u64 total = 0;
            const std::size_t start_row = block_row * SUBMATRIX_DIMENSION;
            const std::size_t start_col = block_col * SUBMATRIX_DIMENSION;
            for (std::size_t row = start_row; row < start_row + SUBMATRIX_DIMENSION; ++row) {
                for (std::size_t col = start_col; col < start_col + SUBMATRIX_DIMENSION; ++col) {
                    total += shared_matrix[idx(row, col)];
                }
            }
            out.submatrix_sums[block_row * 4 + block_col] = total;
        }
    }

    std::array<std::array<std::size_t, 16>, 4> traversals{};
    std::size_t n = 0;
    for (std::size_t row = 0; row < 4; ++row) {
        for (std::size_t col = 0; col < 4; ++col) traversals[0][n++] = row * 4 + col;
    }
    n = 0;
    for (std::size_t row = 0; row < 4; ++row) {
        for (int col = 3; col >= 0; --col) traversals[1][n++] = row * 4 + static_cast<std::size_t>(col);
    }
    n = 0;
    for (std::size_t col = 0; col < 4; ++col) {
        for (std::size_t row = 0; row < 4; ++row) traversals[2][n++] = row * 4 + col;
    }
    n = 0;
    for (std::size_t col = 0; col < 4; ++col) {
        for (int row = 3; row >= 0; --row) traversals[3][n++] = static_cast<std::size_t>(row) * 4 + col;
    }

    for (std::size_t candidate_index = 0; candidate_index < 4; ++candidate_index) {
        Octonion candidate{};
        for (std::size_t component = 0; component < 8; ++component) {
            const u64 first = out.submatrix_sums[traversals[candidate_index][2 * component]];
            const u64 second = out.submatrix_sums[traversals[candidate_index][2 * component + 1]];
            candidate[component] = decimal_concatenate_mod(first, second, p);
        }
        const u64 norm = octonion_norm_squared(candidate, p);
        out.candidates[candidate_index].octonion = candidate;
        out.candidates[candidate_index].norm_squared = norm;
        out.candidates[candidate_index].invertible = candidate != O_NULL && norm != 0;
        if (out.selected_configuration == 0 && out.candidates[candidate_index].invertible) {
            out.selected_configuration = candidate_index + 1;
            out.selected = candidate;
        }
    }

    return out;
}

bool matrix_equal(const Matrix& a, const u64* expected) {
    if (a.size() != MATRIX_ELEMENTS) return false;
    for (std::size_t i = 0; i < MATRIX_ELEMENTS; ++i) {
        if (a[i] != expected[i]) return false;
    }
    return true;
}

bool octonion_equal(const Octonion& a, const u64* expected) {
    for (std::size_t i = 0; i < OCTONION_COMPONENTS; ++i) {
        if (a[i] != expected[i]) return false;
    }
    return true;
}

}  // namespace hk17
