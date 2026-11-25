# Does the agent harness matter? Cline vs Claude Code vs pi vs OpenCode

**Answer as of 2026-11-25: yes, 2–5× on the same model and task.** On Splash, **pi** is fastest; OpenCode and Cline
found the most issues. Prompt reuse on the server matters more than the harness: without it, every harness ran
2.5–5.7× slower ([strata-prompt-cache](strata-prompt-cache.md)).

## On Splash and oMLX (2026-11-24)

Inkling-2-Mini, thinking off, same 3-turn session. Each cell: total time · commit checks passed of 9 · issues found
of 8.

| Engine (wall-clock decode) | Cline | OpenCode | Claude Code | pi |
|---|---|---|---|---|
| **Splash** (116 tok/s) | 75–94 s · 9/9 · 6 | 139 s · 9/9 · **6** | 139 s · 9/9 · 4 | **49 s** · 9/9 · 4 |
| oMLX, MTP (55 tok/s) | 370 s · 9/9 · 6 | 268 s · 8/9 · 5 | 168 s · 9/9 · 4 | 86 s · 9/9 · 4 |

- **pi is fastest on both engines.** It has the smallest system prompt and sends the least over a session (53K prompt
  tokens; OpenCode: 223–323K).
- **Splash is faster than oMLX in every harness** (1.2–4×).
- **OpenCode was fastest on Strata (66 s, below) but not here.** It sends the largest prompts; with fast decode and
  working prompt reuse, pi's smaller prompts win.

## On Strata (2026-11-23)

Inkling-2-Mini SQ-15, 128K context. Driver: `bench/agents/harness_bench.py`. Raw metrics:
[results/agents/harness](../../results/agents/harness/).

| Harness | Version | API it uses | How the driver runs it |
|---|---|---|---|
| Claude Code | 2.1.330 | Anthropic `/v1/messages` | `claude -p --output-format stream-json`, `--session-id` then `--resume` |
| pi | 1.6.0 | OpenAI chat completions | `pi --mode json`, then `--continue` |
| OpenCode | 1.19.6 | OpenAI chat completions | `opencode run --format json --auto --dir WS`, then `--session ID` |
| Cline | 3.0.75 | OpenAI chat completions | ACP (`cline --acp`), one session (`bench/agents/cline_bench.py`) |

Each turn is one headless call that continues the session, with tools auto-approved and an isolated HOME and config.

### With prompt reuse working (Strata 0.2.19 server + #6627 checkpoint engine)

| Harness | Total time per run | Turns 1–2 (9 checks) | Issues found (of 8) | Tool calls | Review length | Prompt from cache |
|---|---|---|---|---|---|---|
| **OpenCode** | **65.9 / 66.2 s** | 8/9, 8/9 | 4, 5 | 10, 10 | ~1.8K chars | 90% |
| pi | 108.5 / 88.1 s | 9/9, 9/9 | 4, 5 | 14, 13 | ~4.5K chars | 87–88% |
| Cline | 105.3 / 112.6 / 119.0 s | 9/9, 9/9, 8/9 | 4, 6, 4 | 11, 12, 11 | ~5K chars | 85–88% |
| Claude Code | 142.2 / 325.6 s | 9/9, 9/9 | 5, **6** | 15, 53 | 4.3K / 11.3K chars | 91–97% |

### On stock Strata 0.2.20 (no reuse when tools are sent)

| Harness | Total time | Slowdown | Cached tokens |
|---|---|---|---|
| OpenCode | 374.3 s | 5.7× | 0 (18 of 20 requests re-read everything) |
| Claude Code | 406.4 s | 2.9× | 0 (14 of 14) |
| Cline | 330.3 / 341.0 s | 3.0× | 0 |
| pi | 268.2 s | 2.5× | 0 (18 of 18) |

Quality was the same on both servers; only time changed.

### Findings on Strata

- **The 0.2.20 cache bug affects every harness**, including Claude Code over `/v1/messages`. All of them send tools,
  and the server's forced empty thinking block breaks the cached prefix. It is a server bug
  ([details](strata-prompt-cache.md#4-strata-0220)).
- **OpenCode was fastest because it does the least:** fewest tool calls, shortest review (~⅓ the length of the
  others), the most consistent time (66 s twice), and as many issues as pi. It missed the permission-only changes in
  turn 1 both times.
- **pi balanced speed and coverage:** smallest system prompt (~1.7K tokens; OpenCode ~8K, Claude Code ~13.5K), 9/9 in
  both runs, 88–108 s.
- **Claude Code was the most thorough and the least predictable.** Prompt caching pays for its large system prompt
  once. In run 2 it read 43 files for the review (265 s for that turn) and found 6 of 8 issues. Against a local
  server it logs an unrecognized model and assumes a 1M context window.
- **Cline fell between pi and Claude Code** on time and coverage.
- Every harness committed without asking under auto-approve.

## Gotcha: OpenCode trusts `$PWD`

OpenCode takes its project folder from the `PWD` environment variable, not the process working directory. Started
by a script inside another repo, it edited and committed in that repo instead of the sandbox. The driver passes
`--dir`, sets `PWD` for every harness and runs from a neutral folder. Do the same when scripting any agent CLI.

Configs for each harness: [guides/agents.md](../guides/agents.md).
