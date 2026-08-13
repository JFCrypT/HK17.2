# HK17.2 Raspberry Pi 3 / Alice-KMS

This directory contains the Python port of Alice, the in-memory KMS session manager, MQTT transport, canonical conformance tests, the laboratory web administration interface, and unattended startup support for the Raspberry Pi 3.

The Raspberry Pi implementation is a platform port of the frozen HK17.2 protocol. The web dashboard, admission control, and node-management functions form a separate laboratory management plane and do not modify the HK17.2 cryptographic transcript.

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

## Laboratory network

The current dedicated laboratory WLAN is:

```text
SSID:          JFCrypT-Lab
Subnet:        192.168.1.0/24
Gateway/AP:    192.168.1.1
RPi3 / KMS:    192.168.1.40
ESP32-01:      192.168.1.75
ESP32-02:      192.168.1.85
MQTT:          192.168.1.40:1883
KMS Web UI:    http://192.168.1.40:8000/
```

The Raspberry Pi and both ESP32 devices remain DHCP clients. Their stable laboratory addresses are assigned by MAC-based DHCP reservations in the dedicated access point.

The Wi-Fi password is not stored in this directory or elsewhere in the repository.

## Mosquitto

The project broker runs on the Raspberry Pi 3.

For manual operation, first ensure that a separate system Mosquitto instance is not already occupying TCP port 1883:

```bash
sudo systemctl disable --now mosquitto
```

Then run the project laboratory configuration:

```bash
cd ~/Documents/Proyectos/HK17.2
mosquitto -c raspberry/mosquitto.conf -v
```

### Local broker address versus LAN broker address

The KMS process and Mosquitto run on the same Raspberry Pi. Therefore, the KMS itself connects to the broker through the loopback interface:

```text
127.0.0.1:1883
```

The ESP32 nodes connect to the same Mosquitto instance through the Raspberry Pi laboratory LAN address:

```text
192.168.1.40:1883
```

These are two addresses for the same broker process, viewed from different hosts.

The administration dashboard displays both values explicitly:

```text
ESP32 endpoint:  192.168.1.40:1883
KMS local link:  127.0.0.1:1883
```

This distinction is intentional and avoids confusing the Raspberry Pi local loopback connection with the endpoint used by remote ESP32 nodes.

## Operational KMS with web administration

Start the operational service with:

```bash
cd ~/Documents/Proyectos/HK17.2
source raspberry/.venv/bin/activate
python3 raspberry/kms_web.py
```

By default:

```text
MQTT KMS local connection: 127.0.0.1:1883
MQTT ESP32 LAN endpoint:   192.168.1.40:1883
Web listener:              0.0.0.0:8000
Browser URL:               http://192.168.1.40:8000/
```

`0.0.0.0:8000` means that Uvicorn listens on all Raspberry Pi interfaces. It is not the browser address. From another host on the laboratory LAN, use:

```text
http://192.168.1.40:8000/
```

The dashboard shows:

- KMS status;
- MQTT broker status;
- the LAN MQTT endpoint used by ESP32 nodes;
- the Raspberry Pi local MQTT link;
- the default HK17.2 modulus;
- pending JOIN requests;
- node and session states;
- masked session keys;
- operator actions for admission and node removal.

The eye/Show control requests the selected locally stored `kA` from the Raspberry Pi and displays it in the administration browser.

The key-display feature is a laboratory management function. It is not part of the HK17.2 cryptographic transcript and the session key is never published over MQTT.

## Admission workflow

ESP32 nodes connect to Wi-Fi and MQTT but do not begin HK17.2 automatically.

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

The validated management flow includes:

```text
NOT_JOINED
    ↓
PENDING_APPROVAL
    ├── REJECTED
    └── KEY_EXCHANGE
            ↓
        ESTABLISHED
```

An established node can later leave the network itself or be removed administratively by the KMS.

## KMS-initiated removal

The dashboard provides `Remove from network` for an established node.

The KMS sends a management command to the selected ESP32:

```text
topic:   hk17/{device_id}/management
payload: REMOVE
```

The operation erases the active session at both endpoints and returns the node to `NOT_JOINED`.

`REMOVE` is management metadata and is not part of the frozen HK17.2 cryptographic transcript.

## Multi-node operation

The KMS keeps independent sessions for both ESP32 devices, identified by their MAC-derived `device_id`.

Current laboratory nodes:

```text
ESP32-01
device_id: esp32-2043a86b2794
IP:        192.168.1.75

ESP32-02
device_id: esp32-6cc8403465b8
IP:        192.168.1.85
```

The two thesis nodes have deterministic laboratory labels based on `device_id`, so their names never depend on connection order. Unknown future nodes receive a stable fallback label derived from their `device_id`.

## MQTT topics

Management:

```text
hk17/join/{device_id}
hk17/leave/{device_id}
hk17/{device_id}/join_status
hk17/{device_id}/management
```

The current KMS-issued management payload is:

```text
REMOVE
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

## Unattended startup

The repository provides:

```text
raspberry/start_kms.sh
```

It starts the project Mosquitto broker and the operational `kms_web.py` service. The script accepts an already-running broker only when it was started with this repository's `raspberry/mosquitto.conf`; it refuses to reuse an arbitrary Mosquitto process that might be bound only to loopback.

Make it executable:

```bash
chmod +x raspberry/start_kms.sh
```

Before enabling unattended startup, disable the distribution Mosquitto service once so it cannot claim TCP/1883 before the project broker:

```bash
sudo systemctl disable --now mosquitto
```

To start the complete KMS stack automatically when the Raspberry Pi boots:

```bash
crontab -e
```

Add:

```cron
@reboot /bin/bash /home/jfcrypt/Documents/Proyectos/HK17.2/raspberry/start_kms.sh
```

The startup script writes logs under:

```text
raspberry/logs/
```

The logs are local runtime artifacts and are ignored by Git.

## Standalone MQTT server

`kms_server.py` remains available for development and diagnostics, but it has no approval dashboard.

The normal operational entry point for the laboratory deployment is:

```bash
python3 raspberry/kms_web.py
```
