#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace hk17 {

constexpr std::size_t MATRIX_DIMENSION = 32;
constexpr std::size_t MATRIX_ELEMENTS = MATRIX_DIMENSION * MATRIX_DIMENSION;
constexpr std::size_t OCTONION_COMPONENTS = 8;
constexpr std::size_t MATRIX_POLY_COEFFICIENTS = 32;
constexpr std::size_t SUBMATRIX_GRID_DIMENSION = 4;
constexpr std::size_t SUBMATRIX_DIMENSION = 8;
constexpr std::size_t OB_CANDIDATES = 4;

using u64 = std::uint64_t;
using Matrix = std::vector<u64>;
using Octonion = std::array<u64, OCTONION_COMPONENTS>;

struct ObCandidate {
    Octonion octonion{};
    u64 norm_squared{0};
    bool invertible{false};
};

struct ObDerivation {
    std::array<u64, 16> submatrix_sums{};
    std::array<ObCandidate, OB_CANDIDATES> candidates{};
    std::size_t selected_configuration{0};  // 1..4; 0 if none
    Octonion selected{};
};

u64 mod_add(u64 a, u64 b, u64 modulus);
u64 mod_sub(u64 a, u64 b, u64 modulus);
u64 mod_mul(u64 a, u64 b, u64 modulus);
u64 mod_pow(u64 base, u64 exponent, u64 modulus);

Octonion oct_sum(const Octonion& a, const Octonion& b, u64 modulus);
Octonion oct_scale(const Octonion& a, u64 scalar, u64 modulus);
Octonion oct_multiply(const Octonion& a, const Octonion& b, u64 modulus);
Octonion oct_power(const Octonion& a, u64 potency, u64 modulus);
Octonion calculate_f(const Octonion& oa, const u64* coefficients, std::size_t coefficient_count, u64 modulus);
u64 octonion_norm_squared(const Octonion& a, u64 modulus);
Octonion octonion_reciprocal(const Octonion& a, u64 modulus);

Matrix matrix_identity();
Matrix matrix_multiply(const Matrix& a, const Matrix& b, u64 modulus);
Matrix matrix_power(const Matrix& a, u64 exponent, u64 modulus);
Matrix calculate_matrix_polynomial(const Matrix& a, const u64* coefficients, std::size_t coefficient_count, u64 modulus);

ObDerivation derive_ob(const Matrix& shared_matrix, u64 octonion_modulus);

bool matrix_equal(const Matrix& a, const u64* expected);
bool octonion_equal(const Octonion& a, const u64* expected);

}  // namespace hk17
