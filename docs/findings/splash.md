# Splash: the fastest runtime on this Mac (and two Qwen3.8-27B fine-tunes)

**Measured:** 2026-11-24, M5 Pro (20-core GPU) 48 GB, [Splash](https://github.com/incoai/splash) 1.7.2 (Homebrew),
plugged in. Same prompts, graders and agent task as the other findings ([methodology](../methodology.md)).
Raw data: [results/decode](../../results/decode/), [results/agents](../../results/agents/).

Splash is a Metal-only engine with hand-written kernels per model family and a trained
[DFlash 2](https://inco.ai/blog/dflash2/) drafter for each. It serves Qwen3.8-27B, Qwen3.6-35B-A3B (and fine-tunes
such as Tiel-Coder), Inkling-2-Mini, Qwen3.8-Flash-Next and a few others, from ordinary GGUF or MLX files.

## Results

Decode: `bench/oai_bench.py`, 3 prompts × 2 runs, `reasoning_effort: none`. Agent: the 3-turn Cline session and the
same session in pi ([agent-models](agent-models.md)), "checks" are the 9 turn 1–2 checks, "issues" the real issues
found of 8.

| Model | Engine | Decode tok/s | Cline session | Cline checks / issues | pi session | pi checks / issues |
|---|---|---:|---:|---|---:|---|
| **Tiel-Coder-35B-A3B UD-Q4_K_XL**, thinking budget 8K | **Splash** | **191** | **101 / 94 s** | 9/9, 8/9 · 6, 2 | **36 s** | 8/9 · 4 |
| | llama.cpp + MTP (before) | 98* | 142 / 168 s | 9/9, 9/9 · 4, 7 | — | — |
| **Inkling-2-Mini UD-IQ4_XS**, thinking off | **Splash** | **101** | **94 / 75 s** | 9/9, 3/9† · 6, 6 | 60 s | 3/9‡ · 4 |
| | Strata 0.2.19 + checkpoint engine (before) | 58 | 105–119 s | 9/9, 9/9, 8/9 · 4–6 | 88–108 s | — |
| **Qwen3.8-Flash-Next GSQ-RCO Q2_0**, 20 GB expert store, thinking budget 8K | **Splash** | **129** | 280 s | 7/9 · **8** | — | — |
| same, 14 GB expert store | Splash | 96 | 348 s | 9/9 · **8** | 204 s | 9/9 · 7 |
| **Qwen3.8-27B-pi-adapted** (Q4_K_M), thinking off | **Splash** | **90** | 228 / 169 s | 7/9, 8/9 · 4, 5 | 57 / 143 s | 7/9, 7/9 · 5, 5 |
| Qwen3.8-27B TURBO-Fable (DavidAU, Q4_K_M), thinking off | Splash | 21 | — | — | — | — |
| | llama.cpp + MTP n-max 2 | 24 | 213 s | 6/9 · 2 | 45 s | 5/9 · 1 |

\* Tiel IQ4_XS; Q4_K_XL is a little slower on llama.cpp.
† Run 2: Splash returned one tool call as text (`<|message_model|><|content_invoke_tool_json|>…`), so the commit
turn ended without running it. ‡ The model stopped to ask for a git identity instead of setting one.

Mini-eval (10 small coding tasks, thinking off): pi-adapted 10/10, DavidAU 10/10, Inkling 10/10, Tiel 9/10,
Flash-Next 9/10 and 8/10.
Swap stayed flat (0.85 GB) for every Splash run.

## Findings

1. **Splash roughly doubles decode speed on this Mac**: Tiel-Coder 191 tok/s (llama.cpp + MTP: 98), Inkling 101
   (Strata: 58–66, llama.cpp: 36–42). Its prompt cache works with Cline and pi out of the box, so agent sessions got
   faster too: **Tiel 94–101 s and Inkling 75–94 s per Cline session**, both faster than our patched Strata.
2. **The speed comes from the drafter, so it depends on the model matching it.** Splash accepted 4–7 tokens per
   cycle on the stock-like models but only 1.7 on DavidAU's TURBO-Fable fine-tune (21 tok/s, slower than llama.cpp's
   24 with the model's own MTP head). A LoRA fine-tune close to its base (pi-adapted) kept 6–7 tokens per cycle.
3. **Of the two Qwen3.8-27B fine-tunes, pi-adapted wins on both axes**: 90 vs 21–24 tok/s, and more checks and
   issues in both harnesses. DavidAU's model answered fastest in pi (45 s) but missed the feature in turn 1 and found
   1–2 issues. Neither beat Tiel or Inkling on this task, and both 27Bs are dense, so long agent turns cost more.
4. **pi-adapted is tuned for pi but works in Cline.** It committed the local config folder in 3 of 4 sessions.
5. **Two rough edges**: one Inkling tool call leaked as text, and Cline over ACP always requests the model name
   `gpt-4o`, which Splash rejects unless served under that name (`--served-model-name gpt-4o`).
6. **Basalt**, the engine people call fast, is NVIDIA Blackwell only (Linux/Windows); its smallest
   Qwen3.8-Flash-Next pack is 65.6 GiB. Splash is its Mac counterpart: see 7.
7. **Qwen3.8-Flash-Next runs on 48 GB by streaming its experts from the SSD, and finds the most issues.** The
   66 GB Q2_0 GGUF (Splash's suggestion for 64 GB Macs) decodes at 96 tok/s with 42% of the routed experts in a
   14 GB store and 129 tok/s with 61% in 20 GB; the 28.8 GB n-gram table shard streams too. In agents (thinking on,
   long prompts) it decodes at 65 and 85 tok/s, ~2 s to first token with prompt reuse. **It found all 8 real
   issues in both Cline runs with no false claims**, a first on this task, but its sessions are slower (280–348 s
   Cline, 204 s pi) because it writes more. Run 2 left the new files out of the commit (7/9).
8. **Set `--expert-memory` and `--max-memory` for Flash-Next.** With the defaults Splash planned to load every
   expert (39 GB minimum), pushed swap from 0.8 to 7 GB while starting and then refused with "not enough free
   memory". With `--expert-memory 20G --max-memory 36G` swap stayed flat and the process stayed at ~3 GiB RSS.

## Setup

```sh
brew install incoai/tap/splash
# Tiel-Coder (Qwen3.6-35B-A3B family), thinking capped
splash serve --model local/tiel --model-dir ~/models/tiel/Tiel-Coder-35B-A3B-MTP-UD-Q4_K_XL.gguf \
  --draft-model ~/models/drafts/Qwen3.6-35B-A3B-DFlash2 --thinking-token-budget 8192 --max-context 128K \
  --language-only --idle-release off --max-cache-disk 4G --served-model-name gpt-4o
# Inkling-2-Mini, thinking off by default
splash serve --model local/inkling --model-dir ~/models/inkling/Inkling-2-Mini-UD-IQ4_XS.gguf \
  --draft-model ~/models/drafts/Inkling-2-Mini-DFlash2 --default-reasoning-effort none --max-context 128K \
  --language-only --idle-release off --max-cache-disk 4G --served-model-name gpt-4o
# Qwen3.8-Flash-Next (66 GB GGUF on a 48 GB Mac), experts streamed from the SSD
splash serve --model local/flashnext \
  --model-dir ~/models/flashnext/Q2_0/Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-00001-of-00002.gguf \
  --draft-model ~/models/drafts/Qwen3.8-Flash-Next-DFlash2 --expert-memory 20G --max-memory 36G \
  --thinking-token-budget 8192 --max-context 128K \
  --language-only --idle-release off --max-cache-disk 4G --served-model-name gpt-4o
```

Drafters: `incoai/Qwen3.6-35B-A3B-DFlash2` (1 GB), `incoai/Inkling-2-Mini-DFlash2` (0.9 GB),
`incoai/Qwen3.8-27B-DFlash2` (3.6 GB), `incoai/Qwen3.8-Flash-Next-DFlash2` (1.2 GB). Flash-Next model:
`ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF`, folder `Q2_0` (37.6 + 28.8 GB). Without `--model-dir`,
`splash serve --model OWNER/REPO:VARIANT` downloads the model and its drafter. Point clients at `http://127.0.0.1:8000/v1`. `splash pi`, `splash opencode` and
`splash claude` start a harness wired to the server.

Model notes: pi-adapted was requantized here from its published Q8_0 merge to Q4_K_M (no imatrix) to match the
other 4-bit files. DavidAU's model card recommends Q6 and calls Q4_K_M the minimum.
