# unified-theory

**Benchmarks for coding with local LLMs on Apple Silicon: models, runtimes and agent harnesses, measured end to end.**

Most local-LLM numbers stop at "tokens per second". On a Mac doing real coding work, that number turned out to be
the least important one: hidden thinking, prompt caching and the agent harness each changed session times by
2–6×. This repo measures what you actually wait for, on one 48 GB M5 Pro, and documents the setups that won.

> Named after unified memory: on a Mac the GPU and CPU share one pool, which decides what fits and how fast it runs.

## Findings at a glance

| Question | Answer (2026-11-24) | Details |
|---|---|---|
| Fastest good coding model? | **Tiel-Coder-35B-A3B on Splash: ~191 tok/s** (Q4_K_XL); 98 on llama.cpp + MTP | [splash](docs/findings/splash.md), [decode-speed](docs/findings/decode-speed.md) |
| Fastest runtime on a Mac? | **Splash**: ~2× llama.cpp and Strata for Tiel, Inkling and Qwen3.8-27B, if the model matches its drafter | [splash](docs/findings/splash.md) |
| Best model inside an agent? | **Tiel-Coder or Inkling-2-Mini on Splash**: 75–101 s per Cline session, 9/9 checks (best runs). Most thorough: **Qwen3.8-Flash-Next** on Splash (66 GB, experts streamed from the SSD): all 8 issues found, but 280–348 s. Of the Qwen3.8-27B fine-tunes, **pi-adapted** beats DavidAU's TURBO-Fable | [splash](docs/findings/splash.md), [agent-models](docs/findings/agent-models.md) |
| Does the agent harness matter? | Yes, ~2× with the same model: **OpenCode** fastest (66 s), **pi** best balance, **Claude Code** most thorough | [agent-harnesses](docs/findings/agent-harnesses.md) |
| What matters most for agents? | **Prompt reuse across turns.** Without it every harness got 2.5–5.7× slower | [strata-prompt-cache](docs/findings/strata-prompt-cache.md) |
| Strata 0.2.20: upgrade? | For chat yes (66 tok/s, instant first token). For agents no, not yet (~3× slower) | [strata-prompt-cache §4](docs/findings/strata-prompt-cache.md#4-strata-0220) |
| Long context on 48 GB? | Inkling-2-Mini: 8/8 recall at 30K, 120K and 240K | [long-context](docs/findings/long-context.md) |

<details>
<summary>Speed leaderboard (decode tok/s, M5 Pro 48 GB)</summary>

| Model / runtime | Decode tok/s | Long answer | Mini-eval |
|---|---|---|---|
| Tiel-Coder-35B-A3B UD-Q4_K_XL, **Splash** 1.7.2 | **191** | 8 s | 9/10 |
| Qwen3.8-Flash-Next GSQ-RCO Q2_0 (66 GB, 20 GB expert store), **Splash** 1.7.2 | 129 | 10 s | 8/10 |
| Inkling-2-Mini UD-IQ4_XS, **Splash** 1.7.2 | 101 | 24 s | 10/10 |
| Qwen3.8-27B-pi-adapted Q4_K_M, **Splash** 1.7.2 | 90 | 22 s | 10/10 |
| Tiel-Coder-35B-A3B UD-IQ4_XS + MTP, Unsloth llama.cpp | 98 | 26 s | 10/10 |
| Tiel-Coder-35B-A3B UD-IQ4_XS, no speculative decoding | 70 | 42 s | — |
| Inkling-2-Mini SQ-15, Strata 0.2.20 (thinking off) | 66 | — | 9/10 |
| Inkling-2-Mini SQ-15, Strata 0.2.19 + DSpark | 58 | 54 s | 10/10 |
| Inkling-2-Mini SQ-20, Strata 0.2.19 + DSpark | 48 | 72 s | 10/10 |
| Inkling-2-Mini UD-IQ4_XS + DSpark, Unsloth llama.cpp | 36 | 57 s | 10/10 |
| Inkling-2-Mini UD-IQ4_XS, Unsloth llama.cpp | 30 | 148 s | — |

Regenerate from raw data: `make summary`.
</details>

## Use the winning setups

| I want to... | Do this |
|---|---|
| Run the fastest coding model | [`configs/llama.cpp/tiel-coder-fast.sh`](configs/llama.cpp/tiel-coder-fast.sh) · [guide](docs/guides/llama-cpp.md) |
| Run the fastest setup (Splash) | [splash setup](docs/findings/splash.md#setup) |
| Run a local model for agents (llama.cpp / Strata) | [`configs/strata/inkling-agent.sh`](configs/strata/inkling-agent.sh) or [`configs/llama.cpp/tiel-coder-agent.sh`](configs/llama.cpp/tiel-coder-agent.sh) · [guide](docs/guides/strata.md) |
| Connect Cline / Claude Code / pi / OpenCode | [`configs/agents/`](configs/agents/) · [guide](docs/guides/agents.md) |

## Benchmark your own Mac

Needs Python 3.11+ and an OpenAI-compatible server (llama-server, Strata, LM Studio, ...). No dependencies for the
core scripts.

```sh
make bench-speed URL=http://127.0.0.1:8092 LABEL=my-model   # decode, long answer, mini-eval
make summary                                               # tables from results/
```

Agent benchmarks on your own project (privately graded), long context and multi-turn reuse:
[bench/README.md](bench/README.md). How numbers are measured and what they don't say:
[docs/methodology.md](docs/methodology.md).

## Repository map

```
bench/        benchmark scripts (one JSON per run into results/)
configs/      launch scripts and agent configs for the winning setups
docs/
  findings/   one page per question, with tables and conclusions
  guides/     how to run Strata, llama.cpp and the agents
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
