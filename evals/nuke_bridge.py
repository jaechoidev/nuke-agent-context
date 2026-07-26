#!/usr/bin/env python3
"""Minimal client for the nuke-mcp addon socket (kleer001/nuke-mcp).

Talks directly to the addon's TCP server (default :54321) so we can execute
Python and BlinkScript inside a running, licensed Nuke and verify our example
corpus for real -- without routing through the MCP layer.

Protocol (from the addon): newline-delimited JSON.
  on connect the server SENDS a handshake line first (nuke_version, variant, ...)
  request : {"type": <command>, "params": {...}}
  reply   : {"status": "ok", "result": ...} | {"status": "error", "error": ...}

Usage:
  python3 evals/nuke_bridge.py ping
  python3 evals/nuke_bridge.py exec 'result = nuke.NUKE_VERSION_STRING'
  python3 evals/nuke_bridge.py execfile path/to/tool.py 'result = my_func()'
  python3 evals/nuke_bridge.py blink path/to/kernel.blink   # compile-check a kernel
"""
from __future__ import annotations

import json
import pathlib
import socket
import sys

HOST, PORT = "127.0.0.1", 54321


def _read_line(s: socket.socket, buf: bytearray) -> bytes:
    while b"\n" not in buf:
        chunk = s.recv(1 << 20)
        if not chunk:
            break
        buf += chunk
    line, _, rest = bytes(buf).partition(b"\n")
    buf[:] = rest
    return line


def call(cmd_type: str, params: dict | None = None, timeout: float = 30.0) -> dict:
    with socket.create_connection((HOST, PORT), timeout=timeout) as s:
        s.settimeout(timeout)
        buf = bytearray()
        _read_line(s, buf)                    # consume the server handshake first
        s.sendall((json.dumps({"type": cmd_type, "params": params or {}}) + "\n").encode())
        line = _read_line(s, buf)
    return json.loads(line.decode())


def execute(code: str) -> dict:
    return call("execute_python", {"code": code})


# Compiling a Blink kernel is subtle: the inline `kernelSource` knob is IGNORED
# (the node keeps its cached kernel), recompile never raises, and node.error()
# stays False on failure. The only reliable signal is `kernelName` -- a
# successful compile sets it to the kernel's declared class; a failure leaves it
# at the previous/default name. So: load from a FILE, recompile, and require
# kernelName to equal the class the source declares.
BLINK_CHECK = '''\
import nuke, re
path = {path!r}
src = open(path).read()
m = re.search(r"\\bkernel\\s+(\\w+)", src)
expected = m.group(1) if m else None
b = nuke.nodes.BlinkScript()
b["kernelSourceFile"].setValue(path)
b["reloadKernelSourceFile"].execute()
b["recompile"].execute()
got = b["kernelName"].value()
nuke.delete(b)
result = "ok" if (expected and got == expected) else ("ERROR: kernel did not compile (kernelName=%r, expected %r)" % (got, expected))
'''


def blink_compile(path: str) -> dict:
    return call("execute_python", {"code": BLINK_CHECK.format(path=path)})


RENDER = '''\
import nuke, os
path = {path!r}
out = {out!r}
if os.path.exists(out): os.remove(out)
for n in list(nuke.allNodes()): nuke.delete(n)
c = nuke.nodes.Constant(format={fmt!r})
b = nuke.nodes.BlinkScript(inputs=[c])
b["kernelSourceFile"].setValue(path)
b["reloadKernelSourceFile"].execute()
b["recompile"].execute()
name = b["kernelName"].value()
w = nuke.nodes.Write(inputs=[b], file=out, file_type="png")
nuke.execute(w, 1, 1)
for n in list(nuke.allNodes()): nuke.delete(n)
result = {{"kernelName": name, "rendered": os.path.exists(out), "path": out}}
'''


def render_blink(path: str, out: str, fmt: str = "square_512") -> dict:
    return call("execute_python", {"code": RENDER.format(path=path, out=out, fmt=fmt)})


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    op = sys.argv[1]
    try:
        if op == "ping":
            print(json.dumps(call("ping"), indent=2))
        elif op == "exec":
            print(json.dumps(execute(sys.argv[2]), indent=2))
        elif op == "execfile":
            code = pathlib.Path(sys.argv[2]).read_text()
            if len(sys.argv) > 3:
                code += "\n" + sys.argv[3]
            print(json.dumps(execute(code), indent=2))
        elif op == "blink":
            print(json.dumps(blink_compile(sys.argv[2]), indent=2))
        elif op == "render":
            out = sys.argv[3] if len(sys.argv) > 3 else "/tmp/nuke_agent_render.png"
            print(json.dumps(render_blink(sys.argv[2], out), indent=2))
        else:
            print(f"unknown op: {op}", file=sys.stderr)
            return 2
    except (ConnectionRefusedError, socket.timeout, OSError) as e:
        print(f"cannot reach Nuke addon on {HOST}:{PORT} -- is Nuke open with "
              f"nuke_mcp_addon.start() run?  ({e})", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
