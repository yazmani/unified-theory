# Which local model makes the best coding agent? (Cline, 3-turn real session)

**Measured:** 2026-11-23. Driver: `bench/cline_bench.py` + `bench/acp_client.py` (Cline CLI 3.0.75 over ACP,
one session, auto-approve, isolated `HOME`). Raw metrics: [results/agents/cline](../../results/agents/cline/),
summary: [results/agents/cline-session-summary.json](../../results/agents/cline-session-summary.json).

## The task

The same three prompts as a real Cline session: *"what are the changes about?"*, *"allright lets commit this"*,
*"how can we improve this project?"*. Each run starts from a fresh sandbox copy of a private JavaScript project
with ~38 uncommitted changes (a new feature, its wiring, rebuilt output, many permission-only file changes and an
untracked local config folder). How it is graded is in [methodology](../methodology.md#agent-benchmarks).

## Results

| Model / settings | Runs | Total time | Turns 1–2 (9 checks) | Real issues (of 8) | False claims |
|---|---|---|---|---|---|
| **Inkling-2-Mini SQ-15**, Strata + #6627 checkpoint engine, 128K | 3 | **105 / 113 / 119 s** | 9/9, 9/9, 8/9 | 4, 6, 4 | 0 |
| **Tiel-Coder Q4_K_XL**, MTP n-max 1, reasoning budget 8K | 2 | 142 / 168 s | 9/9, 9/9 | 4, **7** | 0 |
| Cyber-Tiel-Coder Q4_K_XL, same settings | 2 | 153 / 181 s | 8/9 (committed local config), 9/9 | 3, 4 | 0 |
| Tiel-Coder IQ4_XS, same settings | 2 | 610 / 284 s | 7/9, 9/9 | 4, 4 | 0, 1 |
| Tiel-Coder Q4_K_XL, MTP n-max 3, budget 8K | 1 | 206 s | 8/9 (committed local config) | 3 | 0 |
| Tiel-Coder Q4_K_XL, MTP n-max 1, **no budget** | 1 | 857 s (commit turn 668 s) | 8/9 | 6 | 0 |
| Inkling-2-Mini SQ-15, **stock Strata 0.2.20** | 2 | 330 / 341 s | 7/9, 8/9 | 6, 5 | 0 |

llama.cpp runs: Unsloth fork b12588, `-c 131072 -fa on -ctk q8_0 -ctv q8_0 --jinja --temp 0.6 --top-p 0.95 --top-k 20
--spec-type draft-mtp --spec-draft-p-min 0.0` (the model card's agentic settings).

Server-side: Tiel Q4_K_XL n-max 1 decoded at 57–61 tok/s with 0.84–0.87 MTP acceptance (n-max 3: 47 tok/s, 0.64);
Inkling ~48 tok/s with 85–88% of prompt tokens from cache.

## Findings

1. **Inkling-2-Mini is the fastest agent model here** (105–119 s) with near-perfect turn 1–2 scores. It generates
   far fewer tokens than Tiel, and the checkpoint engine keeps every follow-up cheap.
2. **Tiel-Coder Q4_K_XL with a reasoning budget matches Inkling's quality and found the most issues** (7/8 once),
   at ~1.4× the time. It decodes faster but thinks more.
3. **Tiel needs `--reasoning-budget` in an agent.** Without it one commit turn thought for 668 s (27K+ tokens). The
   budget is per request, so a long tool loop can still be slow (IQ4_XS run 1 had a 476 s turn).
4. **MTP n-max 1 beats 3** (61 vs 47 tok/s; acceptance 0.87 vs 0.64), as the model card says.
5. **Cyber-Tiel (abliterated, no refusals) was no better at coding** and is a risk with auto-approved commands.
6. **Q4_K_XL beat IQ4_XS** on time and consistency (small sample, temperature 0.6).
7. **Stock Strata 0.2.20 makes Inkling ~3× slower as an agent** with the same quality: see
   [strata-prompt-cache.md](strata-prompt-cache.md#4-strata-0220).
8. The MLX MTP builds of Tiel were skipped: they need oMLX, and the model card measured MTP slower on Apple Silicon.
9. **Every model committed without asking** under auto-approve, and two runs committed a local config folder.
   Turn off "execute all commands" auto-approval in real use.

Setups: [guides/strata.md](../guides/strata.md), [guides/llama-cpp.md](../guides/llama-cpp.md),
[guides/agents.md](../guides/agents.md).
