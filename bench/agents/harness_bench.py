#!/usr/bin/env python3
"""Run the same multi-turn coding session through different agent harnesses against one local server.

Harnesses: `claude` (Claude Code, Anthropic /v1/messages), `pi` (pi coding agent, OpenAI chat completions),
`opencode` (OpenCode, OpenAI chat completions). Cline has its own driver (cline_bench.py, over ACP).

Each turn is one non-interactive CLI call that continues the previous turn's session, with tools auto-approved.
Every run gets a fresh copy of a template repo and an isolated HOME / config dir, so the user's real settings and
the real project are never touched.

Raw transcripts may contain private project content: they go to --private-out (outside this repo). Only metrics
(no answer text, no file paths) go to --metrics-out.

  python3 -I bench/agents/harness_bench.py --harness pi --label NAME --base-url http://127.0.0.1:8091 --model MODEL_ID \
      --template DIR --private-out DIR --metrics-out results/agents/harness/harness-NAME.json [--context 131072] [--bin PATH]
"""
import argparse, json, os, shutil, subprocess, time, uuid
from pathlib import Path

DEFAULT_TURNS = ["what are the changes about?", "allright lets commit this", "how can we improve this project?"]
TOOL_MARK = "\x00tool\x00"


def events(path: Path):
    for line in path.read_text(errors="replace").splitlines():
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            pass


# ---- per-harness setup, command line and output parsing -------------------------------------------------------

def setup_claude(a, home):
    cfg = home / ".claude"
    cfg.mkdir(parents=True)
    env = {"CLAUDE_CONFIG_DIR": str(cfg), "ANTHROPIC_BASE_URL": a.base_url, "ANTHROPIC_API_KEY": "local",
           "ANTHROPIC_MODEL": a.model, "ANTHROPIC_DEFAULT_HAIKU_MODEL": a.model, "ANTHROPIC_DEFAULT_SONNET_MODEL": a.model,
           "ANTHROPIC_DEFAULT_OPUS_MODEL": a.model, "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1", "DISABLE_TELEMETRY": "1",
           "CLAUDE_CODE_MAX_OUTPUT_TOKENS": str(a.max_tokens)}
    return env, {"session": str(uuid.uuid4())}


def cmd_claude(a, st, i, prompt):
    sess = ["--session-id", st["session"]] if i == 1 else ["--resume", st["session"]]
    return [a.bin or "claude", "-p", prompt, "--output-format", "stream-json", "--verbose",
            "--dangerously-skip-permissions", *sess]


def parse_claude(path, st):
    chunks, tools, answer, usage = [], 0, "", {}
    for e in events(path):
        if e.get("type") == "assistant":
            for b in (e.get("message") or {}).get("content") or []:
                if b.get("type") == "text":
                    chunks.append(b.get("text", ""))
                elif b.get("type") == "tool_use":
                    tools += 1
                    chunks.append(TOOL_MARK)
        elif e.get("type") == "result":
            answer = e.get("result") or ""
            u = e.get("usage") or {}
            usage = {"prompt_tokens": u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
                     + u.get("cache_read_input_tokens", 0), "cached_tokens": u.get("cache_read_input_tokens", 0),
                     "stop": e.get("stop_reason") or e.get("subtype")}
    return chunks, tools, answer, usage


def setup_pi(a, home):
    agent = home / ".pi" / "agent"
    agent.mkdir(parents=True)
    (agent / "models.json").write_text(json.dumps({"providers": {"local": {
        "baseUrl": a.base_url.rstrip("/") + "/v1", "api": "openai-completions", "apiKey": "local",
        "models": [{"id": a.model, "contextWindow": a.context, "maxTokens": a.max_tokens}]}}}))
    return {"PI_CODING_AGENT_DIR": str(agent), "PI_OFFLINE": "1"}, {}


def cmd_pi(a, st, i, prompt):
    return [a.bin or "pi", "--mode", "json", "--offline", "--model", f"local/{a.model}",
            *([] if i == 1 else ["--continue"]), prompt]


def parse_pi(path, st):
    chunks, tools, usage = [], 0, {"prompt_tokens": 0, "cached_tokens": 0, "stop": None}
    for e in events(path):
        if e.get("type") != "message_end":
            continue
        m = e.get("message") or {}
        if m.get("role") != "assistant":
            continue
        for b in m.get("content") or []:
            if b.get("type") == "text":
                chunks.append(b.get("text", ""))
            elif b.get("type") == "toolCall":
                tools += 1
                chunks.append(TOOL_MARK)
        u = m.get("usage") or {}
        usage["prompt_tokens"] += u.get("input", 0) + u.get("cacheRead", 0)
        usage["cached_tokens"] += u.get("cacheRead", 0)
        usage["stop"] = m.get("stopReason")
    return chunks, tools, None, usage


def setup_opencode(a, home):
    cfg = home / "opencode.json"
    cfg.write_text(json.dumps({"$schema": "https://opencode.ai/config.json", "autoupdate": False, "share": "disabled",
                               "model": f"local/{a.model}", "provider": {"local": {
                                   "npm": "@ai-sdk/openai-compatible", "name": "local",
                                   "options": {"baseURL": a.base_url.rstrip("/") + "/v1", "apiKey": "local"},
                                   "models": {a.model: {"name": a.model, "limit": {"context": a.context, "output": a.max_tokens}}}}}}))
    env = {"OPENCODE_CONFIG": str(cfg), "OPENCODE_DISABLE_AUTOUPDATE": "1", "XDG_CONFIG_HOME": str(home / ".config"),
           "XDG_DATA_HOME": str(home / ".local/share"), "XDG_CACHE_HOME": str(home / ".cache"),
           "XDG_STATE_HOME": str(home / ".local/state")}
    return env, {"session": None}


