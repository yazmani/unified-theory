# Which runtime is fastest on an Apple Silicon Mac?

**Current answer (2026-11-25): [Splash](https://github.com/incoai/splash)**, about 2× llama.cpp and Strata on the
same model, as long as the model matches one of its drafters. Measured on an M5 Pro (20-core GPU), 48 GB
([methodology](../methodology.md)). How to run it: [guides/splash](../guides/splash.md).

## Same model, different runtimes

Decode tok/s from the engine's counter, `reasoning_effort: none`; "wall-clock" rows are completion tokens / wall time
of one non-streamed request (`bench/raw_decode.py`), used where an engine has no counter or streams in bursts.

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
| | Splash 1.7.2, pi-adapted Q4_K_M | 90 | 169–228 s |
| | dspine-hybrid-mlx 0.4.0 (Tencent DSpine drafter), 4-bit MLX | 90 streamed (87 end-to-end) | 166 s |
| | Splash 1.7.2, DavidAU TURBO-Fable Q4_K_M | 21 | — |
| | Unsloth llama.cpp + MTP n-max 2, DavidAU TURBO-Fable Q4_K_M | 24 | 213 s |

**At 100K tokens of context** (prefill / decode tok/s): Tiel on Splash 1,756 / 187, on oMLX 1,451 / 112; Inkling on
Splash 1,213–1,218 / 96–99, on oMLX 682 / 24; Qwen3.8-27B on Splash (GSQ IQ3_S) 512 / 75, on DSpine 416 / 18. More in [long-context](long-context.md).

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

1. **Splash roughly doubles decode speed**: Tiel 191 tok/s (llama.cpp + MTP 98), Inkling 101 (Strata 58–66,
   llama.cpp 30–42). Its prompt cache works with Cline and pi out of the box, so agent sessions got faster too.
2. **Splash's speed comes from the drafter, so the model must match it.** It accepted 4–7 tokens per cycle on
   stock-like models and LoRA-style fine-tunes (pi-adapted kept 6–7), but 1.7 on DavidAU's TURBO-Fable (21 tok/s,
   slower than llama.cpp with the model's own MTP head). The Ornith-trained DFlash2 drafter from jzinno doesn't load
   in 1.7.2 (sliding window 4096, Splash expects 2048), but the stock Qwen3.6-35B-A3B drafter serves the whole family.
3. **Big MoEs fit by streaming experts, if you cap memory.** For Flash-Next (66 GB) Splash's defaults planned to load
   every expert (39 GB minimum), pushed swap from 0.8 to 7 GB and then refused to start. With
   `--expert-memory 20G --max-memory 36G` swap stayed flat.
4. **`--persistent-cache` works, but only from the same working directory.** After a restart Splash restored its
   cache (1.1–1.3 GB) and Cline's first request hit 3,200 of 3,229 cached tokens: first token in 0.1 s instead of
   0.9 s. From another folder it reused nothing, because Cline and pi put the working directory near the top of the
   system prompt. It saves the first turn's system-prompt prefill; cheap to turn on.
5. **Two Splash rough edges:** one Inkling tool call came back as text
   (`<|message_model|><|content_invoke_tool_json|>…`), and Splash rejects model names it doesn't serve, while Cline
   over ACP always requests `gpt-4o` (`--served-model-name gpt-4o` fixes it).
6. **oMLX is slower than Splash on both models it shares**, and its streamed tok/s can't be trusted: it releases
   Inkling's tokens in bursts, so the streamed benchmark showed 261 tok/s where wall-clock and oMLX's own log say 55.
   MTP is worth +24% there. In agents it throttles prefill under its memory guard and caches this hybrid model's
   prompt in 2,048-token blocks, so each turn re-reads 5–9K tokens. Thinking must be turned off server-side
   (`"chat_template_kwargs": {"reasoning_effort": 0.0}` in its per-model settings): per-request
   `enable_thinking=false` doesn't reach Inkling, and harnesses send no thinking settings.
7. **DSpine is thorough at short context, slow at depth.** Tencent's drafter for Qwen3.8-27B (Mac support merged
   upstream as [Tencent/DSpine#3](https://github.com/Tencent/DSpine/pull/3), served by
   [dspine-hybrid-mlx](https://github.com/internet-projects/dspine-hybrid-mlx)) decodes at 90 tok/s here (186 on an
   M5 Max in its README, twice our bandwidth) and found 7 issues in Cline and 8 in pi. 100K took 238 s of prefill,
   decoded at 18 tok/s, and memory peaked at ~37 GB. **Don't run it greedy:** at its default temperature 0 one Cline
   request looped for 32,000 tokens; Qwen's sampling (0.6 / top-p 0.95 / top-k 20) fixed it.
8. **Before Splash, Strata was the Inkling runtime and llama.cpp the general one.** Strata ran Inkling 1.6–1.9×
   faster than llama.cpp. Inkling is slow for its size on any engine: it is a looped MoE (48 virtual layer visits),
   2.3× slower than a 35B-A3B Qwen on the same llama.cpp. On llama.cpp, MTP gave Tiel +40% and DSpark gave Inkling
   +20% at n-max 3; Strata's own DSpark drafter gave nothing on Mac.
9. **Compare wall time to a finished answer, not only tok/s.** Inkling thinks even in "no thinking" mode unless
   `reasoning_effort` is `none` (the template default is 0.9): one answer went from 1,246 to 609 tokens.
10. **Atomic Engine's 77 tok/s README number didn't reproduce on real prompts** (45 here; its benchmark is a
    64-token answer on a repetitive fixture), and its published profiles (4K context, prompt reuse off) can't run an
    agent. AtomicChat's AD-Q4_K quant is the best llama.cpp option for Inkling (42 vs 36 tok/s for UD-IQ4_XS).
11. **TensorSharp** (C#/.NET on ggml) can't run Unsloth's Inkling files on Mac (layer-count mismatch, then no NVFP4
    `MUL_MAT_ID` in ggml Metal) and gave no gain on Tiel.

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

Earlier pages with the full detail: [decode-speed](../archive/2026-11-22-decode-speed.md) (Strata, llama.cpp,
AtomicChat), [tensorsharp](../archive/2026-11-22-tensorsharp.md), [splash](../archive/2026-11-24-splash.md),
[model-sweep](../archive/2026-11-24-model-sweep.md) (oMLX, DSpine). Raw data: [results/](../../results/).
