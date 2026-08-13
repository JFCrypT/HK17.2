"""HK17.2 Raspberry Pi 3 KMS web administration service.

This process runs the MQTT Alice/KMS service and a small FastAPI administration
interface in the same process. The web layer is management-only and is not part
of the frozen HK17.2 cryptographic transcript.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from urllib.parse import unquote

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from kms import DEFAULT_MODULO
from kms_server import HK17MQTTKMS, ServerConfig

WEB_INDEX = Path(__file__).resolve().parent / "web" / "index.html"


def create_app(service: HK17MQTTKMS) -> FastAPI:
    app = FastAPI(
        title="HK17.2 KMS Administration",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    @app.get("/", response_class=HTMLResponse)
    def index() -> HTMLResponse:
        return HTMLResponse(WEB_INDEX.read_text(encoding="utf-8"))

    @app.get("/api/state")
    def state() -> dict[str, object]:
        return service.dashboard_state()

    @app.post("/api/nodes/{device_id}/approve")
    def approve(device_id: str) -> dict[str, str]:
        try:
            service.approve_join(unquote(device_id))
        except (KeyError, ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"status": "approved"}

    @app.post("/api/nodes/{device_id}/reject")
    def reject(device_id: str) -> dict[str, str]:
        try:
            service.reject_join(unquote(device_id))
        except (KeyError, ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"status": "rejected"}

    @app.post("/api/nodes/{device_id}/remove")
    def remove(device_id: str) -> dict[str, str]:
        try:
            service.remove_from_network(unquote(device_id))
        except (KeyError, ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"status": "removed"}

    @app.get("/api/nodes/{device_id}/key")
    def key(device_id: str) -> dict[str, object]:
        try:
            session_key = service.session_key_for(unquote(device_id))
        except (KeyError, ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"device_id": device_id, "key": list(session_key)}

    return app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HK17.2 KMS web administration service")
    parser.add_argument("--broker-host", default="127.0.0.1")
    parser.add_argument("--broker-port", type=int, default=1883)
    parser.add_argument("--modulo", type=int, default=DEFAULT_MODULO)
    parser.add_argument("--qos", type=int, choices=(0, 1), default=1)
    parser.add_argument("--web-host", default="0.0.0.0")
    parser.add_argument("--web-port", type=int, default=8000)
    parser.add_argument("--log-level", choices=("DEBUG", "INFO", "WARNING", "ERROR"), default="INFO")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(message)s",
    )

    service = HK17MQTTKMS(
        ServerConfig(
            broker_host=args.broker_host,
            broker_port=args.broker_port,
            qos=args.qos,
            modulo=args.modulo,
        )
    )
    app = create_app(service)

    service.start_background()
    logging.info("KMS administration UI: http://%s:%d", args.web_host, args.web_port)
    try:
        uvicorn.run(app, host=args.web_host, port=args.web_port, log_level=args.log_level.lower())
    finally:
        service.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
