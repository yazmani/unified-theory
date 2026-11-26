#!/usr/bin/env python3
"""Run the bug-fix suite through one agent harness against one local server, and grade every attempt.

Each attempt is a single-turn session in a fresh copy of the task's template (bench/agents/harness_bench.py), graded
with the hidden upstream tests (grade.py). Runs go round the whole suite before repeating, so a stopped run still
covers every task. Re-running with the same --out resumes: finished attempts are kept.

  python3 -I bench/bugfix/run.py --label splash-katornith --harness pi --bin PATH/TO/pi \
      --base-url http://127.0.0.1:8000 --model local --runs 3 [--only ID ...] [--cache .local/bugfix]

Writes results/bugfix/bugfix-LABEL.json (times, counts, pass/fail; no code). Transcripts stay in --private-out.
"""
import argparse, json, math, os, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import load_tasks  # noqa: E402
from grade import grade  # noqa: E402

SUFFIX = ("\n\nThe repository is in the current directory. A virtualenv in `.venv` has the package installed "
          "(editable) with pytest: use `.venv/bin/python -m pytest`. Fix the bug in the library code; you may add "
          "or update tests. Don't commit.")


def wilson(k, n, z=1.96):
    """95% confidence interval for a pass rate of k out of n."""
    if n == 0:
        return [0.0, 0.0]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0.0, c - h), 3), round(min(1.0, c + h), 3)]


def summarize(res):
    att = [a for runs in res["tasks"].values() for a in runs]
    k, n = sum(a["resolved"] for a in att), len(att)
    per_run = {}
    for a in att:
        per_run.setdefault(a["run"], []).append(a["resolved"])
    res["summary"] = {
        "attempts": n, "resolved": k, "rate": round(k / n, 3) if n else 0, "rate_ci95": wilson(k, n),
        "per_run": {r: f"{sum(v)}/{len(v)}" for r, v in sorted(per_run.items())},
        "tasks_solved_at_least_once": sum(any(a["resolved"] for a in v) for v in res["tasks"].values()),
        "tasks_solved_every_run": sum(all(a["resolved"] for a in v) for v in res["tasks"].values() if v),
        "median_wall_s": sorted(a["wall_s"] for a in att)[n // 2] if n else None,
        "total_wall_s": round(sum(a["wall_s"] for a in att), 1),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--harness", default="pi")
    ap.add_argument("--bin", default=None)
    ap.add_argument("--base-url", required=True, help="server root, without /v1")
    ap.add_argument("--model", required=True)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--cache", default=".local/bugfix")
    ap.add_argument("--private-out", default=os.path.join(os.environ.get("TMPDIR", "/tmp"), "agent-sandbox", "bugfix"))
    ap.add_argument("--context", type=int, default=131072)
    ap.add_argument("--timeout", type=int, default=900, help="seconds per attempt")
    ap.add_argument("--notes", default="")
    ap.add_argument("--out", default=None, help="default results/bugfix/bugfix-LABEL.json")
    a = ap.parse_args()
    cache, priv = Path(a.cache).resolve(), Path(a.private_out).resolve()
    out = Path(a.out or f"results/bugfix/bugfix-{a.label}.json")
    tasks = [t for t in load_tasks(a.only) if json.loads((cache / "tasks" / t["id"] / "meta.json").read_text())["valid"]]
    res = json.loads(out.read_text()) if out.exists() else {
        "label": a.label, "harness": a.harness, "model": a.model, "context": a.context, "timeout_s": a.timeout,
        "notes": a.notes, "started": time.strftime("%Y-%m-%d %H:%M:%S"), "tasks": {}}
    out.parent.mkdir(parents=True, exist_ok=True)
    priv.mkdir(parents=True, exist_ok=True)
    for r in range(1, a.runs + 1):
        for t in tasks:
            done = res["tasks"].setdefault(t["id"], [])
            if any(x["run"] == r for x in done):
                continue
            tdir = cache / "tasks" / t["id"]
            name = f"{a.label}-{t['id']}-r{r}"
            turns = priv / f"{name}.turns.json"
            turns.write_text(json.dumps([t["prompt"] + SUFFIX]))
            metrics = priv / f"{name}.metrics.json"
            cmd = [sys.executable, "-I", str(HERE.parent / "agents" / "harness_bench.py"), "--harness", a.harness,
                   "--label", name, "--base-url", a.base_url, "--model", a.model, "--template", str(tdir / "template"),
                   "--private-out", str(priv), "--metrics-out", str(metrics), "--context", str(a.context),
                   "--turns", str(turns), "--timeout", str(a.timeout)]
            if a.bin:
                cmd += ["--bin", a.bin]
            subprocess.run(cmd, stdout=subprocess.DEVNULL)
            m = json.loads(metrics.read_text())
            row = m["rows"][0] if m["rows"] else {}
            g = grade(priv / name / "ws", tdir)
            done.append({"run": r, "resolved": g["resolved"], "fail_to_pass": g["fail_to_pass"],
                         "pass_to_pass_broken": g["pass_to_pass_broken"], "diff": g["diff"], "commits": g["commits"],
                         "wall_s": m["total_wall_s"], "timeout": row.get("rc") == "timeout",
                         "tool_calls": row.get("tool_calls"), "prompt_tokens": row.get("prompt_tokens"),
                         "cached_tokens": row.get("cached_tokens"), "stop": row.get("stop")})
            summarize(res)
            res["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
            out.write_text(json.dumps(res, indent=1))
            s = res["summary"]
            print(f"{name:48} {'PASS' if g['resolved'] else 'fail'} f2p {g['fail_to_pass']:>6} "
                  f"broke {g['pass_to_pass_broken']:3} {m['total_wall_s']:7.1f}s | total {s['resolved']}/{s['attempts']}",
                  flush=True)
    print(json.dumps(res.get("summary", {}), indent=1))


if __name__ == "__main__":
    main()
