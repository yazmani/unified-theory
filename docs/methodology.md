# Methodology

How every number in this repo was produced, and what it does and doesn't tell you.

## Machine and conditions

- Apple **M5 Pro, 48 GB** unified memory (Metal `recommendedMaxWorkingSetSize` 47.4 GB), macOS 27.2.
- **One model server at a time.** Swap (`sysctl vm.swapusage`) is checked before and after each run; any growth
  invalidates the run. On 2026-11-22 a second model loaded by accident swapped the Mac to 28 GB and froze it.
- Not a clean lab: an OrbStack VM (~15 GB) and other editor agents were often running, as on a real workday.
  Every finding compares setups measured under the same conditions, usually back to back.

## Metrics

| Metric | Where it comes from | Note |
|---|---|---|
| Decode tok/s | the engine's own counter (`timings.predicted_per_second`) | Strata streams in large chunks, so client-side chunk timing is meaningless |
| TTFT | client clock, request → first content | includes hidden thinking on engines that hide it |
| Wall time to a finished answer | client clock | **the number that matters**: a model that thinks 3× longer at the same tok/s is 3× slower |
| Cached tokens | `usage.prompt_tokens_details.cached_tokens`, or the harness's own usage report | the agent benchmarks also read the server log to count full re-reads |
| Mini-eval | 10 Python tasks with hidden asserts, pass@1, greedy | a broken-code smoke test, not a leaderboard |
| Security review | `bench/security_review_eval.py`: 18 planted flaws (10 common, 8 subtle) + 3 clean snippets, regex-graded | defensive; refusals and empty answers counted |
| Session stats | `bench/session_stats.py` over the Splash server log: decode peak / median / token-weighted mean, prefill tok/s, prefix-cache hit, TTFT p50/p95, acceptance | covers every request of a run, harness turns included |
| 100K context | `bench/long_context.py --tokens 100000`: prefill time and speed, decode at depth, 8-needle recall | timed client-side when the server sends no timings (oMLX, DSpine) |

Generation settings: greedy (temperature 0) for speed, eval and long-context runs; the model card's agentic
sampling (temperature 0.6, top-p 0.95, top-k 20) for Tiel-Coder in the agent runs.

## Agent benchmarks

A real 3-turn session (*explain the changes → commit them → suggest improvements*) on a sandbox copy of a private
project. Every run gets a fresh copy (no git remote) and an isolated HOME, so neither the real project nor the
user's agent settings are touched.

The project and its grader stay private (in the gitignored `.local/` folder); only generic scores are published:

- **Turns 1–2: 9 checks.** Explained the feature; explained its wiring; noticed the permission-only file changes;
  committed; included the new files; left the local config folder out; conventional commit message; message names
  the feature; clean tree afterwards.
- **Turn 3: real issues found, out of 8** that were verified by hand in the code.
- **False claims:** suggestions that are wrong about the code (for example "add X" when X already exists).

The grader matches keywords and inspects the resulting commit, and answers on disputed points were read by hand.
One early "false claim" turned out to be correct on inspection and was moved to the real-issues list.

**To run it on your own project:** copy a repo with uncommitted work as the template, write a grader in the shape
of [`bench/examples/grade_template.py`](../bench/examples/grade_template.py), and keep both outside git
(e.g. in `.local/`). See [bench/README.md](../bench/README.md).

## Limits

- One machine. Numbers on other Apple Silicon chips scale roughly with memory bandwidth, but verify.
- Agent runs: 1–3 runs per setup, temperature 0.6 for Tiel. Gaps of one or two issues between setups are within
  run-to-run noise; the timing differences reported as findings (2× and more) are not.
- The mini-eval is too easy to rank models on quality.