def cmd_opencode(a, st, i, prompt):
    sess = ["--session", st["session"]] if st.get("session") else []
    # --dir: opencode resolves the project from $PWD, not the process cwd (it once worked in the caller's repo).
    return [a.bin or "opencode", "run", "--format", "json", "--auto", "--dir", st["ws"], "-m", f"local/{a.model}", *sess, prompt]


def parse_opencode(path, st):
    chunks, tools, usage = [], 0, {"prompt_tokens": 0, "cached_tokens": 0, "stop": None}
    for e in events(path):
        st["session"] = st.get("session") or e.get("sessionID")
        p = e.get("part") or {}
        if e.get("type") == "text":
            chunks.append(p.get("text", ""))
        elif e.get("type") == "tool_use":
            tools += 1
            chunks.append(TOOL_MARK)
        elif e.get("type") == "step_finish":
            t = p.get("tokens") or {}
            usage["prompt_tokens"] += t.get("input", 0) + (t.get("cache") or {}).get("read", 0)
            usage["cached_tokens"] += (t.get("cache") or {}).get("read", 0)
            usage["stop"] = p.get("reason")
    return chunks, tools, None, usage


HARNESSES = {"claude": (setup_claude, cmd_claude, parse_claude), "pi": (setup_pi, cmd_pi, parse_pi),
             "opencode": (setup_opencode, cmd_opencode, parse_opencode)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--harness", required=True, choices=sorted(HARNESSES))
    ap.add_argument("--label", required=True)
    ap.add_argument("--base-url", required=True, help="server root, without /v1")
    ap.add_argument("--model", required=True)
    ap.add_argument("--template", required=True)
    ap.add_argument("--private-out", required=True)
    ap.add_argument("--metrics-out", required=True)
    ap.add_argument("--bin", default=None, help="harness executable (default: found on PATH)")
    ap.add_argument("--context", type=int, default=131072)
    ap.add_argument("--max-tokens", type=int, default=16384)
    ap.add_argument("--turns", default=None, help="JSON list of prompts (default: the 3-turn review/commit/improve session)")
    ap.add_argument("--timeout", type=int, default=1800, help="seconds per turn")
    a = ap.parse_args()
    turns = json.loads(Path(a.turns).read_text()) if a.turns else DEFAULT_TURNS
    setup, cmd, parse = HARNESSES[a.harness]

    run = Path(a.private_out) / a.label
    if run.exists():
        shutil.rmtree(run)
    ws, home = run / "ws", run / "home"
    shutil.copytree(a.template, ws, symlinks=True)
    home.mkdir(parents=True)
    extra, st = setup(a, home)
    env = {k: v for k, v in os.environ.items() if not k.startswith(("CLAUDECODE", "CLAUDE_CODE_", "ANTHROPIC_"))}
    env.update({"HOME": str(home), "PWD": str(ws), **extra})   # PWD too: some harnesses trust it over the real cwd
    st["ws"] = str(ws)

    rows = []
    for i, prompt in enumerate(turns, 1):
        out = run / f"turn{i}.jsonl"
        t0 = time.perf_counter()
        try:
            with open(out, "w") as fo, open(run / f"turn{i}.stderr", "w") as fe:
                rc = subprocess.run(cmd(a, st, i, prompt), cwd=ws, env=env, stdin=subprocess.DEVNULL, stdout=fo,
                                    stderr=fe, timeout=a.timeout).returncode
        except subprocess.TimeoutExpired:
            rc = "timeout"
        wall = time.perf_counter() - t0
        chunks, tools, answer, usage = parse(out, st)
        full = "".join(chunks)
        if answer is None:
            answer = full.rsplit(TOOL_MARK, 1)[-1].strip()
        full = full.replace(TOOL_MARK, "\n").strip()
        (run / f"turn{i}.answer.md").write_text(answer)
        (run / f"turn{i}.full.md").write_text(full)
        rows.append({"turn": i, "wall_s": round(wall, 1), "rc": rc, "stop": usage.get("stop"), "tool_calls": tools,
                     "answer_chars": len(answer), "prompt_tokens": usage.get("prompt_tokens"),
                     "cached_tokens": usage.get("cached_tokens")})
        print(f"{a.label} turn{i}: {wall:6.1f}s rc={rc} stop={usage.get('stop')} tools={tools} chars={len(answer)} "
              f"prompt={usage.get('prompt_tokens')} cached={usage.get('cached_tokens')}", flush=True)
        if rc == "timeout":
            break
    m = {"label": a.label, "harness": a.harness, "model": a.model, "base_url": a.base_url, "context": a.context,
         "when": time.strftime("%Y-%m-%d %H:%M:%S"), "turns": len(turns),
         "total_wall_s": round(sum(r["wall_s"] for r in rows), 1), "rows": rows}
    Path(a.metrics_out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.metrics_out).write_text(json.dumps(m, indent=1))
    print(f"== {a.label}: total {m['total_wall_s']}s; private transcripts in {run}")


if __name__ == "__main__":
    main()
