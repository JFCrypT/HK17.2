#if !defined(ESP_PLATFORM) || defined(HK17_CONFORMANCE_APP)
#include "canonical_vectors.hpp"
#include "hk17_math.hpp"

#include <array>
#include <cinttypes>
#include <cstdio>
#include <exception>
#include <vector>
#ifndef ESP_PLATFORM
#include <chrono>
#endif

#ifdef ESP_PLATFORM
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#endif

namespace {

using hk17::Matrix;
using hk17::Octonion;
using hk17::u64;
using hk17::canonical::BobVector;

std::uint64_t now_us() {
#ifdef ESP_PLATFORM
    return static_cast<std::uint64_t>(esp_timer_get_time());
#else
    using namespace std::chrono;
    return duration_cast<microseconds>(steady_clock::now().time_since_epoch()).count();
#endif
}

Matrix matrix_from(const u64* values) {
    return Matrix(values, values + hk17::MATRIX_ELEMENTS);
}

Octonion octonion_from(const u64* values) {
    Octonion out{};
    for (std::size_t i = 0; i < hk17::OCTONION_COMPONENTS; ++i) {
        out[i] = values[i];
    }
    return out;
}

bool array_equal(const u64* actual, const u64* expected, std::size_t count) {
    for (std::size_t i = 0; i < count; ++i) {
        if (actual[i] != expected[i]) {
            return false;
        }
    }
    return true;
}

bool check_matrix(const char* label, const Matrix& actual, const u64* expected) {
    if (!hk17::matrix_equal(actual, expected)) {
        std::printf("    [FAIL] %s\n", label);
        for (std::size_t i = 0; i < hk17::MATRIX_ELEMENTS; ++i) {
            if (actual[i] != expected[i]) {
                std::printf("           first mismatch at [%zu][%zu]: actual=%" PRIu64 ", expected=%" PRIu64 "\n",
                            i / hk17::MATRIX_DIMENSION,
                            i % hk17::MATRIX_DIMENSION,
                            actual[i], expected[i]);
                break;
            }
        }
        return false;
    }
    return true;
}

bool check_octonion(const char* label, const Octonion& actual, const u64* expected) {
    if (!hk17::octonion_equal(actual, expected)) {
        std::printf("    [FAIL] %s\n", label);
        for (std::size_t i = 0; i < hk17::OCTONION_COMPONENTS; ++i) {
            if (actual[i] != expected[i]) {
                std::printf("           component %zu: actual=%" PRIu64 ", expected=%" PRIu64 "\n",
                            i, actual[i], expected[i]);
                break;
            }
        }
        return false;
    }
    return true;
}

bool run_vector(const BobVector& vector) {
    bool ok = true;
    std::printf("[RUN ] %s\n", vector.name);
    std::fflush(stdout);
    const std::uint64_t start_us = now_us();

    try {
        const Matrix A = matrix_from(vector.A);
        const Matrix B = matrix_from(vector.B);
        const Matrix TA = matrix_from(vector.TA);
        const Octonion oA = octonion_from(vector.oA);
        const Octonion oS2 = octonion_from(vector.oS2);
        const Octonion rA = octonion_from(vector.rA);

        Matrix J = hk17::calculate_matrix_polynomial(
            A,
            vector.j_coefficients,
            hk17::MATRIX_POLY_COEFFICIENTS,
            vector.q
        );
        ok &= check_matrix("J", J, vector.expected_J);

        Matrix J_u = hk17::matrix_power(J, vector.u, vector.q);
        ok &= check_matrix("J_u", J_u, vector.expected_J_u);

        Matrix J_v = hk17::matrix_power(J, vector.v, vector.q);
        ok &= check_matrix("J_v", J_v, vector.expected_J_v);

        Matrix temp = hk17::matrix_multiply(J_u, B, vector.q);
        Matrix TB = hk17::matrix_multiply(temp, J_v, vector.q);
        ok &= check_matrix("TB", TB, vector.expected_TB);

        temp = hk17::matrix_multiply(J_u, TA, vector.q);
        Matrix MB = hk17::matrix_multiply(temp, J_v, vector.q);
        ok &= check_matrix("MB", MB, vector.expected_MB);

        const hk17::ObDerivation ob = hk17::derive_ob(MB, vector.p);
        if (!array_equal(ob.submatrix_sums.data(), vector.expected_submatrix_sums, 16)) {
            std::printf("    [FAIL] submatrix_sums\n");
            ok = false;
        }

        for (std::size_t candidate = 0; candidate < hk17::OB_CANDIDATES; ++candidate) {
            const u64* expected_oct = vector.expected_candidates + candidate * hk17::OCTONION_COMPONENTS;
            if (!hk17::octonion_equal(ob.candidates[candidate].octonion, expected_oct)) {
                std::printf("    [FAIL] oB candidate %zu\n", candidate + 1);
                ok = false;
            }
            if (ob.candidates[candidate].norm_squared != vector.expected_candidate_norms[candidate]) {
                std::printf("    [FAIL] oB candidate %zu norm\n", candidate + 1);
                ok = false;
            }
            if (static_cast<std::uint8_t>(ob.candidates[candidate].invertible ? 1 : 0)
                != vector.expected_candidate_invertible[candidate]) {
                std::printf("    [FAIL] oB candidate %zu invertibility\n", candidate + 1);
                ok = false;
            }
        }

        if (ob.selected_configuration != vector.selected_oB_configuration) {
            std::printf("    [FAIL] selected_oB_configuration: actual=%zu expected=%zu\n",
                        ob.selected_configuration, vector.selected_oB_configuration);
            ok = false;
        }
        ok &= check_octonion("oB", ob.selected, vector.expected_oB);

        const Octonion oB_inverse = hk17::octonion_reciprocal(ob.selected, vector.p);
        ok &= check_octonion("oB_inverse", oB_inverse, vector.expected_oB_inverse);

        Octonion shifted{};
        for (std::size_t i = 0; i < hk17::OCTONION_COMPONENTS; ++i) {
            shifted[i] = hk17::mod_sub(oS2[i], oA[i], vector.p);
        }
        ok &= check_octonion("-oA + oS2", shifted, vector.expected_shifted);

        const Octonion h_oA = hk17::calculate_f(
            oA,
            vector.h_coefficients,
            vector.octonion_degree,
            vector.p
        );
        ok &= check_octonion("h(oA)", h_oA, vector.expected_h_oA);

        const Octonion h_shifted = hk17::calculate_f(
            shifted,
            vector.h_coefficients,
            vector.octonion_degree,
            vector.p
        );
        ok &= check_octonion("h(-oA+oS2)", h_shifted, vector.expected_h_shifted);

        const Octonion h1 = hk17::oct_power(h_oA, vector.n, vector.p);
        ok &= check_octonion("h1", h1, vector.expected_h1);

        const Octonion h2 = hk17::oct_power(h_shifted, vector.n, vector.p);
        ok &= check_octonion("h2", h2, vector.expected_h2);

        const Octonion h_autoconvolution = hk17::oct_multiply(h1, h2, vector.p);
        ok &= check_octonion("h_autoconvolution", h_autoconvolution, vector.expected_h_autoconvolution);

        const Octonion rB = hk17::oct_multiply(h_autoconvolution, ob.selected, vector.p);
        ok &= check_octonion("rB", rB, vector.expected_rB);

        const Octonion recovered_f = hk17::oct_multiply(rA, oB_inverse, vector.p);
        ok &= check_octonion("recovered_f_autoconvolution", recovered_f, vector.expected_recovered_f);

        const Octonion kB = hk17::oct_multiply(recovered_f, rB, vector.p);
        ok &= check_octonion("kB", kB, vector.expected_kB);

    } catch (const std::exception& exc) {
        std::printf("    [EXCEPTION] %s\n", exc.what());
        ok = false;
    }

    const std::uint64_t elapsed_us = now_us() - start_us;
    std::printf("[%s] %s (%.3f s)\n",
                ok ? "PASS" : "FAIL",
                vector.name,
                static_cast<double>(elapsed_us) / 1000000.0);
    return ok;
}

int run_all_vectors() {
    std::printf("====================================================================================================\n");
    std::printf("HK17.2 ESP32 / BOB CANONICAL CONFORMANCE TEST\n");
    std::printf("====================================================================================================\n");

    std::size_t passed = 0;
    for (const BobVector* vector : hk17::canonical::ALL) {
        if (run_vector(*vector)) {
            ++passed;
        }
#ifdef ESP_PLATFORM
        // Give ESP-IDF housekeeping/idle tasks an explicit scheduling point
        // between canonical vectors.
        vTaskDelay(1);
#endif
    }

    std::printf("====================================================================================================\n");
    if (passed == hk17::canonical::ALL.size()) {
        std::printf("SUCCESS: the ESP32/Bob C++ port matches all five canonical HK17.2 vectors.\n");
        return 0;
    }

    std::printf("FAILURE: %zu/%zu canonical vectors passed.\n", passed, hk17::canonical::ALL.size());
    return 1;
}

}  // namespace

#ifdef ESP_PLATFORM
extern "C" void app_main() {
    (void)run_all_vectors();
}
#else
int main() {
    return run_all_vectors();
}
#endif

#endif  // !ESP_PLATFORM || HK17_CONFORMANCE_APP
