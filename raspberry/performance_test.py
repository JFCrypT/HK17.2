#!/usr/bin/env python3
"""HK17.2 Raspberry Pi 3 performance benchmark.

Two complementary local benchmarks are provided without MQTT, HTTP, Wi-Fi,
or serialization overhead:

1. reference
   Executes the frozen `general/hk17_2-v2.py` implementation exactly as the
   general-purpose PC benchmark does. This is the directly comparable
   hardware-to-hardware workload.

2. kms
   Executes the deployed Raspberry Pi Alice/KMS port. Bob is implemented as a
   local driver only to supply TB and rB; Bob computations are deliberately
   excluded from the primary Alice/KMS timing. This measures the cryptographic
   cost actually borne by the Raspberry Pi KMS role.

The frozen reference implementation is never modified by this benchmark.
"""

from __future__ import annotations

import argparse
import csv
import platform
import random as randomlib
import re
import subprocess
import sys
import time
from pathlib import Path
from statistics import mean, median, stdev
from typing import Iterable, Sequence

from hk17_math import (
    O_NULL,
    calculate_f,
    calculate_matrix_polynomial,
    generate_octonion_candidates,
    matrix_multiply,
    matrix_null,
    matrix_power,
    multiply,
    obtain_polynomial,
    octonion_reciprocal,
    power,
    scale,
    select_first_invertible_octonion,
    summ,
)
from kms import (
    DEFAULT_MODULO,
    MATRIX_DEGREE,
    MATRIX_DIMENSION,
    POWERS,
    AliceSession,
    derive_system_parameters,
)


DEFAULT_EXECUTIONS = 1000
REFERENCE_SUCCESS_MARKER = "SUCCESS!!! Alice and Bob generated the same key."
REFERENCE_TIME_RE = re.compile(r"Time\s*=\s*(\d+):(\d+):(\d+(?:\.\d+)?)")


def percentile(values: Sequence[float], percentile_value: float) -> float | None:
    if not values:
        return None

    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]

    position = (len(ordered) - 1) * percentile_value
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def descriptive_stats(prefix: str, values: Sequence[float]) -> dict[str, float]:
    if not values:
        return {}

    return {
        f"mean_{prefix}_s": mean(values),
        f"median_{prefix}_s": median(values),
        f"std_{prefix}_s": stdev(values) if len(values) > 1 else 0.0,
        f"min_{prefix}_s": min(values),
        f"max_{prefix}_s": max(values),
        f"p95_{prefix}_s": percentile(values, 0.95),
    }


def parse_reference_protocol_time(output: str) -> float | None:
    match = REFERENCE_TIME_RE.search(output)
    if match is None:
        return None

    hours = int(match.group(1))
    minutes = int(match.group(2))
    seconds = float(match.group(3))
    return hours * 3600 + minutes * 60 + seconds


def _read_text(path: str) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace").strip("\x00\n ")
    except (OSError, PermissionError):
        return None


def cpu_model() -> str:
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.is_file():
        entries: dict[str, str] = {}
        for line in cpuinfo.read_text(encoding="utf-8", errors="replace").splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            normalized = key.strip().lower()
            if normalized not in entries:
                entries[normalized] = value.strip()
        for key in ("model name", "hardware", "processor", "model"):
            if entries.get(key):
                return entries[key]
    return platform.processor() or "unknown"


def device_model() -> str:
    return _read_text("/proc/device-tree/model") or "unknown"


def cpu_governor() -> str:
    return _read_text("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor") or "unknown"


def cpu_temperature_c() -> float | None:
    raw = _read_text("/sys/class/thermal/thermal_zone0/temp")
    if raw is None:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    return value / 1000.0 if value > 1000 else value


def cpu_frequency_mhz() -> float | None:
    raw = _read_text("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq")
    if raw is None:
        return None
    try:
        return float(raw) / 1000.0
    except ValueError:
        return None


def common_metadata(mode: str, executions: int, modulo: int) -> dict[str, object]:
    params = derive_system_parameters(modulo)
    return {
        "benchmark_mode": mode,
        "executions_requested": executions,
        "octonion_modulo_p": params.modulo,
        "powers": params.powers,
        "octonion_polynomial_coefficients": params.degree,
        "octonion_component_bits": params.component_bits,
        "matrix_dimension": params.matrix_dimension,
        "matrix_polynomial_coefficients": params.matrix_degree,
        "matrix_component_bits": params.matrix_component_bits,
        "matrix_modulo_q": params.matrix_modulo,
        "submatrix_grid_dimension": params.submatrix_grid_dimension,
        "submatrix_dimension": params.submatrix_dimension,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_model": cpu_model(),
        "device_model": device_model(),
        "cpu_governor": cpu_governor(),
    }


