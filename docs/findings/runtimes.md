# Which runtime is fastest on an Apple Silicon Mac?

**Answer as of 2026-11-25: [Splash](https://github.com/incoai/splash)**, about 2× llama.cpp and Strata on the same
model, when Splash has a drafter that matches the model. M5 Pro (20-core GPU), 48 GB ([methodology](../methodology.md)).
Setup: [guides/splash](../guides/splash.md).

## Same model, different runtimes

Decode is tok/s from the engine's counter with `reasoning_effort: none`. Engines without a counter are timed by the
client: "streamed" from first to last token, "wall-clock" and "end-to-end" as completion tokens / total request time
(`bench/raw_decode.py`).

| Model | Runtime | Decode tok/s | Cline session |
|---|---|---:|---|
| **Tiel-Coder-35B-A3B** | **Splash 1.7.2** (DFlash 2 drafter), UD-Q4_K_XL | **191** | 94–101 s |
| | oMLX 0.8.3, oQ4e + MTP | 126 streamed (117 end-to-end) | 85 s |
| | Unsloth llama.cpp b12588 + MTP n-max 1, UD-IQ4_XS | 98 | 142–168 s (Q4_K_XL) |
| | TensorSharp `5c97544` + MTP, UD-IQ4_XS | 75–92 (streamed) | — |
| | Unsloth llama.cpp b12588, no speculative decoding | 70 | — |
| **Inkling-2-Mini** | **Splash 1.7.2**, UD-IQ4_XS / UD-Q4_K_M | **101 / 92** (109–116 wall-clock) | 72–94 s |
| | Strata 0.2.20, SQ-15, thinking forced off | 66 | 330–341 s (no prompt reuse with tools) |
| | Strata 0.2.19 + DSpark, SQ-15 (+ #6627 checkpoint engine for agents) | 58 | 105–119 s |
| | oMLX 0.8.3, oQ4e + MTP | 55 (wall-clock) | 370 s |
| | Atomic Engine (SSD expert streaming), AD-Q4_K + DSpark, 20 GiB budget | 45 | — (4K context profiles) |
| | llama.cpp PR #32218, AD-Q4_K + DSpark n=3 | 42 | 218–278 s |
| | Unsloth llama.cpp b12588 + DSpark n=3, UD-IQ4_XS | 36 | — |
| | Unsloth llama.cpp b12588, UD-IQ4_XS | 30 | — |
| **Qwen3.8-27B** | **Splash 1.7.2**, GSQ-RCO IQ3_S (11.8 GB) | **96** (107 wall-clock) | 154 s |
| | Splash 1.7.2, Ternary Bonsai 2.5 PQ2_0 (7.5 GB) | 145 (160 wall-clock) | 268 s |
| | llama.cpp (upstream + PR #32891) + MTP head, Ternary Bonsai 2.5 Q2_0 | 31 | 650 s |
| | Splash 1.7.2, pi-adapted Q4_K_M | 90 | 169–228 s |
| | dspine-hybrid-mlx 0.4.0 (Tencent DSpine drafter), 4-bit MLX | 90 streamed (87 end-to-end) | 166 s |
| | Splash 1.7.2, DavidAU TURBO-Fable Q4_K_M | 21 | — |
| | Unsloth llama.cpp + MTP n-max 2, DavidAU TURBO-Fable Q4_K_M | 24 | 213 s |

At 100K tokens of context ([long-context](long-context.md)):

| Model | Runtime | Prefill / decode tok/s |
|---|---|---|
| Tiel-Coder | Splash / oMLX | 1,756 / 187 · 1,451 / 112 |
| Inkling-2-Mini | Splash / oMLX | 1,213–1,218 / 96–99 · 682 / 24 |
| Qwen3.8-27B | Splash (GSQ IQ3_S) / DSpine (4-bit) | 512 / 75 · 416 / 18 |
| Ternary Bonsai 2.5 27B | Splash (PQ2_0) / llama.cpp (Q2_0 + MTP) | 400 / 99 · 217 / 15 |

## What runs where

| Runtime | Inkling-2-Mini | Qwen3.6-35B-A3B family | Qwen3.8-27B / Flash-Next | Notes |
|---|---|---|---|---|
| **Splash** 1.7.2 (Metal) | ✅ fastest | ✅ fastest | ✅ (Flash-Next streams experts from the SSD) | needs a matching DFlash 2 drafter |
| Strata (`strata-inkling`, Metal) | ✅ | ❌ its Qwen3.6 engine is CUDA/HIP only | — | agents need the checkpoint engine ([prompt cache](strata-prompt-cache.md)) |
| Unsloth llama.cpp fork | ✅ (`inkling2`, DSpark) | ✅ (MTP) | ✅ | best general runtime before Splash |
| Homebrew llama.cpp 0.7.0 | ❌ unknown architecture | ✅ (not benched) | — | behind the fork at the time |
| oMLX 0.8.3 | ✅ (MTP) | ✅ (MTP) | — | slower than Splash on both; uninstalled |
| dspine-hybrid-mlx 0.4.0 | — | — | ✅ 27B | most thorough 27B setup, slow at depth |
| TensorSharp | ❌ on Mac | ✅ | — | no gain over llama.cpp |
| Atomic Engine | ✅ | — | — | memory cap, not speed |
| Basalt | — | — | — | NVIDIA Blackwell only |

## Findings

1. **Splash roughly doubles decode speed.** Tiel: 191 tok/s (llama.cpp + MTP: 98). Inkling: 101 (Strata: 58–66,
   llama.cpp: 30–42). Its prompt cache works with Cline and pi without configuration, so agent sessions are faster
   too.
2. **Splash's speed depends on the drafter matching the model.** Stock models and light fine-tunes accepted 4–7
   tokens per cycle (pi-adapted: 6–7). DavidAU's TURBO-Fable accepted 1.7 and ran at 21 tok/s, slower than llama.cpp
   with the model's own MTP head (24). The Ornith-trained drafter `jzinno/Ornith-1.5-35B-A3B-DFlash2` does not load
   in 1.7.2 (sliding window 4096; Splash expects 2048). The stock Qwen3.6-35B-A3B drafter serves the whole family.
3. **MoE files larger than memory run if you cap memory.** For Flash-Next (66 GB), Splash's defaults tried to load
   every expert (39 GB minimum), pushed swap from 0.8 to 7 GB and refused to start. With
   `--expert-memory 20G --max-memory 36G`, swap stayed flat.
4. **`--persistent-cache` only helps from the same working directory.** After a restart, Splash restored 1.1–1.3 GB
   of cache and Cline's first request hit 3,200 of 3,229 cached tokens: first token in 0.1 s instead of 0.9 s. From
   another folder nothing was reused, because Cline and pi put the working directory in the system prompt.
5. **Splash issues:** one Inkling tool call came back as text (`<|message_model|><|content_invoke_tool_json|>…`).
   Splash rejects model names it doesn't serve, and Cline over ACP always requests `gpt-4o`; serve under that name
   (`--served-model-name gpt-4o`).
6. **oMLX is slower than Splash on both shared models, and its streamed tok/s is unreliable.** It releases Inkling's
   tokens in bursts: the streamed benchmark showed 261 tok/s, wall-clock and oMLX's log show 55. MTP adds 24%. In
   agents it throttles prefill under its memory guard and caches this model's prompt in 2,048-token blocks, so each
   turn re-reads 5–9K tokens. Thinking has to be turned off in its per-model settings
   (`"chat_template_kwargs": {"reasoning_effort": 0.0}`); per-request `enable_thinking=false` does not reach Inkling,
   and harnesses send no thinking settings.
7. **DSpine finds the most issues at short context and slows down at depth.** Tencent's drafter for Qwen3.8-27B (Mac
   support merged as [Tencent/DSpine#3](https://github.com/Tencent/DSpine/pull/3), served by
   [dspine-hybrid-mlx](https://github.com/internet-projects/dspine-hybrid-mlx)) decodes at 90 tok/s here (186 on an
   M5 Max per its README, which has twice the bandwidth) and found 7 issues in Cline and 8 in pi. At 100K: 238 s of
   prefill, 18 tok/s decode, ~37 GB peak memory. Its default temperature 0 made one Cline request loop for 32,000
   tokens; use Qwen's sampling (temperature 0.6, top-p 0.95, top-k 20).
8. **Before Splash, Strata ran Inkling and llama.cpp ran everything else.** Strata was 1.6–1.9× faster than llama.cpp
   on Inkling. Inkling is slow on every engine: it is a looped MoE (48 virtual layer visits) and runs 2.3× slower
   than a 35B-A3B Qwen on the same llama.cpp. On llama.cpp, MTP added 40% for Tiel and DSpark added 20% for Inkling
   (n-max 3); Strata's DSpark drafter added nothing on Mac.
9. **Measure wall time to a finished answer, not only tok/s.** Inkling thinks in "no thinking" mode unless
   `reasoning_effort` is `none` (template default: 0.9). Setting it cut one answer from 1,246 to 609 tokens.
10. **Atomic Engine's README figure (77 tok/s) did not reproduce on real prompts** (45 here; the README measures a
    64-token answer on a repetitive fixture). Its published profiles (4K context, prompt reuse off) cannot run an
    agent. AtomicChat's AD-Q4_K quant is the fastest llama.cpp option for Inkling (42 tok/s; UD-IQ4_XS: 36).
11. **Splash runs ternary Bonsai 2.5 5× faster than llama.cpp** (160 vs 31 tok/s wall-clock, Cline 268 vs 650 s),
    from PrismML's `PQ2_0` file with the stock Qwen3.8-27B drafter (4.1 tokens per cycle). It refuses the `Q2_0` file.
    On llama.cpp the MTP head gives about PrismML's M4 Pro figure (29 tok/s).
12. **TensorSharp** (C#/.NET on ggml) cannot run Unsloth's Inkling files on Mac (layer-count mismatch, then no NVFP4
    `MUL_MAT_ID` in ggml Metal) and was no faster on Tiel.

## Setup

Splash: [guides/splash](../guides/splash.md). llama.cpp: [guides/llama-cpp](../guides/llama-cpp.md). Strata:
[guides/strata](../guides/strata.md).

```sh
# oMLX (foreground only, settings in a throwaway --base-path)
brew tap jundot/omlx https://github.com/jundot/omlx
xcodebuild -downloadComponent MetalToolchain        # needed for --with-custom-kernel on current Xcode
brew install jundot/omlx/omlx --with-custom-kernel
omlx serve --model-dir DIR --base-path TMP --port 8000 --headless
#   per-model settings in TMP/model_settings.json, e.g.
#   {"version": 3, "models": {"MODEL": {"mtp_enabled": true, "chat_template_kwargs": {"reasoning_effort": 0.0}}}}

# DSpine on Qwen3.8-27B (MLX)
pip install "dspine-hybrid-mlx[fast] @ git+https://github.com/internet-projects/dspine-hybrid-mlx.git@v0.4.0"
dspine-hybrid-serve --target mlx-community/Qwen3.8-27B-4bit --draft netprojects/Qwen3.8-27B-DSpine-b16-MLX \
  --fast --temperature 0.6 --top-p 0.95 --top-k 20 --port 8000
```

Full detail of each run: [decode-speed](../archive/2026-11-22-decode-speed.md) (Strata, llama.cpp,
AtomicChat), [tensorsharp](../archive/2026-11-22-tensorsharp.md), [splash](../archive/2026-11-24-splash.md),
[model-sweep](../archive/2026-11-24-model-sweep.md) (oMLX, DSpine). Raw data: [results/](../../results/).
