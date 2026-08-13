# HK17.2

HK17.2 is an experimental post-quantum key exchange protocol based on modular octonion arithmetic, polynomial matrix exchange, secret displacement, and discrete modular pointwise self-convolution.

The protocol extends the HK17 family by incorporating a polynomial matrix exchange over a modular matrix ring. Alice and Bob independently obtain the same shared matrix and deterministically derive from it a private shared octonion `oB`. Since `oB` is not transmitted through the public channel in the definitive HK17.2 construction, the protocol prevents its direct cancellation from the public octonion tokens.

## Research context

This repository contains the experimental software associated with the doctoral research project:

**Design, Development, and Cryptanalysis of a Key Exchange Protocol Based on Hypercomplex Numbers and Modular Discrete Convolution and Noncommutative Matrix Rings**

Universidad Abierta Interamericana  
PhD in Computer Science

---

## Main components

- Modular arithmetic over octonions.
- Non-commutative and non-associative algebraic operations.
- Polynomial matrix exchange over modular matrix rings.
- Deterministic derivation of the private shared octonion `oB`.
- Secret octonion displacements.
- Discrete modular pointwise self-convolution.
- Experimental cryptanalysis of HK17 and HK17.2.
- General-purpose hardware performance evaluation.
- Statistical and experimental security analysis.
- Official deterministic canonical test vectors for all selectable HK17.2 octonion moduli.
- Raspberry Pi 3/Alice-KMS implementation in Python.
- ESP32/Bob implementation in C++ using PlatformIO and ESP-IDF.
- Binary MQTT transport between the Raspberry Pi 3 KMS and ESP32 nodes.
- Cross-platform implementation-conformance validation against the canonical test vectors.

## Current development status

The definitive HK17.2 Python implementation, cryptanalytic experiments, general-purpose hardware performance benchmark, statistical security analysis, complete numerical example, and five canonical conformance vectors are available in the repository.

The distributed embedded implementation is also functional:

1. The Raspberry Pi 3/Alice-KMS port is implemented in Python.
2. The Raspberry Pi 3 implementation reproduces all five official canonical test vectors.
3. The binary wire representation used by the distributed implementation reproduces all five official canonical test vectors.
4. The ESP32/Bob port is implemented in C++ using PlatformIO and ESP-IDF.
5. The C++ port reproduces all five official canonical test vectors in the native PlatformIO environment.
6. Both physical ESP32 devices reproduce all five canonical vectors on hardware.
7. A Raspberry Pi 3 running the Alice-KMS and Mosquitto broker has completed real HK17.2 exchanges with both ESP32 nodes over Wi-Fi/MQTT.
8. In both physical-node experiments, Alice and Bob independently derived the same session key.

The implementation methodology followed by the project is:

```text
frozen reference implementation
        ↓
official canonical test vectors
        ↓
Raspberry Pi 3 / ESP32 conformance
        ↓
distributed integration
        ↓
performance evaluation
```

The next experimental stage is the controlled performance evaluation of the Raspberry Pi 3, ESP32, and complete distributed exchange.


---

## Repository structure

```text
HK17.2/
├── attacks/
│   ├── bernstein_li-attack.py
│   ├── cayley_hamilton-attack.py
│   ├── exhaustive_attack.py
│   └── oB_cancellation-attack.py
├── esp32/
│   ├── .gitignore
│   ├── README.md
│   ├── platformio.ini
│   ├── sdkconfig.defaults
│   ├── include/
│   │   ├── canonical_vectors.hpp
│   │   ├── hk17_math.hpp
│   │   ├── hk17_network_config.hpp
│   │   ├── hk17_wire.hpp
│   │   └── network_secrets.example.hpp
│   ├── src/
│   │   ├── hk17_math.cpp
│   │   ├── hk17_wire.cpp
│   │   ├── idf_component.yml
│   │   ├── main.cpp
│   │   └── network_main.cpp
│   └── tools/
│       └── generate_canonical_header.py
├── general/
│   ├── hk17_2-v2.py
│   ├── octonions.py
│   └── test_vectors/
│       ├── generate_test_vectors.py
│       ├── README.md
│       ├── SHA256SUMS
│       ├── test_vector_p13.json
│       ├── test_vector_p251.json
│       ├── test_vector_p65521.json
│       ├── test_vector_p4294967279.json
│       ├── test_vector_p18446744073709551557.json
│       ├── validate_test_vectors.py
│       └── vector_core.py
├── HK17.2.code-workspace
├── old/
│   ├── hk17_2-v1.py
│   └── hk17.py
├── performance/
│   ├── performance_results.csv
│   ├── performance_summary.csv
│   └── performance_test.py
├── properties/
│   ├── non_commutativity.py
│   ├── non_distributibity.py
│   └── octonion_times_inverse.py
├── raspberry/
│   ├── README.md
│   ├── bob_simulator.py
│   ├── conformance_test.py
│   ├── hk17_math.py
│   ├── kms.py
│   ├── kms_server.py
│   ├── mosquitto.conf
│   ├── requirements.txt
│   ├── wire.py
│   └── wire_conformance_test.py
├── security/
│   ├── analyze_security_results.py
│   ├── derived_security_summary.csv
│   ├── exponent_diversity.csv
│   ├── keyspace_period_analysis.py
│   ├── keyspace_summary.csv
│   ├── matrix_distribution.csv
│   ├── norm_correlation.csv
│   ├── norm_distribution.csv
│   ├── ob_candidates.csv
│   ├── octonion_layer_full.csv
│   ├── octonion_layer_full_summary.csv
│   ├── octonion_power_classes.csv
│   ├── octonion_security_analysis.py
│   ├── security_analysis.py
│   └── security_summary.csv
└── README.md
```


Python `__pycache__/` directories are runtime-generated artifacts and are intentionally omitted from the repository map above.

The repository uses a single octonion arithmetic module:

```text
general/octonions.py
```

Scripts located outside `general/` that require octonion operations resolve this shared implementation from that directory.

## Repository contents

### Definitive protocol implementation

- `general/hk17_2-v2.py`: definitive and frozen HK17.2 research implementation.
- `general/octonions.py`: unique octonion arithmetic and auxiliary-function module used by the repository.

The definitive protocol implementation is the reference semantics for the project and is not modified for the Raspberry Pi 3 or ESP32 ports. Platform-specific implementations must reproduce its behavior.

### Canonical test vectors

The `general/test_vectors/` directory contains the official deterministic conformance vectors for the frozen HK17.2 implementation. One canonical vector is provided for each selectable octonion modulus supported by the definitive protocol:

| Canonical vector | Octonion modulus $p$ | Component size | Octonion polynomial coefficients | Matrix modulus $q$ |
|---|---:|---:|---:|---:|
| `test_vector_p13.json` | 13 | 4 bits | 8 | 4 |
| `test_vector_p251.json` | 251 | 8 bits | 16 | 16 |
| `test_vector_p65521.json` | 65521 | 16 bits | 32 | 256 |
| `test_vector_p4294967279.json` | 4294967279 | 32 bits | 64 | 65536 |
| `test_vector_p18446744073709551557.json` | 18446744073709551557 | 64 bits | 128 | 4294967296 |

Each vector stores fixed protocol inputs and the expected intermediate and final values for a complete deterministic execution. The stored results cover the matrix polynomial evaluations, matrix powers, matrix tokens `TA` and `TB`, shared matrices `MA` and `MB`, the shared matrix `M`, the sixteen submatrix sums, the four deterministic `oB` candidates, the selected `oB`, octonion polynomial evaluations, powered values, self-convolutions, public tokens `rA` and `rB`, Alice's self-convolution recovered by Bob, and the final session keys.

All five vectors have been validated successfully against the frozen reference implementation:

```text
[PASS] test_vector_p13.json
[PASS] test_vector_p251.json
[PASS] test_vector_p65521.json
[PASS] test_vector_p4294967279.json
[PASS] test_vector_p18446744073709551557.json

SUCCESS: all five HK17.2 canonical test vectors match the frozen reference implementation.
```

The five JSON files are now the official canonical HK17.2 test vectors for this project. They are frozen and are not regenerated during normal validation.

- `validate_test_vectors.py` loads the fixed inputs from each canonical JSON file, recomputes the protocol operations, and compares the calculated values against the stored expected values.
- `generate_test_vectors.py` is retained for provenance and controlled reconstruction. Regeneration is not part of the normal validation workflow.
- `SHA256SUMS` stores integrity hashes for the official JSON vectors.
- JSON is used only as a machine-readable repository format for the conformance material; it is not part of the HK17.2 communication protocol.

The same canonical vectors are used as the conformance reference for the Raspberry Pi 3/KMS and ESP32 ports. No independent platform-specific test-vector sets are introduced. The Raspberry Pi 3 port, binary wire representation, native C++ port, and both physical ESP32 devices have successfully reproduced the corresponding canonical results.

### Cryptanalytic experiments

The `attacks/` directory contains experimental attacks against the protocol versions for which each attack was designed.

- `attacks/bernstein_li-attack.py`: applies the Bernstein-Li-style linearization analysis to the original HK17 construction and to the definitive HK17.2 v2 construction for comparison.
- `attacks/cayley_hamilton-attack.py`: Cayley-Hamilton-type matrix-factor recovery experiment against the definitive HK17.2 v2 matrix layer.
- `attacks/exhaustive_attack.py`: exhaustive search over ordered left-associated products of public elements against HK17.2 v1, where `oB` is available.
- `attacks/oB_cancellation-attack.py`: direct cancellation attack against HK17.2 v1, demonstrating that knowledge of an invertible public `oB` enables recovery of the shared key.

The target versions are therefore:

| Attack | Target protocol |
|---|---|
| Bernstein-Li-style linearization | Original HK17 and HK17.2 v2 |
| Cayley-Hamilton-type attack | HK17.2 v2 |
| Exhaustive public-element attack | HK17.2 v1 |
| `oB` cancellation attack | HK17.2 v1 |

The exhaustive attack does not enumerate arbitrary octonionic expressions. It evaluates ordered products of lengths 2, 3, and 4 formed from the available public elements using left-associated multiplication.

### Security analysis

The `security/` directory contains the statistical and experimental security analysis of the definitive HK17.2 construction.

The current analysis includes:

- shared-matrix coefficient distributions;
- deterministic `oB` candidate behavior and norm distributions;
- candidate-norm correlations;
- full octonion-layer intermediate-value analysis;
- private-exponent diversity and exponent power classes;
- nominal private-parameter spaces;
- session-key space and empirical key diversity;
- derived security summaries.

The generated CSV files contain the raw and summarized experimental results used by the current research analysis. These experiments complement the attack-specific scripts in `attacks/`; they do not constitute a formal cryptographic security proof.

### Algebraic experiments

- `properties/non_commutativity.py`: experimental verification of octonion non-commutativity.
- `properties/non_distributibity.py`: experimental verification that exponentiation does not distribute over octonion multiplication in the tested construction.
- `properties/octonion_times_inverse.py`: experimental verification of multiplication of an octonion by its multiplicative inverse.

### Performance evaluation

- `performance/performance_test.py`: benchmark harness for independent executions of `general/hk17_2-v2.py`.
- `performance/performance_results.csv`: raw results from the benchmark.
- `performance/performance_summary.csv`: statistical summary of the benchmark.

The general-purpose hardware benchmark currently consists of 1000 independent executions of the definitive HK17.2 implementation.

