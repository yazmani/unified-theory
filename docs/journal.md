# Journal

What was done, in order, with links to the write-ups. New work gets a line here; its results go into the matching
page under [findings/](findings/).

## 2026-11-22

- Benched Inkling-2-Mini on Strata 0.2.19 (SQ-10/15/20) against Unsloth's llama.cpp fork, plus Tiel-Coder-35B-A3B
  with MTP. → [decode-speed](archive/2026-11-22-decode-speed.md)
- One model at a time from now on: an auto-serving `strata install` next to `llama-bench` pushed swap to 28 GB. → [methodology](methodology.md), [guides/strata](guides/strata.md)
- Long context at 30K / 120K / 240K: recall 8/8, but Strata re-read the whole prompt every turn.
  → [long-context](findings/long-context.md)
- Built TensorSharp from source: no Inkling on Mac, no gain for Tiel. → [tensorsharp](archive/2026-11-22-tensorsharp.md)
- Wrote a server-side fix for Strata's Inkling re-reads, then measured the engine checkpoint posted on #6627, which
  won (8-turn session 333 s → 163 s). Added PR #6665's reporting. Found the tag-leak bug (#6675).
  → [strata-prompt-cache](findings/strata-prompt-cache.md)

## 2026-11-23

- Cline agent benchmark on a real 3-turn session: Inkling vs Tiel-Coder variants, MTP and reasoning-budget settings.
  → [agent-models](archive/2026-11-23-agent-models.md)
