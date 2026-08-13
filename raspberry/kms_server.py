"""Operational MQTT Key Management Server for HK17.2.

The Raspberry Pi 3 plays Alice and stores one active HK17.2 session per ESP32
node. MQTT is used only as the message transport. Admission control is a
management layer outside the frozen HK17.2 cryptographic transcript:

1. A node sends an empty JOIN request.
2. The KMS records it as pending and waits for operator approval.
3. After approval, the original HK17.2 message sequence begins unchanged.

No session key, shared matrix, shared octonion, private polynomial, private
exponent, or secret displacement is transported by MQTT.
"""

from __future__ import annotations

import argparse
import logging
import re
import threading
from dataclasses import dataclass, field
from datetime import datetime

import paho.mqtt.client as mqtt

from kms import DEFAULT_MODULO, HK17KMS, SessionState
from wire import (
    decode_matrix,
    decode_octonion,
    encode_matrix,
    encode_matrix_parameters,
    encode_octonion,
    encode_octonion_parameters,
)

BASE_TOPIC = "hk17"
DEFAULT_BROKER_HOST = "127.0.0.1"
DEFAULT_BROKER_PORT = 1883
DEFAULT_QOS = 1
DEFAULT_KEEPALIVE = 60
KMS_CLIENT_ID = "hk17-kms"
DEVICE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

STATUS_PENDING = "PENDING_APPROVAL"
STATUS_KEY_EXCHANGE = "KEY_EXCHANGE"
STATUS_ESTABLISHED = "ESTABLISHED"
STATUS_REJECTED = "REJECTED"
STATUS_NOT_JOINED = "NOT_JOINED"


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


@dataclass(frozen=True)
class ServerConfig:
    broker_host: str = DEFAULT_BROKER_HOST
    broker_port: int = DEFAULT_BROKER_PORT
    keepalive: int = DEFAULT_KEEPALIVE
    qos: int = DEFAULT_QOS
    modulo: int = DEFAULT_MODULO


@dataclass
class NodeRecord:
    device_id: str
    label: str
    status: str = STATUS_NOT_JOINED
    requested_at: str | None = None
    approved_at: str | None = None
    established_at: str | None = None
    rejected_at: str | None = None
    last_activity: str = field(default_factory=_now)

    def as_public_dict(self, key_available: bool) -> dict[str, object]:
        return {
            "device_id": self.device_id,
            "label": self.label,
            "status": self.status,
            "requested_at": self.requested_at,
            "approved_at": self.approved_at,
            "established_at": self.established_at,
            "rejected_at": self.rejected_at,
            "last_activity": self.last_activity,
            "key_available": key_available,
        }