def write_results(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(path: Path, summary: dict[str, object]) -> None:
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["metric", "value"])
        for metric, value in summary.items():
            writer.writerow([metric, value])


def run_reference_benchmark(
    repository_root: Path,
    output_directory: Path,
    executions: int,
    modulo: int,
) -> int:
    if modulo != 251:
        raise ValueError(
            "reference mode is fixed to p=251 because general/hk17_2-v2.py is frozen "
            "with p=251 selected. Do not edit the frozen reference implementation."
        )

    script_path = repository_root / "general" / "hk17_2-v2.py"
    if not script_path.is_file():
        raise FileNotFoundError(f"Frozen reference implementation not found: {script_path}")

    results_path = output_directory / "performance_reference_results.csv"
    summary_path = output_directory / "performance_reference_summary.csv"

    results: list[dict[str, object]] = []
    benchmark_start = time.perf_counter()

    print("=" * 100)
    print("HK17.2 RASPBERRY PI 3 PERFORMANCE TEST — FROZEN REFERENCE WORKLOAD")
    print("=" * 100)
    print(f"Script = {script_path}")
    print(f"Executions = {executions}")
    print("Modulus p = 251")
    print("Network/MQTT = excluded")
    print(f"Results CSV = {results_path}")
    print(f"Summary CSV = {summary_path}")
    print("=" * 100)

    for execution in range(1, executions + 1):
        wall_start = time.perf_counter()
        process = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            cwd=script_path.parent,
        )
        wall_time = time.perf_counter() - wall_start

        combined_output = process.stdout + process.stderr
        protocol_time = parse_reference_protocol_time(combined_output)
        success = (
            process.returncode == 0
            and REFERENCE_SUCCESS_MARKER in combined_output
            and protocol_time is not None
        )

        error = ""
        if not success:
            tail = combined_output.strip().splitlines()[-1:] or [""]
            error = tail[0][:500]

        results.append(
            {
                "execution": execution,
                "success": success,
                "return_code": process.returncode,
                "protocol_time_s": protocol_time if protocol_time is not None else "",
                "wall_time_s": wall_time,
                "cpu_temperature_c": cpu_temperature_c() or "",
                "cpu_frequency_mhz": cpu_frequency_mhz() or "",
                "error": error,
            }
        )

        print(
            f"[{execution:04d}/{executions}] "
            f"success={success} "
            f"protocol_time={protocol_time if protocol_time is not None else 'N/A'} "
            f"wall_time={wall_time:.6f}s"
        )

    benchmark_total_time = time.perf_counter() - benchmark_start
    successful = [row for row in results if bool(row["success"])]
    protocol_times = [float(row["protocol_time_s"]) for row in successful]
    wall_times = [float(row["wall_time_s"]) for row in successful]
    temperatures = [float(row["cpu_temperature_c"]) for row in results if row["cpu_temperature_c"] != ""]
    frequencies = [float(row["cpu_frequency_mhz"]) for row in results if row["cpu_frequency_mhz"] != ""]

    summary = common_metadata("reference", executions, modulo)
    summary.update(
        {
            "successful_executions": len(successful),
            "failed_executions": executions - len(successful),
            "success_rate_percent": (len(successful) * 100 / executions) if executions else 0.0,
            "total_benchmark_time_s": benchmark_total_time,
        }
    )
    summary.update(descriptive_stats("protocol_time", protocol_times))
    summary.update(descriptive_stats("wall_time", wall_times))
    if temperatures:
        summary.update({
            "min_cpu_temperature_c": min(temperatures),
            "max_cpu_temperature_c": max(temperatures),
            "mean_cpu_temperature_c": mean(temperatures),
        })
    if frequencies:
        summary.update({
            "min_cpu_frequency_mhz": min(frequencies),
            "max_cpu_frequency_mhz": max(frequencies),
            "mean_cpu_frequency_mhz": mean(frequencies),
        })

    write_results(
        results_path,
        results,
        [
            "execution",
            "success",
            "return_code",
            "protocol_time_s",
            "wall_time_s",
            "cpu_temperature_c",
            "cpu_frequency_mhz",
            "error",
        ],
    )
    write_summary(summary_path, summary)

    print("\n" + "=" * 100)
    print("REFERENCE PERFORMANCE SUMMARY")
    print("=" * 100)
    for metric, value in summary.items():
        print(f"{metric} = {value}")

    return 0 if len(successful) == executions else 1


