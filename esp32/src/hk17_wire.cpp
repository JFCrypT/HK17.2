#include "hk17_wire.hpp"

#include <limits>
#include <stdexcept>

namespace hk17::wire {
namespace {

u64 decode_uint(const std::uint8_t* data, std::size_t length, std::size_t& offset, std::size_t width) {
    if (width == 0 || width > 8 || offset + width > length) {
        throw std::runtime_error("truncated or invalid unsigned integer");
    }
    u64 value = 0;
    for (std::size_t i = 0; i < width; ++i) {
        value = (value << 8U) | static_cast<u64>(data[offset + i]);
    }
    offset += width;
    return value;
}

void encode_uint(std::vector<std::uint8_t>& out, u64 value, std::size_t width) {
    if (width == 0 || width > 8) {
        throw std::runtime_error("invalid unsigned integer width");
    }
    if (width < 8 && value >= (1ULL << (8U * width))) {
        throw std::runtime_error("integer does not fit requested width");
    }
    for (std::size_t i = 0; i < width; ++i) {
        const std::size_t shift = 8U * (width - 1U - i);
        out.push_back(static_cast<std::uint8_t>((value >> shift) & 0xFFU));
    }
}

std::size_t component_width(u64 modulus) {
    if (modulus <= 1) {
        throw std::runtime_error("modulus must be greater than one");
    }
    const u64 maximum = modulus - 1;
    std::size_t bits = 0;
    u64 value = maximum;
    while (value != 0) {
        ++bits;
        value >>= 1U;
    }
    return (bits + 7U) / 8U;
}

}  // namespace

std::size_t matrix_component_width(u64 q) {
    return component_width(q);
}

std::size_t octonion_component_width(u64 p) {
    return component_width(p);
}

Matrix decode_matrix(const std::uint8_t* data, std::size_t length, u64 q) {
    const std::size_t width = matrix_component_width(q);
    const std::size_t expected = MATRIX_ELEMENTS * width;
    if (length != expected) {
        throw std::runtime_error("invalid matrix payload length");
    }

    Matrix matrix(MATRIX_ELEMENTS, 0);
    std::size_t offset = 0;
    for (std::size_t i = 0; i < MATRIX_ELEMENTS; ++i) {
        const u64 value = decode_uint(data, length, offset, width);
        if (value >= q) {
            throw std::runtime_error("matrix component outside modulus");
        }
        matrix[i] = value;
    }
    return matrix;
}

std::vector<std::uint8_t> encode_matrix(const Matrix& matrix, u64 q) {
    if (matrix.size() != MATRIX_ELEMENTS) {
        throw std::runtime_error("invalid matrix size");
    }
    const std::size_t width = matrix_component_width(q);
    std::vector<std::uint8_t> out;
    out.reserve(MATRIX_ELEMENTS * width);
    for (const u64 value : matrix) {
        if (value >= q) {
            throw std::runtime_error("matrix component outside modulus");
        }
        encode_uint(out, value, width);
    }
    return out;
}

Octonion decode_octonion(const std::uint8_t* data, std::size_t length, u64 p) {
    const std::size_t width = octonion_component_width(p);
    const std::size_t expected = OCTONION_COMPONENTS * width;
    if (length != expected) {
        throw std::runtime_error("invalid octonion payload length");
    }

    Octonion out{};
    std::size_t offset = 0;
    for (std::size_t i = 0; i < OCTONION_COMPONENTS; ++i) {
        const u64 value = decode_uint(data, length, offset, width);
        if (value >= p) {
            throw std::runtime_error("octonion component outside modulus");
        }
        out[i] = value;
    }
    return out;
}

std::vector<std::uint8_t> encode_octonion(const Octonion& octonion, u64 p) {
    const std::size_t width = octonion_component_width(p);
    std::vector<std::uint8_t> out;
    out.reserve(OCTONION_COMPONENTS * width);
    for (const u64 value : octonion) {
        if (value >= p) {
            throw std::runtime_error("octonion component outside modulus");
        }
        encode_uint(out, value, width);
    }
    return out;
}

MatrixParameters decode_matrix_parameters(const std::uint8_t* data, std::size_t length) {
    if (length < 12) {
        throw std::runtime_error("truncated matrix parameter payload");
    }

    std::size_t offset = 0;
    const u64 q = decode_uint(data, length, offset, 8);
    const u64 u_value = decode_uint(data, length, offset, 2);
    const u64 v_value = decode_uint(data, length, offset, 2);
    if (u_value > std::numeric_limits<std::uint16_t>::max() || v_value > std::numeric_limits<std::uint16_t>::max()) {
        throw std::runtime_error("matrix exponent outside uint16");
    }

    const std::size_t matrix_length = MATRIX_ELEMENTS * matrix_component_width(q);
    const std::size_t expected = 12 + 2 * matrix_length;
    if (length != expected) {
        throw std::runtime_error("invalid matrix parameter payload length");
    }

    MatrixParameters params;
    params.q = q;
    params.u = static_cast<std::uint16_t>(u_value);
    params.v = static_cast<std::uint16_t>(v_value);
    params.A = decode_matrix(data + offset, matrix_length, q);
    offset += matrix_length;
    params.B = decode_matrix(data + offset, matrix_length, q);
    return params;
}

OctonionParameters decode_octonion_parameters(const std::uint8_t* data, std::size_t length) {
    if (length < 8) {
        throw std::runtime_error("truncated octonion parameter payload");
    }

    std::size_t offset = 0;
    const u64 p = decode_uint(data, length, offset, 8);
    const std::size_t oct_length = OCTONION_COMPONENTS * octonion_component_width(p);
    if (length != 8 + oct_length) {
        throw std::runtime_error("invalid octonion parameter payload length");
    }

    OctonionParameters params;
    params.p = p;
    params.oA = decode_octonion(data + offset, oct_length, p);
    return params;
}

}  // namespace hk17::wire
