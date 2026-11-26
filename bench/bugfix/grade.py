#!/usr/bin/env python3
"""Grade one bug-fix workspace: put the hidden upstream tests in place and run them.

Resolved = every fail-to-pass test now passes and every pass-to-pass test still passes. Grades in place, so run it
on a throwaway workspace (run.py does). Prints JSON without any code or test output.

  python3 -I bench/bugfix/grade.py WORKSPACE CACHE/tasks/ID
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import git, overlay, pytest_outcomes  # noqa: E402


def grade(ws: Path, tdir: Path) -> dict:
    meta = json.loads((tdir / "meta.json").read_text())
    root = git(ws, "rev-list", "--max-parents=0", "HEAD", check=False).strip().splitlines()
    stat = git(ws, "diff", "--shortstat", root[0], check=False).strip() if root else ""
    commits = int(git(ws, "rev-list", "--count", "HEAD", check=False).strip() or 1) - 1
    overlay(ws, tdir / "hidden", meta["hidden_tests"])
    out, tail = pytest_outcomes(ws, meta["targets"])
    f2p_ok = [t for t in meta["fail_to_pass"] if out.get(t) == "PASSED"]
    p2p_bad = [t for t in meta["pass_to_pass"] if out.get(t) != "PASSED"]
    return {"id": meta["id"], "resolved": len(f2p_ok) == len(meta["fail_to_pass"]) and not p2p_bad,
            "fail_to_pass": f"{len(f2p_ok)}/{len(meta['fail_to_pass'])}", "pass_to_pass_broken": len(p2p_bad),
            "pass_to_pass_broken_ids": p2p_bad[:10], "diff": stat, "commits": commits,
            "collected": len(out), "pytest_tail": tail.splitlines()[-1] if tail else ""}


if __name__ == "__main__":
    print(json.dumps(grade(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()), indent=1))