| Metric | Result |
|---|---:|
| Executions | 1000 |
| Successful executions | 1000 |
| Observed success rate | 100% |
| Mean protocol execution time | 0.128664 s |
| Median protocol execution time | 0.128403 s |
| Standard deviation | 0.009181 s |
| Minimum execution time | 0.101773 s |
| Maximum execution time | 0.201470 s |
| 95th percentile | 0.141965 s |

The benchmark was performed on Ubuntu (Xubuntu) 24.04.4 LTS x86_64 using Python 3.12.3, an Intel Core i7-13620H processor, and 64 GB of RAM. No GPU acceleration was used.

Equivalent controlled benchmarks for the Raspberry Pi 3 and ESP32 implementations, followed by an end-to-end distributed-session benchmark, are the next experimental stage.

### Embedded and KMS implementations

The distributed implementation preserves the frozen HK17.2 protocol semantics while assigning the Alice role to a Raspberry Pi 3 KMS and the Bob role to two physical ESP32 nodes.

#### Raspberry Pi 3 / Alice-KMS

The Raspberry Pi 3 implementation is located in `raspberry/` and is written in Python. The tested platform uses 64-bit Raspberry Pi OS with Python 3.11.2.

The KMS implementation includes:

- the independent Alice-side HK17.2 mathematical port;
- in-memory session management;
- binary serialization and deserialization of protocol values;
- an MQTT-based network service;
- support for multiple independent ESP32 nodes;
- canonical-vector conformance tests;
- a Python Bob simulator retained as a development and diagnostic tool.

The Raspberry Pi 3 implementation successfully reproduces all five official canonical vectors. The binary wire representation also passes the same five-vector conformance suite.

#### ESP32 / Bob

The ESP32 implementation is located in `esp32/` and is written in C++ using PlatformIO and ESP-IDF. Both physical boards use the same firmware. Each node derives its runtime `device_id` from its hardware MAC address, so separate firmware images are not required for the two devices.

The project provides three PlatformIO environments:

- `native`: executes the Bob C++ conformance implementation on the development PC;
- `conformance`: executes the five canonical test vectors on an ESP32;
- `esp32dev`: builds the distributed Wi-Fi/MQTT Bob implementation.

The native C++ implementation and both physical ESP32 devices successfully reproduce all five official HK17.2 canonical test vectors, including the 64-bit octonion-modulus configuration.

#### Distributed HK17.2 exchange

The tested laboratory architecture is:

```text
                     Wi-Fi / MQTT
      ┌─────────────────────────────────────┐
      │                                     │
      ▼                                     ▼
ESP32-01 / Bob                       Raspberry Pi 3
ESP32-02 / Bob                       Alice / KMS
                                      Mosquitto
```

The broker runs on the Raspberry Pi 3. MQTT is used only as the transport mechanism; HK17.2 itself is not modified.

For each node, the distributed exchange is:

```text
ESP32 / Bob                         Raspberry Pi 3 / Alice-KMS

JOIN ----------------------------->

              <------------- A, B, q, u, v
              <------------- TA

TB ------------------------------->

              <------------- p, oA
              <------------- rA

rB ------------------------------->
```

The payload representation is binary. JSON is not used on the network.

Only the protocol values required by the frozen public transcript are transported. In particular, the following values are **not** transmitted:

- the session key `kA` / `kB`;
- the shared octonion `oB`;
- the shared matrix `M`;
- private matrix polynomials `g(x)` and `j(x)`;
- private octonion polynomials `f(x)` and `h(x)`;
- private exponents `m` and `n`;
- secret displacements `oS1` and `oS2`;
- private self-convolution values.

Alice and Bob derive the session key independently. Real exchanges were completed successfully between the Raspberry Pi 3 KMS and both physical ESP32 nodes, with matching locally derived keys at both endpoints.

No additional cryptographic layer has been introduced into HK17.2 by the embedded port. The implementation is intended to preserve the protocol sequence and algebraic behavior of the frozen reference implementation.


### Historical protocol implementations

The `old/` directory contains previous versions retained for historical comparison, reproducibility, and cryptanalytic experiments.

- `old/hk17.py`: original HK17 protocol implementation.
- `old/hk17_2-v1.py`: first HK17.2 development version, in which `oB` is available to the adversary model used by the corresponding attacks.

## Running the code

From the repository root, run the definitive protocol with:

```bash
/usr/bin/python3 general/hk17_2-v2.py
```

Validate the five official canonical test vectors with:

```bash
/usr/bin/python3 general/test_vectors/validate_test_vectors.py
```

Verify the integrity hashes of the canonical JSON files with:

```bash
cd general/test_vectors
sha256sum -c SHA256SUMS
cd ../..
```

The normal conformance workflow is validation only. The official JSON vectors must not be regenerated during routine testing.

Run the algebraic-property experiments with:

```bash
/usr/bin/python3 properties/non_commutativity.py
/usr/bin/python3 properties/non_distributibity.py
/usr/bin/python3 properties/octonion_times_inverse.py
```

Run the cryptanalytic experiments with:

```bash
/usr/bin/python3 attacks/bernstein_li-attack.py
/usr/bin/python3 attacks/exhaustive_attack.py
/usr/bin/python3 attacks/oB_cancellation-attack.py
/usr/bin/python3 attacks/cayley_hamilton-attack.py
```

The Cayley-Hamilton-type experiment targets an exhaustive coefficient space of

```math
16^{32}=2^{128}.
```

for the definitive $32\times32$ matrix construction over $\mathbb{Z}_{16}$ and is therefore not expected to complete by exhaustive enumeration.

Run the performance benchmark with:

```bash
/usr/bin/python3 performance/performance_test.py
```

The benchmark invokes the definitive implementation located in `general/` and writes its CSV results to `performance/`.


### Raspberry Pi 3 / KMS

Create the Raspberry Pi virtual environment and install its Python dependency:

```bash
cd ~/Documents/Proyectos/HK17.2
python3 -m venv raspberry/.venv
source raspberry/.venv/bin/activate
python -m pip install -r raspberry/requirements.txt
```

Validate the Alice/KMS port and binary wire representation:

```bash
python3 raspberry/conformance_test.py
python3 raspberry/wire_conformance_test.py
```

Run Mosquitto with the project laboratory configuration:

```bash
mosquitto -c raspberry/mosquitto.conf -v
```

In another terminal, start the KMS:

```bash
cd ~/Documents/Proyectos/HK17.2
source raspberry/.venv/bin/activate
python3 raspberry/kms_server.py
```

`bob_simulator.py` can be used from another host for diagnostic testing, but the validated distributed configuration uses physical ESP32 nodes.

### ESP32 / PlatformIO

`esp32/include/network_secrets.hpp` is a local untracked file derived from `network_secrets.example.hpp` and contains the laboratory Wi-Fi credentials. It must not be committed.

From the `esp32/` directory, run the native C++ conformance test with:

```bash
pio run -e native
.pio/build/native/program
```

Build and execute the canonical-vector conformance firmware on an ESP32 with:

```bash
pio run -e conformance
pio run -e conformance -t upload --upload-port /dev/ttyUSB0
pio device monitor -p /dev/ttyUSB0 -b 115200
```

Build the distributed Wi-Fi/MQTT firmware with:

```bash
pio run -e esp32dev
```

Upload it to the first or second ESP32 by selecting the corresponding serial port:

```bash
pio run -e esp32dev -t upload --upload-port /dev/ttyUSB0
pio run -e esp32dev -t upload --upload-port /dev/ttyUSB1
```

The two physical nodes use the same firmware image and are distinguished at runtime by their MAC-derived `device_id`.

## Status

This repository is an academic research prototype intended for protocol specification, algebraic experimentation, cryptanalytic analysis, numerical examples, cross-platform implementation, embedded-system validation, and reproducibility of research results.

The current implementation has been validated functionally on a general-purpose PC, Raspberry Pi 3, and two physical ESP32 devices, but it has not been designed, audited, or approved for production cryptographic use.

## Complete numerical example

This section gives a complete reproducible numerical execution of the definitive HK17.2 research implementation. The purpose of the example is to expose every intermediate value needed to inspect the matrix exchange, the deterministic construction of the private shared octonion `oB`, the octonion tokens, and the final session key.

> **Important:** private values are intentionally disclosed in this section only for academic reproducibility. In an actual protocol execution, the private matrix polynomials, private octonion polynomials, private exponents, secret displacements, evaluated private matrices, shared matrix, and derived octonion `oB` are not part of the public transcript.

### Numerical parameters

| Parameter | Value |
|---|---:|
| Octonion modulus $p$ | $251$ |
| Maximum exponent bound | $257$ |
| Octonion coefficient size | $8$ bits |
| Octonion polynomial coefficients | $16$ |
| Highest octonion-polynomial power | $15$ |
| Matrix dimension | $32\times32$ |
| Matrix coefficient size | $4$ bits |
| Matrix modulus $q$ | $16$ |
| Matrix polynomial coefficients | $32$ |
| Highest matrix-polynomial power | $31$ |
| Submatrix grid | $4\times4$ |
| Submatrix dimension | $8\times8$ |
| Public matrix exponent $u$ | $18$ |
| Public matrix exponent $v$ | $252$ |
| Alice private octonion exponent $m$ | $100$ |
| Bob private octonion exponent $n$ | $191$ |

The matrix stage is performed in

```math
M_{32}(\mathbb{Z}_{16}),
```

whereas the octonion stage is performed over modular octonions with coefficients in

```math
\mathbb{Z}_{251}.
```

All matrix products and matrix polynomial evaluations are reduced modulo $q=16$. All octonion operations are reduced modulo $p=251$.

### 1. Private polynomials

Alice's private octonion polynomial is

```math
\begin{aligned}
f(x)={}&72\cdot x^{15}+36\cdot x^{14}+149\cdot x^{13}+107\cdot x^{12}+63\cdot x^{11}+103\cdot x^{10}\\
&+152\cdot x^9+166\cdot x^8+48\cdot x^7+65\cdot x^6+222\cdot x^5+37\cdot x^4\\
&+186\cdot x^3+64\cdot x^2+114\cdot x+73.
\end{aligned}
```

Bob's private octonion polynomial is

```math
\begin{aligned}
h(x)={}&200\cdot x^{15}+45\cdot x^{14}+134\cdot x^{13}+87\cdot x^{12}+177\cdot x^{11}+172\cdot x^{10}\\
&+194\cdot x^9+161\cdot x^8+194\cdot x^7+108\cdot x^6+14\cdot x^5+120\cdot x^4\\
&+234\cdot x^3+88\cdot x^2+10\cdot x+212.
\end{aligned}
```

Alice's private matrix polynomial is

```math
\begin{aligned}
g(x)={}&7\cdot x^{31}+3\cdot x^{30}+3\cdot x^{29}+8\cdot x^{28}+5\cdot x^{27}+15\cdot x^{26}+6\cdot x^{25}+5\cdot x^{24}\\
&+3\cdot x^{23}+12\cdot x^{22}+11\cdot x^{21}+15\cdot x^{20}+7\cdot x^{19}+14\cdot x^{18}+6\cdot x^{17}+1\cdot x^{16}\\
&+6\cdot x^{15}+7\cdot x^{14}+12\cdot x^{13}+14\cdot x^{12}+4\cdot x^{11}+3\cdot x^{10}+1\cdot x^9+2\cdot x^8\\
&+14\cdot x^7+9\cdot x^6+14\cdot x^5+4\cdot x^4+1\cdot x^3+6\cdot x^2+10\cdot x+6
\pmod{16}.
\end{aligned}
```

Bob's private matrix polynomial is