def bob_matrix_stage(alice: AliceSession, rng) -> tuple[tuple[tuple[int, ...], ...], tuple[tuple[int, ...], ...]]:
    p = alice.parameters
    j = obtain_polynomial(MATRIX_DEGREE, p.matrix_modulo, rng)
    J = calculate_matrix_polynomial(
        alice.A,
        j,
        MATRIX_DIMENSION,
        p.matrix_modulo,
    )
    if J == matrix_null(MATRIX_DIMENSION):
        raise ValueError("J = j(A) is the null matrix")

    J_u = matrix_power(J, alice.u, MATRIX_DIMENSION, p.matrix_modulo)
    J_v = matrix_power(J, alice.v, MATRIX_DIMENSION, p.matrix_modulo)

    TB = matrix_multiply(
        matrix_multiply(J_u, alice.B, MATRIX_DIMENSION, p.matrix_modulo),
        J_v,
        MATRIX_DIMENSION,
        p.matrix_modulo,
    )
    MB = matrix_multiply(
        matrix_multiply(J_u, alice.TA, MATRIX_DIMENSION, p.matrix_modulo),
        J_v,
        MATRIX_DIMENSION,
        p.matrix_modulo,
    )

    if MB == matrix_null(MATRIX_DIMENSION):
        raise ValueError("The shared matrix MB is null")

    return TB, MB


def bob_octonion_stage(
    alice: AliceSession,
    MB: Sequence[Sequence[int]],
    rng,
) -> tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]]:
    p = alice.parameters

    _, candidates = generate_octonion_candidates(
        MB,
        p.modulo,
        p.submatrix_grid_dimension,
        p.submatrix_dimension,
    )
    _, oB = select_first_invertible_octonion(candidates)
    if oB is None:
        raise ValueError("None of the four Bob oB candidates is invertible")

    n = rng.randrange(2, POWERS)
    h = obtain_polynomial(p.degree, p.modulo, rng)
    oS2 = tuple(rng.randrange(p.modulo) for _ in range(8))

    h_oA = calculate_f(alice.oA, h, p.modulo)
    shifted = summ(scale(alice.oA, -1, p.modulo), oS2, p.modulo)
    h_shifted = calculate_f(shifted, h, p.modulo)
    h1 = power(h_oA, n, p.modulo)
    h2 = power(h_shifted, n, p.modulo)
    h_autoconvolution = multiply(h1, h2, p.modulo)
    rB = multiply(h_autoconvolution, oB, p.modulo)

    if alice.rA is None:
        raise RuntimeError("Alice rA is unavailable")

    oB_inverse = octonion_reciprocal(oB, p.modulo)
    recovered_f = multiply(alice.rA, oB_inverse, p.modulo)
    kB = multiply(recovered_f, rB, p.modulo)

    if kB == O_NULL:
        raise ValueError("The generated Bob session key is null")

    return tuple(rB), tuple(kB), tuple(oB)


