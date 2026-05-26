#!/usr/bin/env python3
from __future__ import annotations

import argparse
import selectors
import socket
import threading


def main() -> None:
    parser = argparse.ArgumentParser(description="Small TCP bridge for benchmark provider port isolation.")
    parser.add_argument("--listen-host", default="127.0.0.1")
    parser.add_argument("--listen-port", type=int, required=True)
    parser.add_argument("--target-host", default="127.0.0.1")
    parser.add_argument("--target-port", type=int, required=True)
    args = parser.parse_args()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((args.listen_host, args.listen_port))
    server.listen(128)
    print(f"bridge {args.listen_host}:{args.listen_port} -> {args.target_host}:{args.target_port}", flush=True)
    while True:
        client, _ = server.accept()
        thread = threading.Thread(target=bridge_connection, args=(client, args.target_host, args.target_port), daemon=True)
        thread.start()


def bridge_connection(client: socket.socket, target_host: str, target_port: int) -> None:
    try:
        upstream = socket.create_connection((target_host, target_port), timeout=10)
    except OSError:
        client.close()
        return
    with client, upstream:
        client.setblocking(False)
        upstream.setblocking(False)
        selector = selectors.DefaultSelector()
        selector.register(client, selectors.EVENT_READ, upstream)
        selector.register(upstream, selectors.EVENT_READ, client)
        while True:
            events = selector.select(timeout=60)
            if not events:
                return
            for key, _ in events:
                source = key.fileobj
                target = key.data
                try:
                    data = source.recv(65536)
                except OSError:
                    return
                if not data:
                    return
                try:
                    target.sendall(data)
                except OSError:
                    return


if __name__ == "__main__":
    main()