- Strata 0.2.20: faster plain chat (thinking forced off), but agents ~3× slower (no reuse with tools).
  → [strata-prompt-cache §4](findings/strata-prompt-cache.md#4-strata-0220)
- Harness comparison: Cline, Claude Code, pi, OpenCode on the same model and task.
  → [agent-harnesses](findings/harnesses.md)
- Repo restructured into findings / guides / configs, with a privacy check.
- Mixed setup (0.2.20 engine under the 0.2.19 server): 344 s, no better. Cause: 0.2.20 has prompt checkpoints for
  CUDA/CPU only, none on Metal. → [strata-prompt-cache §4](findings/strata-prompt-cache.md#4-strata-0220)
- Reported both 0.2.20 gaps upstream with a repro: [Niko1221/Strata#6904](https://github.com/Niko1221/Strata/issues/6904).
- Opened [PR #6914](https://github.com/Niko1221/Strata/pull/6914): Metal prompt-end checkpoint. With #6827, Cline
  session 408.5 s → 145.7–154.8 s on `main`.

## 2026-11-24

- AtomicChat AD-Q4_K quant + Atomic Engine (SSD expert streaming fork) on Inkling: AD-Q4_K on llama.cpp PR #32218
  is the best llama.cpp option (42 tok/s, Cline 218–278 s), still behind Strata. Atomic Engine: 45 tok/s on real
  prompts (README's 77 is a repetitive 64-token fixture); its profiles are 4K context with no prompt reuse.
  → [decode-speed](archive/2026-11-22-decode-speed.md#atomicchat-ad-quants-and-atomic-engine-2026-11-24),
  [agent-models](archive/2026-11-23-agent-models.md)

- Splash 1.7.2 (Metal engine with DFlash 2 drafters): Tiel-Coder 191 tok/s and Cline 94–101 s, Inkling 101 tok/s
  and Cline 75–94 s, both faster than every earlier setup. Qwen3.8-27B fine-tunes: pi-adapted (90 tok/s on Splash)
  beats DavidAU's TURBO-Fable (21–24 tok/s, weaker in both harnesses). Basalt is NVIDIA-only.
  → [splash](archive/2026-11-24-splash.md)
- Agent sandboxes moved outside the repo after a model `cd`-ed from its sandbox up into this repo and committed there
  (undone, not pushed).
- Qwen3.8-Flash-Next Q2_0 (66 GB) on Splash with SSD expert streaming: 96–129 tok/s, and the first model to find
  all 8 issues in Cline (twice, no false claims), at 280–348 s per session. Defaults tried to load every expert and
  pushed swap to 7 GB; set `--expert-memory`. → [splash](archive/2026-11-24-splash.md)
- Flint (40B MoE, ~2.5B active) on Splash: 139 tok/s and a 63 s Cline session (fastest yet), but only 1–4 of 8
  issues found. Ornith-1.5-122B IQ3_XXS with expert streaming: 44 tok/s, 249 s Cline, 4/8 issues, 7/10 mini-eval;
  not worth it on 48 GB. → [splash](archive/2026-11-24-splash.md)
- Ornith-35B family (Tiel's base) on Splash: **KAT-Ornith-HERO fusion 235 tok/s, Cline 52–79 s with 6/8 issues**
  (both runs), the new everyday pick over Tiel. Stock Ornith-1.5-35B: 219 tok/s, weaker. The Ornith DFlash2 drafter
  from jzinno doesn't load in Splash. → [splash](archive/2026-11-24-splash.md)
- Model sweep: KAT-Coder-V2.5, AgentWorld, Qwopus3.6-Coder, Qwen3.8-35B-Distill, HauhauCS, RavenX, Cyber-Tiel on Splash;
  none beat KAT-Ornith in agents. New security review check (all 16–18/18) and per-session engine stats; 100K runs:
  every Qwen3.6-35B 8/8 at ~160–223 tok/s decode. oMLX (Inkling 261 tok/s, slow in agents) and DSpine on Qwen3.8-27B
  (90 tok/s, 7–8 issues, 18 tok/s at 100K). → [model-sweep](archive/2026-11-24-model-sweep.md)
- Correction: oMLX Inkling is 55 tok/s wall-clock, not 261 (bursty streaming fooled the streamed benchmark; new
  `bench/raw_decode.py`). Harness comparison on Inkling: pi fastest on Splash (49 s) and oMLX (86 s); Splash faster
  in every harness. Deleted the models that lost (KAT-Coder, AgentWorld, Qwopus, Distill, RavenX, oMLX Tiel).
- oMLX removed (no gain on this Mac). Splash 1.7.2 follow-ups: Inkling UD-Q4_K_M = UD-IQ4_XS in speed (109 tok/s);
  `--persistent-cache` restores the system prompt after a restart (TTFT 0.9 → 0.1 s) when the working directory is
  the same. → [splash](archive/2026-11-24-splash.md)

## 2026-11-25

- Docs restructured by question: [models](findings/models.md), [runtimes](findings/runtimes.md),
  [harnesses](findings/harnesses.md), [long-context](findings/long-context.md),
  [security-review](findings/security-review.md), each with the current answer first. The dated pages moved to
  [archive/](archive/). New [guides/splash](guides/splash.md) and `configs/splash/` launch scripts; agent configs
  now default to Splash on :8000. Results: wall-clock decode moved to `results/raw-decode/`, Splash engine stats to
  `results/engine-stats/` (they shared folders with other scripts' output).
- ISTA-DASLab GSQ-RCO models on Splash. Flash-Next Coder (half the experts pruned, 58 GB, all in memory): 130 tok/s
  wall-clock like Q2_0, Cline 327 s · 7 issues, pi 171 s · 7, security 18/18, 100K at 1,210 / 119 tok/s; a tie with
  Q2_0 (17/18, 1,196 / 127 at 100K). Qwen3.8-27B IQ3_S (11.8 GB): 96 tok/s, Cline 154 s · 9/9 · 5, pi 54 s, 75 tok/s
  at 100K: the best 27B setup here. → [models](findings/models.md)
- Ternary Bonsai 2.5 27B and Kolibri 1.1 (both released 2026-11-24). Bonsai on Splash (`PQ2_0`, 7.5 GB): 160 tok/s
  wall-clock, Cline 268 s · 5 issues, 100K at 400 / 99 tok/s; on llama.cpp with its MTP head: 31 tok/s, 650 s.
  Splash rejects the `Q2_0` file. Kolibri on llama.cpp PR #32891: 69 tok/s, 10/10 mini-eval, but 1–4 of 8 issues in
  agents. Neither beats KAT-Ornith or the 27B GSQ. → [models](findings/models.md)
- LiveCodeBench v6 (February 2025, EvalScope) on KAT-Ornith, stopped at 44 of 51: 22 passed, 22 of 26 when the answer
  finished; all 18 answers cut at the 32K limit failed. → [models](findings/models.md)
- 250K context on Splash (`--max-context 256K`): all four models 8/8 with swap flat. Flash-Next 104 tok/s and 3.7 min
  to read the prompt; KAT-Ornith 145 tok/s, 4.4 min; the 27B models 13–15 min. GGUF metadata explains it:
  Flash-Next's full-attention layers attend to 2,048 indexer-picked tokens. Flash-Next becomes the pick for long agent
  sessions; the KAT-Ornith and Flash-Next scripts and agent configs now default to 256K.
  → [long-context](findings/long-context.md)

## Open threads

- [ ] Harder quality set (multi-file edits, SWE-style tasks) to rank models on quality, not only speed.
- [ ] A long agent session (150K+ tokens of context) on Flash-Next: the 3-turn task stays under 77K.
- [ ] LiveCodeBench with a 64–96K answer limit for Flash-Next, KAT-Ornith, the 27B GSQ and Bonsai.
- [ ] Harder security set: every model scores 16–18/18 on the current one.
- [ ] LM Studio (MLX engine) and mlx-lm on the same models (oMLX done: [runtimes](findings/runtimes.md)).
- [ ] Session stats parser for oMLX and DSpine server logs (Splash only so far).
- [ ] DSpine on the Qwen3.8-27B coding fine-tunes (pi-adapted) and with `--copy` for edits.
- [ ] More models: Qwen3-Coder-30B-A3B.
- [x] Qwen3.8-Flash-Next on Splash with SSD expert streaming ([models](findings/models.md)).
- [ ] Flash-Next: thinking off, to trade some quality for session time; a second Cline run of the Coder to settle Coder vs Q2_0.
- [ ] Splash: Inkling tool call returned as text once; report upstream with a repro.
- [ ] The harness comparison on Tiel-Coder (llama.cpp).
- [ ] Re-run the decode table with no VM running, to measure what it cost.
- [ ] Tiel-Coder MTP `--spec-draft-n-max` sweep beyond 1 and 3.
- [ ] Memory-bandwidth roofline: GB read per token vs measured tok/s, to see the headroom left.
