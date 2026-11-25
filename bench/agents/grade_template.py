#!/usr/bin/env python3
"""Template grader for the 3-turn agent session (cline_bench.py / harness_bench.py).

Copy this OUTSIDE git (e.g. .local/agent-bench/grade.py) and fill in checks for your own project: real file names,
the feature you changed, the issues you verified by hand. Keep project specifics out of the public repo; this script
prints only generic scores.

  python3 -I grade.py RUN_DIR > RUN_DIR/grade.json
"""
import json, re, subprocess, sys
from pathlib import Path

run = Path(sys.argv[1])
ws = run / "ws"                                    # the sandbox repo the agent worked in
read = lambda p: (run / p).read_text().lower() if (run / p).exists() else ""
t1, t3 = read("turn1.full.md"), read("turn3.full.md")
git = lambda *a: subprocess.run(["git", *a], cwd=ws, capture_output=True, text=True).stdout

FEATURE = "my-feature"                             # TODO: a word every good turn-1 answer must contain
NEW_FILES = ["src/my_feature.js"]                  # TODO: files the commit must include
LOCAL_ONLY = ".claude"                             # TODO: a folder that must NOT be committed
BASE_COMMIT = "abc1234"                            # TODO: HEAD of the template before the session

score = {}
score["t1_feature_identified"] = FEATURE in t1
committed = BASE_COMMIT not in (git("log", "--oneline", "-1") or BASE_COMMIT)
score["t2_committed"] = committed
files = git("show", "--name-only", "--format=", "HEAD").split() if committed else []
score["t2_new_files_included"] = committed and all(f in files for f in NEW_FILES)
score["t2_local_config_excluded"] = committed and not any(f.startswith(LOCAL_ONLY) for f in files)
score["t2_message_conventional"] = bool(re.match(r"(feat|fix|chore|refactor)(\(.+\))?: ", git("log", "-1", "--format=%B")))

TRUE_FINDINGS = {                                  # TODO: issues you verified in the code -> regex over turn 3
    "no_tests": r"no tests|unit tests|test suite",
}
FALSE_CLAIMS = {                                   # TODO: wrong suggestions to catch (e.g. "add X" when X exists)
}
score["t3_true_findings"] = sorted(k for k, rx in TRUE_FINDINGS.items() if re.search(rx, t3))
score["t3_false_claims"] = sorted(k for k, rx in FALSE_CLAIMS.items() if re.search(rx, t3))

checks = [k for k in score if k.startswith(("t1_", "t2_"))]
score["summary"] = {"t1_t2_checks_passed": sum(score[k] is True for k in checks), "t1_t2_checks_total": len(checks),
                    "t3_true_findings": len(score["t3_true_findings"]), "t3_true_total": len(TRUE_FINDINGS),
                    "t3_false_claims": len(score["t3_false_claims"])}
print(json.dumps(score, indent=1))
