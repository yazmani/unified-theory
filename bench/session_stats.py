#!/usr/bin/env python3
"""Session statistics from a Splash server log: what a whole benchmark session looked like from the engine's side.

Splash logs one line per finished request:
  HH:MM:SS Done · request 12 · input 55,769 · cached 54,592 · ... · output 3,467 · TTFT 1.3s · 60.9 tok/s · 3.6 tok/cycle

From those it reports, over every request in the log (decode benchmark, Cline, pi, security review...):
  - decode: peak, median and token-weighted mean tok/s, and the share of requests above 100 tok/s
  - generated tokens and requests in total
  - prefill: uncached prompt tokens / TTFT, peak and token-weighted mean (short prompts are dominated by fixed cost,
    so it also reports the mean over requests with >= 2,000 new prompt tokens)
  - prefix cache: share of prompt tokens served from cache
  - TTFT p50 / p95, and the largest prompt seen with its TTFT and decode speed
  - speculative acceptance: mean tokens per cycle

  python3 -I bench/session_stats.py LOG [--label NAME] [--out results/sessions/session-NAME.json]
"""
import argparse, json, re, statistics, sys
from pathlib import Path

LINE = re.compile(r"Done · request (?P<req>\d+) · input (?P<inp>[\d,]+) · cached (?P<cached>[\d,]+)"
                  r".*?output (?P<out>[\d,]+) .*?TTFT (?P<ttft>[\d.]+)s · (?P<tps>[\d.]+) tok/s"
                  r"(?: · (?P<cyc>[\d.]+) tok/cycle)?")


def num(s):
    return int(s.replace(",", ""))


def pct(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(p / 100 * (len(xs) - 1))))] if xs else None


def stats(lines):
    rows = []
    for ln in lines:
        m = LINE.search(ln)
        if m:
            rows.append({"input": num(m["inp"]), "cached": num(m["cached"]), "output": num(m["out"]),
                         "ttft": float(m["ttft"]), "tps": float(m["tps"]),
                         "cycle": float(m["cyc"]) if m["cyc"] else None})
    if not rows:
        return None
    dec = [r for r in rows if r["output"] >= 32]            # decode speed of tiny answers is noise
    out_total = sum(r["output"] for r in rows)
    inp_total = sum(r["input"] for r in rows)
    cached_total = sum(r["cached"] for r in rows)
    pre = [r for r in rows if r["input"] - r["cached"] > 0 and r["ttft"] > 0]
    pre_big = [r for r in pre if r["input"] - r["cached"] >= 2000]

    def pre_tps(rs):
        new = sum(r["input"] - r["cached"] for r in rs)
        t = sum(r["ttft"] for r in rs)
        return round(new / t) if t else None

    biggest = max(rows, key=lambda r: r["input"])
    cyc = [r["cycle"] for r in rows if r["cycle"]]
    return {
        "requests": len(rows),
        "generated_tokens": out_total,
        "decode_peak_tps": max(r["tps"] for r in dec) if dec else None,
        "decode_median_tps": round(statistics.median(r["tps"] for r in dec), 1) if dec else None,
        "decode_weighted_tps": round(sum(r["tps"] * r["output"] for r in dec) / sum(r["output"] for r in dec), 1) if dec else None,
        "decode_share_over_100": round(sum(r["tps"] > 100 for r in dec) / len(dec), 2) if dec else None,
        "prefill_peak_tps": round(max((r["input"] - r["cached"]) / r["ttft"] for r in pre)) if pre else None,
        "prefill_mean_tps": pre_tps(pre),
        "prefill_mean_tps_2k_plus": pre_tps(pre_big),
        "prefix_cache_hit": round(cached_total / inp_total, 3) if inp_total else None,
        "ttft_p50_s": pct([r["ttft"] for r in rows], 50),
        "ttft_p95_s": pct([r["ttft"] for r in rows], 95),
        "largest_prompt": {"input": biggest["input"], "cached": biggest["cached"], "ttft_s": biggest["ttft"],
                           "decode_tps": biggest["tps"]},
        "accept_tokens_per_cycle": round(statistics.mean(cyc), 2) if cyc else None,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log")
    ap.add_argument("--label", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    label = a.label or Path(a.log).stem.replace("server-", "")
    s = stats(Path(a.log).read_text(errors="replace").splitlines())
    if not s:
        sys.exit(f"no 'Done ·' request lines in {a.log}")
    out = Path(a.out or f"results/sessions/session-{label}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"label": label, **s}, indent=1))
    lp = s["largest_prompt"]
    print(f"== {label}: {s['requests']} requests, {s['generated_tokens']:,} tokens generated | decode peak "
          f"{s['decode_peak_tps']} / median {s['decode_median_tps']} / weighted {s['decode_weighted_tps']} tok/s | "
          f"prefill peak {s['prefill_peak_tps']} / mean(>=2k) {s['prefill_mean_tps_2k_plus']} tok/s | cache hit "
          f"{s['prefix_cache_hit']:.0%} | TTFT p50 {s['ttft_p50_s']}s p95 {s['ttft_p95_s']}s | largest prompt "
          f"{lp['input']:,} ({lp['cached']:,} cached): TTFT {lp['ttft_s']}s, {lp['decode_tps']} tok/s | "
          f"accept {s['accept_tokens_per_cycle']} tok/cycle")


if __name__ == "__main__":
    main()
