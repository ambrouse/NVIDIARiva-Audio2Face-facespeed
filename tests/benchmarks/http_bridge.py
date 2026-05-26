#!/usr/bin/env python3
from __future__ import annotations

import argparse
import http.server
import urllib.error
import urllib.request


class BridgeHandler(http.server.BaseHTTPRequestHandler):
    target_base = ""

    def do_GET(self) -> None:
        self.forward()

    def do_POST(self) -> None:
        self.forward()

    def do_OPTIONS(self) -> None:
        self.forward()

    def forward(self) -> None:
        length = int(self.headers.get("Content-Length") or "0")
        body = self.rfile.read(length) if length else None
        target = f"{self.target_base}{self.path}"
        headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() not in {"host", "content-length", "connection", "accept-encoding"}
        }
        request = urllib.request.Request(target, data=body, method=self.command, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                payload = response.read()
                self.send_response(response.status)
                for key, value in response.headers.items():
                    if key.lower() not in {"connection", "transfer-encoding", "content-encoding"}:
                        self.send_header(key, value)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
        except urllib.error.HTTPError as exc:
            payload = exc.read()
            self.send_response(exc.code)
            for key, value in exc.headers.items():
                if key.lower() not in {"connection", "transfer-encoding", "content-encoding"}:
                    self.send_header(key, value)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        except Exception as exc:  # noqa: BLE001 - bridge reports provider failures.
            payload = str(exc).encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} {self.command} {self.path} - {format % args}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="HTTP bridge for benchmark provider port isolation.")
    parser.add_argument("--listen-host", default="127.0.0.1")
    parser.add_argument("--listen-port", type=int, required=True)
    parser.add_argument("--target-base", required=True)
    args = parser.parse_args()

    handler = type("ConfiguredBridgeHandler", (BridgeHandler,), {"target_base": args.target_base.rstrip("/")})
    server = http.server.ThreadingHTTPServer((args.listen_host, args.listen_port), handler)
    print(f"http bridge {args.listen_host}:{args.listen_port} -> {args.target_base.rstrip('/')}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
