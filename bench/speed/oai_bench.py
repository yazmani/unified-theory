#!/usr/bin/env python3
"""Engine-agnostic decode benchmark for any OpenAI-compatible /v1/chat/completions server.

Measures, per prompt: time to first token (TTFT), decode tok/s (completion tokens after the
first / time from first to last token), and end-to-end tok/s. Token counts come from the
server's `usage` (stream_options.include_usage), falling back to counting stream chunks.

Usage:
  python bench/speed/oai_bench.py --url http://127.0.0.1:8080 --label strata-sq20 \
      [--model NAME] [--max-tokens 512] [--runs 3] [--api-key KEY] [--out results/decode/x.json]
"""
import argparse, json, os, statistics, sys, time, urllib.request
from pathlib import Path

PROMPTS = json.loads((Path(__file__).parent / "prompts.json").read_text())


def one(url, model, prompt, max_tokens, api_key, extra=None):
    body = {
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    if model:
        body["model"] = model
    if extra:
        body.update(extra)
    req = urllib.request.Request(
        url.rstrip("/") + "/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", **({"Authorization": f"Bearer {api_key}"} if api_key else {})},
    )
    t0 = time.perf_counter()
    t_first = t_last = None
    chunks, usage, text, reasoning, timings = 0, None, [], [], None
    with urllib.request.urlopen(req, timeout=900) as r:
        for raw in r:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            try:
                ev = json.loads(data)
            except json.JSONDecodeError:
                continue
            if ev.get("usage"):
                usage = ev["usage"]
            if ev.get("timings"):
                timings = ev["timings"]
            for ch in ev.get("choices") or []:
                d = ch.get("delta") or {}
                piece = d.get("content") or ""
                rpiece = d.get("reasoning_content") or d.get("reasoning") or ""
                if rpiece:
                    reasoning.append(rpiece)
                if piece:
                    now = time.perf_counter()
                    t_first = t_first or now
                    t_last = now
                    chunks += 1
                    text.append(piece)
    t_end = time.perf_counter()
    n = (usage or {}).get("completion_tokens") or chunks
    ttft = (t_first - t0) if t_first else None
    dec_time = (t_last - t_first) if t_first and t_last and t_last > t_first else None
    vis = "".join(text)
    wall = t_end - t0
    return {
        "wall_s": wall,
        "engine_decode_tps": (timings or {}).get("predicted_per_second"),
        "engine_prefill_tps": (timings or {}).get("prompt_per_second"),
        "visible_chars": len(vis),
        # ~3.5 chars/token for code: rough visible-output throughput, engine independent
        "visible_tps_est": (len(vis) / 3.5) / wall if wall else None,
        "completion_tokens": n,
        "prompt_tokens": (usage or {}).get("prompt_tokens"),
        "ttft_s": ttft,
        "decode_tps": (n - 1) / dec_time if dec_time and n > 1 else None,
        "e2e_tps": n / (t_end - t0),
        "chunks": chunks,
        "text": vis,
        "reasoning_chars": len("".join(reasoning)),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8080")
    ap.add_argument("--label", required=True)
    ap.add_argument("--model", default=None)
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--api-key", default=os.environ.get("BENCH_API_KEY"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--notes", default="")
    ap.add_argument("--extra", default=None, help='JSON merged into the request body, e.g. {"chat_template_kwargs":{"reasoning_effort":"none"}}')
    a = ap.parse_args()
    extra = json.loads(a.extra) if a.extra else None

    one(a.url, a.model, "Say hi.", 16, a.api_key)  # warm-up
    rows = []
    for p in PROMPTS:
        for i in range(a.runs):
            r = one(a.url, a.model, p["prompt"], a.max_tokens, a.api_key, extra)
            r.update(prompt_id=p["id"], run=i)
            rows.append(r)
            print(f"{a.label:28s} {p['id']:14s} run{i} tok={r['completion_tokens']:4d} "
                  f"wall={r['wall_s']:6.2f}s engine_decode={r['engine_decode_tps'] or 0:6.1f} stream_decode={r['decode_tps'] or 0:6.1f} visible~{r['visible_tps_est'] or 0:6.1f} t/s chars={r['visible_chars']}", flush=True)
    dec = [r["engine_decode_tps"] or r["decode_tps"] for r in rows if (r["engine_decode_tps"] or r["decode_tps"])]
    summary = {
        "label": a.label, "url": a.url, "model": a.model, "max_tokens": a.max_tokens,
        "notes": a.notes, "extra": extra, "when": time.strftime("%Y-%m-%d %H:%M:%S"),
        "decode_tps_median": statistics.median(dec) if dec else None,
        "decode_tps_by_prompt": {p["id"]: statistics.median([(r["engine_decode_tps"] or r["decode_tps"] or 0) for r in rows if r["prompt_id"] == p["id"]] or [0]) for p in PROMPTS},
        "visible_tps_est_median": statistics.median([r["visible_tps_est"] for r in rows]),
        "wall_s_total": sum(r["wall_s"] for r in rows),
        "completion_tokens_total": sum(r["completion_tokens"] for r in rows),
        "visible_chars_total": sum(r["visible_chars"] for r in rows),
        "rows": rows,
    }
    print(json.dumps({k: v for k, v in summary.items() if k != "rows"}, indent=1))
    out = Path(a.out or f"results/decode/{time.strftime('%Y%m%d-%H%M%S')}-{a.label}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=1))
    print("saved", out)


if __name__ == "__main__":
    sys.exit(main())
