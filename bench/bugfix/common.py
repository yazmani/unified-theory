"""Shared helpers for the bug-fix suite: task list, git, pytest runs and result parsing."""
import json, os, re, shutil, subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASKS = HERE / "tasks.json"
PYTEST_TIMEOUT = 1200
# setuptools-scm / hatch-vcs need a version when the tree has no tags (the template is a fresh one-commit repo)
BUILD_ENV = {"SETUPTOOLS_SCM_PRETEND_VERSION": "0.0.0", "UV_NO_PROGRESS": "1"}
SUBTEST_ID = re.compile(r"\s(\S+?\.py::\S+)")
OUTCOMES = ("PASSED", "FAILED", "ERROR", "XFAIL", "XPASS", "SKIPPED")


def load_tasks(ids=None):
    tasks = json.loads(TASKS.read_text())
    if ids:
        known = {t["id"] for t in tasks}
        missing = set(ids) - known
        if missing:
            raise SystemExit(f"unknown task ids: {sorted(missing)}")
        tasks = [t for t in tasks if t["id"] in ids]
    return tasks


def git(repo, *args, check=True):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=check).stdout


def is_test_path(path: str) -> bool:
    parts = path.lower().split("/")
    return any(p in ("test", "tests", "testing") for p in parts[:-1]) or parts[-1].startswith("test_") \
        or parts[-1].endswith("_test.py")


def changed_files(repo, base, fix):
    """(test files, other files) changed between base and fix, with their status (A/M/D)."""
    rows = [l.split("\t") for l in git(repo, "diff", "--name-status", "--no-renames", base, fix).splitlines()]
    tests = [(s, p) for s, p in rows if is_test_path(p)]
    other = [(s, p) for s, p in rows if not is_test_path(p)]
    return tests, other


def targets_for(task, tests):
    """Test modules to run: the task's explicit targets, else the changed test modules."""
    if task.get("targets"):
        return task["targets"]
    return [p for s, p in tests if s != "D" and p.endswith(".py") and Path(p).name.startswith("test")]


def pytest_outcomes(ws: Path, targets):
    """Run pytest on targets in ws; return ({node id: outcome}, tail of the log)."""
    cmd = [str(ws / ".venv/bin/python"), "-m", "pytest", "-p", "no:cacheprovider", "-rA", "-q",
           "-o", "addopts=", "--tb=no", "--color=no", *targets]
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    try:
        p = subprocess.run(cmd, cwd=ws, capture_output=True, text=True, timeout=PYTEST_TIMEOUT, env=env)
        log = p.stdout + p.stderr
    except subprocess.TimeoutExpired as e:
        log = (e.stdout or b"").decode(errors="replace") + "\nTIMEOUT"
    out = {}
    for line in log.splitlines():
        word, _, rest = line.partition(" ")
        if word.startswith("SUBFAILED"):   # pytest 9 subtests: "SUBFAILED[case, may have spaces] test_id - message"
            m = SUBTEST_ID.search(line)
            if not m:
                continue
            word, rest = "FAILED", m.group(1)
        if word in OUTCOMES and "::" in rest:
            if word in ("FAILED", "ERROR") and " - " in rest:
                rest = rest.split(" - ", 1)[0]
            rest = rest.strip()
            if out.get(rest) not in ("FAILED", "ERROR"):   # a failed subtest fails its test even if it reports PASSED
                out[rest] = word
    return out, "\n".join(log.strip().splitlines()[-5:])


def overlay(ws: Path, hidden: Path, manifest):
    """Write the hidden (fix-version) test files into ws; delete those the fix deleted."""
    for status, path in manifest:
        dst = ws / path
        if status == "D":
            dst.unlink(missing_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(hidden / path, dst)
