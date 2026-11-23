# Long context: does Inkling-2-Mini really go to 128K / 256K on 48 GB?

**Measured:** 2026-11-22. Script: `bench/long_context.py` (haystack of real source code from a Strata checkout,
sized with Inkling's tokenizer, 8 hidden constants at 5–95% depth). Raw data: [results/long-context](../../results/long-context/).

| Engine | Prompt | Prefill | Decode | Needles | Follow-up turn at same context |
|---|---|---|---|---|---|
| Strata SQ-15, `--context 256k` | 30K | 973 tok/s (31 s) | 63 tok/s | 8/8 | not run |
| Strata SQ-15 | 120K | 629 tok/s (189 s) | 27.5 tok/s | 8/8 | **204 s: re-reads everything (cached 0)**, correct |
| Strata SQ-15 | 240K | 428 tok/s (554 s) | 19.2 tok/s | 8/8 | identical repeat: 554 s again, cached 0 |
| Unsloth llama.cpp IQ4_XS + DSpark n=3, `-c 131072`, effort none | 120K | **103 tok/s (1217 s)** | 23.8 tok/s | 8/8 | **32 s: 118,939 of 119,136 cached**, correct |

## Findings

- **Context really goes long.** 1M is the engine's maximum (`MAX_CONTEXT = 1048576`); Strata's menu offers up to 256K.
- **Memory at 256K on Strata:** KV 8,352 MiB, engine total 26.52 GiB (SQ-15). The KV is full precision (fp16
  sizing). Estimated 1M: about 34.5 GB of KV alone, which doesn't fit a 48 GB Mac with anything else running.
- **Recall holds:** 8/8 at 30K, 120K and 240K on Strata, and 8/8 at 120K on llama.cpp.
- **Decode falls with depth on both engines:** Strata 63 → 27.5 → 19 tok/s; llama.cpp ~24 at 120K.
- **The real difference was caching.** Strata reads a long prompt 6× faster than llama.cpp, but (in 0.2.19) re-read
  the whole conversation on every turn for Inkling. llama.cpp reads slowly once, then answers follow-ups in ~30 s.
  That led to the fixes in [strata-prompt-cache.md](strata-prompt-cache.md): with the engine checkpoint, a 120K
  follow-up's prompt read went from ~190 s to ~0.4 s.
