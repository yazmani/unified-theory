# Bug-fix suite: real upstream bugs, hidden upstream tests

Ranks models on coding quality, not speed: can an agent fix a real bug from its report? Each task is a bug fixed
upstream in October–November 2026, in a pure-Python library with a fast test suite. The agent gets the code as it
was before the fix and a bug report (symptom, reproduction, expected behaviour; never the cause or the fix). It is
graded with the regression tests upstream added with the fix, which it never sees.

The fixes are recent so that few models can have seen them in training; check a model's release date against the
fix dates in `tasks.json` before trusting its score.

## Tasks

[`tasks.json`](tasks.json): 21 tasks from sqlglot, more-itertools, isort, tomlkit, Black, markdown-it-py, NetworkX,
Loguru, pyparsing and SymPy, each with the upstream fix commit and the prompt. Fixes range from one line to ~60
lines over 1–3 files.

## Grading

As in SWE-bench: with the hidden tests in place, a task is **resolved** when every *fail-to-pass* test passes (tests
the template fails and the upstream fix passes) and no *pass-to-pass* test breaks (tests in the same modules that
pass before and after the fix). `build.py` computes both lists by running the tests on the template and on the
template plus the upstream fix, and rejects a task with no fail-to-pass test.

The prompts give exact expected outputs where the hidden tests check exact strings (formatters, SQL generation), so
a correct fix that formats differently isn't failed for it.

## Run

```sh
python3 -I bench/bugfix/build.py --cache .local/bugfix           # clone, build templates, validate (needs uv, git)
python3 -I bench/bugfix/run.py --label my-model --harness pi --bin PATH/TO/pi \
  --base-url http://127.0.0.1:8000 --model local --runs 3 [--jobs 4]
```

One attempt per task per run, single turn, 15 min limit, fresh workspace each time. `run.py` resumes if
interrupted. `--jobs N` runs N attempts at once against the same server (Splash serves 4 requests together by
default), which cuts a 21-task run from ~80 to ~45 min on a 35B-A3B model. Each attempt then decodes more slowly, so
compare models only at the same `--jobs`, and check the server isn't queueing: Flash-Next Coder (58 GB, part of its
weights read from the SSD) waited ~16 s per request for the other three at `--jobs 4`, and needs `--jobs 1`.

Results: `results/bugfix/bugfix-LABEL.json` with the pass rate, its 95% confidence interval (Wilson), and
per-attempt time, tool calls and tokens. Transcripts stay in `--private-out`.

## Limits

- Python only, one harness per run (pi by default).
- Small fixes: close to saturated. The best local model solved 19 of 21 in one run, and one task (black-5634) has
  defeated every model so far ([models.md](../../docs/findings/models.md)). Harder tasks can be added to
  `tasks.json`; `build.py` validates them.
- Three runs of 21 tasks give a margin of about ±12 points on the pass rate; differences smaller than that are noise.
