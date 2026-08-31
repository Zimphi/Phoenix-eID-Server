"""Minimal hardened HTTPS runner; deploy one listener per trust boundary."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .config import ServerConfig, ServiceProvider
from .eac import PAOSBackend
from .http import HTTPApplication
from .message_security import MessageSecurity
from .service import EIDService
from .tls import psk_context, public_context, service_context


def _load_config(path: str) -> tuple[ServerConfig, dict]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    providers = {
        item["identifier"].lower(): ServiceProvider(
            identifier=item["identifier"].lower(),
            refresh_url=item["refresh_url"],
            communication_error_url=item.get("communication_error_url"),
            terminal_rights=frozenset(item["terminal_rights"]),
            max_sessions=item.get("max_sessions", 32),
        )
        for item in raw["providers"]
    }
    config = ServerConfig(
        ecard_server_url=raw["ecard_server_url"],
        providers=providers,
        session_ttl_seconds=raw.get("session_ttl_seconds", 300),
        token_ttl_seconds=raw.get("token_ttl_seconds", 120),
        psk_bytes=raw.get("psk_bytes", 32),
        max_xml_bytes=raw.get("max_xml_bytes", 1_048_576),
    )
    return config, raw


def _load_component(specification: str | None, expected_type):
    if not specification:
        return None
    module_name, separator, attribute = specification.partition(":")
    if not separator:
        raise ValueError("backend must use module:factory syntax")
    factory = getattr(importlib.import_module(module_name), attribute)
    component = factory()
    if not isinstance(component, expected_type):
        raise TypeError(f"component factory did not return {expected_type.__name__}")
    return component


def _handler(application: HTTPApplication, listener: str):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
        server_version = "Phoenix-eID-Server"
        sys_version = ""

        def do_GET(self):  # noqa: N802
            self._dispatch()

        def do_POST(self):  # noqa: N802
            self._dispatch()

        def _dispatch(self) -> None:
            path = self.path.split("?", 1)[0]
            allowed = {
                "soap": path in {"/eid", "/health"},
                "public": path == "/health" or path.startswith("/tctoken/"),
                "ecard": path in {"/ecard", "/health"},
            }[listener]
            if not allowed:
                self.send_error(404)
                return
            maximum = application.service.config.max_xml_bytes
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self.send_error(400)
                return
            if length < 0 or length > maximum:
                self.send_error(413)
                return
            body = self.rfile.read(length) if length else b""
            headers = {name.lower(): value for name, value in self.headers.items()}
            provider_id = None
            if listener == "soap":
                peer = self.connection.getpeercert(binary_form=True)
                if peer:
                    provider_id = hashlib.sha256(peer).hexdigest()
            response = application.handle(
                self.command,
                self.path,
                headers,
                body,
                provider_id=provider_id,
                psk_authenticated=listener == "ecard",
            )
            self.send_response(response.status)
            self.send_header("Content-Type", response.content_type)
            self.send_header("Content-Length", str(len(response.body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'none'")
            for name, value in response.headers:
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(response.body)

        def log_message(self, format, *args):  # noqa: A002
            # Deliberately omit request targets: TC Token handles are bearer secrets.
            print(f"{self.address_string()} - {args[1] if len(args) > 1 else '-'}")

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser(description="Phoenix test eID server")
    parser.add_argument("--config", required=True)
    parser.add_argument("--listener", default="all", choices=("all", "soap", "public", "ecard"))
    parser.add_argument("--backend", help="PAOS backend factory as module:attribute")
    parser.add_argument(
        "--message-security", help="WS-Security backend factory as module:attribute"
    )
    args = parser.parse_args()
    config, raw = _load_config(args.config)
    service = EIDService(config)
    application = HTTPApplication(
        service,
        _load_component(args.backend, PAOSBackend),
        _load_component(args.message_security, MessageSecurity),
    )

    def create_server(name: str) -> ThreadingHTTPServer:
        listener = raw["listeners"][name]
        address = (listener.get("host", "127.0.0.1"), int(listener["port"]))
        server = ThreadingHTTPServer(address, _handler(application, name))
        server.daemon_threads = True
        if name == "soap":
            context = service_context(
                listener["certfile"], listener["keyfile"], listener["client_ca"]
            )
        elif name == "ecard":
            if application.paos is None:
                parser.error("the ecard listener requires --backend")

            def resolver(identity: str) -> bytes | None:
                session = service.sessions.by_psk_identity(identity)
                return bytes(session.psk) if session else None

            context = psk_context(listener["certfile"], listener["keyfile"], resolver)
        else:
            context = public_context(listener["certfile"], listener["keyfile"])
        server.socket = context.wrap_socket(server.socket, server_side=True)
        return server

    names = ("soap", "public", "ecard") if args.listener == "all" else (args.listener,)
    if "ecard" in names and application.paos is None:
        parser.error("the ecard listener requires --backend")
    if "soap" in names and application.message_security is None:
        parser.error("the soap listener requires --message-security")
    servers = [create_server(name) for name in names]
    threads = []
    for server in servers[1:]:
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.5})
        thread.daemon = True
        thread.start()
        threads.append(thread)
    try:
        servers[0].serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        for server in servers:
            server.shutdown()
            server.server_close()
        for thread in threads:
            thread.join(timeout=2)


if __name__ == "__main__":
    main()
