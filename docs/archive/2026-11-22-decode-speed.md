# Decode speed: which model and runtime is fastest on an M5 Pro

> **Archived snapshot.** Kept as measured on that date; the current answer is in [runtimes](../findings/runtimes.md).

**Question:** what is the fastest *good* coding model on a 48 GB Apple Silicon Mac, and which runtime should run it?
**Measured:** 2026-11-22, conditions in [methodology](../methodology.md). Raw data: [results/decode](../../results/decode/),
[results/long-answer](../../results/long-answer/), [results/eval](../../results/eval/), [results/llama-bench](../../results/llama-bench/).

## Results

| Rank | Model / runtime | Decode tok/s (engine) | Long answer* | Mini-eval |
|---|---|---|---|---|
| 1 | **Tiel-Coder-35B-A3B UD-IQ4_XS + MTP**, Unsloth llama.cpp b12588 | **98** (90–103) | **26 s** | 10/10 thinking (70 s), 9/10 no-think (24 s) |
| 2 | Tiel-Coder-35B-A3B UD-IQ4_XS, no speculative decoding | 70 | 42 s | not run |
| 3 | Inkling-2-Mini **Strata SQ-15** + DSpark | 58 (54–63) | 54 s | 10/10 (145 s) |
| 4 | Inkling-2-Mini Strata SQ-10 + DSpark | 55–60 | 52 s | 10/10 (124 s) |
| 5 | Inkling-2-Mini Strata SQ-20 (lossless) + DSpark | 48 (41–51) | 72 s | 10/10 (144 s) |
| 6 | Inkling-2-Mini UD-IQ4_XS + DSpark n=3, Unsloth llama.cpp | 36 | 57 s | 10/10 (203 s) |
| 7 | Inkling-2-Mini UD-IQ4_XS, Unsloth llama.cpp, no speculative decoding (≈ Unsloth Studio defaults) | 30 | 148 s | not run |
| — | Inkling-2-Mini **AtomicChat AD-Q4_K** + DSpark n=3, Atomic Engine (20 GiB budget, 4K context) | 45 (42–48) | 73 s | 10/10 (220 s) |
| — | Inkling-2-Mini **AtomicChat AD-Q4_K** + DSpark n=3, llama.cpp PR #32218 | 42 (39–46) | 63 s | 10/10 (180 s) |

\* Wall time to a finished answer for the `gen-python` prompt (LRU cache with TTL, thread safety, decorator),
max 8000 tokens, finish reason `stop`. Every engine's code compiled and imported. Thinking length varies run to
run, so this is noisier than decode tok/s.

**Kernel baseline** (`llama-bench -p 512 -n 128 -r 3 -fa 1`, Unsloth llama.cpp b12588):

| Model | pp512 | tg128 |
|---|---|---|
| Inkling-2-Mini UD-IQ4_XS | 508 | 31.6 ± 0.3 |
| Tiel-Coder-35B-A3B UD-IQ4_XS | 1772 | 71.6 ± 0.2 |

