#!/usr/bin/env python3
"""Three-turn chat over a ~120K-token code dump: turn 1 lists the hidden constants, turns 2-3 ask follow-ups.
Saves every turn's timing, usage and full answer.  Used to A/B Strata's Inkling prefix reuse (STRATA_INKLING_REUSE).

  .venv/bin/python -I bench/context/longctx_multiturn.py URL LABEL [TOKENS]

Haystack: a source checkout (STRATA_DIR, default ../../strata next to this repo). Tokenizer: INKLING_TOKENIZER
(default ~/Documents/Strata/Models/inkling-2-mini/tokenizer.json).
"""
import json, os, re, sys, time, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import long_context as lc
from tokenizers import Tokenizer

url, label = sys.argv[1], sys.argv[2]
n = int(sys.argv[3]) if len(sys.argv) > 3 else 120000
tok = Tokenizer.from_file(str(Path(os.environ.get("INKLING_TOKENIZER", "~/Documents/Strata/Models/inkling-2-mini/tokenizer.json")).expanduser()))
root = Path(os.environ.get("STRATA_DIR") or Path(__file__).resolve().parents[3] / "strata")
hay, needles = lc.build(root, tok, n, 8, n)
truth = {"after03": re.search(r"# ===== file: (\S+)", hay[hay.index("KINTSUGI_PROBE_03"):]).group(1),
         "before06": re.findall(r"# ===== file: (\S+)", hay[:hay.index("KINTSUGI_PROBE_06")])[-1]}
q = ("\n\n----\nThe text above is a code dump. Somewhere in it are constants named KINTSUGI_PROBE_00, KINTSUGI_PROBE_01, "
     "and so on. List every KINTSUGI_PROBE constant you can find with its exact string value, one per line, as "
     "NAME = \"value\". Output nothing else.")
qs = [("after03", "Which file comes right after KINTSUGI_PROBE_03 in the dump? Give just the path."),
      ("before06", "And which file comes right before KINTSUGI_PROBE_06? Just the path.")]


def call(msgs):
    t = time.perf_counter()
    r = json.load(urllib.request.urlopen(urllib.request.Request(url + "/v1/chat/completions", json.dumps(
        {"messages": msgs, "max_tokens": 3000, "temperature": 0}).encode(), {"Content-Type": "application/json"}), timeout=3600))
    return r, time.perf_counter() - t


m = [{"role": "user", "content": hay + q}]
out = {"label": label, "truth": truth, "turns": []}
r, w = call(m)
c = r["choices"][0]["message"]["content"] or ""
hits = sum(f'{a} = "{b}"' in c for a, b in needles)
out["turns"].append({"wall_s": w, "usage": r["usage"], "timings": r.get("timings"), "answer": c, "needles": hits})
print(f"{label} turn1 {w:.0f}s prompt_ms={r.get('timings', {}).get('prompt_ms')} needles {hits}/8", flush=True)
for i, (key, qq) in enumerate(qs, 2):
    m += [{"role": "assistant", "content": c}, {"role": "user", "content": qq}]
    r, w = call(m)
    c = r["choices"][0]["message"]["content"] or ""
    ok = truth[key] in c
    out["turns"].append({"wall_s": w, "usage": r["usage"], "timings": r.get("timings"), "answer": c, "correct": ok,
                         "finish": r["choices"][0]["finish_reason"]})
    print(f"{label} turn{i} {w:.1f}s prompt_ms={r.get('timings', {}).get('prompt_ms')} cached={r['usage'].get('prompt_tokens_details')} "
          f"completion={r['usage']['completion_tokens']} correct={ok} answer={c[:80]!r}", flush=True)
Path("results/long-context").mkdir(parents=True, exist_ok=True)
Path(f"results/long-context/multiturn-{label}.json").write_text(json.dumps(out, indent=1))
