#!/usr/bin/env python3
"""Push a local file to a running MatrixBox over Wi-Fi — "scp for the device".

Text files go through the file manager (/system/fm/write). Binary files (e.g. .mpy)
go through /repl + base64, because the device's HTTP transport is text-only and
truncates at the first null byte. Format is auto-detected (override with
--binary / --text).

Both routes are only live from the device's SELECTOR screen — a running app
clears them, so exit any app first.

Usage:
    python3 tools/push.py <local> <device_path> [--host IP]
    MATRIXBOX_HOST=192.168.1.10 python3 tools/push.py apps/my_app/code.mpy /my_app/code.mpy
"""

import argparse
import base64
import json
import os
import sys
import urllib.request

TIMEOUT = 20


def looks_text(data: bytes) -> bool:
    if b"\x00" in data:
        return False
    try:
        data.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def post(url: str, body: bytes, headers: dict | None = None) -> str:
    req = urllib.request.Request(url, data=body, method="POST", headers=headers or {})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8", "replace")


def repl(host: str, snippet: str) -> str:
    """Run a Python snippet on the device via /repl, return its printed output."""
    out = post(f"http://{host}/repl", base64.b64encode(snippet.encode()))
    res = json.loads(out)
    msg = base64.b64decode(res.get("output", "")).decode("utf-8", "replace").strip()

    if not res.get("ok"):
        sys.exit(f"device error: {msg or out}")

    return msg


def push_text(host: str, device_path: str, data: bytes) -> None:
    res = json.loads(post(f"http://{host}/system/fm/write", data, {"x-path": device_path}))
    if not res.get("ok"):
        sys.exit(f"device error: {res.get('error', res)}")


def push_binary(host: str, device_path: str, data: bytes) -> None:
    payload = base64.b64encode(data).decode()
    # Inner snippet writes the file in binary; !r quotes the path/payload as
    # valid Python literals, payload is base64 (quote-safe).
    snippet = (
        f"import binascii; "
        f"open({device_path!r}, 'wb').write(binascii.a2b_base64({payload!r}))"
    )
    repl(host, snippet)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("local")
    ap.add_argument(
        "device_path", help="absolute path on the device, e.g. /lastfm/code.mpy"
    )
    ap.add_argument("--host", default=os.environ.get("MATRIXBOX_HOST"))

    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--binary", action="store_true", help="force the /repl route")
    mode.add_argument("--text", action="store_true", help="force the /fm/write route")

    args = ap.parse_args()

    host = (args.host or "").replace("http://", "").replace("https://", "").strip("/")
    if not host:
        sys.exit("set --host or MATRIXBOX_HOST")

    with open(args.local, "rb") as f:
        data = f.read()

    binary = args.binary or (not args.text and not looks_text(data))
    route = "/repl (base64)" if binary else "/system/fm/write"
    print(f"{args.local} -> {host}:{args.device_path}  [{route}, {len(data)} B]")

    if binary:
        push_binary(host, args.device_path, data)
    else:
        push_text(host, args.device_path, data)


if __name__ == "__main__":
    main()
