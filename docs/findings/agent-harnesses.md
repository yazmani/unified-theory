# Agent harnesses compared: Cline vs Claude Code vs pi vs OpenCode

**Question:** with the same local model and the same task, how much does the agent harness itself matter?
**Measured:** 2026-11-23. Same 3-turn session and grader as [agent-models.md](agent-models.md), model Inkling-2-Mini
SQ-15 at 128K. Driver: `bench/harness_bench.py`. Raw metrics: [results/agents/harness](../../results/agents/harness/).

| Harness | Version | API it uses | How the driver runs it |
|---|---|---|---|
| Claude Code | 2.1.330 | Anthropic `/v1/messages` | `claude -p --output-format stream-json`, `--session-id` then `--resume` |
| pi | 1.6.0 | OpenAI chat completions | `pi --mode json`, then `--continue` |
| OpenCode | 1.19.6 | OpenAI chat completions | `opencode run --format json --auto --dir WS`, then `--session ID` |
| Cline | 3.0.75 | OpenAI chat completions | ACP (`cline --acp`), one session (`bench/cline_bench.py`) |

Each turn is one headless call that continues the session, with tools auto-approved and an isolated HOME/config.

## With prompt reuse working (Strata 0.2.19 server + #6627 checkpoint engine)

| Harness | Total time per run | Turns 1–2 (9 checks) | Issues found (of 8) | Tool calls | Review length | Prompt from cache |
|---|---|---|---|---|---|---|
| **OpenCode** | **65.9 / 66.2 s** | 8/9, 8/9 | 4, 5 | 10, 10 | ~1.8K chars | 90% |
| pi | 108.5 / 88.1 s | 9/9, 9/9 | 4, 5 | 14, 13 | ~4.5K chars | 87–88% |
| Cline | 105.3 / 112.6 / 119.0 s | 9/9, 9/9, 8/9 | 4, 6, 4 | 11, 12, 11 | ~5K chars | 85–88% |
| Claude Code | 142.2 / 325.6 s | 9/9, 9/9 | 5, **6** | 15, 53 | 4.3K / 11.3K chars | 91–97% |

## On stock Strata 0.2.20 (no reuse when tools are sent)

| Harness | Total time | Slowdown | Cached tokens |
|---|---|---|---|
| OpenCode | 374.3 s | 5.7× | 0 (18 of 20 requests re-read everything) |
| Claude Code | 406.4 s | 2.9× | 0 (14 of 14) |
| Cline | 330.3 / 341.0 s | 3.0× | 0 |
| pi | 268.2 s | 2.5× | 0 (18 of 18) |

Quality was the same on both servers; only time changed.

## Findings

- **The 0.2.20 cache bug hits every harness**, including Claude Code over `/v1/messages`. All of them send tools,
  and the server's forced empty thinking block breaks the prefix. It is a server bug, not a harness one
  ([details](strata-prompt-cache.md#4-strata-0220)).
- **OpenCode is fastest because it does the least:** fewest tool calls, shortest answers (its review is ~⅓ the
  length of the others), no wasted turns, and the most consistent time (66 s twice). It still found as many real
  issues as pi. It missed one turn-1 detail (the permission-only changes) both times.
- **pi is the best balance:** the smallest system prompt (~1.7K tokens vs ~8K for OpenCode and ~13.5K for Claude
  Code), 9/9 in both runs, a fuller review than OpenCode, 88–108 s.
- **Claude Code is the most thorough and the least predictable.** Its large system prompt is paid once thanks to the
  cache. In run 2 it read 43 files for the review (265 s for that turn) and found the most issues (6/8). Against a
  local server it logs an unrecognized model and assumes a 1M context window.
- **Cline sits between pi and Claude Code** on time and thoroughness.
- Every harness committed without asking under auto-approve.

**Pick:** quick iterative work → OpenCode or pi; deep reviews → Claude Code (or Tiel-Coder in Cline). Whatever you
pick, make sure prompt reuse works on your server: it is a bigger factor than the harness.

## Gotcha: OpenCode trusts `$PWD`

OpenCode takes its project folder from the `PWD` environment variable, not the process working directory. Started
by a script from inside another repo, it worked (and committed) in that repo instead of the sandbox. The driver now
passes `--dir` and sets `PWD` for every harness, and runs from a neutral folder. If you script any agent CLI, do
the same.

Configs for each harness: [guides/agents.md](../guides/agents.md).