Strata 0.2.20 (2026-11-23) moved Inkling SQ-15 to **65.9 tok/s** with thinking forced off; see
[strata-prompt-cache.md](../findings/strata-prompt-cache.md#4-strata-0220).

## AtomicChat AD quants and Atomic Engine (2026-11-24)

[AtomicChat/Inkling-2-Mini-GGUF](https://huggingface.co/AtomicChat/Inkling-2-Mini-GGUF) publishes per-tensor
"AD" quants with KL-divergence against BF16: **AD-Q4_K is 16.5 GB with 96.3% top-1 agreement** (stock Q4_K_M:
94.7%). [Atomic Engine](https://github.com/AtomicBot-ai/atomic-engine) is their llama.cpp fork that streams
experts from SSD under a memory budget. Both rows above use AD-Q4_K and AtomicChat's own DSpark drafter
(revision `3095098`), same prompts and settings as the other rows (`reasoning_effort: none`, 2048 max tokens).

- llama.cpp: [PR #32218](https://github.com/ggml-org/llama.cpp/pull/32218) head `9f57b44` (DSpark for Inkling, not
  merged yet), `-c 32768 -ctk q8_0 -ctv q8_0`, 16.9 GiB RSS, draft acceptance 0.62–0.75.
- Atomic Engine: branch `codex/expert-weight-source` at `e110381`, the README's Q4_K profile (20 GiB budget,
  `-c 4096`, Q4_0 KV, `--ctx-checkpoints 0 --cache-ram 0`), 15.7 GiB RSS, acceptance 0.66–0.83.

Findings:

1. **AD-Q4_K on llama.cpp is ~15% faster than Unsloth UD-IQ4_XS** (42 vs 36 tok/s, both DSpark n=3) and passed
   every task. It is the best llama.cpp option for Inkling measured here.
2. **Strata is still faster**: SQ-15 at 58 (0.2.19) / 66 (0.2.20) tok/s against 42–45.
3. **Atomic Engine's 77 tok/s at 20 GiB (M4 Max, README) didn't reproduce on real prompts**: 45 tok/s here.
   Its benchmark is a 64-token answer on a repetitive fixture. Its value is the memory cap, not speed on a Mac
   that already fits the model.
4. **Atomic's published profiles can't run an agent**: 4K context, one slot, prompt reuse off. Not benched in Cline.

## Findings

1. **Strata runs Inkling 1.6–1.9× faster than llama.cpp on this Mac**: SQ-15 at 58 tok/s, against 30 for Unsloth
   IQ4_XS on llama.cpp and 36 with llama.cpp's own DSpark drafter.
2. **Inkling is slow for its size on any engine.** It is a looped MoE: the middle layers run several times per token
   (48 virtual layer visits). A 35B-A3B Qwen-family model is 2.3× faster on the same llama.cpp (72 vs 31.6 tg128).
3. **Strata's DSpark drafter gives nothing on Mac** (SQ-20: 48 tok/s on, 47 off). llama.cpp's DSpark gives +20% at
   n-max 3 (acceptance 0.56–0.67) and less at n-max 7 (0.35–0.44).
4. **SQ-15 is the Strata sweet spot**: faster than SQ-20 (58 vs 48), passed every task. SQ-10 is no faster in
   practice and once spent 2048 tokens thinking with no visible answer.
5. **Inkling thinks even in "no thinking" mode.** With no `reasoning_effort`, the template's default effort is 0.9
   (what llama.cpp and Unsloth Studio use unless set). Strata 0.2.19 forces `none` and throws the thinking away, but
   the model still spends 2–4× the visible tokens on it. With `reasoning_effort: none` on llama.cpp, one answer went
   from 1246 to 609 tokens. **Compare wall time to a finished answer, not only the tok/s an engine prints.**
6. **MTP on Tiel-Coder is the biggest single win: +40% (70 → 98 tok/s)**, acceptance 0.66–0.74, from a 0.9 GB draft
   head built into the GGUF (`--spec-type draft-mtp`).
7. **Thinking off on Tiel-Coder roughly triples task speed** (70 s → 24 s for the 10 tasks) for one failure. Good for
   quick edits; keep thinking on for anything non-trivial.
8. **The mini-eval is too easy to rank quality** (everything 9–10/10). It only shows the fast settings don't write
   broken code. The [agent benchmarks](2026-11-23-agent-models.md) separate models better.

## Runtimes on this Mac

| Runtime | Inkling-2-Mini | Qwen-family MoE (Tiel-Coder) | Notes |
|---|---|---|---|
| Strata (`strata-inkling`, Metal) | ✅ fastest for Inkling | ❌ its Qwen3.6-35B-A3B engine is CUDA/HIP only | Worth it for Inkling only |
| Unsloth llama.cpp fork (b12588) | ✅ (`inkling2` arch, `draft-dspark`) | ✅ with `draft-mtp` | Best general runtime; Unsloth Studio uses it |
| Homebrew llama.cpp 0.7.0 | ❌ `unknown model architecture: 'inkling2'` | ✅ (not benched) | Behind the fork |
| [TensorSharp](2026-11-22-tensorsharp.md) | ❌ on Mac | ✅ 75–92 tok/s | No gain over the fork |
| LM Studio / mlx-lm | not tested | not tested | Open thread |

How to run the winners: [guides/llama-cpp.md](../guides/llama-cpp.md), [guides/strata.md](../guides/strata.md).
