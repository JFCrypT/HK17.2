"""Python Bob simulator for testing the Raspberry Pi 3 KMS before the ESP32 port.

This file is only an integration test tool. It is not the ESP32 implementation.
It follows the frozen Bob side of HK17.2 and exchanges the same values that the
future ESP32 implementation will exchange with the KMS.
"""

from __future__ import annotations

import argparse
import logging
import random as randomlib

import paho.mqtt.client as mqtt

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
from wire import (
    decode_matrix,
    decode_matrix_parameters,
    decode_octonion,
    decode_octonion_parameters,
    encode_matrix,
    encode_octonion,
)

BASE_TOPIC = "hk17"
POWERS = 257
MATRIX_DIMENSION = 32
MATRIX_DEGREE = 32
SUBMATRIX_GRID_DIMENSION = 4
SUBMATRIX_DIMENSION = 8


class BobSimulator:
    def __init__(self, broker_host: str, broker_port: int, device_id: str, qos: int = 1):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.device_id = device_id
        self.qos = qos
        self.rng = randomlib.SystemRandom()

        self.q = None
        self.u = None
        self.v = None
        self.A = None
        self.B = None
        self.TA = None
        self.J = None
        self.J_u = None
        self.J_v = None
        self.TB = None
        self.MB = None

        self.p = None
        self.oA = None
        self.rA = None
        self.oB = None
        self.rB = None
        self.session_key = None
        self._tb_sent = False
        self._rb_sent = False

        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"hk17-{device_id}",
            protocol=mqtt.MQTTv311,
            clean_session=True,
        )
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _publish(self, suffix: str, payload: bytes) -> None:
        topic = f"{BASE_TOPIC}/{self.device_id}/{suffix}"
        info = self.client.publish(topic, payload=payload, qos=self.qos, retain=False)
        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(f"MQTT publish failed for {topic}: rc={info.rc}")

    def _on_connect(self, client, userdata, connect_flags, reason_code, properties) -> None:
        if getattr(reason_code, "is_failure", False):
            raise RuntimeError(f"MQTT connection refused: {reason_code}")

        base = f"{BASE_TOPIC}/{self.device_id}"
        client.subscribe(f"{base}/matrix_parameters", qos=self.qos)
        client.subscribe(f"{base}/ta", qos=self.qos)
        client.subscribe(f"{base}/octonion_parameters", qos=self.qos)
        client.subscribe(f"{base}/ra", qos=self.qos)

        # Empty JOIN payload: the node identity is carried by the MQTT topic.
        client.publish(f"{BASE_TOPIC}/join/{self.device_id}", payload=b"", qos=self.qos, retain=False)
        logging.info("JOIN request sent for %s", self.device_id)

    def _on_message(self, client, userdata, message) -> None:
        try:
            suffix = message.topic.rsplit("/", 1)[-1]
            payload = bytes(message.payload)

            if suffix == "matrix_parameters":
                params = decode_matrix_parameters(payload)
                self.A = params["A"]
                self.B = params["B"]
                self.q = int(params["q"])
                self.u = int(params["u"])
                self.v = int(params["v"])
                logging.info("Matrix parameters received")
                self._try_matrix_stage()

            elif suffix == "ta":
                if self.q is None:
                    # TA cannot be decoded until q is known. MQTT ordering is normally preserved
                    # for publications from one client, but keep raw bytes to make the simulator robust.
                    self._ta_payload = payload
                else:
                    self.TA = decode_matrix(payload, self.q)
                logging.info("TA received")
                self._try_matrix_stage()

            elif suffix == "octonion_parameters":
                params = decode_octonion_parameters(payload)
                self.p = int(params["p"])
                self.oA = params["oA"]
                logging.info("Octonion parameters received (p=%d)", self.p)
                self._try_octonion_stage()

            elif suffix == "ra":
                if self.p is None:
                    self._ra_payload = payload
                else:
                    self.rA = decode_octonion(payload, self.p)
                logging.info("rA received")
                self._try_octonion_stage()

        except Exception:
            logging.exception("Bob simulator failed while processing %s", message.topic)
            self.client.disconnect()

    def _try_matrix_stage(self) -> None:
        if self.q is None or self.A is None or self.B is None or self._tb_sent:
            return

        if self.TA is None and hasattr(self, "_ta_payload"):
            self.TA = decode_matrix(self._ta_payload, self.q)
            del self._ta_payload

        if self.TA is None:
            return

        j = obtain_polynomial(MATRIX_DEGREE, self.q, self.rng)
        self.J = calculate_matrix_polynomial(self.A, j, MATRIX_DIMENSION, self.q)
        if self.J == matrix_null(MATRIX_DIMENSION):
            raise ValueError("J = j(A) is the null matrix")

        self.J_u = matrix_power(self.J, self.u, MATRIX_DIMENSION, self.q)
        self.J_v = matrix_power(self.J, self.v, MATRIX_DIMENSION, self.q)

        self.TB = matrix_multiply(
            matrix_multiply(self.J_u, self.B, MATRIX_DIMENSION, self.q),
            self.J_v,
            MATRIX_DIMENSION,
            self.q,
        )
        self.MB = matrix_multiply(
            matrix_multiply(self.J_u, self.TA, MATRIX_DIMENSION, self.q),
            self.J_v,
            MATRIX_DIMENSION,
            self.q,
        )
        if self.MB == matrix_null(MATRIX_DIMENSION):
            raise ValueError("The shared matrix MB is null")

        self._publish("tb", encode_matrix(self.TB, self.q))
        self._tb_sent = True
        logging.info("TB sent")

    def _try_octonion_stage(self) -> None:
        if self.p is None or self.oA is None or self.MB is None or self._rb_sent:
            return

        if self.rA is None and hasattr(self, "_ra_payload"):
            self.rA = decode_octonion(self._ra_payload, self.p)
            del self._ra_payload

        if self.rA is None:
            return

        degree_map = {
            13: 8,
            251: 16,
            65521: 32,
            4294967279: 64,
            18446744073709551557: 128,
        }
        try:
            degree = degree_map[self.p]
        except KeyError as exc:
            raise ValueError(f"Unsupported p={self.p}") from exc

        _, candidates = generate_octonion_candidates(
            self.MB,
            self.p,
            SUBMATRIX_GRID_DIMENSION,
            SUBMATRIX_DIMENSION,
        )
        _, self.oB = select_first_invertible_octonion(candidates)
        if self.oB is None:
            raise ValueError("None of the four oB candidates is invertible")

        n = self.rng.randrange(2, POWERS)
        h = obtain_polynomial(degree, self.p, self.rng)
        oS2 = tuple(self.rng.randrange(self.p) for _ in range(8))

        h_oA = calculate_f(self.oA, h, self.p)
        shifted = summ(scale(self.oA, -1, self.p), oS2, self.p)
        h_shifted = calculate_f(shifted, h, self.p)
        h1 = power(h_oA, n, self.p)
        h2 = power(h_shifted, n, self.p)
        h_autoconvolution = multiply(h1, h2, self.p)
        self.rB = multiply(h_autoconvolution, self.oB, self.p)

        oB_inverse = octonion_reciprocal(self.oB, self.p)
        recovered_f_autoconvolution = multiply(self.rA, oB_inverse, self.p)
        self.session_key = multiply(recovered_f_autoconvolution, self.rB, self.p)

        if self.session_key == O_NULL:
            raise ValueError("The generated Bob session key is null")

        self._publish("rb", encode_octonion(self.rB, self.p))
        self._rb_sent = True
        logging.info("rB sent")
        logging.info("kB[%s] = %s", self.device_id, self.session_key)

    def run(self) -> None:
        self.client.connect(self.broker_host, self.broker_port, keepalive=60)
        self.client.loop_forever()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HK17.2 Python Bob MQTT integration simulator")
    parser.add_argument("--broker-host", default="127.0.0.1")
    parser.add_argument("--broker-port", type=int, default=1883)
    parser.add_argument("--device-id", default="esp32-01")
    parser.add_argument("--qos", type=int, choices=(0, 1), default=1)
    parser.add_argument("--log-level", choices=("DEBUG", "INFO", "WARNING", "ERROR"), default="INFO")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(message)s",
    )
    BobSimulator(args.broker_host, args.broker_port, args.device_id, args.qos).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
