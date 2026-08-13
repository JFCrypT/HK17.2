#pragma once

#include "hk17_math.hpp"

#include <cstddef>
#include <cstdint>
#include <vector>

namespace hk17::wire {

struct MatrixParameters {
    Matrix A;
    Matrix B;
    u64 q{0};
    std::uint16_t u{0};
    std::uint16_t v{0};
};

struct OctonionParameters {
    u64 p{0};
    Octonion oA{};
};

std::size_t matrix_component_width(u64 q);
std::size_t octonion_component_width(u64 p);

Matrix decode_matrix(const std::uint8_t* data, std::size_t length, u64 q);
std::vector<std::uint8_t> encode_matrix(const Matrix& matrix, u64 q);

Octonion decode_octonion(const std::uint8_t* data, std::size_t length, u64 p);
std::vector<std::uint8_t> encode_octonion(const Octonion& octonion, u64 p);

MatrixParameters decode_matrix_parameters(const std::uint8_t* data, std::size_t length);
OctonionParameters decode_octonion_parameters(const std::uint8_t* data, std::size_t length);

}  // namespace hk17::wire
