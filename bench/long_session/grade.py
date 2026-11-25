#!/usr/bin/env python3
"""Grade a long-session workspace: Rich v14.3.4 plus the agent's fixes for four bugs fixed upstream in v15.0.0.

Per bug, runs the regression test upstream added (taken from the v15.0.0 test file, never shown to the agent).
Also runs the agent's final test suite and reports any failures (unmodified 14.3.4 passes them all).

  python3 -I bench/long_session/grade.py WORKSPACE UPSTREAM_CLONE > grade.json
"""
import json, shutil, subprocess, sys, tempfile
from pathlib import Path

BUGS = {  # bug: (test file, regression test added upstream)
    "empty_print_end": ("tests/test_console.py", "test_print_empty_with_end"),
    "from_ansi_newlines": ("tests/test_ansi.py", "test_decode_newlines"),
    "file_proxy_isatty": ("tests/test_file_proxy.py", "test_isatty"),
    "markdown_table_inline_code": ("tests/test_markdown.py", "test_inline_code_in_table_cells"),
}
BASELINE_FAILURES: set = set()  # unmodified 14.3.4 passes every test with the pinned venv


def pytest(cwd, *args):
    p = subprocess.run([str(cwd / ".venv/bin/python"), "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rf", *args],
                       cwd=cwd, capture_output=True, text=True, timeout=600)
    return p.returncode, p.stdout


def main():
    ws, upstream = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    out = {"bugs": {}}
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "ws"
        shutil.copytree(ws, copy, symlinks=True, ignore=shutil.ignore_patterns(".git"))
        for bug, (path, test) in BUGS.items():
            src = subprocess.run(["git", "-C", str(upstream), "show", f"v15.0.0:{path}"], capture_output=True,
                                 text=True, check=True).stdout
            hidden = copy / "tests" / f"hidden_{bug}.py"
            hidden.write_text(src)
            rc, _ = pytest(copy, f"{hidden.relative_to(copy)}::{test}")
            out["bugs"][bug] = rc == 0
    rc, log = pytest(ws, "tests")
    failed = sorted({l.split()[1] for l in log.splitlines() if l.startswith("FAILED ")})
    out["new_failures"] = [f for f in failed if f not in BASELINE_FAILURES]
    out["suite_summary"] = log.strip().splitlines()[-1] if log.strip() else ""
    git = lambda *a: subprocess.run(["git", "-C", str(ws), *a], capture_output=True, text=True).stdout
    out["commits_added"] = int(git("rev-list", "--count", "HEAD").strip() or 1) - 1
    out["tree_clean"] = git("status", "--porcelain") == ""
    out["bugs_fixed"] = sum(out["bugs"].values())
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
