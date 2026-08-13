# HK17.2 ESP32 / Bob

This directory contains the C++/PlatformIO port of the Bob role of the frozen HK17.2 protocol.

## Environments

- `native`: canonical conformance test on the development PC.
- `conformance`: canonical conformance test on physical ESP32 hardware.
- `esp32dev`: distributed ESP32 Bob node using Wi-Fi, MQTT, a local web UI, and a serial management CLI.

Both physical ESP32 nodes use the same firmware. Their runtime `device_id` values are derived from their Wi-Fi MAC addresses.

## Local credentials

Create the local credentials file from the public template:

```bash
cp include/network_secrets.example.hpp include/network_secrets.hpp
```

`include/network_secrets.hpp` is ignored by Git and must never be committed.

## Network admission

The distributed firmware no longer sends a JOIN request automatically at boot. After Wi-Fi and MQTT connect, the node remains `NOT_JOINED` until an operator requests admission.

A JOIN can be requested either from the local ESP32 web interface or from the serial CLI. The KMS records the request as pending; the frozen HK17.2 exchange starts only after approval in the Raspberry Pi KMS web administration interface.

Admission control is a management layer outside the HK17.2 cryptographic transcript.

## ESP32 local web UI

The serial log prints the node IP after Wi-Fi association:

```text
Node web UI: http://<ESP32-IP>/
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
