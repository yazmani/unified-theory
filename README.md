# unified-theory

**Benchmarks for coding with local LLMs on Apple Silicon: models, runtimes and agent harnesses.**

Decode speed is the least useful number for real coding work. Hidden thinking, prompt caching and the agent harness
each changed session times by 2–6× in these runs. This repo measures time to a finished task on one M5 Pro (48 GB)
and publishes the setups that won.

The name refers to unified memory: on a Mac the CPU and GPU share one memory pool, which decides what fits and how
fast it runs.

## Findings

| Question | Answer (2026-11-25) | Details |
|---|---|---|
| Best model for real agent work? | **Qwen3.8-Flash-Next on Splash** at 256K context. Q2_0 (66 GB): 8 of 8 issues in both Cline runs, 104 tok/s at a 250K prompt. Coder (58 GB): 7 of 8, 18/18 on security. Sessions take 170–350 s | [models](docs/findings/models.md) |
| Fastest good agent for short tasks? | **KAT-Ornith-HERO-35B-A3B on Splash**: 235 tok/s, Cline session 52–79 s, 6 of 8 issues in both runs. Nine other 35B-A3B models scored lower | [models](docs/findings/models.md) |
| Best dense model? | **Qwen3.8-27B GSQ-RCO IQ3_S** (11.8 GB) on Splash: 96 tok/s, Cline 154 s, 75 tok/s at 100K. Slow past ~64K: 13 min to read 250K | [models](docs/findings/models.md) |
| Fastest runtime? | **Splash**: ~2× llama.cpp and Strata on the same model, when a matching drafter exists. oMLX and DSpine were slower | [runtimes](docs/findings/runtimes.md) |
| Does the harness matter? | Yes, 2–5× on the same model. Fastest on Splash: **pi** (49 s). Fastest on Strata: OpenCode (66 s) | [harnesses](docs/findings/harnesses.md) |
| What matters most for agents? | **Prompt reuse across turns.** Without it, every harness ran 2.5–5.7× slower | [strata-prompt-cache](docs/findings/strata-prompt-cache.md) |
| Long context on 48 GB? | 256K fits, and every model recalled 8 of 8 facts at 99–250K. Speed at depth depends on the attention design: Flash-Next (sparse attention) keeps 81% of its decode speed at 250K, KAT-Ornith 62%; dense 27B models take 13–15 min to read 250K | [long-context](docs/findings/long-context.md) |
| Best model for security review? | Any good coder: 16–18 of 18 planted flaws, no refusals. Uncensored builds scored no higher | [security-review](docs/findings/security-review.md) |

