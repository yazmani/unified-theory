#!/usr/bin/env python3
"""Print Markdown tables straight from results/, so docs never drift from the raw data.

  python3 tools/summarize.py            # all sections
  python3 tools/summarize.py decode     # one of: decode, eval, long-answer, agents
"""
import json, sys
from pathlib import Path

RESULTS = Path(__file__).resolve().parent.parent / "results"


def load(pattern):
    for p in sorted(RESULTS.glob(pattern)):
        try:
            yield p, json.loads(p.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            print(f"<!-- skipped unreadable {p.relative_to(RESULTS)} -->")


def table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    cell = lambda c: "" if c is None else f"{c:.1f}" if isinstance(c, float) else str(c)
    out += ["| " + " | ".join(cell(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def decode():
    rows = [(d["label"], d.get("decode_tps_median"), round(d.get("wall_s_total", 0), 1), d.get("when", "")[:10],
             (d.get("notes") or "")[:60]) for _, d in load("decode/*.json")]
    rows.sort(key=lambda r: -(r[1] or 0))
    return "## Decode (bench/oai_bench.py)\n\n" + table(["label", "decode tok/s (median)", "wall s", "date", "notes"], rows)


def evals():
    rows = [(d["label"], f'{d["passed"]}/{d["total"]}', round(d["wall_s_total"], 1), d.get("tokens_total"))
            for _, d in load("eval/*.json")]
    return "## Mini-eval (bench/mini_eval.py)\n\n" + table(["label", "passed", "wall s", "tokens"], rows)


def long_answer():
    rows = [(d["label"], round(d["wall_s"], 1), d.get("finish"), d.get("engine_tps"), d.get("reasoning_chars"))
            for _, d in load("long-answer/*.json")]
    return "## Long answer (bench/long_answer.py)\n\n" + table(["label", "wall s", "finish", "engine tok/s", "reasoning chars"], rows)


def agents():
    rows = []
    for _, d in list(load("agents/cline/*.json")) + list(load("agents/harness/*.json")):
        r = d.get("rows", [])
        prompt = sum(x.get("prompt_tokens") or 0 for x in r)
        cached = sum(x.get("cached_tokens") or 0 for x in r)
        rows.append((d.get("harness", "cline"), d["label"], d["total_wall_s"], " / ".join(str(x["wall_s"]) for x in r),
                     sum(x.get("tool_calls") or 0 for x in r) or None,
                     f"{100 * cached // prompt}%" if prompt else None))
    rows.sort(key=lambda r: (r[0], r[2]))
    return ("## Agent sessions (bench/cline_bench.py, bench/harness_bench.py)\n\n"
            + table(["harness", "label", "total s", "per turn s", "tool calls", "prompt from cache"], rows)
            + "\n\nQuality scores come from a private grader; see results/agents/cline-session-summary.json and docs/findings/.")


SECTIONS = {"decode": decode, "eval": evals, "long-answer": long_answer, "agents": agents}

if __name__ == "__main__":
    wanted = sys.argv[1:] or list(SECTIONS)
    print("\n\n".join(SECTIONS[w]() for w in wanted))
