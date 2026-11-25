# unified-theory

**Benchmarks for coding with local LLMs on Apple Silicon: models, runtimes and agent harnesses, measured end to end.**

Most local-LLM numbers stop at "tokens per second". On a Mac doing real coding work, that number turned out to be
the least important one: hidden thinking, prompt caching and the agent harness each changed session times by
2–6×. This repo measures what you actually wait for, on one 48 GB M5 Pro, and documents the setups that won.

> Named after unified memory: on a Mac the GPU and CPU share one pool, which decides what fits and how fast it runs.

## Findings at a glance

| Question | Answer (2026-11-25) | Details |
|---|---|---|
| Best model for a coding agent? | **KAT-Ornith-HERO-35B-A3B on Splash**: 235 tok/s, 52–79 s per Cline session, 6 of 8 issues found in both runs. Nine other 35B-A3B coders, uncensored and security builds: none beat it | [models](docs/findings/models.md) |
| Most thorough? | **Qwen3.8-Flash-Next** on Splash: Q2_0 (66 GB, experts streamed from the SSD) found all 8 issues in both Cline runs; the expert-pruned Coder (58 GB) found 7 and scored 18/18 on security. 170–350 s per session | [models](docs/findings/models.md) |
| Best dense model? | **Qwen3.8-27B GSQ-RCO IQ3_S** (11.8 GB) on Splash: 96 tok/s, 154 s Cline, 75 tok/s at 100K | [models](docs/findings/models.md) |
| Fastest runtime on a Mac? | **Splash**: ~2× llama.cpp and Strata on the same model, if the model matches its drafter. oMLX and DSpine are slower here | [runtimes](docs/findings/runtimes.md) |
| Does the agent harness matter? | Yes, 2–5× with the same model. On Splash **pi** is fastest (49 s); OpenCode sends the largest prompts. On Strata OpenCode was fastest | [harnesses](docs/findings/harnesses.md) |
| What matters most for agents? | **Prompt reuse across turns.** Without it every harness got 2.5–5.7× slower | [strata-prompt-cache](docs/findings/strata-prompt-cache.md) |
| Long context on 48 GB? | 8/8 recall at 99–240K for every model tested. Qwen3.6-35B on Splash: ~56 s to read 100K, 160–223 tok/s decode at that depth | [long-context](docs/findings/long-context.md) |
| Best model for security review? | Any good coder: 16–18 of 18 planted flaws, no refusals. Uncensored builds aren't better | [security-review](docs/findings/security-review.md) |

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
| Qwen3.8-27B GSQ-RCO IQ3_S (11.8 GB) | Splash 1.7.2 | 96 | 14 s | 9/10 |
| Qwen3.8-27B-pi-adapted Q4_K_M | Splash 1.7.2 | 90 | 22 s | 10/10 |
| Ornith-1.5-122B UD-IQ3_XXS (24 GB expert store) | Splash 1.7.2 | 44 | 41 s | 7/10 |
| Tiel-Coder-35B-A3B UD-IQ4_XS + MTP | Unsloth llama.cpp | 98 | 26 s | 10/10 |
| Tiel-Coder-35B-A3B UD-IQ4_XS, no speculative decoding | Unsloth llama.cpp | 70 | 42 s | — |
| Inkling-2-Mini SQ-15 (thinking off) | Strata 0.2.20 | 66 | — | 9/10 |
| Inkling-2-Mini SQ-15 + DSpark | Strata 0.2.19 | 58 | 54 s | 10/10 |
| Inkling-2-Mini oQ4e-mtp (wall-clock; streamed numbers are bursty) | oMLX 0.8.3 | 55 | 54 s | 10/10 |
| Inkling-2-Mini SQ-20 + DSpark | Strata 0.2.19 | 48 | 72 s | 10/10 |
| Inkling-2-Mini UD-IQ4_XS + DSpark | Unsloth llama.cpp | 36 | 57 s | 10/10 |
| Inkling-2-Mini UD-IQ4_XS | Unsloth llama.cpp | 30 | 148 s | — |

Regenerate from raw data: `make summary`.
</details>

## Use the winning setups

| I want to... | Do this |
|---|---|
| Run the everyday coding-agent model | [`configs/splash/kat-ornith-agent.sh`](configs/splash/kat-ornith-agent.sh) · [guide](docs/guides/splash.md) |
| Run the most thorough reviewer on 48 GB | [`configs/splash/flashnext-review.sh`](configs/splash/flashnext-review.sh) · [guide](docs/guides/splash.md) |
| Run Inkling-2-Mini | [`configs/splash/inkling.sh`](configs/splash/inkling.sh) |
| Run a model Splash has no drafter for | [`configs/llama.cpp/`](configs/llama.cpp/) · [guide](docs/guides/llama-cpp.md) |
| Connect Cline / Claude Code / pi / OpenCode | [`configs/agents/`](configs/agents/) · [guide](docs/guides/agents.md) |

## Benchmark your own Mac

Needs Python 3.11+ and an OpenAI-compatible server (Splash, llama-server, Strata, LM Studio, ...). No dependencies for the
core scripts.

```sh
make bench-speed URL=http://127.0.0.1:8000 MODEL=local LABEL=my-model   # decode, long answer, mini-eval, wall-clock decode
make summary                                               # tables from results/
```

Agent benchmarks on your own project (privately graded), long context and multi-turn reuse:
[bench/README.md](bench/README.md). How numbers are measured and what they don't say:
[docs/methodology.md](docs/methodology.md).

## Repository map

```
bench/        benchmark scripts (one JSON per run into results/)
configs/      launch scripts (splash/, llama.cpp/, strata/) and agent configs (agents/)
docs/
  findings/   one page per question, current answer first
  guides/     how to run Splash, llama.cpp, Strata and the agents
  archive/    findings pages as written on the day (superseded)
  methodology.md, journal.md (chronological log + open threads)
results/      raw JSON, by benchmark (see results/README.md)
tools/        summarize.py (tables from results), check_private.py (leak guard)
.local/       your private files (gitignored): grader, sandbox project, transcripts
```

## Contributing

Results from other Macs are very welcome, and so are new models, runtimes and harnesses:
[CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE). Model names and upstream projects belong to their authors; this repo only measures them.
