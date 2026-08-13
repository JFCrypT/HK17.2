#ifdef HK17_PERFORMANCE_APP

#include "canonical_vectors.hpp"
#include "hk17_math.hpp"

#include <array>
#include <cinttypes>
#include <cstdio>
#include <exception>
#include <string>
#include <vector>

#include "esp_heap_caps.h"
#include "esp_mac.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "sdkconfig.h"

#ifndef HK17_PERF_EXECUTIONS
#define HK17_PERF_EXECUTIONS 1000
#endif

#ifndef HK17_PERF_START_DELAY_MS
#define HK17_PERF_START_DELAY_MS 5000
#endif

namespace {

using hk17::Matrix;
using hk17::Octonion;
using hk17::u64;
using hk17::canonical::BobVector;

constexpr const BobVector& VECTOR = hk17::canonical::v_251;

std::uint64_t now_us() {
    return static_cast<std::uint64_t>(esp_timer_get_time());
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

std::string device_id_from_mac(const std::uint8_t mac[6]) {
    char buffer[32]{};
    std::snprintf(
        buffer,
        sizeof(buffer),
        "esp32-%02x%02x%02x%02x%02x%02x",
        mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]
    );
    return std::string(buffer);
}

bool validate_iteration(
    const Matrix& J,
    const Matrix& TB,
    const Matrix& MB,
    const hk17::ObDerivation& ob,
    const Octonion& rB,
    const Octonion& recovered_f,
    const Octonion& kB
) {
    return
        hk17::matrix_equal(J, VECTOR.expected_J) &&
        hk17::matrix_equal(TB, VECTOR.expected_TB) &&
        hk17::matrix_equal(MB, VECTOR.expected_MB) &&
        ob.selected_configuration == VECTOR.selected_oB_configuration &&
        hk17::octonion_equal(ob.selected, VECTOR.expected_oB) &&
        hk17::octonion_equal(rB, VECTOR.expected_rB) &&
        hk17::octonion_equal(recovered_f, VECTOR.expected_recovered_f) &&
        hk17::octonion_equal(kB, VECTOR.expected_kB);
}

struct Measurement {
    bool success{false};
    std::uint64_t total_us{0};
    std::uint64_t matrix_polynomial_us{0};
    std::uint64_t matrix_exchange_us{0};
    std::uint64_t ob_derivation_us{0};
    std::uint64_t octonion_stage_us{0};
    std::uint64_t key_recovery_us{0};
    std::size_t heap_before{0};
    std::size_t heap_after{0};
    std::size_t heap_min_since_boot{0};
};

Measurement run_once() {
    Measurement result{};
    result.heap_before = heap_caps_get_free_size(MALLOC_CAP_8BIT);

    const std::uint64_t total_start = now_us();

    try {
        const Matrix A = matrix_from(VECTOR.A);
        const Matrix B = matrix_from(VECTOR.B);
        const Matrix TA = matrix_from(VECTOR.TA);
        const Octonion oA = octonion_from(VECTOR.oA);
        const Octonion oS2 = octonion_from(VECTOR.oS2);
        const Octonion rA = octonion_from(VECTOR.rA);

        std::uint64_t stage_start = now_us();

        const Matrix J = hk17::calculate_matrix_polynomial(
            A,
            VECTOR.j_coefficients,
            hk17::MATRIX_POLY_COEFFICIENTS,
            VECTOR.q
        );

        result.matrix_polynomial_us = now_us() - stage_start;
        stage_start = now_us();

        const Matrix J_u = hk17::matrix_power(J, VECTOR.u, VECTOR.q);
        const Matrix J_v = hk17::matrix_power(J, VECTOR.v, VECTOR.q);

        Matrix temp = hk17::matrix_multiply(J_u, B, VECTOR.q);
        const Matrix TB = hk17::matrix_multiply(temp, J_v, VECTOR.q);

        temp = hk17::matrix_multiply(J_u, TA, VECTOR.q);
        const Matrix MB = hk17::matrix_multiply(temp, J_v, VECTOR.q);

        result.matrix_exchange_us = now_us() - stage_start;
        stage_start = now_us();

        const hk17::ObDerivation ob = hk17::derive_ob(MB, VECTOR.p);
        const Octonion oB_inverse = hk17::octonion_reciprocal(ob.selected, VECTOR.p);

        result.ob_derivation_us = now_us() - stage_start;
        stage_start = now_us();

        Octonion shifted{};
        for (std::size_t i = 0; i < hk17::OCTONION_COMPONENTS; ++i) {
            shifted[i] = hk17::mod_sub(oS2[i], oA[i], VECTOR.p);
        }

        const Octonion h_oA = hk17::calculate_f(
            oA,
            VECTOR.h_coefficients,
            VECTOR.octonion_degree,
            VECTOR.p
        );

        const Octonion h_shifted = hk17::calculate_f(
            shifted,
            VECTOR.h_coefficients,
            VECTOR.octonion_degree,
            VECTOR.p
        );

        const Octonion h1 = hk17::oct_power(h_oA, VECTOR.n, VECTOR.p);
        const Octonion h2 = hk17::oct_power(h_shifted, VECTOR.n, VECTOR.p);
        const Octonion h_autoconvolution = hk17::oct_multiply(h1, h2, VECTOR.p);
        const Octonion rB = hk17::oct_multiply(h_autoconvolution, ob.selected, VECTOR.p);

        result.octonion_stage_us = now_us() - stage_start;
        stage_start = now_us();

        const Octonion recovered_f = hk17::oct_multiply(rA, oB_inverse, VECTOR.p);
        const Octonion kB = hk17::oct_multiply(recovered_f, rB, VECTOR.p);

        result.key_recovery_us = now_us() - stage_start;
        result.success = validate_iteration(J, TB, MB, ob, rB, recovered_f, kB);

    } catch (const std::exception& exc) {
        std::printf("HK17_PERF_ERROR,%s\n", exc.what());
        result.success = false;
    }

    result.total_us = now_us() - total_start;
    result.heap_after = heap_caps_get_free_size(MALLOC_CAP_8BIT);
    result.heap_min_since_boot = heap_caps_get_minimum_free_size(MALLOC_CAP_8BIT);
    return result;
}

void print_banner() {
    std::printf("====================================================================================================\n");
    std::printf("HK17.2 ESP32 / BOB LOCAL CRYPTOGRAPHIC PERFORMANCE BENCHMARK\n");
    std::printf("====================================================================================================\n");
    std::printf("Workload: frozen canonical p=251 Bob computation\n");
    std::printf("Network/MQTT/HTTP: excluded\n");
    std::printf("Executions: %d\n", HK17_PERF_EXECUTIONS);
    std::printf("Start delay: %d ms\n", HK17_PERF_START_DELAY_MS);
    std::printf("====================================================================================================\n");
}

}  // namespace

