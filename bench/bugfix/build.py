#!/usr/bin/env python3
"""Build and validate the bug-fix suite: one workspace template per task, plus the hidden upstream tests.

For each task in tasks.json:
  1. clone the upstream repo (blobless) into CACHE/repos/,
  2. write the code at the commit before the fix as a fresh one-commit repo (no future history to peek at), with a
     virtualenv in .venv (package installed editable, plus pytest and the task's extras),
  3. save the test files as the fix left them (the agent never sees these),
  4. validate: with the hidden tests in place, the template must fail at least one test that the upstream fix makes
     pass (fail-to-pass); tests passing both before and after are kept as pass-to-pass (regression checks).

  python3 -I bench/bugfix/build.py --cache .local/bugfix [--only ID ...] [--python 3.12] [--force]

Needs git, uv and network access. Writes CACHE/tasks/ID/{template,hidden,meta.json}.
"""
import argparse, json, os, shutil, subprocess, sys, tempfile, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "agents"))
from common import BUILD_ENV, changed_files, git, load_tasks, overlay, pytest_outcomes, targets_for  # noqa: E402
from harness_bench import relocate_venv  # noqa: E402


def run(cmd, cwd=None, **kw):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env={**os.environ, **BUILD_ENV}, **kw)
    if p.returncode:
        raise RuntimeError(f"{' '.join(map(str, cmd))} failed:\n{(p.stdout + p.stderr)[-2000:]}")
    return p.stdout


def clone(cache: Path, repo: str) -> Path:
    d = cache / "repos" / repo.replace("/", "__")
    if not d.exists():
        d.parent.mkdir(parents=True, exist_ok=True)
        run(["git", "clone", "-q", "--filter=blob:none", f"https://github.com/{repo}.git", str(d)])
    return d


def make_template(src: Path, base: str, dest: Path, task, python: str):
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    archive = subprocess.run(["git", "-C", str(src), "archive", base], capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(dest)], input=archive, check=True)
    run(["git", "init", "-q", "-b", "main"], dest)
    run(["git", "add", "-A"], dest)
    run(["git", "-c", "user.name=dev", "-c", "user.email=dev", "commit", "-qm", "base"], dest)
    if task.get("tag"):   # some projects (SymPy) derive their version from `git describe`
        run(["git", "tag", task["tag"]], dest)
    with open(dest / ".git/info/exclude", "a") as f:
        f.write(".venv/\n")
    run(["uv", "venv", "-q", "--python", python, ".venv"], dest)
    run(["uv", "pip", "install", "-q", "--python", ".venv/bin/python", "-e", ".", "pytest", *task.get("install", [])], dest)


def copy_ws(template: Path, dest: Path):
    shutil.copytree(template, dest, symlinks=True)
    relocate_venv(dest, template)


def build(task, cache: Path, python: str, force: bool):
    src = clone(cache, task["repo"])
    git(src, "fetch", "-q", "origin", task["fix"], check=False)
    fix = git(src, "rev-parse", task["fix"]).strip()
    base = git(src, "rev-parse", task.get("base", f"{fix}^1")).strip()
    tdir = cache / "tasks" / task["id"]
    meta_path = tdir / "meta.json"
    if meta_path.exists() and not force:
        return json.loads(meta_path.read_text())
    t0 = time.time()
    tests, other = changed_files(src, base, fix)
    make_template(src, base, tdir / "template", task, python)
    hidden = tdir / "hidden"
    if hidden.exists():
        shutil.rmtree(hidden)
    for status, path in tests:
        if status != "D":
            (hidden / path).parent.mkdir(parents=True, exist_ok=True)
            (hidden / path).write_bytes(subprocess.run(["git", "-C", str(src), "show", f"{fix}:{path}"],
                                                       capture_output=True, check=True).stdout)
    targets = targets_for(task, tests)
    with tempfile.TemporaryDirectory() as tmp:
        ws = Path(tmp) / "ws"
        copy_ws(tdir / "template", ws)
        overlay(ws, hidden, tests)
        before, log_before = pytest_outcomes(ws, targets)
        patch = subprocess.run(["git", "-C", str(src), "diff", "--binary", base, fix, "--", *[p for _, p in other]],
                               capture_output=True, check=True).stdout
        subprocess.run(["git", "apply", "--whitespace=nowarn", "-"], cwd=ws, input=patch, check=True)
        after, log_after = pytest_outcomes(ws, targets)
    f2p = sorted(t for t, o in after.items() if o == "PASSED" and before.get(t) != "PASSED")
    p2p = sorted(t for t, o in after.items() if o == "PASSED" and before.get(t) == "PASSED")
    meta = {"id": task["id"], "repo": task["repo"], "base": base, "fix": fix, "targets": targets,
            "hidden_tests": tests, "fixed_files": [p for _, p in other], "fail_to_pass": f2p, "pass_to_pass": p2p,
            "after_not_passing": sorted(t for t, o in after.items() if o not in ("PASSED", "SKIPPED", "XFAIL")),
            "valid": bool(f2p), "log_before": log_before, "log_after": log_after, "build_s": round(time.time() - t0)}
    meta_path.write_text(json.dumps(meta, indent=1))
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=".local/bugfix")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--python", default="3.12")
    ap.add_argument("--force", action="store_true", help="rebuild tasks that already have a meta.json")
    a = ap.parse_args()
    cache = Path(a.cache).resolve()
    for task in load_tasks(a.only):
        try:
            m = build(task, cache, a.python, a.force)
            print(f"{task['id']:22} {'ok ' if m['valid'] else 'BAD'} fail-to-pass {len(m['fail_to_pass']):3}  "
                  f"pass-to-pass {len(m['pass_to_pass']):5}  not passing after fix {len(m['after_not_passing'])}  "
                  f"{m['build_s']}s", flush=True)
        except Exception as e:  # keep going: one broken task shouldn't stop the others
            print(f"{task['id']:22} ERROR {str(e)[-600:]}", flush=True)


if __name__ == "__main__":
    main()
