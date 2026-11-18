#!/usr/bin/env python3
"""Comet Clash local server.

Serves the game (index.html) and the phone controller (pad.html), and relays
controller button presses to the game screen over WebSockets.

    python3 server.py            # then open the printed address on the TV machine
    PORT=9000 python3 server.py  # different port

Standard library only: no installs needed.
"""
import asyncio
import base64
import hashlib
import json
import os
import random
import socket
import struct

PORT = int(os.environ.get("PORT", "8765"))
# Public address phones should use, e.g. a Tailscale Funnel URL (set by play-online.sh).
PUBLIC_URL = os.environ.get("PUBLIC_URL", "").rstrip("/")
ROOT = os.path.dirname(os.path.abspath(__file__))
WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
# Only these files are served; nothing else on disk is reachable.
FILES = {"/": "index.html", "/index.html": "index.html", "/pad": "pad.html", "/pad.html": "pad.html"}
CODE_LETTERS = "ABCDEFGHJKLMNPQRSTUVWXYZ"  # no I/O, easy to read off a TV

rooms = {}  # code -> {"host": WS | None, "pads": {id: {"ws": WS, "token": str, "name": str}}}
next_id = 0


def lan_ip():
    """This machine's address on the local network (no packets are sent)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


class WS:
    """Minimal RFC 6455 WebSocket (text frames; messages here are tiny)."""

    def __init__(self, reader, writer):
        self.r, self.w = reader, writer
        self.lock = asyncio.Lock()
        self.closed = False

    async def recv(self):
        while True:
            h = await self.r.readexactly(2)
            op, masked, n = h[0] & 0x0F, h[1] & 0x80, h[1] & 0x7F
            if n == 126:
                n = struct.unpack("!H", await self.r.readexactly(2))[0]
            elif n == 127:
                n = struct.unpack("!Q", await self.r.readexactly(8))[0]
            if n > 65536:
                raise ConnectionError("frame too large")
            mask = await self.r.readexactly(4) if masked else b""
            data = bytearray(await self.r.readexactly(n))
            if masked:
                for i in range(n):
                    data[i] ^= mask[i & 3]
            if op == 8:
                raise ConnectionError("closed by peer")
            if op == 9:  # ping -> pong
                await self._send(10, bytes(data))
                continue
            if op in (0, 1):
                return data.decode("utf-8", "replace")

    async def _send(self, op, payload):
        if self.closed:
            return
        n = len(payload)
        if n < 126:
            hdr = struct.pack("!BB", 0x80 | op, n)
        elif n < 65536:
            hdr = struct.pack("!BBH", 0x80 | op, 126, n)
        else:
            hdr = struct.pack("!BBQ", 0x80 | op, 127, n)
        async with self.lock:
            try:
                self.w.write(hdr + payload)
                await self.w.drain()
            except (ConnectionError, OSError):
                self.closed = True

    async def send(self, obj):
        await self._send(1, json.dumps(obj).encode())


def new_code():
    while True:
        code = "".join(random.choice(CODE_LETTERS) for _ in range(4))
        if code not in rooms:
            return code


async def ws_session(ws):
    global next_id
    role = room = my_id = None
    try:
        while True:
            try:
                msg = json.loads(await ws.recv())
            except ValueError:
                continue
            if not isinstance(msg, dict):
                continue
            t = msg.get("t")

            if role is None and t == "host":
                # A reloading game screen asks for its old code back so phones reconnect on their own.
                want = str(msg.get("want") or "").upper()
                valid = len(want) == 4 and all(c in CODE_LETTERS for c in want)
                if valid and (want not in rooms or rooms[want]["host"] is None):
                    code = want
                else:
                    code = new_code()
                rooms.setdefault(code, {"host": None, "pads": {}})["host"] = ws
                role, room = "host", code
                await ws.send({"t": "room", "code": code, "lan": PUBLIC_URL or f"http://{lan_ip()}:{PORT}"})
                for pid, pad in rooms[code]["pads"].items():
                    await ws.send({"t": "join", "id": pid, "token": pad["token"], "name": pad["name"]})
                    await pad["ws"].send({"t": "hostback"})
                print(f"game screen connected, room {code}")

            elif role is None and t == "join":
                code = str(msg.get("room") or "").upper()
                if code not in rooms:
                    await ws.send({"t": "noroom", "room": code})
                    continue
                next_id += 1
                my_id, role, room = next_id, "pad", code
                token = str(msg.get("token") or "")[:40]
                name = str(msg.get("name") or "")[:16]
                rooms[code]["pads"][my_id] = {"ws": ws, "token": token, "name": name}
                host = rooms[code]["host"]
                if host:
                    await host.send({"t": "join", "id": my_id, "token": token, "name": name})
                else:
                    await ws.send({"t": "nohost"})
                print(f"controller {my_id} joined room {code}")

            elif role == "pad" and t == "in":
                host = rooms.get(room, {}).get("host")
                if host:
                    await host.send({"t": "in", "id": my_id, "turn": bool(msg.get("turn")), "fire": bool(msg.get("fire"))})

            elif role == "host" and t == "to":
                pad = rooms[room]["pads"].get(msg.get("id"))
                if pad and isinstance(msg.get("m"), dict):
                    await pad["ws"].send(msg["m"])
    except (asyncio.IncompleteReadError, ConnectionError, OSError):
        pass
    finally:
        r = rooms.get(room)
        if r is not None:
            if role == "host" and r["host"] is ws:
                r["host"] = None
                for pad in r["pads"].values():
                    await pad["ws"].send({"t": "nohost"})
                print(f"game screen left room {room}")
            elif role == "pad":
                r["pads"].pop(my_id, None)
                if r["host"]:
                    await r["host"].send({"t": "leave", "id": my_id})
                print(f"controller {my_id} left room {room}")
            if r["host"] is None and not r["pads"]:
                rooms.pop(room, None)


async def handle(reader, writer):
    try:
        req = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), 10)
    except (asyncio.TimeoutError, asyncio.IncompleteReadError, asyncio.LimitOverrunError, ConnectionError):
        writer.close()
        return
    lines = req.decode("latin-1").split("\r\n")
    parts = lines[0].split(" ")
    method, path = (parts + ["", ""])[:2]
    path = path.split("?")[0]
    headers = {}
    for line in lines[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()
    try:
        if path == "/ws" and headers.get("upgrade", "").lower() == "websocket":
            accept = base64.b64encode(hashlib.sha1((headers.get("sec-websocket-key", "") + WS_GUID).encode()).digest()).decode()
            writer.write(
                ("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                 f"Sec-WebSocket-Accept: {accept}\r\n\r\n").encode()
            )
            await writer.drain()
            await ws_session(WS(reader, writer))
        elif method == "GET" and path in FILES:
            with open(os.path.join(ROOT, FILES[path]), "rb") as f:
                body = f.read()
            writer.write(
                b"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n"
                + f"Content-Length: {len(body)}\r\nCache-Control: no-store\r\nConnection: close\r\n\r\n".encode()
                + body
            )
            await writer.drain()
        else:
            body = b"Not found"
            writer.write(b"HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\nContent-Length: 9\r\nConnection: close\r\n\r\n" + body)
            await writer.drain()
    except (ConnectionError, OSError):
        pass
    finally:
        writer.close()


async def main():
    server = await asyncio.start_server(handle, "0.0.0.0", PORT)
    ip = lan_ip()
    print("\n  COMET CLASH server running\n")
    print(f"  Game screen (TV):  http://localhost:{PORT}   or   http://{ip}:{PORT}")
    if PUBLIC_URL:
        print(f"  Phones (anywhere): {PUBLIC_URL}/pad   (or scan the QR code in the lobby)")
        print("  Shared over the internet via Tailscale Funnel. Ctrl+C to stop.\n")
    else:
        print(f"  Phones:            http://{ip}:{PORT}/pad   (or scan the QR code in the lobby)")
        print("  Phones must be on the same Wi-Fi network. Ctrl+C to stop.\n")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