```math
\begin{aligned}
j(x)={}&4\cdot x^{31}+1\cdot x^{30}+12\cdot x^{29}+9\cdot x^{28}+6\cdot x^{27}+7\cdot x^{26}+11\cdot x^{25}+7\cdot x^{24}\\
&+14\cdot x^{23}+2\cdot x^{22}+5\cdot x^{21}+4\cdot x^{20}+4\cdot x^{19}+3\cdot x^{18}+3\cdot x^{17}+4\cdot x^{16}\\
&+8\cdot x^{15}+14\cdot x^{14}+14\cdot x^{13}+13\cdot x^{12}+11\cdot x^{11}+11\cdot x^{10}+5\cdot x^9+11\cdot x^8\\
&+5\cdot x^7+11\cdot x^6+4\cdot x^5+6\cdot x^4+15\cdot x^3+7\cdot x^2+6\cdot x+10
\pmod{16}.
\end{aligned}
```

### 2. Polynomial matrix exchange

Let $A,B\in M_{32}(\mathbb{Z}_{16})$ be the non-zero public matrices shown in full below.

Alice evaluates

```math
G=g(A)=\sum_{i=0}^{31}g_i\cdot A^i \pmod{16}
```

and Bob evaluates

```math
J=j(A)=\sum_{i=0}^{31}j_i\cdot A^i \pmod{16}.
```

Alice computes the public matrix token

```math
T_A=G^u\cdot B\cdot G^v
   =G^{18}\cdot B\cdot G^{252}
   \pmod{16},
```

and Bob computes

```math
T_B=J^u\cdot B\cdot J^v
   =J^{18}\cdot B\cdot J^{252}
   \pmod{16}.
```

Alice then obtains

```math
\begin{aligned}
M_A
&=G^u\cdot T_B\cdot G^v \pmod{16}\\
&=G^u\cdot J^u\cdot B\cdot J^v\cdot G^v \pmod{16},
\end{aligned}
```

while Bob obtains

```math
\begin{aligned}
M_B
&=J^u\cdot T_A\cdot J^v \pmod{16}\\
&=J^u\cdot G^u\cdot B\cdot G^v\cdot J^v \pmod{16}.
\end{aligned}
```

Because $G=g(A)$ and $J=j(A)$ are polynomial functions of the same matrix $A$,

```math
G\cdot J=J\cdot G,
```

and therefore

```math
G^u\cdot J^u=J^u\cdot G^u,
\qquad
J^v\cdot G^v=G^v\cdot J^v.
```

Hence both participants derive exactly the same secret matrix:

```math
\boxed{M_A=M_B=M}.
```

### 3. Full $32\times32$ matrix data

The following blocks contain the complete numerical matrix values for this execution. They are collapsed by default only to keep the README readable.


<details>
<summary><strong>Public matrix A</strong></summary>

```text
A =
    (0, 9, 5, 9, 4, 6, 4, 12, 0, 10, 13, 1, 8, 14, 1, 1, 13, 3, 2, 13, 14, 4, 2, 12, 4, 2, 6, 11, 0, 7, 0, 14)
    (7, 9, 11, 15, 5, 3, 8, 4, 8, 10, 3, 0, 6, 11, 15, 2, 4, 8, 1, 2, 5, 2, 15, 6, 0, 2, 13, 1, 8, 4, 11, 3)
    (13, 14, 7, 15, 6, 3, 4, 2, 4, 14, 7, 0, 4, 4, 8, 4, 4, 8, 6, 0, 13, 2, 12, 1, 2, 1, 5, 11, 11, 1, 14, 2)
    (13, 14, 10, 8, 12, 10, 5, 8, 6, 12, 5, 0, 14, 13, 15, 14, 7, 10, 15, 0, 8, 13, 2, 4, 13, 1, 15, 2, 15, 6, 0, 8)
    (8, 6, 6, 0, 11, 9, 12, 1, 8, 4, 0, 3, 15, 15, 6, 0, 2, 3, 10, 13, 12, 7, 1, 10, 8, 2, 0, 7, 4, 1, 5, 14)
    (5, 15, 14, 11, 0, 12, 13, 4, 11, 10, 9, 7, 1, 15, 8, 5, 11, 7, 15, 3, 0, 0, 4, 2, 10, 13, 11, 14, 10, 2, 1, 9)
    (3, 14, 15, 11, 0, 4, 3, 14, 1, 3, 1, 15, 13, 6, 4, 8, 14, 13, 15, 11, 13, 1, 9, 9, 14, 8, 12, 0, 12, 1, 8, 1)
    (1, 14, 15, 2, 7, 6, 0, 11, 7, 14, 2, 1, 13, 8, 3, 1, 4, 9, 11, 9, 7, 5, 5, 11, 0, 13, 1, 14, 15, 1, 0, 13)
    (8, 14, 0, 13, 11, 1, 1, 12, 2, 2, 10, 9, 10, 7, 3, 11, 5, 11, 7, 12, 3, 11, 5, 9, 1, 12, 2, 11, 7, 15, 0, 15)
    (6, 7, 8, 13, 3, 12, 4, 15, 2, 6, 4, 10, 5, 0, 9, 15, 4, 6, 6, 12, 2, 7, 4, 5, 12, 3, 10, 8, 12, 0, 3, 4)
    (12, 11, 13, 15, 6, 15, 15, 14, 5, 10, 12, 2, 10, 11, 9, 4, 1, 15, 9, 12, 11, 0, 12, 2, 8, 15, 0, 15, 1, 9, 14, 0)
    (14, 7, 3, 5, 14, 9, 8, 3, 0, 15, 15, 12, 2, 8, 12, 4, 10, 10, 6, 15, 7, 4, 12, 13, 2, 11, 14, 4, 2, 8, 6, 9)
    (1, 8, 4, 6, 0, 4, 5, 8, 13, 11, 11, 13, 14, 0, 14, 15, 5, 3, 12, 13, 7, 5, 11, 7, 1, 13, 10, 11, 15, 4, 10, 9)
    (6, 5, 6, 4, 4, 5, 12, 5, 3, 14, 3, 3, 4, 4, 12, 4, 6, 2, 0, 2, 5, 5, 0, 4, 0, 6, 12, 8, 8, 3, 9, 13)
    (10, 4, 15, 7, 12, 4, 8, 10, 14, 13, 6, 15, 12, 0, 9, 8, 2, 11, 14, 4, 6, 2, 13, 7, 14, 15, 9, 13, 4, 9, 14, 10)
    (4, 13, 7, 1, 15, 7, 11, 8, 0, 9, 13, 13, 12, 5, 10, 12, 12, 0, 8, 6, 1, 9, 12, 12, 6, 10, 5, 9, 10, 15, 5, 11)
    (11, 10, 6, 14, 11, 9, 15, 5, 0, 14, 2, 10, 5, 8, 14, 6, 2, 7, 2, 13, 14, 0, 0, 11, 0, 4, 11, 11, 13, 15, 6, 2)
    (5, 1, 8, 13, 9, 3, 6, 3, 4, 2, 4, 0, 6, 9, 4, 7, 13, 2, 4, 11, 1, 5, 13, 15, 8, 14, 0, 7, 11, 5, 15, 12)
    (11, 2, 15, 4, 3, 10, 10, 8, 8, 2, 6, 2, 12, 13, 4, 8, 9, 8, 5, 7, 9, 15, 4, 14, 10, 7, 1, 5, 4, 8, 2, 14)
    (10, 12, 5, 1, 3, 3, 6, 4, 10, 15, 9, 6, 15, 13, 11, 12, 0, 11, 7, 14, 14, 0, 11, 11, 14, 11, 11, 2, 4, 11, 8, 8)
    (2, 14, 12, 4, 15, 11, 9, 9, 4, 11, 5, 2, 4, 15, 5, 7, 1, 4, 4, 6, 9, 9, 6, 1, 2, 12, 7, 13, 6, 13, 12, 12)
    (0, 8, 13, 3, 1, 10, 4, 0, 7, 5, 6, 2, 4, 11, 12, 7, 0, 3, 2, 14, 3, 14, 7, 8, 2, 12, 13, 11, 14, 10, 11, 5)
    (8, 12, 12, 1, 5, 5, 14, 7, 13, 5, 15, 7, 14, 9, 2, 2, 4, 7, 8, 12, 4, 2, 4, 12, 7, 11, 15, 9, 2, 7, 4, 5)
    (3, 10, 12, 2, 6, 4, 6, 15, 1, 14, 15, 9, 11, 11, 4, 9, 6, 12, 5, 2, 11, 0, 0, 2, 14, 2, 13, 10, 14, 3, 9, 1)
    (15, 10, 8, 5, 11, 1, 2, 1, 12, 13, 8, 4, 0, 7, 4, 1, 3, 8, 11, 5, 6, 3, 14, 12, 2, 6, 2, 0, 7, 13, 6, 2)
    (11, 7, 4, 15, 13, 10, 4, 8, 1, 5, 14, 11, 10, 3, 10, 15, 2, 0, 6, 12, 6, 9, 13, 1, 5, 0, 0, 14, 15, 4, 10, 10)
    (6, 6, 10, 5, 4, 7, 11, 4, 0, 11, 1, 8, 12, 14, 10, 0, 2, 12, 9, 1, 14, 10, 12, 15, 2, 13, 13, 6, 3, 1, 8, 14)
    (10, 10, 8, 10, 4, 8, 5, 15, 9, 15, 10, 5, 9, 10, 0, 13, 3, 14, 5, 13, 11, 9, 7, 14, 1, 5, 7, 13, 2, 15, 1, 4)
    (3, 13, 2, 9, 4, 7, 9, 11, 7, 10, 11, 12, 2, 8, 12, 5, 3, 15, 12, 4, 1, 9, 14, 15, 7, 6, 11, 3, 9, 7, 9, 13)
    (0, 12, 4, 2, 5, 3, 13, 10, 5, 9, 8, 7, 1, 8, 12, 8, 1, 2, 0, 1, 0, 13, 3, 4, 11, 0, 6, 8, 5, 9, 2, 7)
    (1, 8, 6, 12, 6, 5, 0, 14, 3, 9, 14, 0, 8, 3, 10, 5, 6, 0, 14, 15, 11, 6, 6, 11, 2, 4, 9, 8, 8, 4, 6, 9)
    (8, 11, 4, 9, 5, 7, 5, 12, 14, 3, 12, 15, 7, 11, 13, 6, 3, 6, 8, 9, 7, 8, 13, 4, 7, 3, 2, 1, 10, 10, 5, 14)
```

</details>

<details>
<summary><strong>Public matrix B</strong></summary>

