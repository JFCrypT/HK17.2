# HK17.2 ESP32 / Bob

This directory contains the C++/PlatformIO port of the Bob role of the frozen HK17.2 protocol.

## Environments

- `native`: canonical conformance test on the development PC.
- `conformance`: canonical conformance test on physical ESP32 hardware.
- `esp32dev`: distributed ESP32 Bob node using Wi-Fi, MQTT, a local web UI, and a serial management CLI.
- `performance-smoke`: five-iteration local cryptographic performance smoke test using the canonical `p=251` workload.
- `performance`: 1000-iteration local cryptographic performance benchmark using the canonical `p=251` workload.

Both physical ESP32 nodes use the same distributed firmware. Their runtime `device_id` values are derived from their Wi-Fi MAC addresses.

## Local credentials

Create the local credentials file from the public template:

```bash
cp include/network_secrets.example.hpp include/network_secrets.hpp
```

`include/network_secrets.hpp` is ignored by Git and must never be committed.

## Network admission

The distributed firmware does not send a JOIN request automatically at boot. After Wi-Fi and MQTT connect, the node remains `NOT_JOINED` until an operator requests admission.

A JOIN can be requested either from the local ESP32 web interface or from the serial CLI. The KMS records the request as pending; the frozen HK17.2 exchange starts only after approval in the Raspberry Pi KMS web administration interface.

Admission control is a management layer outside the HK17.2 cryptographic transcript.

## ESP32 local web UI

The laboratory node addresses are currently assigned by DHCP reservations:

```text
ESP32-01: http://192.168.1.75/
ESP32-02: http://192.168.1.85/
```

The local page shows device ID, Wi-Fi/MQTT state, network state, and session-key status. It provides:

- `Request network join`
- `Leave network`
- masked local `kB` with an eye/show control

The displayed key is the key derived locally by Bob. It is not received from the KMS.

## Serial CLI

Open the PlatformIO serial monitor at 115200 baud and send commands followed by Enter:

```text
help
status
join
leave
show-key
```

`show-key` prints the locally derived `kB` only after a successful exchange.

## MQTT transcript

Management topics:

```text
hk17/join/{device_id}
hk17/leave/{device_id}
hk17/{device_id}/join_status
hk17/{device_id}/management
```

After approval, the frozen HK17.2 public exchange remains:

```text
KMS -> ESP32: A, B, q, u, v
KMS -> ESP32: TA
ESP32 -> KMS: TB
KMS -> ESP32: p, oA
KMS -> ESP32: rA
ESP32 -> KMS: rB
```

The session key, `oB`, shared matrix, private polynomials, private exponents, and secret displacements are not transported by MQTT.

The web-management APIs use JSON only between a browser and its local endpoint. JSON is not used for HK17.2 MQTT payloads.

## Local ESP32 performance benchmark

The ESP32 benchmark measures the cryptographic work performed by Bob locally and excludes Wi-Fi, MQTT, HTTP, and serial-output overhead from the measured interval.

For reproducibility, every measured iteration executes the frozen canonical `p=251` Bob workload. Repeating an identical validated workload isolates platform execution cost from random-input variation. Each iteration validates the resulting `J`, `TB`, `MB`, `oB`, `rB`, recovered Alice self-convolution, and `kB` against the official canonical vector.

The raw timing is split into:

```text
matrix polynomial evaluation
matrix exchange and shared-matrix derivation
deterministic oB derivation and inversion
octonion polynomial/power/autoconvolution stage
key recovery
total Bob cryptographic execution
```

Heap availability is also recorded.

### Collector dependency

From the repository root:

```bash
python3 -m pip install -r esp32/tools/requirements.txt
```

### Smoke test

Upload the five-execution image to one ESP32:

```bash
cd esp32
pio run -e performance-smoke -t upload --upload-port /dev/ttyUSB0
```

Then start the collector:

```bash
python3 tools/capture_performance.py --port /dev/ttyUSB0
```

If the performance firmware already started before the collector opened the serial port, press `EN/RESET` once. The firmware emits `HK17_PERF_READY`, waits five seconds, and then begins the benchmark.

### Official 1000-execution benchmark

Build and upload:

```bash
cd esp32
pio run -e performance -t upload --upload-port /dev/ttyUSB0
```

Capture:

```bash
python3 tools/capture_performance.py --port /dev/ttyUSB0
```

The collector creates device-specific files under `esp32/performance/`:

```text
<device_id>_performance_results.csv
<device_id>_performance_summary.csv
```

The 1000-execution benchmark can take well over one hour on an ESP32 because each iteration performs the complete Bob-side 32x32 matrix and octonion computation.

The official performance campaign was executed on ESP32-01 (`esp32-2043a86b2794`). Repeating the same 1000-execution campaign on ESP32-02 was intentionally omitted because both boards use the same hardware class, firmware, and Bob implementation, and the second run would not add a distinct implementation target for the present thesis objective.

The resulting files are:

```text
performance/esp32-2043a86b2794_performance_results.csv
performance/esp32-2043a86b2794_performance_summary.csv
```

After the benchmark completed, ESP32-01 was reflashed with the operational `esp32dev` image. Both ESP32 nodes were then functionally revalidated on `JFCrypT-Lab`, including Wi-Fi, MQTT connectivity, admission, HK17.2 key establishment, and KMS administration. The two boards are therefore left in the normal distributed firmware state for thesis-defense demonstration.


## Final operational state

The performance and conformance firmware images are experimental modes only. The final laboratory configuration leaves both physical boards running:

```text
esp32dev
```

with:

```text
ESP32-01
device_id: esp32-2043a86b2794
IP:        192.168.1.75

ESP32-02
device_id: esp32-6cc8403465b8
IP:        192.168.1.85
```

Both nodes use the same firmware image and connect to:

```text
MQTT broker: 192.168.1.40:1883
```

The final two-node system has been revalidated after performance testing and is the configuration intended for the thesis-defense demonstration.
