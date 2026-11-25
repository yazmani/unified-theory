# Long context on 48 GB: how deep can local models go, and how fast?

**Current answer (2026-11-25):** every model tested recalled 8 of 8 hidden facts at 99–240K tokens. On Splash the
Qwen3.6-35B-A3B models read 100K tokens in ~56 s and still decode at 160–223 tok/s at that depth; Inkling-2-Mini
went to 240K on Strata. What decides agent speed at depth is whether follow-up turns reuse the prompt.

Script: `bench/long_context.py` (haystack of real source code, sized with the model's tokenizer, 8 hidden constants
at 5–95% depth). Raw data: [results/long-context](../../results/long-context/).

## 100K on Splash, oMLX and DSpine (2026-11-24)

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
| Qwen3.8-27B 4-bit + DSpine | dspine-hybrid-mlx | 416 (238 s) | 18 | 8/8 |

- **The Qwen3.6-35B-A3B models barely slow down at depth**: their linear-attention layers keep decode at 160–223
  tok/s at 99K. A dual RTX 5070 Ti user reported 5,400–6,400 tok/s prefill and 184 tok/s decode at 103K on Basalt:
  about 3× our prefill (memory bandwidth), but the same decode.
- **Dense and looped models pay at depth**: Inkling falls to ~97 tok/s, and Qwen3.8-27B to 75 tok/s on Splash and 18
  on DSpine (memory peaking at ~37 GB). The dense 27B also reads a 100K prompt 3× slower than the MoEs.
- **Flash-Next keeps ~120–127 tok/s at 100K** whether its experts stream from the SSD (Q2_0) or sit in memory (Coder).

## Inkling-2-Mini to 240K on Strata and llama.cpp (2026-11-22)

| Engine | Prompt | Prefill | Decode | Needles | Follow-up turn at same context |
|---|---|---|---|---|---|
| Strata SQ-15, `--context 256k` | 30K | 973 tok/s (31 s) | 63 tok/s | 8/8 | not run |
| Strata SQ-15 | 120K | 629 tok/s (189 s) | 27.5 tok/s | 8/8 | **204 s: re-reads everything (cached 0)**, correct |
| Strata SQ-15 | 240K | 428 tok/s (554 s) | 19.2 tok/s | 8/8 | identical repeat: 554 s again, cached 0 |
| Unsloth llama.cpp IQ4_XS + DSpark n=3, `-c 131072`, effort none | 120K | **103 tok/s (1217 s)** | 23.8 tok/s | 8/8 | **32 s: 118,939 of 119,136 cached**, correct |

### Findings

- **Context really goes long.** 1M is the engine's maximum (`MAX_CONTEXT = 1048576`); Strata's menu offers up to 256K.
- **Memory at 256K on Strata:** KV 8,352 MiB, engine total 26.52 GiB (SQ-15). The KV is full precision (fp16
  sizing). Estimated 1M: about 34.5 GB of KV alone, which doesn't fit a 48 GB Mac with anything else running.
- **Recall holds:** 8/8 at 30K, 120K and 240K on Strata, and 8/8 at 120K on llama.cpp.
- **Decode falls with depth on both engines:** Strata 63 → 27.5 → 19 tok/s; llama.cpp ~24 at 120K.
- **The real difference was caching.** Strata reads a long prompt 6× faster than llama.cpp, but (in 0.2.19) re-read
  the whole conversation on every turn for Inkling. llama.cpp reads slowly once, then answers follow-ups in ~30 s.
  That led to the fixes in [strata-prompt-cache.md](strata-prompt-cache.md): with the engine checkpoint, a 120K
  follow-up's prompt read went from ~190 s to ~0.4 s.