```text
B =
    (10, 8, 2, 9, 5, 0, 8, 6, 6, 8, 13, 6, 6, 11, 14, 4, 5, 6, 3, 12, 9, 9, 11, 13, 15, 1, 1, 13, 0, 5, 2, 2)
    (8, 5, 4, 8, 10, 3, 14, 7, 13, 13, 13, 10, 14, 5, 2, 14, 10, 1, 0, 10, 14, 8, 4, 11, 1, 12, 4, 5, 7, 12, 14, 12)
    (4, 14, 4, 14, 15, 9, 2, 12, 4, 3, 7, 1, 6, 13, 3, 2, 12, 9, 15, 13, 8, 12, 14, 3, 11, 6, 1, 15, 2, 12, 2, 5)
    (8, 1, 10, 15, 1, 11, 6, 9, 0, 5, 3, 6, 13, 14, 1, 9, 0, 11, 11, 3, 5, 11, 2, 10, 5, 0, 4, 7, 8, 14, 4, 1)
    (7, 9, 7, 15, 14, 9, 6, 5, 6, 1, 9, 15, 7, 0, 0, 1, 14, 4, 1, 5, 1, 0, 15, 11, 0, 7, 6, 6, 13, 0, 1, 7)
    (1, 15, 15, 9, 11, 6, 4, 6, 7, 12, 8, 10, 3, 1, 0, 3, 13, 6, 15, 12, 1, 8, 15, 10, 0, 12, 7, 8, 14, 7, 4, 7)
    (10, 9, 13, 11, 15, 1, 7, 6, 6, 10, 0, 4, 1, 14, 3, 3, 10, 6, 14, 4, 12, 11, 14, 15, 14, 0, 5, 10, 3, 9, 3, 3)
    (5, 2, 1, 1, 3, 9, 1, 1, 15, 11, 14, 8, 1, 6, 0, 13, 15, 6, 2, 6, 3, 8, 9, 3, 9, 5, 12, 1, 11, 5, 3, 2)
    (5, 5, 4, 11, 2, 7, 7, 14, 8, 0, 4, 15, 7, 15, 5, 9, 13, 4, 10, 3, 2, 7, 1, 8, 9, 9, 14, 15, 2, 9, 1, 5)
    (13, 10, 0, 7, 10, 2, 4, 4, 10, 6, 13, 12, 0, 7, 6, 1, 11, 3, 15, 7, 7, 0, 9, 12, 15, 1, 5, 7, 6, 3, 6, 12)
    (10, 7, 8, 0, 14, 11, 0, 2, 2, 3, 5, 0, 10, 8, 5, 8, 10, 2, 11, 13, 15, 15, 11, 7, 2, 5, 13, 15, 7, 3, 13, 4)
    (12, 4, 1, 10, 15, 5, 11, 11, 10, 11, 14, 1, 11, 13, 6, 5, 2, 3, 9, 6, 15, 13, 8, 8, 15, 5, 8, 8, 8, 0, 4, 11)
    (11, 6, 11, 5, 4, 12, 0, 11, 5, 8, 3, 6, 6, 5, 0, 3, 9, 11, 13, 5, 12, 8, 5, 15, 12, 9, 7, 3, 10, 10, 5, 12)
    (7, 15, 1, 10, 10, 10, 6, 3, 12, 8, 3, 10, 8, 10, 8, 1, 9, 4, 14, 1, 11, 6, 1, 12, 1, 15, 11, 3, 2, 3, 5, 9)
    (2, 8, 10, 10, 12, 9, 5, 10, 8, 2, 14, 6, 2, 13, 4, 7, 9, 10, 8, 1, 13, 5, 15, 2, 2, 3, 2, 6, 15, 4, 3, 8)
    (8, 12, 7, 2, 12, 10, 9, 3, 10, 14, 14, 8, 10, 4, 0, 14, 15, 1, 13, 2, 1, 1, 0, 12, 6, 8, 6, 3, 3, 6, 8, 11)
    (0, 1, 3, 2, 4, 10, 13, 6, 5, 14, 10, 10, 2, 11, 15, 1, 9, 1, 13, 8, 1, 7, 8, 1, 8, 9, 1, 13, 2, 11, 9, 9)
    (9, 11, 5, 15, 6, 2, 8, 0, 2, 14, 7, 11, 14, 10, 5, 6, 0, 6, 4, 4, 14, 13, 13, 8, 4, 15, 1, 7, 15, 4, 9, 4)
    (8, 13, 13, 15, 5, 2, 6, 9, 3, 6, 12, 0, 5, 8, 1, 0, 9, 8, 1, 0, 0, 10, 6, 4, 2, 3, 15, 3, 2, 2, 15, 2)
    (8, 12, 6, 6, 1, 11, 3, 2, 4, 7, 14, 3, 6, 9, 12, 5, 12, 3, 4, 6, 11, 3, 12, 1, 1, 3, 10, 11, 0, 9, 2, 2)
    (0, 12, 9, 5, 2, 12, 14, 7, 3, 8, 5, 2, 8, 0, 9, 2, 13, 10, 13, 8, 14, 12, 10, 5, 11, 5, 2, 13, 14, 2, 5, 2)
    (9, 1, 3, 12, 0, 10, 4, 15, 15, 15, 4, 6, 4, 5, 2, 11, 12, 13, 4, 10, 9, 7, 14, 10, 4, 7, 11, 8, 3, 14, 5, 14)
    (14, 6, 15, 1, 0, 13, 10, 15, 6, 3, 2, 8, 2, 8, 1, 15, 15, 15, 1, 14, 4, 0, 3, 0, 2, 10, 14, 5, 9, 14, 12, 7)
    (14, 13, 7, 11, 10, 6, 9, 13, 9, 10, 1, 0, 0, 11, 10, 2, 5, 13, 5, 2, 1, 5, 1, 8, 15, 3, 2, 10, 14, 13, 9, 4)
    (14, 13, 3, 6, 3, 3, 11, 0, 1, 5, 1, 12, 11, 7, 10, 15, 0, 7, 10, 8, 14, 14, 15, 4, 13, 13, 14, 3, 15, 9, 10, 5)
    (8, 13, 0, 5, 13, 5, 9, 3, 13, 10, 1, 1, 4, 0, 0, 0, 10, 5, 0, 9, 7, 8, 11, 11, 10, 15, 6, 9, 10, 10, 9, 14)
    (5, 3, 3, 3, 10, 4, 11, 5, 6, 6, 5, 1, 4, 11, 13, 5, 10, 8, 2, 13, 7, 7, 5, 15, 3, 3, 9, 0, 5, 2, 3, 3)
    (12, 15, 12, 10, 12, 12, 10, 11, 8, 12, 9, 11, 12, 15, 7, 13, 12, 4, 3, 4, 9, 7, 0, 8, 15, 0, 15, 10, 10, 3, 11, 13)
    (9, 9, 11, 2, 0, 15, 10, 1, 13, 8, 8, 7, 10, 15, 9, 1, 8, 2, 12, 3, 7, 1, 4, 0, 6, 4, 4, 13, 7, 1, 12, 5)
    (1, 8, 1, 3, 11, 2, 15, 9, 10, 13, 8, 8, 13, 13, 5, 7, 6, 6, 5, 9, 0, 13, 6, 0, 2, 4, 10, 2, 14, 0, 1, 5)
    (1, 2, 14, 12, 14, 14, 6, 1, 10, 11, 3, 15, 7, 4, 1, 12, 9, 7, 11, 4, 5, 7, 15, 14, 7, 12, 13, 2, 14, 7, 8, 15)
    (0, 10, 15, 9, 13, 10, 7, 12, 13, 8, 6, 3, 14, 14, 3, 11, 7, 1, 7, 13, 9, 11, 1, 4, 13, 5, 15, 0, 10, 7, 9, 15)
```

</details>

<details>
<summary><strong>Alice private evaluated matrix G = g(A)</strong></summary>

```text
G =
    (10, 10, 2, 13, 13, 9, 11, 2, 1, 11, 0, 12, 0, 6, 13, 13, 13, 14, 3, 8, 11, 5, 3, 3, 15, 4, 14, 14, 0, 5, 13, 12)
    (2, 10, 6, 14, 0, 15, 11, 9, 1, 9, 8, 9, 14, 2, 0, 5, 8, 7, 6, 8, 9, 12, 5, 9, 3, 6, 7, 6, 11, 12, 10, 15)
    (1, 5, 6, 8, 1, 13, 8, 13, 1, 1, 11, 4, 0, 0, 13, 15, 5, 1, 8, 5, 9, 0, 2, 0, 13, 6, 15, 13, 7, 7, 15, 11)
    (14, 2, 0, 8, 11, 0, 3, 12, 10, 9, 11, 10, 3, 12, 7, 1, 6, 0, 8, 10, 10, 3, 12, 3, 3, 6, 11, 1, 4, 7, 5, 4)
    (3, 12, 6, 3, 14, 4, 12, 9, 13, 11, 3, 3, 10, 15, 7, 2, 12, 4, 4, 8, 9, 15, 2, 3, 14, 5, 12, 11, 7, 4, 10, 3)
    (4, 15, 14, 5, 11, 10, 5, 15, 7, 8, 5, 1, 11, 11, 10, 2, 10, 9, 2, 2, 14, 6, 1, 7, 6, 14, 6, 11, 12, 3, 12, 6)
    (13, 14, 14, 4, 3, 14, 1, 4, 4, 13, 14, 4, 3, 9, 15, 9, 12, 6, 0, 7, 11, 15, 12, 12, 0, 7, 9, 7, 12, 14, 4, 1)
    (2, 6, 15, 3, 6, 13, 6, 9, 8, 12, 9, 3, 8, 7, 0, 14, 9, 3, 2, 14, 15, 4, 12, 8, 9, 12, 13, 11, 4, 2, 9, 4)
    (6, 4, 15, 1, 5, 11, 5, 10, 1, 0, 13, 15, 12, 11, 5, 1, 12, 2, 0, 1, 8, 8, 11, 6, 7, 9, 0, 6, 2, 8, 10, 8)
    (12, 11, 8, 9, 13, 5, 3, 11, 12, 3, 9, 12, 11, 5, 7, 0, 6, 5, 13, 0, 10, 11, 15, 10, 12, 14, 0, 6, 3, 4, 8, 14)
    (12, 4, 9, 10, 5, 15, 15, 0, 15, 10, 0, 7, 0, 6, 2, 11, 10, 7, 1, 12, 11, 1, 7, 6, 3, 10, 1, 9, 2, 2, 7, 12)
    (3, 8, 11, 12, 4, 0, 11, 9, 14, 14, 2, 10, 9, 9, 3, 14, 2, 10, 2, 11, 7, 3, 0, 13, 4, 8, 1, 2, 0, 4, 0, 2)
    (10, 8, 14, 4, 6, 12, 0, 1, 5, 7, 8, 8, 15, 5, 7, 5, 0, 13, 8, 0, 14, 14, 5, 0, 7, 10, 14, 14, 0, 9, 0, 12)
    (8, 2, 10, 15, 14, 4, 12, 3, 3, 5, 0, 6, 5, 12, 1, 5, 15, 4, 8, 1, 9, 0, 4, 14, 6, 14, 0, 1, 6, 3, 10, 4)
    (14, 15, 3, 11, 10, 5, 5, 5, 4, 0, 12, 4, 11, 9, 8, 2, 1, 0, 0, 5, 1, 1, 6, 2, 10, 3, 12, 3, 5, 6, 6, 6)
    (1, 5, 6, 5, 11, 15, 14, 2, 5, 14, 0, 13, 3, 2, 6, 6, 1, 14, 3, 7, 8, 3, 11, 0, 8, 11, 9, 7, 0, 2, 3, 12)
    (2, 14, 11, 12, 0, 6, 7, 7, 12, 13, 10, 9, 10, 7, 2, 5, 8, 13, 4, 12, 4, 7, 3, 11, 11, 8, 2, 14, 12, 1, 14, 14)
    (9, 10, 0, 9, 2, 7, 6, 10, 2, 1, 0, 15, 13, 7, 9, 4, 11, 13, 1, 6, 4, 2, 5, 7, 14, 8, 0, 4, 1, 15, 11, 4)
    (7, 3, 11, 13, 12, 2, 9, 1, 15, 2, 12, 8, 4, 7, 14, 15, 8, 7, 10, 3, 3, 12, 5, 9, 14, 15, 15, 8, 5, 12, 2, 5)
    (11, 10, 4, 14, 3, 10, 12, 1, 8, 11, 2, 0, 3, 2, 5, 9, 7, 0, 7, 4, 10, 3, 11, 10, 2, 10, 9, 10, 7, 6, 6, 12)
    (13, 6, 7, 3, 9, 4, 8, 3, 9, 9, 2, 13, 15, 9, 6, 0, 5, 2, 10, 6, 8, 0, 11, 2, 5, 3, 6, 9, 5, 10, 10, 11)
    (7, 4, 14, 3, 1, 8, 1, 6, 1, 0, 6, 3, 1, 12, 1, 8, 5, 9, 6, 6, 9, 2, 10, 12, 10, 14, 11, 0, 9, 8, 8, 4)
    (0, 0, 3, 3, 9, 11, 9, 15, 5, 7, 0, 14, 7, 12, 2, 8, 10, 0, 13, 0, 10, 3, 9, 0, 8, 3, 12, 7, 12, 14, 4, 14)
    (15, 9, 5, 11, 15, 3, 8, 14, 8, 8, 15, 9, 4, 13, 11, 6, 7, 10, 12, 8, 13, 0, 9, 10, 6, 15, 2, 6, 15, 14, 13, 11)
    (8, 7, 4, 7, 14, 6, 13, 2, 14, 5, 14, 5, 3, 14, 9, 6, 12, 8, 8, 5, 15, 8, 12, 11, 7, 2, 14, 11, 4, 8, 7, 5)
    (0, 13, 4, 11, 9, 7, 9, 5, 1, 15, 13, 2, 12, 8, 9, 1, 11, 1, 8, 0, 15, 4, 0, 2, 7, 7, 4, 5, 15, 14, 10, 5)
    (15, 12, 11, 6, 11, 11, 14, 11, 1, 2, 10, 9, 5, 12, 8, 1, 15, 7, 5, 9, 8, 3, 6, 0, 1, 1, 6, 15, 1, 3, 15, 12)
    (0, 13, 5, 2, 5, 14, 3, 8, 10, 2, 2, 5, 2, 7, 9, 0, 5, 1, 9, 8, 3, 15, 11, 12, 6, 12, 3, 2, 12, 5, 0, 2)
    (15, 3, 14, 15, 0, 6, 4, 13, 13, 12, 8, 3, 0, 7, 15, 9, 5, 4, 15, 4, 5, 8, 11, 14, 9, 5, 3, 0, 4, 10, 4, 13)
    (15, 5, 2, 2, 5, 5, 5, 5, 11, 11, 11, 9, 13, 1, 7, 6, 9, 4, 6, 10, 12, 10, 1, 6, 15, 0, 11, 10, 6, 4, 3, 1)
    (5, 3, 12, 7, 11, 1, 11, 3, 5, 14, 11, 8, 8, 2, 2, 3, 9, 11, 14, 7, 13, 14, 4, 8, 13, 12, 10, 4, 14, 5, 10, 9)
    (9, 3, 1, 5, 13, 12, 10, 2, 12, 2, 0, 7, 15, 13, 11, 6, 13, 6, 8, 2, 14, 7, 1, 15, 8, 11, 6, 1, 15, 13, 4, 5)
```

