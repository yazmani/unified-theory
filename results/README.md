# results/

Raw output of the scripts in [bench/](../bench/), one JSON per run. Findings that use them are in
[docs/findings/](../docs/findings/). `make summary` prints tables from these files.

| Folder | Written by | File names |
|---|---|---|
| `decode/` | `oai_bench.py` | `YYYYMMDD-HHMMSS-<label>.json` |
| `raw-decode/` | `raw_decode.py` | `raw-<label>.json` (wall-clock decode, non-streamed) |
| `long-answer/` | `long_answer.py` | `long-genpython-<label>.json` |
| `eval/` | `mini_eval.py` | `eval-<label>.json` |
| `security/` | `security_review_eval.py` | `sec-<label>.json` (per-snippet hit / refusal, no answer text) |
| `long-context/` | `long_context.py`, `longctx_multiturn.py` | `longctx-<label>-<N>k.json`, `multiturn-<label>.json` |
| `engine-stats/` | `session_stats.py` | `stats-<label>.json`: every request of a run, from the Splash server log |
| `sessions/` | `agent_session.py` | `session-<label>.json`: the 8-turn pasted-source chat (Strata) |
| `agents/cline/` | `cline_bench.py` | `cline-<label>.json` (timing and counts only) |
| `agents/harness/` | `harness_bench.py` | `harness-<harness>-<label>.json` or `harness-<label>-<harness>.json` (timing, counts, cached tokens) |
| `agents/long-session/` | `harness_bench.py` + `long_session/grade.py` | `longsess-<label>-<harness>.json` (timing, tokens per turn), `grade-<label>-<harness>.json` (bugs fixed, test failures, commit) |
| `agents/cline-session-summary.json` | private grader | generic quality scores for the early Cline runs |
| `livecodebench/` | EvalScope `live_code_bench`, graded with its `codegen_metrics` | `lcb-<label>-<window>.json`: settings, totals, and difficulty / pass / output tokens per problem (no code) |
| `llama-bench/` | `llama-bench` | Markdown tables |
| `invalid/` | — | smoke and debug runs kept for the record; not used in any finding |

**Labels** encode the setup: `<engine>-<model/quant>-<options>`, e.g. `splash-katornith-q4km-tb8k` (thinking budget
8K), `strata-sq15-dspark`, `unsloth-llamacpp-iq4xs-dspark3`, `tiel-q4kxl-mtp1-rb8k` (llama.cpp, MTP n-max 1,
reasoning budget 8K). Suffixes: `-r2` second run, `-lc` long-context run, `-sec3` security run (third version of the
check), `-effortnone` / `-nothink` thinking off, `-think` the model's default thinking, `-clean` a rerun with the Mac idle, `-expNN` an NN GB expert store, `-pc-*` persistent-cache runs,
`-ctx256k` run with `--max-context 256K`, `-ckpt` / `-0220` Strata with the #6627 checkpoint engine / stock 0.2.20.

All runs: Apple M5 Pro, 48 GB, macOS 27.2 ([methodology](../docs/methodology.md)).
