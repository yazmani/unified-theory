#!/usr/bin/env python3
"""Wall-clock decode check: one non-streamed request, completion tokens / total time.

Streamed tok/s (first token -> last token) can be badly wrong when a server buffers tokens and releases them in a
burst; this number can't be. Prompt is tiny, so wall time is ~all decode. Reports visible vs reasoning size too.

  python3 -I bench/speed/raw_decode.py --url http://127.0.0.1:8000 --label NAME [--model M] [--extra JSON] [--max-tokens 1500]
"""
import argparse, json, time, urllib.request
from pathlib import Path

PROMPT = ("Write a complete Python CLI todo app with argparse, JSON file storage, add/list/done/delete commands, "
          "type hints and docstrings. Output only the code.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--model", default="local")
    ap.add_argument("--extra", default=None)
    ap.add_argument("--max-tokens", type=int, default=1500)
    ap.add_argument("--runs", type=int, default=2)
    a = ap.parse_args()
    rows = []
    for i in range(a.runs):
        body = {"model": a.model, "messages": [{"role": "user", "content": PROMPT}], "max_tokens": a.max_tokens,
                "temperature": 0, **(json.loads(a.extra) if a.extra else {})}
        t = time.perf_counter()
        r = json.load(urllib.request.urlopen(urllib.request.Request(
            a.url.rstrip("/") + "/v1/chat/completions", json.dumps(body).encode(),
            {"Content-Type": "application/json"}), timeout=1800))
        wall = time.perf_counter() - t
        m = r["choices"][0]["message"]
        ct = (r.get("usage") or {}).get("completion_tokens", 0)
        row = {"run": i, "completion_tokens": ct, "wall_s": round(wall, 2), "wall_tps": round(ct / wall, 1),
               "visible_chars": len(m.get("content") or ""),
               "reasoning_chars": len(m.get("reasoning_content") or m.get("reasoning") or "")}
        rows.append(row)
        print(f"{a.label} run{i}: {ct} tokens in {wall:.1f}s = {row['wall_tps']} tok/s wall | visible "
              f"{row['visible_chars']} chars, reasoning {row['reasoning_chars']} chars", flush=True)
    out = Path(f"results/raw-decode/raw-{a.label}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    best = max(r["wall_tps"] for r in rows)
    out.write_text(json.dumps({"label": a.label, "extra": a.extra, "when": time.strftime("%Y-%m-%d %H:%M:%S"),
                               "wall_tps_best": best, "rows": rows}, indent=1))
    print(f"== {a.label}: wall decode {best} tok/s (best of {a.runs}), saved {out}")


if __name__ == "__main__":
    main()
