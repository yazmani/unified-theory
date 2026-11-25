# Long context on 48 GB: how deep can local models go, and how fast?

**Answer as of 2026-11-25:** every model tested recalled 8 of 8 hidden facts at 99–250K tokens, and 256K of context fits
on 48 GB for every model below. What changes with depth is speed. At a 250K prompt on Splash, Qwen3.8-Flash-Next keeps
80% of its decode speed (104 tok/s) and reads the prompt in 3.7 min. KAT-Ornith (Qwen3.6-35B-A3B) decodes faster (145
tok/s) but has lost 38% of its short-prompt speed. The dense 27B models need 13–15 min to read 250K. The cause is the
attention design ([below](#why-flash-next-holds-up-model-structure)). After the first read, agent speed depends on
whether follow-up turns reuse the prompt.

Script: `bench/context/long_context.py`: a haystack of real source code sized with the model's tokenizer, with 8 constants
hidden at 5–95% depth. Raw data: [results/long-context](../../results/long-context/).

## 250K on Splash (2026-11-25)

`--max-context 256K`, a 248K-token prompt, one model at a time. Swap stayed at 4.2 GB before and after every run.
Flash-Next ran with its 20 GB expert store and `--max-memory 36G`, as in the agent runs.

| Model | Prompt read: tok/s (time) | Decode at 250K | at 100K | short prompt | Recall |
|---|---|---:|---:|---:|---|
| **Swift-1.5 Qwen3.8-Flash-Next Q2_0** | 1,115 (3.7 min) | 120 | — | 125 | 8/8 |
| **Qwen3.8-Flash-Next GSQ-RCO Q2_0** | **1,118 (3.7 min)** | 104 | 127 | 129 | 8/8 |
| KAT-Ornith-HERO fusion | 951 (4.4 min) | **145** | 160 | 235 | 8/8 |
| Qwen3.8-27B GSQ-RCO IQ3_S | 320 (12.9 min) | 61 | 75 | 96 | 8/8 |
| Ternary Bonsai 2.5 27B PQ2_0 | 267 (15.5 min) | 69 | 99 | 145 | 8/8 |

- **Flash-Next slows least.** From 100K to 250K its prompt read drops 7% and its decode 18%. KAT-Ornith's prompt
  read drops 46%; the 27B models' drop 33–37%, from a much lower start.
- **The 27B models are not usable at full depth.** 13–15 min to read 250K, and 61–69 tok/s after that.
- **Thinking models need room to answer.** The answer limit was 6,000 tokens for KAT-Ornith and the 27B GSQ, and
  12,000 for Flash-Next and Bonsai (thinking budget 8K).

## Why Flash-Next holds up: model structure

From the GGUF metadata of the files tested (parameter counts summed from the tensor shapes):

| | Qwen3.8-Flash-Next | KAT-Ornith (Qwen3.6-35B-A3B) | Qwen3.8-27B, Bonsai 2.5 |
|---|---|---|---|
| Type | MoE: 512 experts, 10 + 1 shared per token | MoE: 256 experts, 8 + 1 shared per token | dense |
| Parameters in the file | 177B: 126B model + a 51B n-gram lookup table | 35.5B | 26.9B |
| Parameters computed per token | ~6.6B | ~3B | ~26B |
| Linear-attention / full-attention layers | 36 / 12 | 30 / 10 | 48 / 16 |
| Tokens each full-attention layer reads | **~2,048 picked by an indexer** (top-k), compression ratio 4 | all | all |

- **File size is not work per token.** Each token runs through 10 of 512 experts per layer, so Flash-Next computes about
  a quarter of what the dense 27B does, although its file is more than 5× larger. Splash keeps the most-used experts in
  memory (`--expert-memory`) and reads the rest from the SSD. The 51B table is a lookup: a few rows per token.
- **All three families use mostly linear attention** (Gated DeltaNet: a fixed-size state, cost flat with depth), with
  full attention in every 4th layer. Those full-attention layers are what slows down with depth.
- **Flash-Next's full-attention layers are sparse.** A small indexer (4 heads, 128-dim keys) scans the context and each
  query attends to the top 2,048 tokens. In KAT-Ornith and the 27B models, every query attends to every token.

A rough count of the work per prompt token (2 FLOPs per computed parameter, plus attention at the average position
of 125K for a 250K prompt) matches the measured slowdown:

| Model | Weights | Attention at 250K | Predicted prompt read 250K vs 100K | Measured |
|---|---:|---:|---:|---:|
| Flash-Next | ~13 GFLOP | ~2 GFLOP (2,048 tokens + the indexer scan) | 0.94× | 0.93× |
| KAT-Ornith | ~6 GFLOP | ~20 GFLOP (10 layers × 16 heads × 256 dims, all tokens) | 0.54× | 0.54× |
| Qwen3.8-27B | ~52 GFLOP | ~49 GFLOP (16 layers × 24 heads × 256 dims, all tokens) | 0.71× | 0.63× |

Decode follows the same pattern. Each new token reads the keys and values of the full-attention layers: about
64 KiB per context token for the 27B models at 16-bit (16 GB at 250K, more than the 11.8 GB of weights) and 20 KiB
for KAT-Ornith (5 GB). Flash-Next reads 2,048 tokens' worth plus the indexer's 128-dim keys.

### Other models built for long context (Hugging Face, 2026-11-25)

Models that fit on 48 GB and use the same tricks: few parameters per token, and linear or sparse attention. Facts
are from each repo's `config.json` and model card. Only Swift-1.5 has been tested ([models](models.md), finding 14).

| Model | Total / per token | Attention | Fits 48 GB as | Runtime |
|---|---|---|---|---|
| ukisai Swift1.5-Qwen3.8-Flash-Next (**tested**: 120 tok/s at 250K) | Flash-Next | same as Flash-Next; trained further for coding and agent work | GSQ-RCO Q2_0, 66.5 GB, with expert streaming | Splash, with the Flash-Next drafter |
| Meituan LongCat-Flash-Lite-Sparse | 69B / ~3B | indexer on every layer (top 2,048 tokens), plus an n-gram embedding | MLX 4-bit, 38.6 GB | mlx-vlm; llama.cpp PR #19167 open |
| inclusionAI Ling-3.2-air | 124B / 5.5B | linear (KDA) and MLA layers, 5:1; no indexer | GGUF IQ2_XXS, 38.4 GB | llama.cpp |
| Moonshot Kimi-Linear-48B-A3B | 48B / 3B | linear (KDA) and MLA layers, 20 / 7 | GGUF Q4_K_M, 30.1 GB | llama.cpp, MLX |
| NVIDIA Nemotron-3.5-Lightning-30B-A3B | 31.6B / 3B | Mamba-2 plus 6 attention layers | GGUF Q4_K_XL, 25.5 GB | llama.cpp |

Splash serves only the families it has kernels and a drafter for. The non-Qwen models above would run on llama.cpp or
MLX, about half Splash's speed on the same model ([runtimes](runtimes.md)). The closest designs to Flash-Next, with an
indexer and linear attention, are too large for 48 GB: GLM-5.3-Flash (321B), DeepSeek-V4-Flash (291B),
MiniMax-M3.1-Flash (220B).

## 100K on Splash, oMLX, DSpine and llama.cpp (2026-11-24/25)

| Model | Runtime | Prefill tok/s (time) | Decode tok/s at depth | Recall |
|---|---|---|---|---|
| HauhauCS Aggressive | Splash | 1,770 | **223** | 8/8 |
| Cyber-Tiel | Splash | 1,769 | 206 | 8/8 |
| Qwen-AgentWorld | Splash | 1,783 | 199 | 8/8 |
| Qwopus3.6-Coder | Splash | 1,753 | 190 | 8/8 |
| Tiel-Coder | Splash | 1,756 | 187 | 8/8 |
| KAT-Coder-V2.5-Dev | Splash | 1,755 | 180 | 8/8 |
| Qwen3.8-35B-A3B-Distill | Splash | 1,756 | 171 | 8/8 |
| KAT-Ornith-HERO fusion | Splash | 1,757 (~56 s) | 160 | 8/8 |
| Qwen3.8-Flash-Next Q2_0 (20 GB expert store) | Splash | 1,196 (83 s) | 127 | 8/8 |
| Qwen3.8-Flash-Next Coder | Splash | 1,210 (82 s) | 119 | 8/8 |
| Inkling-2-Mini UD-Q4_K_M / UD-IQ4_XS | Splash | 1,218 / 1,213 (~82 s) | 96 / 99 | 8/8 |
| Tiel-Coder oQ4e-MTP | oMLX | 1,451 | 112 | 8/8 |
| Inkling-2-Mini oQ4e-mtp | oMLX | 682 | 24 | 8/8 |
| Qwen3.8-27B GSQ-RCO IQ3_S | Splash | 512 (194 s) | 75 | 8/8 |
| Ternary Bonsai 2.5 27B PQ2_0 | Splash | 400 (248 s) | 99 | 8/8 |
| Ternary Bonsai 2.5 27B Q2_0 + MTP | llama.cpp | 217 (455 s) | 15 | 8/8 |
| Kolibri 1.1 GSQ-RCO IQ2_XS | llama.cpp | 614 (162 s) | 48 | 8/8 |
| Kolibri 1.1 Q3_K_M | llama.cpp | 584 (170 s) | 49 | 8/8 |
| Qwen3.8-27B 4-bit + DSpine | dspine-hybrid-mlx | 416 (238 s) | 18 | 8/8 |

- **The Qwen3.6-35B-A3B models barely slow down at depth**: 160–223 tok/s at 99K, likely because most of their layers
  use linear attention. A dual RTX 5070 Ti user reported 5,400–6,400 tok/s prefill and 184 tok/s decode at 103K on
  Basalt: about 3× our prefill (memory bandwidth), the same decode.
- **Dense and looped models slow down more.** Inkling drops to ~97 tok/s; Qwen3.8-27B to 75 tok/s on Splash and 18 on
  DSpine (~37 GB peak memory). The 27B also reads a 100K prompt 3× slower than the MoEs.
- **Thinking models need a larger answer limit.** Kolibri GSQ-RCO and Bonsai spent the default 3,000 tokens thinking
  and returned no answer; with 12,000 they recalled 8/8 (Kolibri used 6,911 tokens).
- **Flash-Next holds 119–127 tok/s at 100K**, with experts streamed from the SSD (Q2_0) or all in memory (Coder).

## Inkling-2-Mini to 240K on Strata and llama.cpp (2026-11-22)

| Engine | Prompt | Prefill | Decode | Needles | Follow-up turn at same context |
|---|---|---|---|---|---|
| Strata SQ-15, `--context 256k` | 30K | 973 tok/s (31 s) | 63 tok/s | 8/8 | not run |
| Strata SQ-15 | 120K | 629 tok/s (189 s) | 27.5 tok/s | 8/8 | **204 s: re-reads everything (cached 0)**, correct |
| Strata SQ-15 | 240K | 428 tok/s (554 s) | 19.2 tok/s | 8/8 | identical repeat: 554 s again, cached 0 |
| Unsloth llama.cpp IQ4_XS + DSpark n=3, `-c 131072`, effort none | 120K | **103 tok/s (1217 s)** | 23.8 tok/s | 8/8 | **32 s: 118,939 of 119,136 cached**, correct |

### Findings

- **Context limit:** the engine's maximum is 1M tokens (`MAX_CONTEXT = 1048576`); Strata's menu offers up to 256K.
- **Memory at 256K on Strata (SQ-15):** 8,352 MiB of KV cache (full precision), 26.52 GiB for the engine. 1M would
  need ~34.5 GB of KV alone, which does not fit on 48 GB with anything else running.
- **Recall:** 8/8 at 30K, 120K and 240K on Strata; 8/8 at 120K on llama.cpp.
- **Decode drops with depth:** Strata 63 → 27.5 → 19 tok/s; llama.cpp ~24 at 120K.
- **Prompt reuse decides follow-up speed.** Strata 0.2.19 reads a long prompt 6× faster than llama.cpp but re-read
  the whole conversation on every Inkling turn. llama.cpp reads slowly once, then answers follow-ups in ~30 s. The
  engine checkpoint in [strata-prompt-cache](strata-prompt-cache.md) cut a 120K follow-up's prompt read from ~190 s
  to ~0.4 s.
