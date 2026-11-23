#!/usr/bin/env python3
"""Time to a complete long answer: one prompt (the first in prompts.json, `gen-python`), up to 8000 tokens, greedy.

Records wall time, finish reason, the engine's decode rate and how much of the output was hidden reasoning.

  python3 -I bench/long_answer.py --url http://127.0.0.1:8092 --label NAME [--extra JSON] [--max-tokens 8000]
"""
import argparse, json, time, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--extra", default="{}", help='JSON merged into the request, e.g. {"chat_template_kwargs":{"reasoning_effort":"none"}}')
    ap.add_argument("--max-tokens", type=int, default=8000)
    a = ap.parse_args()
    prompt = json.loads((HERE / "prompts.json").read_text())[0]["prompt"]
    body = {"messages": [{"role": "user", "content": prompt}], "max_tokens": a.max_tokens, "temperature": 0, **json.loads(a.extra)}
    t = time.perf_counter()
    req = urllib.request.Request(a.url.rstrip("/") + "/v1/chat/completions", json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=1200))
    w = time.perf_counter() - t
    m = r["choices"][0]["message"]
    out = {"label": a.label, "wall_s": w, "usage": r["usage"], "finish": r["choices"][0]["finish_reason"],
           "engine_tps": (r.get("timings") or {}).get("predicted_per_second"), "content_chars": len(m.get("content") or ""),
           "reasoning_chars": len(m.get("reasoning_content") or ""), "content": m.get("content")}
    p = Path(f"results/long-answer/long-genpython-{a.label}.json")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1))
    print({k: v for k, v in out.items() if k != "content"})


if __name__ == "__main__":
    main()
