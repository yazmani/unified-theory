# Methodology

How the numbers in this repo were produced, and their limits.

## Machine and conditions

- Apple **M5 Pro (20-core GPU), 48 GB** unified memory (Metal `recommendedMaxWorkingSetSize` 47.4 GB), macOS 27.2,
  on mains power.
- **One model server at a time.** Swap (`sysctl vm.swapusage`) is recorded before and after each run; findings note
  any run where it grew. On 2026-11-22 a second model loaded by accident pushed swap to 28 GB and froze the Mac.
- Not an idle machine: an OrbStack VM (~15 GB) and editor agents were often running. Each finding compares setups
  measured under the same conditions, usually back to back.

## Metrics

| Metric | Source | Note |
|---|---|---|
| Decode tok/s | the engine's counter (`timings.predicted_per_second`) | Strata streams in large chunks, so client-side chunk timing is meaningless. Engines without a counter (oMLX, DSpine) are timed by the client and cross-checked with `bench/speed/raw_decode.py` (one non-streamed request: tokens / wall time) |
| TTFT | client clock, request to first content | includes hidden thinking on engines that hide it |
| Wall time to a finished answer | client clock | **the main number**: a model that thinks 3× longer at the same tok/s takes 3× longer |
| Cached tokens | `usage.prompt_tokens_details.cached_tokens`, or the harness's usage report | the agent benchmarks also read the server log to count full re-reads |
| Mini-eval | 10 Python tasks with hidden asserts, pass@1, greedy | catches broken code; does not rank models |
| Security review | `bench/security/security_review_eval.py`: 18 planted flaws (10 common, 8 subtle) and 3 clean snippets, regex-graded | review only; refusals and empty answers counted |
| Engine stats | `tools/session_stats.py` over the Splash server log (`results/engine-stats/`): decode peak / median / token-weighted mean, prefill tok/s, prefix-cache hit, TTFT p50/p95, draft acceptance | covers every request of a run, harness turns included |
| 100K / 250K context | `bench/context/long_context.py --tokens 100000` (or `250000`): prefill time and speed, decode at depth, recall of 8 hidden facts | timed by the client when the server sends no timings (oMLX, DSpine) |
| LiveCodeBench | EvalScope 1.15.0 `live_code_bench`, `release_v6`, one month of contest problems, official prompt, code run locally with 6 s per test | `--limit` applies before the date filter, so a window is selected by dates only |

Sampling: greedy (temperature 0) for speed, mini-eval and long-context runs. Agent runs use whatever the harness sends
on top of the server's defaults, except Tiel-Coder on llama.cpp and DSpine, whose servers were started with Qwen's recommended sampling (temperature 0.6, top-p 0.95,
top-k 20).

## Agent benchmarks

A 3-turn session (explain the changes, commit them, suggest improvements) on a sandbox copy of a private project.
Each run gets a fresh copy with no git remote and an isolated HOME, so neither the real project nor the user's agent
settings are touched.

The project and its grader stay in the gitignored `.local/` folder; only generic scores are published:

- **Turns 1–2, 9 checks:** explained the feature; explained its wiring; noticed the permission-only file changes;
  committed; included the new files; left the local config folder out; conventional commit message; message names
  the feature; clean tree afterwards.
- **Turn 3, issues found of 8:** real problems in the code, each verified by hand.
- **False claims:** suggestions that are wrong about the code (for example "add X" when X already exists).

The grader matches keywords and inspects the resulting commit. Disputed answers were read by hand; one early "false
claim" proved correct and moved to the issues list.

**On your own project:** copy a repo with uncommitted work as the template, write a grader based on
[`bench/agents/grade_template.py`](../bench/agents/grade_template.py), and keep both outside git (for example in
`.local/`). See [bench/README.md](../bench/README.md).

## Bug-fix suite

21 bugs fixed upstream in October–November 2026 in pure-Python libraries ([bench/bugfix](../bench/bugfix/README.md)).
Each attempt is one agent turn in a fresh copy of the code before the fix, with a bug report written for this suite
(symptom, reproduction, expected behaviour). Graded as in SWE-bench with upstream's own regression tests, which the
agent never sees: resolved when every fail-to-pass test passes and no pass-to-pass test breaks. Each model is
screened with one run of 4 attempts at once (`--jobs 4`); close models get more runs. The pass rate is reported with
a 95% interval. A screen stops early when 4 of its first 6+ attempts run out of time (too slow), or at the 5th failed task (it can
no longer reach the top three).

## Limits

- One machine. Results on other Apple Silicon chips should scale roughly with memory bandwidth; verify before
  relying on them.
- 1–3 agent runs per setup. Differences of 1–2 issues between setups are within run-to-run noise; the timing
  differences reported as findings (2× or more) are not. Pass/fail rates over a handful of sessions (commits made,
  say 0 of 4 against 4 of 10) are not significant either (p ≈ 0.2).
- The 3-turn task measures explaining, committing and reviewing on one private project. It never asks for code to be
  written, and its review score is keyword-graded.
- The mini-eval and the security check are too easy to rank strong models. LiveCodeBench ranks them, but needs a
  64K+ answer limit for thinking models and hours per model.
