# HK17.2 Raspberry Pi 3 / Alice-KMS

This directory contains the Python port of Alice, the in-memory KMS session manager, MQTT transport, canonical conformance tests, and the laboratory web administration interface.

## Conformance

From the repository root:

```bash
python3 raspberry/conformance_test.py
python3 raspberry/wire_conformance_test.py
```

Both tests must pass all five official canonical HK17.2 vectors before network or performance experiments are considered valid.

## Dependencies

```bash
python3 -m venv raspberry/.venv
source raspberry/.venv/bin/activate
python -m pip install -r raspberry/requirements.txt
```

The web administration layer uses FastAPI and Uvicorn. MQTT transport uses Paho MQTT.

## Mosquitto

Run the project laboratory broker configuration:

```bash
mosquitto -c raspberry/mosquitto.conf -v
```

## Operational KMS with web administration

In another terminal:

```bash
cd ~/Documents/Proyectos/HK17.2
source raspberry/.venv/bin/activate
python3 raspberry/kms_web.py
```

By default:

```text
MQTT broker: 127.0.0.1:1883
Web UI:      0.0.0.0:8000
```

From another host on the laboratory LAN, open:

```text
http://<RASPBERRY-PI-IP>:8000/
```

The dashboard shows pending JOIN requests, node/session states, and masked session keys. The eye/show control requests the selected locally stored `kA` from the Raspberry Pi and displays it in the administration browser.

The key-display feature is a laboratory management function. It is not part of the HK17.2 cryptographic transcript and the key is never published over MQTT.

## Admission workflow

ESP32 nodes connect to Wi-Fi and MQTT but no longer begin HK17.2 automatically.

```text
ESP32                          KMS web administration
  |                                      |
  |----- JOIN request ------------------>|
  |                                      | PENDING_APPROVAL
  |                                      | operator Approve / Reject
  |                                      |
  |<---- APPROVED + HK17.2 public data --|  (if approved)
  |                                      |
  |----- frozen HK17.2 exchange -------->|
```

The `APPROVED` / `REJECTED` status message is management metadata only. After approval, the cryptographic sequence is unchanged.

## Multi-node operation

The KMS keeps independent sessions for the two ESP32 devices, identified by their MAC-derived `device_id`. Friendly labels `ESP32-01`, `ESP32-02`, ... are assigned in memory in order of first contact.

## MQTT topics

Management:

```text
hk17/join/{device_id}
hk17/leave/{device_id}
hk17/{device_id}/join_status
```

Frozen HK17.2 public exchange:

```text
hk17/{device_id}/matrix_parameters
hk17/{device_id}/ta
hk17/{device_id}/tb
hk17/{device_id}/octonion_parameters
hk17/{device_id}/ra
hk17/{device_id}/rb
```

The session key, `oB`, shared matrix, private polynomials, private exponents, secret displacements, and private self-convolution values are not transported by MQTT.

## Standalone MQTT server

`kms_server.py` remains available for development/diagnostics, but it has no approval UI. The normal operational entry point is `kms_web.py`.
