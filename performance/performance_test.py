import csv
import re
import subprocess
import sys
import time
from pathlib import Path
from statistics import mean, median, stdev


SCRIPT_NAME = "hk17_2-v2.py"
EXECUTIONS = 1000

RESULTS_CSV = "performance_results.csv"
SUMMARY_CSV = "performance_summary.csv"


def parse_protocol_time(output):
    match = re.search(
        r"Time\s*=\s*(\d+):(\d+):(\d+(?:\.\d+)?)",
        output
    )

    if match is None:
        return None

    hours = int(match.group(1))
    minutes = int(match.group(2))
    seconds = float(match.group(3))

    return hours * 3600 + minutes * 60 + seconds


def percentile(values, percentile_value):
    if not values:
        return None

    ordered = sorted(values)

    if len(ordered) == 1:
        return ordered[0]

    position = (len(ordered) - 1) * percentile_value
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower

    return (
        ordered[lower]
        + (ordered[upper] - ordered[lower]) * fraction
    )


base_path = Path(__file__).resolve().parent
project_root = base_path.parent

script_path = project_root / "general" / SCRIPT_NAME

results_csv_path = base_path / RESULTS_CSV
summary_csv_path = base_path / SUMMARY_CSV

results = []

benchmark_start = time.perf_counter()

print("=" * 100)
print("HK17.2 PERFORMANCE TEST")
print("=" * 100)
print("Script =", script_path)
print("Executions =", EXECUTIONS)
print("Results CSV =", results_csv_path)
print("Summary CSV =", summary_csv_path)
print("=" * 100)

for execution in range(1, EXECUTIONS + 1):
    wall_start = time.perf_counter()

    process = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        cwd=script_path.parent
    )

    wall_time = time.perf_counter() - wall_start

    combined_output = process.stdout + process.stderr
    protocol_time = parse_protocol_time(combined_output)

    success = (
        process.returncode == 0
        and
        "SUCCESS!!! Alice and Bob generated the same key."
        in combined_output
        and protocol_time is not None
    )

    results.append(
        {
            "execution": execution,
            "success": success,
            "return_code": process.returncode,
            "protocol_time_s": protocol_time,
            "wall_time_s": wall_time
        }
    )

    print(
        f"[{execution:04d}/{EXECUTIONS}] "
        f"success={success} "
        f"protocol_time="
        f"{protocol_time if protocol_time is not None else 'N/A'} "
        f"wall_time={wall_time:.6f}s"
    )

benchmark_total_time = time.perf_counter() - benchmark_start

with open(
    results_csv_path,
    "w",
    newline="",
    encoding="utf-8"
) as csv_file:

    writer = csv.DictWriter(
        csv_file,
        fieldnames=[
            "execution",
            "success",
            "return_code",
            "protocol_time_s",
            "wall_time_s"
        ]
    )

    writer.writeheader()
    writer.writerows(results)

successful_results = [
    row
    for row in results
    if row["success"]
]

protocol_times = [
    row["protocol_time_s"]
    for row in successful_results
    if row["protocol_time_s"] is not None
]

wall_times = [
    row["wall_time_s"]
    for row in successful_results
]

summary = {
    "executions_requested": EXECUTIONS,
    "successful_executions": len(successful_results),
    "failed_executions": EXECUTIONS - len(successful_results),
    "success_rate_percent": (
        len(successful_results) * 100 / EXECUTIONS
        if EXECUTIONS > 0
        else 0
    ),
    "total_benchmark_time_s": benchmark_total_time
}

if protocol_times:
    summary.update(
        {
            "mean_protocol_time_s": mean(protocol_times),
            "median_protocol_time_s": median(protocol_times),
            "std_protocol_time_s": (
                stdev(protocol_times)
                if len(protocol_times) > 1
                else 0.0
            ),
            "min_protocol_time_s": min(protocol_times),
            "max_protocol_time_s": max(protocol_times),
            "p95_protocol_time_s": percentile(
                protocol_times,
                0.95
            )
        }
    )

if wall_times:
    summary.update(
        {
            "mean_wall_time_s": mean(wall_times),
            "median_wall_time_s": median(wall_times),
            "std_wall_time_s": (
                stdev(wall_times)
                if len(wall_times) > 1
                else 0.0
            ),
            "min_wall_time_s": min(wall_times),
            "max_wall_time_s": max(wall_times),
            "p95_wall_time_s": percentile(
                wall_times,
                0.95
            )
        }
    )

with open(
    summary_csv_path,
    "w",
    newline="",
    encoding="utf-8"
) as csv_file:

    writer = csv.writer(csv_file)

    writer.writerow(
        [
            "metric",
            "value"
        ]
    )

    for metric, value in summary.items():
        writer.writerow(
            [
                metric,
                value
            ]
        )

print("\n" + "=" * 100)
print("PERFORMANCE SUMMARY")
print("=" * 100)

for metric, value in summary.items():
    print(f"{metric} = {value}")

print("\nFiles generated:")
print(results_csv_path)
print(summary_csv_path)