class HK17MQTTKMS:
    def __init__(self, config: ServerConfig):
        self.config = config
        self.kms = HK17KMS(modulo=config.modulo)
        self._lock = threading.RLock()
        self._nodes: dict[str, NodeRecord] = {}
        self._pending: set[str] = set()
        self._mqtt_connected = False

        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=KMS_CLIENT_ID,
            protocol=mqtt.MQTTv311,
            clean_session=True,
        )
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

    @staticmethod
    def _validate_device_id(device_id: str) -> str:
        if not DEVICE_ID_RE.fullmatch(device_id):
            raise ValueError(
                "Invalid device_id. Allowed characters: A-Z, a-z, 0-9, _ and -, maximum length 64."
            )
        return device_id

    def _record_for(self, device_id: str) -> NodeRecord:
        record = self._nodes.get(device_id)
        if record is None:
            record = NodeRecord(
                device_id=device_id,
                label=f"ESP32-{len(self._nodes) + 1:02d}",
            )
            self._nodes[device_id] = record
        return record

    def _publish(self, topic: str, payload: bytes) -> None:
        info = self.client.publish(topic, payload=payload, qos=self.config.qos, retain=False)
        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(f"MQTT publish failed for {topic}: rc={info.rc}")

    def _publish_join_status(self, device_id: str, status: str) -> None:
        self._publish(f"{BASE_TOPIC}/{device_id}/join_status", status.encode("ascii"))

    def _on_connect(self, client, userdata, connect_flags, reason_code, properties) -> None:
        if getattr(reason_code, "is_failure", False):
            logging.error("MQTT connection refused: %s", reason_code)
            return

        with self._lock:
            self._mqtt_connected = True

        logging.info(
            "Connected to MQTT broker %s:%d using MQTT 3.1.1",
            self.config.broker_host,
            self.config.broker_port,
        )
        client.subscribe(f"{BASE_TOPIC}/join/+", qos=self.config.qos)
        client.subscribe(f"{BASE_TOPIC}/leave/+", qos=self.config.qos)
        client.subscribe(f"{BASE_TOPIC}/+/tb", qos=self.config.qos)
        client.subscribe(f"{BASE_TOPIC}/+/rb", qos=self.config.qos)

    def _on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties) -> None:
        with self._lock:
            self._mqtt_connected = False
        if getattr(reason_code, "is_failure", False):
            logging.warning("Disconnected from MQTT broker: %s", reason_code)
        else:
            logging.info("Disconnected from MQTT broker")

    def _on_message(self, client, userdata, message) -> None:
        try:
            self.process_message(message.topic, bytes(message.payload))
        except Exception:
            logging.exception("Failed to process MQTT message on topic %s", message.topic)

    def process_message(self, topic: str, payload: bytes) -> None:
        parts = topic.split("/")

        if len(parts) == 3 and parts[0] == BASE_TOPIC and parts[1] == "join":
            device_id = self._validate_device_id(parts[2])
            if payload:
                raise ValueError("JOIN request payload must be empty")
            self._handle_join_request(device_id)
            return

        if len(parts) == 3 and parts[0] == BASE_TOPIC and parts[1] == "leave":
            device_id = self._validate_device_id(parts[2])
            if payload:
                raise ValueError("LEAVE request payload must be empty")
            self._handle_leave(device_id)
            return

        if len(parts) == 3 and parts[0] == BASE_TOPIC and parts[2] in {"tb", "rb"}:
            device_id = self._validate_device_id(parts[1])
            if parts[2] == "tb":
                self._handle_tb(device_id, payload)
            else:
                self._handle_rb(device_id, payload)
            return

        logging.debug("Ignoring unrelated MQTT topic %s", topic)

    def _handle_join_request(self, device_id: str) -> None:
        with self._lock:
            record = self._record_for(device_id)
            # A new JOIN means the node is asking for a new network admission.
            # Discard any previous KMS-side session key/state before approval.
            self.kms.remove_session(device_id)
            self._pending.add(device_id)
            record.status = STATUS_PENDING
            record.requested_at = _now()
            record.approved_at = None
            record.established_at = None
            record.rejected_at = None
            record.last_activity = _now()

        logging.info("JOIN REQUEST pending approval from %s", device_id)

    def approve_join(self, device_id: str) -> None:
        device_id = self._validate_device_id(device_id)
        with self._lock:
            if device_id not in self._pending:
                raise KeyError(f"No pending JOIN request for {device_id}")

            self.kms.remove_session(device_id)
            session = self.kms.create_session(device_id)
            params = session.matrix_parameters()

            matrix_parameters = encode_matrix_parameters(
                params["A"],
                params["B"],
                int(params["q"]),
                int(params["u"]),
                int(params["v"]),
            )
            ta = encode_matrix(session.matrix_token(), session.parameters.matrix_modulo)

            self._publish_join_status(device_id, "APPROVED")
            self._publish(f"{BASE_TOPIC}/{device_id}/matrix_parameters", matrix_parameters)
            self._publish(f"{BASE_TOPIC}/{device_id}/ta", ta)

            self._pending.discard(device_id)
            record = self._record_for(device_id)
            record.status = STATUS_KEY_EXCHANGE
            record.approved_at = _now()
            record.last_activity = _now()

            logging.info(
                "JOIN APPROVED %s -> matrix stage sent (p=%d, q=%d, u=%d, v=%d)",
                device_id,
                session.parameters.modulo,
                session.parameters.matrix_modulo,
                session.u,
                session.v,
            )

    def reject_join(self, device_id: str) -> None:
        device_id = self._validate_device_id(device_id)
        with self._lock:
            if device_id not in self._pending:
                raise KeyError(f"No pending JOIN request for {device_id}")
            self._pending.discard(device_id)
            self.kms.remove_session(device_id)
            record = self._record_for(device_id)
            record.status = STATUS_REJECTED
            record.rejected_at = _now()
            record.last_activity = _now()
            self._publish_join_status(device_id, "REJECTED")
        logging.info("JOIN REJECTED for %s", device_id)

    def remove_from_network(self, device_id: str) -> None:
        """Administratively remove an established node from the HK17.2 network.

        This is a management-plane operation, not part of the frozen HK17.2
        cryptographic transcript. The KMS instructs the target ESP32 to erase
        its local Bob session/key, then erases the corresponding Alice/KMS
        session and returns the node record to NOT_JOINED.
        """
        device_id = self._validate_device_id(device_id)
        with self._lock:
            record = self._nodes.get(device_id)
            if record is None:
                raise KeyError(f"Unknown node {device_id}")
            if record.status != STATUS_ESTABLISHED:
                raise RuntimeError(
                    f"Node {device_id} is not ESTABLISHED (current state: {record.status})"
                )

            # Management command only. No session key or HK17.2 private value is sent.
            self._publish(f"{BASE_TOPIC}/{device_id}/management", b"REMOVE")

            self._pending.discard(device_id)
            self.kms.remove_session(device_id)
            record.status = STATUS_NOT_JOINED
            record.requested_at = None
            record.approved_at = None
            record.established_at = None
            record.rejected_at = None
            record.last_activity = _now()

        logging.info("ADMIN REMOVE processed for %s", device_id)

    def _handle_leave(self, device_id: str) -> None:
        with self._lock:
            self._pending.discard(device_id)
            self.kms.remove_session(device_id)
            record = self._record_for(device_id)
            record.status = STATUS_NOT_JOINED
            record.requested_at = None
            record.approved_at = None
            record.established_at = None
            record.last_activity = _now()
        logging.info("LEAVE processed for %s", device_id)

    def _handle_tb(self, device_id: str, payload: bytes) -> None:
        with self._lock:
            session = self.kms.get_session(device_id)
            if session.state != SessionState.MATRIX_READY:
                raise RuntimeError(
                    f"TB received for {device_id} while session is in state {session.state.value}"
                )

            TB = decode_matrix(payload, session.parameters.matrix_modulo)
            session.receive_tb(TB)

            oct_params = session.octonion_parameters()
            octonion_parameters = encode_octonion_parameters(
                int(oct_params["p"]),
                oct_params["oA"],
            )
            ra = encode_octonion(session.octonion_token(), session.parameters.modulo)

            self._publish(f"{BASE_TOPIC}/{device_id}/octonion_parameters", octonion_parameters)
            self._publish(f"{BASE_TOPIC}/{device_id}/ra", ra)

            record = self._record_for(device_id)
            record.status = STATUS_KEY_EXCHANGE
            record.last_activity = _now()

            logging.info(
                "TB %s -> shared matrix and oB derived; octonion stage sent (oB configuration %d)",
                device_id,
                session.selected_oB_configuration,
            )

    def _handle_rb(self, device_id: str, payload: bytes) -> None:
        with self._lock:
            session = self.kms.get_session(device_id)
            if session.state != SessionState.OCTONION_READY:
                raise RuntimeError(
                    f"rB received for {device_id} while session is in state {session.state.value}"
                )

            rB = decode_octonion(payload, session.parameters.modulo)
            key = session.receive_rb(rB)

            record = self._record_for(device_id)
            record.status = STATUS_ESTABLISHED
            record.established_at = _now()
            record.last_activity = _now()

            logging.info("HK17.2 KEY ESTABLISHED for %s", device_id)
            logging.info("kA[%s] = %s", device_id, key)

    def dashboard_state(self) -> dict[str, object]:
        with self._lock:
            nodes = []
            for device_id, record in sorted(self._nodes.items(), key=lambda item: item[1].label):
                session = self.kms.sessions.get(device_id)
                key_available = bool(session and session.session_key is not None)
                nodes.append(record.as_public_dict(key_available=key_available))

            pending = [
                record.as_public_dict(key_available=False)
                for device_id, record in sorted(self._nodes.items(), key=lambda item: item[1].label)
                if device_id in self._pending
            ]

            return {
                "kms_online": True,
                "mqtt_connected": self._mqtt_connected,
                "broker": f"{self.config.broker_host}:{self.config.broker_port}",
                "modulo": self.config.modulo,
                "pending": pending,
                "nodes": nodes,
            }

    def session_key_for(self, device_id: str) -> tuple[int, ...]:
        device_id = self._validate_device_id(device_id)
        with self._lock:
            session = self.kms.get_session(device_id)
            if session.session_key is None:
                raise RuntimeError(f"Session key is not established for {device_id}")
            return tuple(int(value) for value in session.session_key)

    def start_background(self) -> None:
        logging.info(
            "Starting HK17.2 KMS MQTT client: broker=%s:%d, default p=%d",
            self.config.broker_host,
            self.config.broker_port,
            self.config.modulo,
        )
        self.client.connect(
            self.config.broker_host,
            self.config.broker_port,
            keepalive=self.config.keepalive,
        )
        self.client.loop_start()

    def stop(self) -> None:
        try:
            self.client.disconnect()
        finally:
            self.client.loop_stop()

    def run(self) -> None:
        logging.info(
            "Starting HK17.2 KMS: broker=%s:%d, default p=%d",
            self.config.broker_host,
            self.config.broker_port,
            self.config.modulo,
        )
        self.client.connect(
            self.config.broker_host,
            self.config.broker_port,
            keepalive=self.config.keepalive,
        )
        self.client.loop_forever()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HK17.2 Raspberry Pi 3 Alice/KMS MQTT server")
    parser.add_argument("--broker-host", default=DEFAULT_BROKER_HOST)
    parser.add_argument("--broker-port", type=int, default=DEFAULT_BROKER_PORT)
    parser.add_argument("--modulo", type=int, default=DEFAULT_MODULO)
    parser.add_argument("--qos", type=int, choices=(0, 1), default=DEFAULT_QOS)
    parser.add_argument("--log-level", choices=("DEBUG", "INFO", "WARNING", "ERROR"), default="INFO")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(message)s",
    )

    server = HK17MQTTKMS(
        ServerConfig(
            broker_host=args.broker_host,
            broker_port=args.broker_port,
            qos=args.qos,
            modulo=args.modulo,
        )
    )

    logging.warning(
        "Standalone kms_server.py records JOIN requests but has no approval UI. "
        "Use kms_web.py for the operational administration interface."
    )

    try:
        server.run()
    except KeyboardInterrupt:
        logging.info("KMS stopped by user")
        server.client.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
