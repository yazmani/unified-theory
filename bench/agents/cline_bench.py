#!/usr/bin/env python3
"""Drive the Cline CLI (over ACP, `cline --acp`) through a fixed multi-turn coding session against a local OpenAI-compatible server.

Each run gets a fresh copy of a template repo (so the real project is never touched) and an isolated Cline data dir.
Turns go into one ACP session, as an editor would send them. For each turn it records wall time, the number of
tool calls and the final answer text. Note: over ACP Cline reports its model as "gpt-4o"; requests still go to --base-url.

Raw transcripts may contain private project content: they go to --private-out (outside this repo). Only metrics
(no answer text, no file paths) are written to --metrics-out.

  python3 -I bench/agents/cline_bench.py --label NAME --base-url http://127.0.0.1:8092/v1 --model MODEL_ID \
      --template DIR --private-out DIR --metrics-out results/agents/cline/cline-NAME.json [--context 131072] [--turns FILE]
"""
import argparse, json, os, shutil, subprocess, sys, time
from pathlib import Path

DEFAULT_TURNS = ["what are the changes about?", "allright lets commit this", "how can we improve this project?"]


def cline_bin() -> str:
    env = os.environ.get("CLINE_BIN")
    if env:
        return env
    found = shutil.which("cline")
    if not found:
        sys.exit("set CLINE_BIN to the Cline CLI (npm package `cline`)")
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--template", required=True)
    ap.add_argument("--private-out", required=True)
    ap.add_argument("--metrics-out", required=True)
    ap.add_argument("--context", type=int, default=131072)
    ap.add_argument("--max-tokens", type=int, default=16384)
    ap.add_argument("--turns", default=None, help="JSON list of prompts (default: the 3-turn review/commit/improve session)")
    ap.add_argument("--timeout", type=int, default=1800, help="seconds per turn")
    a = ap.parse_args()
    turns = json.loads(Path(a.turns).read_text()) if a.turns else DEFAULT_TURNS
    cline = cline_bin()

    run = Path(a.private_out) / a.label
    if run.exists():
        shutil.rmtree(run)
    ws, home = run / "ws", run / "home"
    shutil.copytree(a.template, ws, symlinks=True)
    home.mkdir(parents=True)
    # Isolated HOME: Cline keeps its config under ~/.cline, so the user's real settings are never read or changed.
    env = {**os.environ, "HOME": str(home), "PWD": str(ws), "CLINE_PROVIDER": "openai-compatible", "CLINE_API_KEY": "local"}
    subprocess.run([cline, "auth", "-p", "openai-compatible", "-k", "local", "-m", a.model, "-b", a.base_url],
                   check=True, capture_output=True, env=env)
    settings = home / ".cline" / "data" / "settings"
    settings.mkdir(parents=True, exist_ok=True)
    (settings / "models.json").write_text(json.dumps({"version": 1, "providers": {"openai-compatible": {
        "models": {a.model: {"maxTokens": a.max_tokens, "contextWindow": a.context}}}}}))

    sys.path.insert(0, str(Path(__file__).parent))
    from acp_client import AcpSession
    rows = []
    with AcpSession([cline, "--acp", "--auto-approve", "true"], cwd=ws, env=env, log_path=run / "acp.jsonl",
                    timeout=a.timeout) as s:
        for i, prompt in enumerate(turns, 1):
            try:
                r = s.prompt(prompt)
            except Exception as e:                       # a turn that fails or times out is recorded, the session ends
                r = {"stop_reason": f"error: {e}"[:200], "wall_s": a.timeout, "tool_calls": 0, "tools": [], "text": "", "answer": ""}
                rows.append({"turn": i, "wall_s": round(r["wall_s"], 1), "stop": r["stop_reason"], "tool_calls": 0, "answer_chars": 0})
                print(f"{a.label} turn{i}: FAILED {r['stop_reason']}", flush=True)
                break
            (run / f"turn{i}.answer.md").write_text(r["answer"])
            (run / f"turn{i}.full.md").write_text(r["text"])
            rows.append({"turn": i, "wall_s": round(r["wall_s"], 1), "stop": r["stop_reason"], "tool_calls": r["tool_calls"],
                         "answer_chars": len(r["answer"])})
            print(f"{a.label} turn{i}: {r['wall_s']:6.1f}s stop={r['stop_reason']} tools={r['tool_calls']} chars={len(r['answer'])}",
                  flush=True)
    m = {"label": a.label, "model": a.model, "base_url": a.base_url, "context": a.context, "when": time.strftime("%Y-%m-%d %H:%M:%S"),
         "turns": len(turns), "total_wall_s": round(sum(r["wall_s"] for r in rows), 1), "rows": rows}
    Path(a.metrics_out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.metrics_out).write_text(json.dumps(m, indent=1))
    print(f"== {a.label}: total {m['total_wall_s']}s; private transcripts in {run}")


if __name__ == "__main__":
    main()
