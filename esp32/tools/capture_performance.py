#!/usr/bin/env python3
"""Capture HK17.2 ESP32 performance output and generate CSV files.

The ESP32 performance firmware emits machine-readable HK17_PERF_* records.
This collector keeps serial I/O outside the cryptographic timing and writes:

- <device_id>_performance_results.csv
- <device_id>_performance_summary.csv

The benchmark itself runs entirely on the ESP32.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
import time
from pathlib import Path
from statistics import mean, median, stdev

try:
    import serial
except ImportError as exc:
    raise SystemExit(
        "pyserial is required. Install it with:\n"
        "  python3 -m pip install -r esp32/tools/requirements.txt"
    ) from exc


RESULT_FIELDS = [
    "execution",
    "success",
    "total_time_us",
    "matrix_polynomial_us",
    "matrix_exchange_us",
    "ob_derivation_us",
    "octonion_stage_us",
    "key_recovery_us",
    "heap_before_bytes",
    "heap_after_bytes",
    "heap_min_since_boot_bytes",
]


def parse_key_values(payload: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in payload.split(","):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def percentile(values: list[float], percentile_value: float) -> float | None:
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


def descriptive_stats(prefix: str, values: list[float]) -> dict[str, float]:
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


def write_results(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = RESULT_FIELDS + [
        "total_time_s",
        "matrix_polynomial_s",
        "matrix_exchange_s",
        "ob_derivation_s",
        "octonion_stage_s",
        "key_recovery_s",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(path: Path, summary: dict[str, object]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["metric", "value"])
        for key, value in summary.items():
            writer.writerow([key, value])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", required=True, help="Serial port, e.g. /dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parent.parent / "performance"),
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 100)
    print("HK17.2 ESP32 PERFORMANCE CAPTURE")
    print("=" * 100)
    print(f"Serial port = {args.port}")
    print(f"Baud = {args.baud}")
    print(f"Output directory = {output_dir}")
    print()
    print("Waiting for HK17_PERF_READY.")
    print("If the benchmark firmware already booted, press EN/RESET on the ESP32.")
    print("=" * 100)

    metadata: dict[str, str] = {}
    done_metadata: dict[str, str] = {}
    rows: list[dict[str, object]] = []
    ready_seen = False
    capture_start = time.perf_counter()

    with serial.Serial(args.port, args.baud, timeout=1) as ser:
        while True:
            raw = ser.readline()
            if not raw:
                continue

            line = raw.decode("utf-8", errors="replace").strip()
            if not line:
                continue

            print(line)

            if line.startswith("HK17_PERF_META,"):
                # A META record marks a new firmware benchmark run. Discard any
                # partial/stale records that may have been buffered from an
                # earlier boot before the collector attached.
                metadata = parse_key_values(line.split(",", 1)[1])
                done_metadata.clear()
                rows.clear()
                ready_seen = False
                continue

            if line == "HK17_PERF_READY":
                # Start a clean capture window. This is especially important
                # when the user presses EN/RESET after opening the collector:
                # serial buffers may still contain RESULT records from the
                # previous automatic boot.
                rows.clear()
                done_metadata.clear()
                ready_seen = True
                capture_start = time.perf_counter()
                continue

            if line.startswith("HK17_PERF_RESULT,"):
                if not ready_seen:
                    # Ignore stale/partial records until the current run has
                    # explicitly announced HK17_PERF_READY.
                    continue
                parts = line.split(",")
                if len(parts) != 12:
                    print(f"WARNING: malformed result line ignored: {line}", file=sys.stderr)
                    continue

                numeric = [int(value) for value in parts[1:]]
                row: dict[str, object] = dict(zip(RESULT_FIELDS, numeric))
                row["success"] = bool(row["success"])

                for source, target in (
                    ("total_time_us", "total_time_s"),
                    ("matrix_polynomial_us", "matrix_polynomial_s"),
                    ("matrix_exchange_us", "matrix_exchange_s"),
                    ("ob_derivation_us", "ob_derivation_s"),
                    ("octonion_stage_us", "octonion_stage_s"),
                    ("key_recovery_us", "key_recovery_s"),
                ):
                    row[target] = float(row[source]) / 1_000_000.0

                rows.append(row)
                continue

            if line.startswith("HK17_PERF_DONE,"):
                done_metadata = parse_key_values(line.split(",", 1)[1])
                break

    capture_wall_time = time.perf_counter() - capture_start

    if not ready_seen:
        raise SystemExit("HK17_PERF_READY was not observed.")
    if not metadata:
        raise SystemExit("HK17_PERF_META was not observed.")
    if not rows:
        raise SystemExit("No HK17_PERF_RESULT rows were captured.")

    device_id = metadata.get("device_id", "esp32-unknown")
    results_path = output_dir / f"{device_id}_performance_results.csv"
    summary_path = output_dir / f"{device_id}_performance_summary.csv"

    successful_rows = [row for row in rows if bool(row["success"])]

    summary: dict[str, object] = {
        "benchmark_mode": "esp32_bob_local_crypto",
        "workload": "frozen canonical p=251 Bob computation",
        "network_mqtt_http_included": False,
        **metadata,
        "results_captured": len(rows),
        "successful_executions": len(successful_rows),
        "failed_executions": len(rows) - len(successful_rows),
        "success_rate_percent": (100.0 * len(successful_rows) / len(rows)) if rows else 0.0,
        "collector_wall_time_s": capture_wall_time,
    }

    for key, value in done_metadata.items():
        summary[f"device_{key}"] = value

    timing_columns = [
        "total_time_s",
        "matrix_polynomial_s",
        "matrix_exchange_s",
        "ob_derivation_s",
        "octonion_stage_s",
        "key_recovery_s",
    ]
    for column in timing_columns:
        values = [float(row[column]) for row in successful_rows]
        prefix = "protocol_time" if column == "total_time_s" else column.removesuffix("_s")
        summary.update(descriptive_stats(prefix, values))

    heap_before = [int(row["heap_before_bytes"]) for row in rows]
    heap_after = [int(row["heap_after_bytes"]) for row in rows]
    heap_min = [int(row["heap_min_since_boot_bytes"]) for row in rows]

    summary.update(
        {
            "min_heap_before_bytes": min(heap_before),
            "max_heap_before_bytes": max(heap_before),
            "mean_heap_before_bytes": mean(heap_before),
            "min_heap_after_bytes": min(heap_after),
            "max_heap_after_bytes": max(heap_after),
            "mean_heap_after_bytes": mean(heap_after),
            "minimum_heap_since_boot_bytes": min(heap_min),
        }
    )

    write_results(results_path, rows)
    write_summary(summary_path, summary)

    print("\n" + "=" * 100)
    print("ESP32 PERFORMANCE SUMMARY")
    print("=" * 100)
    for key, value in summary.items():
        print(f"{key} = {value}")
    print("\nFiles generated:")
    print(results_path)
    print(summary_path)

    return 0 if len(successful_rows) == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