def run_kms_benchmark(
    output_directory: Path,
    executions: int,
    modulo: int,
) -> int:
    results_path = output_directory / "performance_kms_results.csv"
    summary_path = output_directory / "performance_kms_summary.csv"
    rng = randomlib.SystemRandom()

    results: list[dict[str, object]] = []
    benchmark_start = time.perf_counter()

    print("=" * 100)
    print("HK17.2 RASPBERRY PI 3 PERFORMANCE TEST — ALICE/KMS CRYPTOGRAPHIC ROLE")
    print("=" * 100)
    print(f"Executions = {executions}")
    print(f"Modulus p = {modulo}")
    print("Network/MQTT/HTTP/serialization = excluded")
    print("Bob is a local untimed driver used only to supply TB and rB.")
    print(f"Results CSV = {results_path}")
    print(f"Summary CSV = {summary_path}")
    print("=" * 100)

    for execution in range(1, executions + 1):
        session_wall_start = time.perf_counter()
        setup_time = 0.0
        tb_time = 0.0
        rb_time = 0.0
        selected_oB = ""
        error = ""
        success = False

        try:
            t0 = time.perf_counter()
            alice = AliceSession.create_random(modulo, rng=rng)
            setup_time = time.perf_counter() - t0

            # Bob's matrix work drives the protocol but is not part of the
            # Raspberry Pi Alice/KMS primary timing.
            TB, MB = bob_matrix_stage(alice, rng)

            t0 = time.perf_counter()
            alice.receive_tb(TB, rng=rng)
            tb_time = time.perf_counter() - t0

            if alice.MA != MB:
                raise ValueError("Matrix exchange failure: MA != MB")

            rB, kB, bob_oB = bob_octonion_stage(alice, MB, rng)

            if alice.oB != bob_oB:
                raise ValueError("Alice and Bob derived different oB values")

            t0 = time.perf_counter()
            kA = alice.receive_rb(rB)
            rb_time = time.perf_counter() - t0

            if tuple(kA) != tuple(kB):
                raise ValueError("HK17.2 failure: kA != kB")

            selected_oB = alice.selected_oB_configuration or ""
            success = True

        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"[:500]

        alice_total_time = setup_time + tb_time + rb_time
        session_wall_time = time.perf_counter() - session_wall_start

        results.append(
            {
                "execution": execution,
                "success": success,
                "alice_matrix_setup_time_s": setup_time,
                "alice_tb_processing_time_s": tb_time,
                "alice_rb_processing_time_s": rb_time,
                "alice_total_time_s": alice_total_time,
                "session_wall_time_s": session_wall_time,
                "selected_oB_configuration": selected_oB,
                "cpu_temperature_c": cpu_temperature_c() or "",
                "cpu_frequency_mhz": cpu_frequency_mhz() or "",
                "error": error,
            }
        )

        print(
            f"[{execution:04d}/{executions}] "
            f"success={success} "
            f"alice_total={alice_total_time:.6f}s "
            f"wall={session_wall_time:.6f}s"
            + (f" error={error}" if error else "")
        )

    benchmark_total_time = time.perf_counter() - benchmark_start
    successful = [row for row in results if bool(row["success"])]

    def values(name: str) -> list[float]:
        return [float(row[name]) for row in successful]

    summary = common_metadata("kms", executions, modulo)
    summary.update(
        {
            "timing_scope": "Alice/KMS cryptographic computation only; Bob driver and all transport excluded",
            "successful_executions": len(successful),
            "failed_executions": executions - len(successful),
            "success_rate_percent": (len(successful) * 100 / executions) if executions else 0.0,
            "total_benchmark_time_s": benchmark_total_time,
        }
    )
    summary.update(descriptive_stats("alice_total_time", values("alice_total_time_s")))
    summary.update(descriptive_stats("alice_matrix_setup_time", values("alice_matrix_setup_time_s")))
    summary.update(descriptive_stats("alice_tb_processing_time", values("alice_tb_processing_time_s")))
    summary.update(descriptive_stats("alice_rb_processing_time", values("alice_rb_processing_time_s")))
    summary.update(descriptive_stats("session_wall_time", values("session_wall_time_s")))
    temperatures = [float(row["cpu_temperature_c"]) for row in results if row["cpu_temperature_c"] != ""]
    frequencies = [float(row["cpu_frequency_mhz"]) for row in results if row["cpu_frequency_mhz"] != ""]
    if temperatures:
        summary.update({
            "min_cpu_temperature_c": min(temperatures),
            "max_cpu_temperature_c": max(temperatures),
            "mean_cpu_temperature_c": mean(temperatures),
        })
    if frequencies:
        summary.update({
            "min_cpu_frequency_mhz": min(frequencies),
            "max_cpu_frequency_mhz": max(frequencies),
            "mean_cpu_frequency_mhz": mean(frequencies),
        })

    write_results(
        results_path,
        results,
        [
            "execution",
            "success",
            "alice_matrix_setup_time_s",
            "alice_tb_processing_time_s",
            "alice_rb_processing_time_s",
            "alice_total_time_s",
            "session_wall_time_s",
            "selected_oB_configuration",
            "cpu_temperature_c",
            "cpu_frequency_mhz",
            "error",
        ],
    )
    write_summary(summary_path, summary)

    print("\n" + "=" * 100)
    print("ALICE/KMS PERFORMANCE SUMMARY")
    print("=" * 100)
    for metric, value in summary.items():
        print(f"{metric} = {value}")

    return 0 if len(successful) == executions else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HK17.2 Raspberry Pi 3 local performance benchmark")
    parser.add_argument(
        "--mode",
        choices=("reference", "kms"),
        default="reference",
        help="reference = direct PC-comparable frozen workload; kms = deployed Alice/KMS role",
    )
    parser.add_argument("--executions", type=int, default=DEFAULT_EXECUTIONS)
    parser.add_argument("--modulo", type=int, default=DEFAULT_MODULO)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.executions <= 0:
        raise ValueError("--executions must be greater than zero")

    script_path = Path(__file__).resolve()
    output_directory = script_path.parent
    repository_root = output_directory.parent

    if args.mode == "reference":
        return run_reference_benchmark(
            repository_root,
            output_directory,
            args.executions,
            args.modulo,
        )

    return run_kms_benchmark(output_directory, args.executions, args.modulo)


if __name__ == "__main__":
    raise SystemExit(main())
