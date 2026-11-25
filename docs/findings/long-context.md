# Long context on 48 GB: how deep can local models go, and how fast?

**Answer as of 2026-11-25:** every model tested recalled 8 of 8 hidden facts at 99–240K tokens. On Splash, the
Qwen3.6-35B-A3B models read 100K tokens in ~56 s and decode at 160–223 tok/s at that depth. Inkling-2-Mini ran to
240K on Strata. At depth, agent speed depends on whether follow-up turns reuse the prompt.

Script: `bench/long_context.py`: a haystack of real source code sized with the model's tokenizer, with 8 constants
hidden at 5–95% depth. Raw data: [results/long-context](../../results/long-context/).

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