</details>

<details>
<summary><strong>Bob private evaluated matrix J = j(A)</strong></summary>

```text
J =
    (4, 11, 0, 11, 5, 6, 11, 4, 4, 14, 5, 8, 5, 9, 12, 12, 14, 13, 1, 12, 15, 8, 15, 13, 3, 15, 7, 6, 4, 13, 7, 7)
    (8, 10, 8, 5, 14, 9, 7, 8, 14, 7, 1, 11, 1, 5, 14, 2, 11, 0, 7, 4, 3, 9, 4, 3, 9, 8, 7, 4, 1, 1, 9, 9)
    (5, 12, 6, 6, 13, 14, 13, 4, 4, 6, 4, 6, 13, 2, 11, 7, 1, 4, 5, 8, 5, 8, 3, 4, 11, 4, 6, 4, 13, 4, 14, 10)
    (3, 2, 2, 5, 11, 14, 8, 4, 7, 15, 2, 11, 14, 10, 11, 15, 10, 13, 9, 15, 4, 10, 2, 15, 2, 10, 2, 0, 3, 15, 4, 1)
    (11, 3, 14, 5, 0, 8, 5, 11, 9, 6, 12, 1, 15, 8, 7, 6, 1, 3, 6, 4, 0, 1, 6, 7, 13, 6, 1, 9, 7, 12, 7, 4)
    (0, 7, 6, 0, 14, 12, 13, 5, 1, 4, 13, 10, 0, 11, 12, 15, 2, 12, 6, 3, 13, 10, 3, 15, 1, 9, 7, 11, 5, 2, 8, 15)
    (11, 10, 4, 9, 8, 7, 6, 11, 11, 3, 2, 2, 13, 11, 7, 5, 13, 14, 10, 8, 9, 10, 0, 3, 2, 11, 1, 12, 13, 9, 8, 9)
    (14, 5, 10, 4, 0, 8, 14, 10, 13, 0, 13, 3, 11, 13, 9, 10, 8, 1, 15, 14, 2, 15, 7, 4, 15, 9, 2, 14, 5, 11, 12, 12)
    (1, 14, 2, 6, 4, 6, 7, 12, 14, 8, 6, 12, 0, 13, 4, 10, 7, 4, 5, 15, 8, 6, 6, 14, 4, 13, 12, 15, 10, 8, 5, 14)
    (6, 3, 4, 9, 6, 10, 6, 11, 3, 13, 1, 1, 15, 4, 2, 11, 2, 0, 7, 4, 8, 10, 13, 4, 10, 10, 3, 15, 10, 2, 12, 5)
    (15, 10, 13, 4, 1, 1, 14, 2, 11, 6, 10, 7, 12, 13, 12, 14, 7, 6, 11, 7, 2, 11, 2, 2, 3, 8, 10, 8, 2, 0, 6, 11)
    (8, 5, 12, 11, 10, 13, 14, 7, 7, 14, 11, 8, 13, 15, 4, 11, 2, 4, 6, 4, 12, 8, 15, 6, 15, 14, 12, 10, 7, 6, 4, 15)
    (4, 11, 0, 15, 9, 1, 11, 14, 9, 13, 8, 6, 8, 3, 15, 13, 8, 7, 1, 6, 14, 14, 3, 1, 15, 11, 0, 3, 4, 11, 7, 15)
    (0, 6, 1, 6, 8, 14, 2, 4, 5, 1, 12, 5, 3, 2, 3, 15, 6, 12, 9, 4, 13, 11, 15, 4, 1, 15, 7, 4, 4, 3, 13, 11)
    (9, 3, 4, 13, 4, 15, 8, 9, 6, 10, 5, 7, 7, 3, 5, 2, 9, 7, 2, 7, 1, 10, 6, 2, 6, 14, 2, 6, 5, 10, 7, 14)
    (5, 3, 3, 13, 8, 3, 10, 2, 5, 1, 9, 11, 13, 8, 6, 14, 1, 0, 8, 14, 10, 10, 1, 4, 13, 4, 8, 13, 8, 2, 3, 4)
    (3, 7, 9, 0, 6, 6, 2, 1, 10, 6, 11, 14, 11, 13, 5, 10, 15, 2, 6, 7, 9, 4, 15, 14, 3, 15, 4, 8, 15, 1, 12, 2)
    (14, 14, 14, 2, 4, 14, 5, 7, 2, 5, 13, 14, 6, 15, 14, 11, 7, 8, 2, 13, 4, 9, 11, 6, 5, 1, 15, 6, 5, 6, 3, 10)
    (14, 4, 4, 1, 2, 11, 9, 6, 9, 6, 8, 2, 8, 6, 13, 13, 15, 1, 11, 11, 15, 13, 2, 12, 15, 15, 2, 10, 8, 3, 5, 14)
    (9, 7, 4, 7, 4, 14, 6, 8, 9, 10, 4, 15, 0, 9, 8, 13, 1, 6, 13, 4, 4, 14, 0, 5, 0, 5, 9, 11, 7, 7, 3, 6)
    (3, 0, 9, 7, 5, 6, 2, 14, 2, 14, 10, 5, 8, 11, 14, 7, 10, 7, 5, 2, 3, 4, 15, 1, 2, 4, 1, 7, 8, 1, 13, 5)
    (12, 3, 9, 6, 10, 14, 15, 2, 5, 5, 15, 15, 10, 11, 3, 1, 15, 10, 1, 10, 0, 15, 14, 2, 13, 6, 1, 1, 0, 0, 0, 12)
    (14, 8, 6, 4, 13, 3, 1, 3, 8, 4, 1, 8, 4, 5, 6, 10, 15, 14, 11, 7, 14, 6, 4, 14, 7, 6, 4, 0, 11, 7, 12, 1)
    (2, 8, 12, 2, 3, 4, 5, 13, 14, 2, 10, 5, 4, 7, 3, 9, 13, 7, 12, 10, 6, 14, 7, 4, 11, 6, 12, 7, 13, 2, 3, 8)
    (0, 13, 12, 3, 3, 0, 10, 14, 7, 1, 1, 0, 1, 10, 8, 8, 6, 0, 1, 14, 15, 4, 12, 5, 8, 6, 14, 10, 0, 1, 4, 12)
    (13, 3, 8, 9, 5, 9, 12, 4, 7, 15, 6, 3, 3, 6, 10, 13, 7, 8, 3, 6, 3, 2, 0, 1, 2, 2, 9, 4, 12, 5, 7, 9)
    (0, 3, 8, 1, 0, 13, 8, 4, 3, 12, 6, 10, 10, 15, 7, 1, 13, 9, 12, 7, 8, 8, 12, 10, 5, 9, 12, 14, 0, 2, 0, 11)
    (13, 5, 8, 5, 3, 14, 11, 8, 15, 3, 13, 13, 5, 12, 4, 2, 4, 10, 9, 5, 15, 0, 5, 12, 4, 15, 5, 4, 15, 5, 11, 10)
    (12, 12, 8, 3, 11, 11, 1, 7, 7, 15, 4, 7, 5, 10, 8, 10, 12, 6, 0, 2, 14, 15, 12, 15, 8, 11, 0, 6, 6, 1, 4, 8)
    (0, 10, 7, 8, 0, 9, 12, 11, 3, 5, 14, 12, 14, 6, 9, 0, 5, 9, 10, 6, 2, 6, 6, 8, 11, 13, 8, 5, 15, 2, 0, 12)
    (6, 15, 8, 6, 6, 15, 11, 12, 10, 13, 10, 4, 0, 2, 12, 10, 10, 7, 10, 7, 5, 0, 0, 3, 1, 3, 14, 12, 0, 8, 14, 15)
    (9, 14, 4, 9, 5, 12, 6, 8, 14, 7, 12, 11, 8, 8, 4, 0, 14, 5, 10, 6, 4, 7, 3, 0, 12, 0, 5, 7, 6, 12, 13, 12)
```

</details>

<details>
<summary><strong>Alice public matrix token TA</strong></summary>

