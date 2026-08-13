#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VECTORS_DIR = ROOT / "general" / "test_vectors"
OUTPUT = Path(__file__).resolve().parents[1] / "include" / "canonical_vectors.hpp"

VECTOR_FILES = [
    "test_vector_p13.json",
    "test_vector_p251.json",
    "test_vector_p65521.json",
    "test_vector_p4294967279.json",
    "test_vector_p18446744073709551557.json",
]


def u64(value: int) -> str:
    return f"{int(value)}ULL"


def flatten_matrix(matrix):
    return [int(v) for row in matrix for v in row]


def coeffs(polynomial):
    return [int(term[0]) for term in polynomial]


def emit_array(name: str, values, ctype="std::uint64_t", per_line=8):
    values = list(values)
    lines = [f"inline constexpr {ctype} {name}[{len(values)}] = {{"]
    for i in range(0, len(values), per_line):
        chunk = values[i:i+per_line]
        if ctype == "std::uint8_t":
            rendered = ", ".join(str(int(v)) for v in chunk)
        else:
            rendered = ", ".join(u64(v) for v in chunk)
        lines.append("    " + rendered + ("," if i + per_line < len(values) else ""))
    lines.append("};")
    return "\n".join(lines)


def main():
    if not VECTORS_DIR.exists():
        raise SystemExit(f"Canonical vector directory not found: {VECTORS_DIR}")

    out = []
    out.append("#pragma once")
    out.append("")
    out.append("#include <array>")
    out.append("#include <cstddef>")
    out.append("#include <cstdint>")
    out.append("")
    out.append("namespace hk17::canonical {")
    out.append("")
    out.append("struct BobVector {")
    out.append("    const char* name;")
    out.append("    const char* source_sha256;")
    out.append("    std::uint64_t p;")
    out.append("    std::uint64_t q;")
    out.append("    std::uint64_t u;")
    out.append("    std::uint64_t v;")
    out.append("    std::uint64_t n;")
    out.append("    std::size_t octonion_degree;")
    for field in [
        "A", "B", "TA", "j_coefficients", "h_coefficients", "oA", "oS2", "rA",
        "expected_J", "expected_J_u", "expected_J_v", "expected_TB", "expected_MB",
        "expected_submatrix_sums", "expected_candidates", "expected_candidate_norms",
        "expected_candidate_invertible", "expected_oB", "expected_oB_inverse",
        "expected_shifted", "expected_h_oA", "expected_h_shifted", "expected_h1", "expected_h2",
        "expected_h_autoconvolution", "expected_rB", "expected_recovered_f", "expected_kB",
    ]:
        if field == "expected_candidate_invertible":
            out.append(f"    const std::uint8_t* {field};")
        else:
            out.append(f"    const std::uint64_t* {field};")
    out.append("    std::size_t selected_oB_configuration;")
    out.append("};")
    out.append("")

    vector_symbols = []

    for filename in VECTOR_FILES:
        path = VECTORS_DIR / filename
        data = json.loads(path.read_text(encoding="utf-8"))
        p = int(data["parameters"]["modulo"])
        sym = f"v_{p}"
        vector_symbols.append(sym)
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        inputs = data["inputs"]
        expected = data["expected"]

        out.append(f"// Source: {filename}")
        out.append(f"// SHA-256: {sha}")
        arrays = {
            "A": flatten_matrix(inputs["A"]),
            "B": flatten_matrix(inputs["B"]),
            "TA": flatten_matrix(expected["TA"]),
            "j_coefficients": coeffs(inputs["j"]),
            "h_coefficients": coeffs(inputs["h"]),
            "oA": inputs["oA"],
            "oS2": inputs["oS2"],
            "rA": expected["rA"],
            "expected_J": flatten_matrix(expected["J"]),
            "expected_J_u": flatten_matrix(expected["J_u"]),
            "expected_J_v": flatten_matrix(expected["J_v"]),
            "expected_TB": flatten_matrix(expected["TB"]),
            "expected_MB": flatten_matrix(expected["MB"]),
            "expected_submatrix_sums": [v for row in expected["submatrix_sums"] for v in row],
            "expected_candidates": [v for c in expected["oB_candidates"] for v in c["octonion"]],
            "expected_candidate_norms": [c["norm_squared"] for c in expected["oB_candidates"]],
            "expected_candidate_invertible": [1 if c["invertible"] else 0 for c in expected["oB_candidates"]],
            "expected_oB": expected["oB"],
            "expected_oB_inverse": expected["oB_inverse"],
            "expected_shifted": expected["negative_oA_plus_oS2"],
            "expected_h_oA": expected["h_oA"],
            "expected_h_shifted": expected["h_negative_oA_plus_oS2"],
            "expected_h1": expected["h1"],
            "expected_h2": expected["h2"],
            "expected_h_autoconvolution": expected["h_autoconvolution"],
            "expected_rB": expected["rB"],
            "expected_recovered_f": expected["recovered_f_autoconvolution"],
            "expected_kB": expected["kB"],
        }

        for key, values in arrays.items():
            ctype = "std::uint8_t" if key == "expected_candidate_invertible" else "std::uint64_t"
            per_line = 16 if ctype == "std::uint8_t" else 8
            out.append(emit_array(f"{sym}_{key}", values, ctype=ctype, per_line=per_line))
            out.append("")

        params = data["parameters"]
        out.append(f"inline constexpr BobVector {sym} = {{")
        out.append(f'    "{filename}",')
        out.append(f'    "{sha}",')
        out.append(f"    {u64(p)},")
        out.append(f"    {u64(params['matrix_modulo'])},")
        out.append(f"    {u64(inputs['u'])},")
        out.append(f"    {u64(inputs['v'])},")
        out.append(f"    {u64(inputs['n'])},")
        out.append(f"    {int(params['degree'])},")
        for key in arrays:
            out.append(f"    {sym}_{key},")
        out.append(f"    {int(expected['selected_oB_configuration'])}")
        out.append("};")
        out.append("")

    out.append("inline constexpr std::array<const BobVector*, 5> ALL = {")
    for sym in vector_symbols:
        out.append(f"    &{sym},")
    out.append("};")
    out.append("")
    out.append("}  // namespace hk17::canonical")
    out.append("")

    OUTPUT.write_text("\n".join(out), encoding="utf-8")
    print(f"Generated {OUTPUT}")


if __name__ == "__main__":
    main()
