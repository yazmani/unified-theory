#!/usr/bin/env python3
"""Long-context test: prefill speed, decode speed at depth, and needle retrieval.

Builds a haystack of real source code (default: the Strata checkout next to this repo), sized with the model's own
tokenizer, hides N needles (unique constants) at evenly spread depths, and asks for all of them.

  .venv/bin/python -I bench/long_context.py --url http://127.0.0.1:8091 --label strata-sq15 \
      --tokens 120000 --tokenizer ~/Documents/Strata/Models/inkling-2-mini/tokenizer.json [--extra JSON]
"""
import argparse, json, random, re, time, urllib.request
from pathlib import Path

from tokenizers import Tokenizer

HERE = Path(__file__).resolve().parent


def haystack_files(root: Path):
    exts = {".py", ".cpp", ".h", ".hpp", ".mm", ".metal", ".ts", ".tsx", ".mjs"}
    files = sorted(p for p in root.rglob("*") if p.suffix in exts and p.is_file() and ".git" not in p.parts
                   and "third_party" not in p.parts and p.stat().st_size < 200_000)
    random.Random(0).shuffle(files)
    return files


def build(root, tok, target, n_needles, seed):
    rng = random.Random(seed)
    needles = [(f"KINTSUGI_PROBE_{i:02d}", f"{rng.randrange(16**8):08x}-{rng.randrange(16**4):04x}") for i in range(n_needles)]
    chunks, total = [], 0
    for f in haystack_files(root):
        txt = f"\n# ===== file: {f.relative_to(root)} =====\n" + f.read_text("utf-8", "replace")
        n = len(tok.encode(txt).ids)
        if total + n > target:
            continue
        chunks.append(txt)
        total += n
        if total > target * 0.985:
            break
    # insert needles at evenly spread depths (5% .. 95%)
    for i, (name, val) in enumerate(needles):
        depth = 0.05 + 0.9 * i / max(1, n_needles - 1)
        at = min(len(chunks) - 1, int(depth * len(chunks)))
        chunks.insert(at, f"\n# configuration probe, do not remove\n{name} = \"{val}\"\n")
    return "".join(chunks), needles


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--tokens", type=int, required=True, help="target haystack size in model tokens")
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--root", default=str(HERE.parent.parent / "strata"))
    ap.add_argument("--needles", type=int, default=8)
    ap.add_argument("--max-tokens", type=int, default=3000)
    ap.add_argument("--extra", default=None)
    a = ap.parse_args()
    tok = Tokenizer.from_file(str(Path(a.tokenizer).expanduser()))
    hay, needles = build(Path(a.root), tok, a.tokens, a.needles, seed=a.tokens)
    q = ("\n\n----\nThe text above is a code dump. Somewhere in it are constants named KINTSUGI_PROBE_00, KINTSUGI_PROBE_01, "
         "and so on. List every KINTSUGI_PROBE constant you can find with its exact string value, one per line, as "
         "NAME = \"value\". Output nothing else.")
    prompt = hay + q
    n_prompt = len(tok.encode(prompt).ids)
    body = {"messages": [{"role": "user", "content": prompt}], "max_tokens": a.max_tokens, "temperature": 0,
            "stream": True, "stream_options": {"include_usage": True}, **(json.loads(a.extra) if a.extra else {})}
    t0 = time.perf_counter()
    t_first, t_any, text, usage, timings = None, None, [], None, None
    req = urllib.request.Request(a.url.rstrip("/") + "/v1/chat/completions", json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=7200) as r:
        for raw in r:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:") or line[5:].strip() == "[DONE]":
                continue
            try:
                ev = json.loads(line[5:])
            except json.JSONDecodeError:
                continue
            usage = ev.get("usage") or usage
            timings = ev.get("timings") or timings
            for ch in ev.get("choices") or []:
                d = ch.get("delta") or {}
                if d.get("content") or d.get("reasoning_content") or d.get("reasoning"):
                    t_any = t_any or time.perf_counter()   # first token of any kind = end of prefill
                piece = d.get("content") or ""
                if piece:
                    t_first = t_first or time.perf_counter()
                    text.append(piece)
    wall = time.perf_counter() - t0
    answer = "".join(text)
    found = {m.group(1): m.group(2) for m in re.finditer(r"(KINTSUGI_PROBE_\d\d)\s*=\s*\"?([0-9a-f]{8}-[0-9a-f]{4})", answer)}
    hits = sum(found.get(n) == v for n, v in needles)
    out = {"label": a.label, "when": time.strftime("%Y-%m-%d %H:%M:%S"), "target_tokens": a.tokens,
           "prompt_tokens_local": n_prompt, "usage": usage, "timings": timings, "wall_s": wall,
           "first_visible_s": (t_first - t0) if t_first else None, "needles_found": hits, "needles_total": len(needles),
           "answer": answer, "needles": needles}
    p = Path(f"results/long-context/longctx-{a.label}-{a.tokens // 1000}k.json")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1))
    t = dict(timings or {})
    comp = (usage or {}).get("completion_tokens")
    if not t.get("prompt_per_second") and t_any:      # server sent no timings: measure from the client stream
        pre = t_any - t0
        t = {"prompt_ms": pre * 1000, "prompt_per_second": round(n_prompt / pre, 1),
             "predicted_per_second": round(comp / (wall - pre), 1) if comp and wall > pre else None, "source": "client"}
        out["timings_client"] = t
        p.write_text(json.dumps(out, indent=1))
    print(f"{a.label} {a.tokens//1000}k: prompt={n_prompt} tok, prefill={t.get('prompt_per_second')} tok/s "
          f"({(t.get('prompt_ms') or 0)/1000:.0f}s), decode={t.get('predicted_per_second')} tok/s, "
          f"completion={(usage or {}).get('completion_tokens')}, wall={wall:.0f}s, needles {hits}/{len(needles)}")


if __name__ == "__main__":
    main()