```text
TA =
    (0, 1, 13, 14, 4, 10, 4, 7, 15, 4, 9, 11, 3, 2, 7, 0, 2, 8, 14, 8, 4, 4, 11, 8, 3, 5, 11, 13, 8, 2, 13, 6)
    (4, 2, 8, 11, 3, 11, 5, 7, 14, 14, 8, 14, 4, 14, 0, 9, 15, 6, 11, 8, 9, 13, 14, 12, 15, 14, 2, 6, 1, 8, 1, 14)
    (9, 3, 10, 14, 13, 10, 11, 11, 13, 8, 6, 5, 12, 8, 8, 5, 8, 8, 10, 10, 1, 0, 14, 12, 13, 7, 8, 8, 8, 10, 7, 1)
    (10, 3, 6, 15, 10, 15, 11, 8, 3, 5, 14, 11, 0, 5, 13, 8, 15, 15, 7, 13, 7, 9, 11, 3, 9, 2, 13, 10, 11, 3, 9, 10)
    (12, 12, 12, 1, 6, 14, 12, 11, 12, 4, 4, 2, 14, 5, 11, 6, 8, 10, 15, 2, 5, 0, 5, 13, 8, 2, 14, 7, 4, 10, 1, 6)
    (4, 5, 8, 12, 11, 5, 2, 12, 4, 4, 12, 12, 5, 8, 13, 13, 6, 12, 9, 10, 5, 8, 12, 15, 9, 8, 2, 3, 8, 12, 4, 12)
    (8, 12, 9, 1, 10, 0, 8, 12, 7, 7, 1, 11, 3, 6, 9, 8, 7, 2, 0, 2, 5, 8, 6, 5, 5, 0, 15, 12, 11, 5, 9, 9)
    (0, 3, 15, 12, 2, 10, 0, 2, 5, 5, 7, 13, 2, 10, 13, 12, 2, 12, 7, 4, 7, 4, 0, 9, 10, 8, 15, 5, 15, 6, 5, 10)
    (15, 1, 9, 9, 7, 11, 2, 8, 10, 15, 12, 10, 9, 10, 8, 6, 9, 3, 11, 15, 6, 10, 8, 8, 2, 15, 7, 5, 13, 6, 3, 5)
    (13, 7, 14, 1, 4, 0, 1, 2, 7, 10, 6, 0, 7, 11, 9, 1, 6, 3, 6, 14, 5, 7, 1, 0, 4, 14, 5, 12, 15, 11, 12, 14)
    (8, 12, 6, 14, 0, 14, 14, 8, 12, 2, 13, 0, 5, 11, 1, 6, 3, 0, 14, 5, 4, 0, 15, 3, 7, 6, 1, 14, 14, 3, 11, 4)
    (3, 3, 2, 7, 6, 11, 2, 3, 12, 4, 9, 5, 10, 9, 0, 2, 14, 4, 13, 2, 2, 6, 4, 10, 7, 4, 8, 11, 10, 13, 0, 6)
    (2, 1, 2, 5, 4, 11, 10, 8, 10, 15, 1, 4, 10, 1, 6, 13, 9, 7, 9, 1, 2, 15, 11, 1, 11, 8, 2, 7, 13, 14, 0, 3)
    (4, 15, 8, 5, 4, 15, 4, 6, 2, 12, 6, 11, 13, 13, 7, 1, 8, 2, 3, 6, 7, 2, 5, 12, 13, 8, 5, 6, 4, 2, 9, 2)
    (10, 11, 11, 8, 6, 5, 1, 2, 0, 13, 11, 11, 9, 14, 3, 2, 2, 6, 14, 12, 10, 13, 5, 11, 5, 6, 7, 6, 4, 4, 7, 1)
    (8, 5, 3, 4, 10, 15, 1, 15, 0, 11, 6, 4, 4, 15, 15, 5, 15, 12, 8, 12, 11, 12, 0, 13, 4, 11, 13, 1, 1, 4, 6, 7)
    (11, 12, 5, 1, 7, 13, 1, 14, 6, 9, 11, 4, 11, 2, 3, 2, 10, 10, 11, 13, 9, 7, 12, 13, 1, 2, 12, 0, 9, 3, 15, 3)
    (8, 11, 14, 14, 14, 9, 5, 1, 5, 3, 7, 14, 13, 7, 9, 6, 7, 3, 14, 3, 0, 6, 12, 6, 13, 1, 6, 15, 12, 6, 9, 15)
    (2, 0, 12, 11, 9, 11, 4, 12, 10, 12, 5, 6, 5, 11, 12, 7, 5, 15, 12, 12, 7, 2, 7, 4, 2, 9, 15, 0, 7, 4, 2, 15)
    (10, 0, 8, 14, 0, 15, 7, 4, 13, 1, 4, 0, 6, 9, 3, 0, 6, 11, 2, 2, 6, 12, 1, 14, 11, 0, 8, 1, 13, 11, 12, 2)
    (6, 13, 8, 13, 6, 5, 9, 5, 8, 7, 2, 9, 14, 15, 3, 5, 3, 0, 11, 15, 10, 3, 10, 9, 2, 12, 8, 8, 5, 8, 7, 15)
    (7, 1, 2, 3, 6, 15, 1, 4, 15, 11, 3, 2, 4, 7, 3, 6, 3, 5, 4, 10, 0, 9, 10, 13, 11, 10, 2, 12, 11, 9, 13, 12)
    (1, 3, 11, 2, 10, 2, 13, 9, 5, 4, 0, 2, 13, 13, 15, 5, 9, 7, 4, 8, 3, 15, 2, 8, 9, 7, 8, 5, 1, 15, 9, 14)
    (9, 9, 11, 6, 8, 14, 5, 10, 9, 9, 1, 3, 8, 13, 3, 10, 13, 3, 12, 0, 5, 8, 4, 4, 3, 13, 6, 7, 4, 5, 0, 1)
    (14, 6, 6, 1, 14, 15, 7, 3, 4, 3, 4, 1, 2, 7, 13, 6, 4, 1, 5, 11, 2, 6, 2, 6, 3, 15, 8, 13, 1, 2, 13, 10)
    (5, 7, 14, 15, 13, 12, 3, 13, 0, 12, 14, 7, 1, 8, 8, 9, 2, 8, 5, 2, 5, 9, 0, 7, 0, 14, 2, 10, 14, 12, 12, 1)
    (11, 14, 11, 15, 8, 11, 11, 1, 9, 8, 2, 5, 2, 10, 15, 14, 11, 7, 13, 7, 4, 4, 0, 11, 8, 5, 5, 14, 8, 0, 1, 1)
    (2, 13, 6, 6, 12, 2, 14, 0, 13, 12, 10, 0, 10, 9, 3, 1, 8, 3, 5, 1, 11, 12, 11, 15, 6, 6, 4, 2, 9, 7, 5, 1)
    (10, 0, 4, 9, 10, 13, 8, 14, 5, 1, 7, 14, 14, 8, 15, 0, 7, 5, 4, 14, 6, 0, 5, 12, 3, 5, 5, 4, 6, 4, 0, 3)
    (0, 2, 2, 15, 8, 13, 10, 1, 3, 9, 10, 0, 6, 10, 2, 6, 0, 3, 15, 12, 15, 15, 7, 12, 13, 15, 5, 2, 3, 11, 5, 1)
    (13, 7, 13, 13, 4, 1, 9, 0, 15, 12, 0, 10, 3, 12, 4, 15, 12, 1, 11, 11, 7, 3, 13, 11, 1, 0, 3, 9, 12, 13, 15, 1)
    (8, 8, 4, 9, 8, 4, 1, 3, 13, 5, 14, 12, 4, 0, 7, 4, 10, 9, 3, 1, 3, 2, 4, 7, 13, 15, 2, 8, 2, 14, 2, 0)
```

</details>

<details>
<summary><strong>Bob public matrix token TB</strong></summary>

```text
TB =
    (3, 6, 3, 4, 2, 3, 15, 7, 5, 3, 8, 15, 6, 2, 6, 4, 0, 12, 13, 3, 5, 0, 2, 3, 3, 10, 13, 8, 6, 0, 9, 14)
    (7, 0, 9, 6, 10, 0, 10, 14, 15, 7, 8, 5, 12, 5, 9, 13, 3, 6, 6, 6, 13, 7, 3, 10, 0, 4, 7, 11, 5, 3, 3, 10)
    (6, 8, 2, 9, 0, 1, 1, 3, 12, 14, 4, 3, 9, 1, 11, 7, 4, 7, 15, 2, 5, 13, 5, 3, 3, 7, 8, 0, 15, 13, 5, 10)
    (15, 10, 0, 7, 4, 10, 11, 1, 8, 11, 2, 9, 13, 4, 10, 13, 8, 15, 1, 12, 8, 1, 13, 9, 8, 12, 5, 14, 0, 6, 3, 10)
    (11, 5, 7, 1, 10, 3, 3, 7, 4, 14, 13, 4, 1, 6, 5, 14, 0, 15, 0, 6, 12, 9, 15, 9, 0, 12, 8, 8, 5, 12, 15, 4)
    (11, 9, 2, 10, 10, 15, 11, 13, 2, 2, 1, 6, 1, 8, 3, 0, 10, 8, 3, 10, 8, 8, 6, 12, 9, 9, 1, 12, 14, 4, 15, 6)
    (11, 8, 8, 11, 0, 4, 0, 8, 4, 8, 9, 13, 4, 9, 13, 6, 4, 15, 10, 11, 13, 10, 13, 5, 10, 0, 12, 12, 6, 8, 3, 11)
    (8, 2, 4, 5, 14, 5, 14, 0, 1, 1, 8, 15, 6, 14, 2, 13, 14, 15, 11, 11, 4, 9, 1, 3, 5, 11, 3, 2, 0, 2, 7, 14)
    (13, 0, 6, 6, 3, 3, 0, 10, 4, 11, 6, 7, 12, 7, 10, 7, 4, 7, 4, 15, 1, 3, 9, 11, 2, 6, 9, 8, 14, 9, 7, 3)
    (15, 15, 14, 8, 10, 13, 2, 5, 2, 14, 1, 9, 10, 8, 10, 0, 13, 1, 1, 3, 2, 7, 14, 1, 9, 15, 5, 13, 10, 5, 7, 14)
    (2, 5, 15, 4, 7, 13, 9, 4, 0, 13, 12, 3, 4, 3, 10, 14, 13, 6, 8, 14, 1, 7, 8, 2, 13, 10, 12, 11, 0, 6, 14, 3)
    (0, 5, 9, 7, 5, 13, 2, 14, 0, 7, 2, 12, 5, 11, 11, 6, 9, 6, 10, 11, 14, 2, 8, 15, 11, 14, 6, 2, 12, 13, 2, 7)
    (6, 13, 6, 3, 2, 1, 14, 7, 9, 11, 5, 15, 11, 10, 5, 9, 13, 15, 4, 2, 6, 11, 6, 10, 12, 9, 11, 9, 10, 15, 8, 8)
    (9, 1, 3, 10, 6, 1, 0, 15, 1, 9, 13, 14, 12, 2, 14, 9, 11, 0, 7, 3, 13, 1, 3, 15, 8, 14, 9, 6, 15, 13, 9, 10)
    (13, 9, 2, 9, 10, 1, 8, 3, 6, 15, 4, 13, 9, 11, 14, 5, 5, 11, 13, 6, 5, 2, 1, 9, 9, 12, 15, 3, 8, 12, 11, 5)
    (13, 13, 7, 4, 3, 12, 10, 12, 6, 12, 10, 9, 2, 6, 1, 12, 0, 11, 6, 13, 2, 6, 12, 4, 8, 5, 7, 14, 6, 3, 15, 15)
    (0, 6, 12, 10, 5, 13, 14, 4, 14, 2, 15, 8, 10, 9, 14, 9, 6, 9, 13, 10, 0, 2, 0, 0, 10, 12, 6, 2, 13, 1, 8, 7)
    (7, 7, 2, 5, 11, 6, 6, 4, 9, 1, 5, 1, 8, 5, 1, 3, 1, 7, 15, 1, 3, 1, 0, 1, 8, 15, 1, 0, 0, 0, 10, 12)
    (9, 6, 7, 12, 14, 2, 13, 7, 15, 6, 15, 15, 14, 7, 11, 4, 5, 8, 14, 11, 7, 6, 11, 14, 12, 0, 14, 0, 9, 0, 5, 10)
    (9, 4, 9, 7, 11, 3, 9, 11, 15, 11, 12, 8, 10, 8, 2, 2, 0, 13, 14, 9, 6, 4, 4, 8, 11, 5, 3, 2, 0, 15, 4, 12)
    (0, 10, 9, 11, 10, 4, 2, 9, 15, 0, 0, 6, 7, 8, 0, 9, 6, 8, 0, 12, 0, 8, 9, 13, 15, 1, 14, 7, 4, 1, 2, 14)
    (0, 11, 9, 6, 3, 11, 8, 7, 6, 14, 10, 10, 11, 13, 13, 4, 0, 12, 14, 1, 4, 3, 4, 7, 10, 11, 8, 11, 9, 8, 9, 8)
    (5, 13, 0, 8, 10, 5, 7, 1, 4, 4, 13, 8, 5, 4, 13, 12, 1, 15, 5, 1, 1, 5, 4, 13, 6, 13, 15, 10, 11, 7, 13, 1)
    (6, 14, 14, 14, 1, 8, 6, 15, 0, 1, 9, 5, 0, 11, 5, 3, 9, 10, 15, 4, 8, 9, 1, 12, 10, 4, 9, 14, 5, 12, 0, 6)
    (0, 9, 3, 15, 12, 0, 5, 5, 14, 7, 13, 11, 2, 8, 3, 10, 9, 0, 5, 14, 4, 2, 3, 8, 5, 6, 1, 10, 14, 2, 10, 2)
    (15, 12, 14, 0, 12, 1, 3, 3, 12, 8, 2, 11, 8, 2, 15, 1, 5, 11, 4, 5, 8, 0, 13, 12, 5, 2, 1, 10, 14, 11, 3, 7)
    (4, 14, 10, 9, 14, 15, 14, 4, 9, 14, 3, 4, 1, 6, 6, 6, 1, 4, 6, 15, 5, 13, 7, 1, 6, 15, 0, 14, 2, 0, 1, 0)
    (2, 11, 11, 0, 14, 4, 0, 7, 4, 15, 6, 8, 7, 0, 4, 13, 5, 9, 4, 14, 11, 3, 14, 10, 10, 12, 3, 15, 14, 2, 4, 0)
    (5, 2, 10, 7, 9, 14, 4, 0, 0, 10, 8, 9, 0, 4, 14, 1, 10, 0, 4, 15, 6, 2, 12, 2, 1, 12, 14, 8, 9, 7, 9, 13)
    (14, 6, 1, 1, 15, 5, 8, 0, 8, 14, 2, 11, 1, 0, 13, 13, 13, 1, 3, 8, 8, 14, 10, 15, 8, 9, 8, 8, 14, 3, 15, 2)
    (8, 2, 11, 9, 3, 3, 10, 10, 3, 2, 6, 6, 14, 4, 4, 9, 1, 12, 1, 9, 3, 15, 6, 6, 0, 2, 14, 6, 14, 10, 7, 9)
    (6, 14, 0, 7, 13, 15, 11, 10, 10, 15, 14, 12, 7, 4, 14, 13, 14, 0, 10, 6, 6, 15, 2, 8, 6, 0, 8, 4, 7, 0, 0, 12)
```