"Issues" are the real problems a model found in the review turn of the agent task, out of 8 verified by hand
([methodology](docs/methodology.md#agent-benchmarks)).

<details>
<summary>Speed leaderboard (decode tok/s, M5 Pro 48 GB)</summary>

| Model | Runtime | Decode tok/s | Long answer | Mini-eval |
|---|---|---:|---|---|
| Qwopus3.6-35B-A3B-Coder Q4_K_M | Splash 1.7.2 | **244** | 25 s | 9/10 |
| HauhauCS Qwen3.6-35B-A3B Aggressive Q4_K_M | Splash 1.7.2 | 242 | 6 s | 9/10 |
| KAT-Ornith-HERO-35B-A3B Fusion i1-Q4_K_M | Splash 1.7.2 | 235 | 9 s | 9/10 |
| Ornith-1.5-35B-A3B Q4_K_M | Splash 1.7.2 | 219 | 8 s | 7/10 |
| Tiel-Coder-35B-A3B UD-Q4_K_XL | Splash 1.7.2 | 191 | 8 s | 9/10 |
| Flint UD-Q4_K_XL (thinks even with effort none) | Splash 1.7.2 | 139 | 42 s | 10/10 |
| Qwen3.8-Flash-Next GSQ-RCO Q2_0 (66 GB, 20 GB expert store) | Splash 1.7.2 | 129 | 10 s | 8/10 |
| Qwen3.8-Flash-Next GSQ-RCO Coder (58 GB, all in memory) | Splash 1.7.2 | 124 | 9 s | 9/10 |
| Inkling-2-Mini UD-IQ4_XS | Splash 1.7.2 | 101 | 24 s | 10/10 |
| Ternary Bonsai 2.5 27B PQ2_0 (7.5 GB) | Splash 1.7.2 | 145 | 10 s | 9/10 |
| Qwen3.8-27B GSQ-RCO IQ3_S (11.8 GB) | Splash 1.7.2 | 96 | 14 s | 9/10 |
| Qwen3.8-27B-pi-adapted Q4_K_M | Splash 1.7.2 | 90 | 22 s | 10/10 |
| Ornith-1.5-122B UD-IQ3_XXS (24 GB expert store) | Splash 1.7.2 | 44 | 41 s | 7/10 |
| Tiel-Coder-35B-A3B UD-IQ4_XS + MTP | Unsloth llama.cpp | 98 | 26 s | 10/10 |
| Kolibri 1.1 Q3_K_M (36 GB) | llama.cpp PR #32891 | 69 | 11 s | 10/10 |
| Kolibri 1.1 GSQ-RCO IQ2_XS (21 GB) | llama.cpp PR #32891 | 68 | 10 s | 10/10 |
| Ternary Bonsai 2.5 27B Q2_0 + MTP | llama.cpp | 31 | 44 s | 9/10 |
| Tiel-Coder-35B-A3B UD-IQ4_XS, no speculative decoding | Unsloth llama.cpp | 70 | 42 s | — |
| Inkling-2-Mini SQ-15 (thinking off) | Strata 0.2.20 | 66 | — | 9/10 |
| Inkling-2-Mini SQ-15 + DSpark | Strata 0.2.19 | 58 | 54 s | 10/10 |
| Inkling-2-Mini oQ4e-mtp (wall-clock) | oMLX 0.8.3 | 55 | 54 s | 10/10 |
| Inkling-2-Mini SQ-20 + DSpark | Strata 0.2.19 | 48 | 72 s | 10/10 |
| Inkling-2-Mini UD-IQ4_XS + DSpark | Unsloth llama.cpp | 36 | 57 s | 10/10 |
| Inkling-2-Mini UD-IQ4_XS | Unsloth llama.cpp | 30 | 148 s | — |

Long answer: wall time to a complete answer for one fixed coding prompt (8,000-token cap). Regenerate from raw data with `make summary`.
</details>

## Run the winning setups

| Goal | Script |
|---|---|
| Fast agent, short tasks | [`configs/splash/kat-ornith-agent.sh`](configs/splash/kat-ornith-agent.sh) · [guide](docs/guides/splash.md) |
| Long agent sessions and reviews (256K) | [`configs/splash/flashnext-review.sh`](configs/splash/flashnext-review.sh) · [guide](docs/guides/splash.md) |
| Inkling-2-Mini | [`configs/splash/inkling.sh`](configs/splash/inkling.sh) |
| A model Splash has no drafter for | [`configs/llama.cpp/`](configs/llama.cpp/) · [guide](docs/guides/llama-cpp.md) |
| Connect Cline, Claude Code, pi or OpenCode | [`configs/agents/`](configs/agents/) · [guide](docs/guides/agents.md) |

## Benchmark your own Mac

Requires Python 3.11+ and an OpenAI-compatible server (Splash, llama-server, Strata, LM Studio). The core scripts
have no dependencies.

```sh
make bench-speed URL=http://127.0.0.1:8000 MODEL=local LABEL=my-model   # decode, long answer, mini-eval, wall-clock decode
make summary                                                           # tables from results/
```

Agent, long-context and security benchmarks: [bench/README.md](bench/README.md). Measurement details and limits:
[docs/methodology.md](docs/methodology.md).

## Repository layout

```
bench/        benchmark scripts; each writes one JSON per run to results/
configs/      launch scripts (splash/, llama.cpp/, strata/) and agent configs (agents/)
docs/
  findings/   one page per question, current answer first
  guides/     setup for Splash, llama.cpp, Strata and the agents
  archive/    findings pages as written on the day (superseded)
  methodology.md, journal.md
results/      raw JSON by benchmark (see results/README.md)
tools/        summarize.py (tables from results/), check_private.py (leak check)
.local/       private files, gitignored: grader, sandbox project, transcripts
```

## Contributing

Results from other Macs, and new models, runtimes and harnesses: [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE). Model names and upstream projects belong to their authors.
