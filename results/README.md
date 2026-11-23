# results/

Raw output of the scripts in [bench/](../bench/), one JSON per run. Findings that use them are in
[docs/findings/](../docs/findings/). `make summary` prints tables from these files.

| Folder | Written by | File names |
|---|---|---|
| `decode/` | `oai_bench.py` | `YYYYMMDD-HHMMSS-<label>.json` |
| `long-answer/` | `long_answer.py` | `long-genpython-<label>.json` |
| `eval/` | `mini_eval.py` | `eval-<label>.json` |
| `long-context/` | `long_context.py`, `longctx_multiturn.py` | `longctx-<label>-<N>k.json`, `multiturn-<label>.json` |
| `sessions/` | `agent_session.py` | `session-<label>.json` |
| `agents/cline/` | `cline_bench.py` | `cline-<label>.json` (timing and counts only) |
| `agents/harness/` | `harness_bench.py` | `harness-<harness>-<label>.json` (timing, counts, cached tokens) |
| `agents/cline-session-summary.json` | private grader | generic quality scores for the Cline runs |
| `llama-bench/` | `llama-bench` | Markdown tables |
| `invalid/` | — | smoke tests kept for the record; not used in any finding |

**Labels** encode the setup: `<engine>-<model/quant>-<options>`, e.g. `strata-sq15-dspark`,
`unsloth-llamacpp-iq4xs-dspark3`, `tiel-q4kxl-mtp1-rb8k` (MTP n-max 1, reasoning budget 8K), `-ckpt` (Strata engine
with the #6627 checkpoint), `-0220` (stock Strata 0.2.20), `-r2` (second run).

All runs: Apple M5 Pro, 48 GB, macOS 27.2 ([methodology](../docs/methodology.md)).