</details>

<details>
<summary><strong>Shared matrix MA = MB = M</strong></summary>

```text
M =
    (12, 6, 0, 2, 6, 6, 15, 1, 5, 4, 0, 12, 11, 5, 3, 13, 7, 1, 15, 8, 11, 11, 11, 14, 10, 8, 14, 9, 14, 9, 8, 14)
    (4, 10, 10, 4, 13, 4, 1, 7, 13, 10, 7, 6, 0, 4, 7, 4, 2, 3, 13, 8, 12, 6, 11, 15, 12, 3, 15, 5, 9, 13, 12, 12)
    (8, 5, 2, 2, 15, 12, 0, 13, 5, 2, 5, 7, 6, 9, 11, 9, 15, 8, 15, 5, 9, 13, 6, 3, 8, 1, 1, 9, 10, 7, 12, 10)
    (5, 13, 0, 12, 8, 11, 15, 4, 10, 4, 9, 0, 0, 14, 3, 3, 9, 6, 10, 0, 10, 9, 8, 13, 11, 5, 15, 3, 14, 9, 13, 0)
    (1, 2, 12, 5, 13, 9, 10, 1, 7, 5, 9, 5, 12, 10, 7, 14, 12, 12, 14, 13, 0, 13, 2, 13, 0, 15, 6, 11, 10, 3, 12, 9)
    (14, 6, 9, 12, 8, 15, 0, 7, 15, 10, 10, 6, 10, 10, 11, 13, 10, 5, 5, 4, 4, 14, 10, 5, 0, 12, 12, 6, 7, 8, 0, 11)
    (11, 0, 0, 1, 1, 5, 12, 7, 13, 1, 9, 5, 5, 14, 3, 6, 0, 6, 1, 13, 11, 9, 9, 13, 10, 7, 11, 2, 9, 4, 13, 4)
    (4, 3, 6, 11, 6, 14, 9, 14, 5, 12, 1, 11, 11, 5, 15, 3, 7, 9, 2, 1, 3, 13, 7, 11, 13, 9, 5, 10, 0, 8, 5, 8)
    (14, 5, 0, 13, 7, 4, 9, 11, 11, 4, 4, 1, 9, 10, 6, 15, 4, 9, 9, 11, 4, 0, 1, 1, 10, 4, 9, 0, 15, 3, 13, 4)
    (9, 2, 12, 8, 10, 15, 3, 6, 2, 1, 1, 11, 13, 15, 9, 5, 14, 11, 4, 5, 15, 12, 11, 13, 11, 7, 7, 14, 12, 15, 4, 10)
    (14, 9, 7, 5, 2, 3, 6, 1, 0, 1, 14, 9, 4, 8, 12, 3, 6, 15, 6, 7, 0, 12, 8, 14, 10, 14, 1, 5, 0, 14, 0, 10)
    (6, 6, 15, 2, 7, 5, 6, 5, 9, 1, 4, 15, 9, 11, 6, 12, 14, 6, 11, 6, 1, 4, 1, 0, 11, 14, 6, 11, 8, 7, 4, 3)
    (6, 9, 9, 1, 9, 5, 6, 15, 9, 10, 10, 7, 15, 12, 3, 0, 2, 10, 2, 4, 12, 5, 10, 9, 0, 14, 11, 6, 7, 4, 9, 14)
    (3, 15, 10, 3, 0, 2, 5, 4, 11, 7, 6, 15, 15, 15, 15, 7, 15, 3, 15, 0, 12, 7, 4, 7, 5, 12, 8, 1, 4, 10, 14, 4)
    (7, 6, 4, 15, 8, 6, 3, 12, 13, 5, 5, 11, 2, 0, 11, 1, 15, 12, 7, 13, 0, 10, 1, 7, 5, 12, 0, 2, 3, 2, 15, 4)
    (2, 2, 11, 7, 10, 10, 11, 13, 6, 0, 7, 4, 12, 11, 8, 9, 3, 15, 15, 14, 9, 13, 8, 3, 11, 7, 3, 15, 2, 5, 6, 7)
    (0, 12, 0, 11, 9, 9, 12, 3, 5, 11, 2, 11, 11, 8, 6, 14, 3, 7, 2, 3, 8, 1, 15, 4, 10, 10, 15, 15, 2, 2, 8, 9)
    (6, 13, 7, 7, 15, 4, 9, 13, 8, 15, 2, 9, 14, 10, 9, 3, 8, 15, 2, 12, 11, 2, 4, 11, 2, 9, 13, 0, 14, 4, 7, 7)
    (14, 10, 3, 4, 4, 14, 9, 15, 3, 11, 11, 4, 0, 13, 14, 10, 11, 9, 1, 14, 8, 8, 13, 12, 3, 12, 5, 5, 12, 2, 13, 13)
    (0, 9, 5, 15, 12, 6, 4, 5, 12, 13, 7, 2, 3, 13, 3, 11, 6, 8, 12, 3, 7, 8, 1, 5, 12, 2, 4, 10, 7, 11, 14, 12)
    (10, 4, 5, 11, 8, 3, 4, 14, 15, 10, 1, 15, 4, 8, 15, 15, 9, 10, 10, 6, 8, 12, 14, 5, 6, 1, 6, 9, 13, 5, 13, 9)
    (15, 14, 13, 13, 4, 5, 15, 6, 3, 2, 15, 4, 13, 13, 11, 10, 1, 3, 5, 3, 13, 0, 5, 10, 12, 0, 15, 14, 3, 2, 7, 11)
    (2, 10, 8, 4, 7, 10, 8, 8, 2, 1, 4, 6, 3, 2, 9, 14, 6, 12, 13, 13, 9, 0, 5, 0, 14, 4, 4, 0, 7, 9, 15, 2)
    (1, 13, 8, 10, 2, 7, 10, 1, 11, 14, 5, 6, 9, 9, 10, 2, 5, 15, 13, 3, 11, 4, 14, 10, 11, 5, 5, 9, 6, 10, 1, 15)
    (8, 7, 15, 8, 14, 0, 3, 8, 10, 4, 10, 14, 10, 5, 11, 8, 5, 7, 10, 0, 1, 2, 11, 14, 12, 5, 11, 8, 3, 5, 3, 2)
    (13, 1, 6, 7, 2, 7, 11, 10, 4, 1, 1, 6, 11, 12, 12, 1, 0, 3, 2, 11, 8, 13, 13, 5, 5, 12, 6, 5, 10, 13, 7, 10)
    (9, 11, 0, 13, 4, 3, 10, 10, 6, 10, 0, 4, 15, 6, 0, 15, 10, 4, 6, 15, 5, 9, 15, 8, 9, 15, 9, 3, 5, 6, 7, 10)
    (15, 0, 13, 7, 9, 11, 9, 1, 1, 3, 10, 1, 12, 3, 4, 8, 9, 14, 13, 13, 14, 7, 11, 10, 3, 3, 0, 10, 9, 11, 2, 2)
    (14, 7, 7, 2, 7, 4, 3, 15, 14, 4, 11, 7, 0, 13, 1, 5, 11, 11, 7, 1, 9, 1, 15, 12, 4, 3, 2, 14, 15, 12, 4, 7)
    (5, 15, 1, 14, 12, 5, 14, 13, 4, 15, 11, 5, 5, 14, 10, 13, 10, 15, 7, 14, 5, 3, 13, 9, 4, 15, 6, 9, 12, 0, 0, 8)
    (5, 2, 9, 5, 6, 1, 7, 8, 0, 12, 7, 5, 13, 15, 14, 15, 5, 0, 9, 3, 10, 8, 9, 5, 5, 9, 13, 12, 8, 7, 14, 11)
    (1, 7, 8, 10, 0, 0, 9, 2, 2, 7, 7, 3, 7, 1, 2, 4, 13, 5, 2, 11, 4, 8, 13, 9, 11, 14, 3, 6, 11, 10, 12, 12)
```

