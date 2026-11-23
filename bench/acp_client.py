#!/usr/bin/env python3
"""Minimal Agent Client Protocol (ACP) client: drives `cline --acp` over stdio for a multi-turn session.

The Cline CLI's headless `--json` mode can't resume a session (`--id` forces interactive mode), but ACP keeps one
session alive across prompts, which is how an editor talks to Cline.

  from acp_client import AcpSession
  with AcpSession([cline, "--acp", "--auto-approve", "true"], cwd=ws, env=env) as s:
      result = s.prompt("what are the changes about?")   # -> {"stop_reason", "text", "tool_calls", "wall_s", ...}
"""
import json, queue, subprocess, threading, time

TOOL_MARK = "\x00tool\x00"


class AcpSession:
    def __init__(self, cmd, cwd, env=None, log_path=None, timeout=1800):
        self.cmd, self.cwd, self.env, self.timeout = cmd, str(cwd), env, timeout
        self.log = open(log_path, "w") if log_path else None
        self._id = 0
        self._q: "queue.Queue[dict]" = queue.Queue()

    def __enter__(self):
        self.p = subprocess.Popen(self.cmd, cwd=self.cwd, env=self.env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1)
        threading.Thread(target=self._reader, daemon=True).start()
        self._call("initialize", {"protocolVersion": 1, "clientCapabilities": {
            "fs": {"readTextFile": False, "writeTextFile": False}, "terminal": False}})
        r = self._call("session/new", {"cwd": self.cwd, "mcpServers": []})
        self.session_id = r["sessionId"]
        return self

    def __exit__(self, *exc):
        try:
            self.p.stdin.close()
            self.p.terminate()
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()
        if self.log:
            self.log.close()

    def _reader(self):
        for line in self.p.stdout:
            line = line.strip()
            if not line:
                continue
            if self.log:
                self.log.write(line + "\n")
                self.log.flush()
            try:
                self._q.put(json.loads(line))
            except json.JSONDecodeError:
                pass
        self._q.put({"__eof__": True})

    def _send(self, obj):
        self.p.stdin.write(json.dumps(obj) + "\n")
        self.p.stdin.flush()

    def _call(self, method, params, on_update=None):
        self._id += 1
        rid = self._id
        self._send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        deadline = time.monotonic() + self.timeout
        while True:
            left = deadline - time.monotonic()
            if left <= 0:
                raise TimeoutError(f"{method} took longer than {self.timeout}s")
            msg = self._q.get(timeout=left)
            if msg.get("__eof__"):
                raise RuntimeError(f"agent exited during {method}")
            if msg.get("id") == rid and ("result" in msg or "error" in msg):
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg["result"]
            if msg.get("method") == "session/request_permission":      # auto-approve: pick an allow option
                opts = msg["params"].get("options") or []
                pick = next((o for o in opts if o.get("kind", "").startswith("allow")), opts[0] if opts else None)
                self._send({"jsonrpc": "2.0", "id": msg["id"], "result": {
                    "outcome": {"outcome": "selected", "optionId": pick["optionId"]} if pick else {"outcome": "cancelled"}}})
            elif "method" in msg and "id" in msg:                     # any other client request: not supported
                self._send({"jsonrpc": "2.0", "id": msg["id"], "error": {"code": -32601, "message": "not supported"}})
            elif msg.get("method") == "session/update" and on_update:
                on_update(msg["params"].get("update") or {})

    def prompt(self, text):
        chunks, tools = [], []

        def on_update(u):
            kind = u.get("sessionUpdate")
            if kind == "agent_message_chunk":
                c = u.get("content") or {}
                if c.get("type") == "text":
                    chunks.append(c.get("text", ""))
            elif kind == "tool_call":
                tools.append(u.get("title") or u.get("kind") or "tool")
                chunks.append(TOOL_MARK)                              # keep only the text after the last tool call as the answer
        t0 = time.perf_counter()
        r = self._call("session/prompt", {"sessionId": self.session_id, "prompt": [{"type": "text", "text": text}]}, on_update)
        full = "".join(chunks)
        answer = full.rsplit(TOOL_MARK, 1)[-1].strip()
        full = full.replace(TOOL_MARK, "\n")
        return {"stop_reason": r.get("stopReason"), "wall_s": time.perf_counter() - t0, "tool_calls": len(tools),
                "tools": tools, "text": full.strip(), "answer": answer}