extern "C" void app_main() {
    print_banner();

    std::uint8_t mac[6]{};
    ESP_ERROR_CHECK(esp_read_mac(mac, ESP_MAC_WIFI_STA));
    const std::string device_id = device_id_from_mac(mac);

    const std::size_t heap_start = heap_caps_get_free_size(MALLOC_CAP_8BIT);
    const std::size_t heap_min_start = heap_caps_get_minimum_free_size(MALLOC_CAP_8BIT);

    std::printf(
        "HK17_PERF_META,"
        "device_id=%s,"
        "mac=%02x:%02x:%02x:%02x:%02x:%02x,"
        "executions=%d,"
        "p=%" PRIu64 ","
        "q=%" PRIu64 ","
        "u=%" PRIu64 ","
        "v=%" PRIu64 ","
        "n=%" PRIu64 ","
        "octonion_degree=%zu,"
        "matrix_dimension=%zu,"
        "matrix_degree=%zu,"
        "cpu_mhz=%d,"
        "heap_start=%zu,"
        "heap_min_start=%zu\n",
        device_id.c_str(),
        mac[0], mac[1], mac[2], mac[3], mac[4], mac[5],
        HK17_PERF_EXECUTIONS,
        VECTOR.p,
        VECTOR.q,
        VECTOR.u,
        VECTOR.v,
        VECTOR.n,
        VECTOR.octonion_degree,
        hk17::MATRIX_DIMENSION,
        hk17::MATRIX_POLY_COEFFICIENTS,
        CONFIG_ESP_DEFAULT_CPU_FREQ_MHZ,
        heap_start,
        heap_min_start
    );

    std::printf("HK17_PERF_READY\n");
    std::fflush(stdout);

    vTaskDelay(pdMS_TO_TICKS(HK17_PERF_START_DELAY_MS));

    std::size_t passed = 0;
    const std::uint64_t benchmark_start = now_us();

    for (std::size_t execution = 1; execution <= HK17_PERF_EXECUTIONS; ++execution) {
        const Measurement m = run_once();
        if (m.success) {
            ++passed;
        }

        std::printf(
            "HK17_PERF_RESULT,"
            "%zu,"
            "%d,"
            "%" PRIu64 ","
            "%" PRIu64 ","
            "%" PRIu64 ","
            "%" PRIu64 ","
            "%" PRIu64 ","
            "%" PRIu64 ","
            "%zu,"
            "%zu,"
            "%zu\n",
            execution,
            m.success ? 1 : 0,
            m.total_us,
            m.matrix_polynomial_us,
            m.matrix_exchange_us,
            m.ob_derivation_us,
            m.octonion_stage_us,
            m.key_recovery_us,
            m.heap_before,
            m.heap_after,
            m.heap_min_since_boot
        );
        std::fflush(stdout);

        // Serial printing is deliberately outside the measured cryptographic interval.
        // Yield between executions so ESP-IDF idle/housekeeping tasks can run.
        vTaskDelay(1);
    }

    const std::uint64_t benchmark_total_us = now_us() - benchmark_start;
    const std::size_t heap_end = heap_caps_get_free_size(MALLOC_CAP_8BIT);
    const std::size_t heap_min_end = heap_caps_get_minimum_free_size(MALLOC_CAP_8BIT);

    std::printf(
        "HK17_PERF_DONE,"
        "successful=%zu,"
        "failed=%zu,"
        "benchmark_total_us=%" PRIu64 ","
        "heap_end=%zu,"
        "heap_min_end=%zu\n",
        passed,
        static_cast<std::size_t>(HK17_PERF_EXECUTIONS) - passed,
        benchmark_total_us,
        heap_end,
        heap_min_end
    );

    std::printf("====================================================================================================\n");
    if (passed == HK17_PERF_EXECUTIONS) {
        std::printf("SUCCESS: all ESP32 performance iterations reproduced the canonical p=251 Bob result.\n");
    } else {
        std::printf(
            "FAILURE: %zu/%d ESP32 performance iterations reproduced the canonical p=251 Bob result.\n",
            passed,
            HK17_PERF_EXECUTIONS
        );
    }
    std::printf("====================================================================================================\n");
    std::fflush(stdout);
}

#endif  // HK17_PERFORMANCE_APP