</details>

### 4. Deterministic derivation of the private shared octonion `oB`

The shared matrix contains

```math
32^2=1024
```

entries and is partitioned into a $4\times4$ grid of $8\times8$ submatrices:

```math
M=
\begin{pmatrix}
M_{00}&M_{01}&M_{02}&M_{03}\\
M_{10}&M_{11}&M_{12}&M_{13}\\
M_{20}&M_{21}&M_{22}&M_{23}\\
M_{30}&M_{31}&M_{32}&M_{33}
\end{pmatrix}.
```

For each $8\times8$ block,

```math
S_{ij}
=
\sum_{r=0}^{7}\sum_{c=0}^{7}(M_{ij})_{r,c}.
```

The sums are **not** reduced modulo $p$ before decimal concatenation. For this execution,

```math
\left(S_{ij}\right)=
\begin{pmatrix}
454&474&538&535\\
456&497&497&478\\
512&529&481&507\\
463&464&525&494
\end{pmatrix}.
```

Exactly four public deterministic traversals are used.

#### Traversal 1 — rows left-to-right, top-to-bottom

```math
\begin{aligned}
R_1=(&M_{00},M_{01},M_{02},M_{03},
M_{10},M_{11},M_{12},M_{13},\\
&M_{20},M_{21},M_{22},M_{23},
M_{30},M_{31},M_{32},M_{33}).
\end{aligned}
```

Ordered sums:

```text
(454, 474, 538, 535, 456, 497, 497, 478,
 512, 529, 481, 507, 463, 464, 525, 494)
```

#### Traversal 2 — rows right-to-left, top-to-bottom

```math
\begin{aligned}
R_2=(&M_{03},M_{02},M_{01},M_{00},
M_{13},M_{12},M_{11},M_{10},\\
&M_{23},M_{22},M_{21},M_{20},
M_{33},M_{32},M_{31},M_{30}).
\end{aligned}
```

Ordered sums:

```text
(535, 538, 474, 454, 478, 497, 497, 456,
 507, 481, 529, 512, 494, 525, 464, 463)
```

#### Traversal 3 — columns top-to-bottom, left-to-right

```math
\begin{aligned}
R_3=(&M_{00},M_{10},M_{20},M_{30},
M_{01},M_{11},M_{21},M_{31},\\
&M_{02},M_{12},M_{22},M_{32},
M_{03},M_{13},M_{23},M_{33}).
\end{aligned}
```

Ordered sums:

```text
(454, 456, 512, 463, 474, 497, 529, 464,
 538, 497, 481, 525, 535, 478, 507, 494)
```

#### Traversal 4 — columns bottom-to-top, left-to-right

```math
\begin{aligned}
R_4=(&M_{30},M_{20},M_{10},M_{00},
M_{31},M_{21},M_{11},M_{01},\\
&M_{32},M_{22},M_{12},M_{02},
M_{33},M_{23},M_{13},M_{03}).
\end{aligned}
```

Ordered sums:

```text
(463, 512, 456, 454, 464, 529, 497, 474,
 525, 481, 497, 538, 494, 507, 478, 535)
```

For traversal $r$, let

```math
\left(S_0^{(r)},S_1^{(r)},\ldots,S_{15}^{(r)}\right)
```

denote its ordered sums. The candidate octonion is

```math
o_B^{(r)}
=
\left(
b_0^{(r)},b_1^{(r)},\ldots,b_7^{(r)}
\right),
```

where

```math
b_k^{(r)}
=
\mathrm{conc}
\left(
S_{2k}^{(r)},S_{2k+1}^{(r)}
\right)
\pmod{251},
\qquad
0\leq k\leq 7.
```

Here $\mathrm{conc}(a,b)$ denotes decimal concatenation. For example,

```math
\mathrm{conc}(454,474)=454474.
```

For the first traversal, every component is therefore obtained explicitly as

```math
\begin{aligned}
b_0&=454474\pmod{251}=164,\\
b_1&=538535\pmod{251}=140,\\
b_2&=456497\pmod{251}=179,\\
b_3&=497478\pmod{251}=247,\\
b_4&=512529\pmod{251}=238,\\
b_5&=481507\pmod{251}=89,\\
b_6&=463464\pmod{251}=118,\\
b_7&=525494\pmod{251}=151.
\end{aligned}
```

Thus

```math
o_B^{(1)}
=
(164,140,179,247,238,89,118,151).
```

The modular quadratic norm of a candidate

```math
o=(a_0,a_1,\ldots,a_7)
```

is

```math
N(o)
=
\sum_{i=0}^{7}a_i^2
\pmod{251}.
```

For the first candidate,

```math
\begin{aligned}
N\left(o_B^{(1)}\right)
&=
164^2+140^2+179^2+247^2\\
&\quad+238^2+89^2+118^2+151^2
\pmod{251}\\
&=
240836\pmod{251}\\
&=
127.
\end{aligned}
```

The four candidates are:

| Configuration | Candidate $o_B^{(r)}$ | $N(o_B^{(r)})\pmod{251}$ | Invertible |
|---:|---|---:|:---:|
| 1 | $(164,140,179,247,238,89,118,151)$ | 127 | Yes |
| 2 | $(155,64,91,225,210,153,55,113)$ | 152 | Yes |
| 3 | $(146,172,107,105,102,107,95,223)$ | 118 | Yes |
| 4 | $(166,136,179,243,138,56,37,129)$ | 126 | Yes |

Alice and Bob test the candidates in the fixed order

```math
o_B^{(1)},\;
o_B^{(2)},\;
o_B^{(3)},\;
o_B^{(4)}
```

and select the first invertible candidate. Therefore,

```math
\boxed{
o_B=
(164,140,179,247,238,89,118,151)
}
```

with

```math
\boxed{N(o_B)=127\neq0\pmod{251}}.
```

Since

```math
127^{-1}\equiv168\pmod{251},
```

the inverse is

```math
\boxed{
o_B^{-1}
=
(193,74,48,170,176,108,5,234)
}.
```

Both sides obtain exactly the same value:

```text
oB obtained by Alice = (164, 140, 179, 247, 238, 89, 118, 151)
oB obtained by Bob   = (164, 140, 179, 247, 238, 89, 118, 151)
```

The octonion `oB` is a **private shared value** derived from $M$; it is not transmitted as a public protocol parameter.

### 5. Octonion-stage values

The public octonion is

```math
o_A=(110,77,55,246,49,37,180,227).
```

Alice's secret displacement is

```math
o_{S1}=(90,99,173,196,56,179,159,183),
```

and Bob's secret displacement is

```math
o_{S2}=(105,132,26,79,96,86,74,246).
```

The shifted arguments are

```math
-o_A+o_{S1}
=
(231,22,118,201,7,142,230,207)
\pmod{251},
```

and

```math
-o_A+o_{S2}
=
(246,55,222,84,47,49,145,19)
\pmod{251}.
```

#### Polynomial evaluations

Alice obtains

```math
f(o_A)
=
(161,167,191,188,15,165,9,49),
```

and

```math
f(-o_A+o_{S1})
=
(242,208,66,189,89,156,235,86).
```

Bob obtains

```math
h(o_A)
=
(36,70,50,178,113,239,118,1),
```

and

```math
h(-o_A+o_{S2})
=
(23,219,26,193,105,8,121,208).
```

Octonion powers use iterative left association:

```math
x^1=x,
\qquad
x^{k+1}=x^k\cdot x.
```

Using $m=100$,

```math
f_1=f(o_A)^{100}
=
(210,192,173,144,145,89,87,139),
```

```math
f_2=f(-o_A+o_{S1})^{100}
=
(242,35,28,103,91,89,229,181).
```

Using $n=191$,

```math
h_1=h(o_A)^{191}
=
(164,221,122,103,95,41,57,143),
```

```math
h_2=h(-o_A+o_{S2})^{191}
=
(87,1,109,143,83,188,208,119).
```

### 6. Discrete modular pointwise self-convolutions

For this implementation, define Alice's self-convolution value as

```math
F
=
(f*f)(o_A,o_{S1},m)
=
f_1\cdot f_2
\pmod{251},
```

and Bob's value as

```math
H
=
(h*h)(o_A,o_{S2},n)
=
h_1\cdot h_2
\pmod{251}.
```

Numerically,

```math
\boxed{
F=
(143,24,73,69,112,249,151,110)
}
```

and

```math
\boxed{
H=
(37,248,29,58,24,40,56,191)
}.
```

### 7. Public octonion tokens

Alice computes

```math
r_A
=
F\cdot o_B
\pmod{251},
```

therefore

```math
\begin{aligned}
r_A
&=
(143,24,73,69,112,249,151,110)\\
&\quad\cdot
(164,140,179,247,238,89,118,151)
\pmod{251}\\
&=
\boxed{(109,143,239,222,30,224,64,69)}.
\end{aligned}
```

Bob computes

```math
r_B
=
H\cdot o_B
\pmod{251},
```

therefore

```math
\begin{aligned}
r_B
&=
(37,248,29,58,24,40,56,191)\\
&\quad\cdot
(164,140,179,247,238,89,118,151)
\pmod{251}\\
&=
\boxed{(231,237,167,18,158,187,189,8)}.
\end{aligned}
```

The public octonion tokens are therefore

```text
rA = (109, 143, 239, 222, 30, 224, 64, 69)
rB = (231, 237, 167, 18, 158, 187, 189, 8)
```

### 8. Session-key computation

Alice directly computes

```math
k_A
=
F\cdot r_B
\pmod{251}.
```

Keeping the binary parenthesization used by the implementation,

```math
\begin{aligned}
k_A
&=
(143,24,73,69,112,249,151,110)\\
&\quad\cdot
(231,237,167,18,158,187,189,8)
\pmod{251}\\
&=
\boxed{(52,214,127,106,248,51,170,142)}.
\end{aligned}
```

Bob first recovers Alice's self-convolution using his private knowledge of the shared octonion:

```math
F_B
=
r_A\cdot o_B^{-1}
\pmod{251}.
```

Numerically,

```math
\begin{aligned}
F_B
&=
(109,143,239,222,30,224,64,69)\\
&\quad\cdot
(193,74,48,170,176,108,5,234)
\pmod{251}\\
&=
(143,24,73,69,112,249,151,110)\\
&=F.
\end{aligned}
```

Bob then computes

```math
k_B
=
F_B\cdot r_B
\pmod{251},
```

which gives

```math
\boxed{
k_B=(52,214,127,106,248,51,170,142)
}.
```

Consequently,

```math
\boxed{
k_A=k_B=k
=
(52,214,127,106,248,51,170,142)
}.
```

The implementation therefore terminates with

```text
SUCCESS!!! Alice and Bob generated the same key.

kA = (52, 214, 127, 106, 248, 51, 170, 142)
kB = (52, 214, 127, 106, 248, 51, 170, 142)
Session key k = (52, 214, 127, 106, 248, 51, 170, 142)
```

For the recorded execution used in this example:

```text
Execution time = 0:00:00.128410
```

This numerical execution is intended as a reproducibility example for the research implementation. Equality of the generated keys demonstrates correctness for this run; it does not by itself constitute a cryptographic security proof.

---

## Authors

**José Federico Castro Tramontina**  
PhD candidate. Design, development, implementation, numerical validation, and cryptanalysis of HK17.2.

**Pedro Hecht**  
PhD thesis director and co-author of the original HK17 protocol.

**Jorge Kamlofsky**  
PhD thesis co-director and co-author of the original HK17 protocol.
