# Which local model for coding on a 48 GB Mac?

**Answer as of 2026-11-25.** All models ran on [Splash](runtimes.md) 1.7.2 on an M5 Pro (20-core GPU, 48 GB), with
the same prompts, graders and agent task ([methodology](../methodology.md)). Setup: [guides/splash](../guides/splash.md).

| Use | Pick | Why |
|---|---|---|
| Long agent sessions and thorough review | **Qwen3.8-Flash-Next**: Swift-1.5 Q2_0 (66.5 GB), ISTA Q2_0 (66 GB) or Coder (58 GB) | All 4 bugs fixed in the 213K-token long session (Swift-1.5 and ISTA Q2_0). Swift-1.5: 20 min for it, 120 tok/s at a 250K prompt. ISTA Q2_0: 23 min, 104 tok/s, 8 of 8 issues in both Cline runs. Coder: 7 of 8, 18/18 on security |
| Fast agent for short tasks | **KAT-Ornith-HERO-35B-A3B** (i1-Q4_K_M, 21.7 GB) | 235 tok/s. Only fast model with 6 of 8 issues in both Cline runs (52–79 s). 145 tok/s at a 250K prompt |
| Dense model, contexts under ~64K | **Qwen3.8-27B GSQ-RCO IQ3_S** (11.8 GB) | 96 tok/s, Cline 154 s with 5 issues, 75 tok/s at 100K; 13 min to read a 250K prompt. Ternary Bonsai 2.5 (7.5 GB) decodes faster (145 tok/s) and finds as many issues, but thinks longer: Cline 268 s |
| Quick edits and commits | **Flint** or **Qwopus3.6-Coder** | Cline sessions of 42–63 s, but 1–4 issues |
| Fewer refusals | **HauhauCS Qwen3.6-35B-A3B Aggressive** | 242 tok/s, security score equal to the best coders |
| Inkling-2-Mini | **UD-Q4_K_M** | Same speed as UD-IQ4_XS (109 tok/s wall-clock), higher precision |

## Results

| Column | Meaning |
|---|---|
| Decode | tok/s from `bench/oai_bench.py`, 3 prompts × 2 runs, `reasoning_effort: none`. Wall-clock (`bench/raw_decode.py`) in brackets where measured |
| Mini-eval | 10 small Python tasks passed |
| Cline, pi | 3-turn agent session (explain the changes, commit them, suggest improvements): total time · commit checks passed of 9 · issues found of 8 |
| Security | planted flaws found of 18 · clean snippets judged clean of 3 |
| 100K | prefill / decode tok/s at 99K tokens of context · facts recalled of 8 |

Two values in a cell are two runs. — means not run.

### Qwen3.6-35B-A3B family (drafter `Qwen3.6-35B-A3B-DFlash2`, thinking budget 8K)

| Model | Decode | Mini-eval | Cline | pi | Security | 100K |
|---|---:|---|---|---|---|---|
| **KAT-Ornith-HERO fusion** | 235 | 9/10 | **79 / 52 s · 8/9, 9/9 · 6, 6** | 26 / 35 s · 8/9, 7/9 · 3, 3 | 17/18 · 3/3 | 1,757 / 160 · 8/8 |
| Ornith-1.5-35B-A3B (official) | 219 | 7/10 | 86 s · 8/9 · 4 | 28 s · 7/9 · 5 | — | — |
| Tiel-Coder (Ornith fine-tune) | 191 | 9/10 | 101 / 94 s · 9/9, 8/9 · 6, 2 | 36 s · 8/9 · 4 | 17/18 · 3/3 | 1,756 / 187 · 8/8 |
| Kwaipilot KAT-Coder-V2.5-Dev | 206 | 9/10 | 82 s · 9/9 · 4 | 32 s · 3 | 17/18 · 3/3 | 1,755 / 180 · 8/8 |
| Qwen-AgentWorld-35B-A3B | 220 | 9/10 | 73 s · 9/9 · 1 | 36 s · 1 | **18/18** · 3/3 | 1,783 / 199 · 8/8 |
| Qwopus3.6-35B-A3B-Coder | **244** | 9/10 | **45 s** · 8/9 · 3 | 48 s · 1 | 16/18 · 3/3 | 1,753 / 190 · 8/8 |
| Qwen3.8-35B-A3B-Distill (empero) | 229 | 9/10 | 86 s · 8/9 · 3 | 31 s · 2 | 16/18 · 2/3 | 1,756 / 171 · 8/8 |
| HauhauCS Aggressive (uncensored) | 242 | 9/10 | 50 s · 8/9 · 4 | 40 s · 2 | 17/18 · 3/3 | 1,770 / **223** · 8/8 |
| RavenX-CyberAgent (security-tuned) | 174 | 10/10 | 42 s · 7/9 · 0 | 21 s · 2 | 17/18 · 3/3 | — |
| Cyber-Tiel (abliterated Tiel) | 194 | 9/10 | 88 s · 8/9 · 5 | 42 s · 5 | 17/18 · 3/3 | 1,769 / 206 · 8/8 |

### Other families

| Model | Decode | Mini-eval | Cline | pi | Security | 100K |
|---|---:|---|---|---|---|---|
| **Qwen3.8-Flash-Next GSQ-RCO Q2_0**, 20 GB expert store, thinking budget 8K | 129 (130) | 8/10 | 280 s · 7/9 · **8** | — | 17/18 · 3/3 | 1,196 / 127 · 8/8 |
| same, 14 GB expert store | 96 | 9/10 | 348 s · 9/9 · **8** | 204 s · 9/9 · 7 | — | — |
| **Swift-1.5 Qwen3.8-Flash-Next GSQ-RCO Q2_0** (ukisai, 66.5 GB), 20 GB expert store, thinking budget 8K | 125 (134) | 10/10 | 352 s · 9/9 · 7 | — | — | 250K: 1,115 / 120 · 8/8 |
| **Qwen3.8-Flash-Next GSQ-RCO Coder** (256 of 512 experts, 58 GB, all in memory), thinking budget 8K | 124 (130) | 9/10 | 327 s · 8/9 · 7 | 171 s · 9/9 · 7 | **18/18** · 3/3 | 1,210 / 119 · 8/8 |
| Flint UD-Q4_K_XL (40B MoE, ~2.5B active), thinking budget 8K | 139 | 10/10 | **63 s** · 8/9 · 4 | 88 s · 9/9 · 1 | — | — |
| Inkling-2-Mini UD-IQ4_XS, thinking off | 101 (109–116) | 10/10 | 94 / 75 s · 9/9, 3/9† · 6, 6 | 60 s · 3/9‡ · 4 | — | 1,213 / 99 · 8/8 |
| Inkling-2-Mini UD-Q4_K_M, thinking off | 92 (109) | 10/10 | 72 s · 9/9 · 4 | 70 s · 9/9 · 6 | — | 1,218 / 96 · 8/8 |
| **Qwen3.8-27B GSQ-RCO IQ3_S** (11.8 GB), thinking off | 96 (107) | 9/10 | 154 s · 9/9 · 5 | 54 s · 8/9 · 5 | 16/18 · 3/3 | 512 / 75 · 8/8 |
| Ternary Bonsai 2.5 27B PQ2_0 (7.5 GB), thinking budget 8K | 145 (160) | 9/10 | 268 s · 9/9 · 5 | 176 s · 9/9 · 4 | 16/18 · 3/3 | 400 / 99 · 8/8 |
| Qwen3.8-27B-pi-adapted Q4_K_M, thinking off | 90 | 10/10 | 228 / 169 s · 7/9, 8/9 · 4, 5 | 57 / 143 s · 7/9, 7/9 · 5, 5 | — | — |
| Qwen3.8-27B TURBO-Fable (DavidAU) Q4_K_M, thinking off | 21 | 10/10 | — | — | — | — |
| Ornith-1.5-122B UD-IQ3_XXS (49.5 GB), 24 GB expert store | 44 | 7/10 | 249 s · 9/9 · 4 | 141 s · 8/9 · 4 | — | — |

† Splash returned one tool call as text, so the commit turn ended without running it.
‡ The model stopped to ask for a git identity instead of setting one.

Outside Splash, Qwen3.8-27B 4-bit with Tencent's DSpine drafter found the most issues at short context (Cline 166 s ·
9/9 · 7, pi 115 s · 8) but decoded at 18 tok/s at 100K ([runtimes](runtimes.md)).

Models Splash doesn't serve, on llama.cpp (thinking budget 8K, the model cards' sampling, `--min-p 0`):

| Model | Decode | Mini-eval | Cline | pi | Security | 100K |
|---|---:|---|---|---|---|---|
| Kolibri 1.1 (75B MoE, 3.4B active) Q3_K_M (36 GB), llama.cpp PR #32891 | 69 (69) | 10/10 | 337 s · 8/9 · 3 | 211 s · 8/9 · 4 | 16/18 · 3/3 | 584 / 49 · 8/8 |
| Kolibri 1.1 GSQ-RCO IQ2_XS (2.25 bpw, 21 GB), llama.cpp PR #32891 | 68 (67) | 10/10 | 309 s · 7/9 · 1 | 307 s · 9/9 · 2 | 16/18 · 3/3 | 614 / 48 · 8/8 |
| Ternary Bonsai 2.5 27B Q2_0 + MTP head (7.9 GB) | 31 (31) | 9/10 | 650 s · 9/9 · 4 | 244 s · 7/9 · 5 | 16/18 · 3/3 | 217 / 15 · 8/8 |

Engine stats per run (`bench/session_stats.py`; decode peak / token-weighted mean tok/s, prefix-cache hit):

| Model | Decode peak / mean | Cache hit |
|---|---|---|
| KAT-Ornith | 320 / 205 | 67% |
| Tiel | 337 / 160 | 88% |
| KAT-Coder | 327 / 182 | 62% |
| AgentWorld | 315 / 178 | 74% |
| Qwopus | 398 / 284 | 63% |
| Distill | 352 / 195 | 67% |
| HauhauCS | 333 / 220 | 73% |
| RavenX | 426 / 296 | 69% |
| Cyber-Tiel | 291 / 149 | 81% |

## Findings

1. **KAT-Ornith-HERO is the everyday pick.** It is a merge of KAT-Coder-V2.5, Ornith-1.5 and HERO-35B-A3B, and is
   faster and more thorough than Tiel-Coder. Its weak spot is pi: 3 issues, and it committed the local config
   folder. The other models in the family match its speed but find 1–4 issues (AgentWorld: 1 per harness).
2. **Flash-Next finds the most issues, and fits on 48 GB by streaming experts from the SSD.** Q2_0 (66 GB) decodes at
   96 tok/s with 42% of its routed experts in memory (14 GB) and 129 tok/s with 61% (20 GB). It found 8 of 8 issues
   in both Cline runs. Sessions take 4–5× longer than KAT-Ornith's because it writes more. Run 2 left the new files
   out of the commit (7/9).
3. **The Flash-Next Coder matches Q2_0 at 58 GB.** ISTA-DASLab removed half of the routed experts, keeping those that
   code, tool use and vision need. Its 24.6 GB of experts fit in memory, so it needs no `--expert-memory` cap. Speed
   is the same (130 tok/s wall-clock). It found 7 of 8 issues in Cline and in pi (Q2_0: 8 and 7), ran pi in 171 s
   (Q2_0: 204 s) and scored 18/18 on security (Q2_0: 17). The Coder has one run per harness, so the 7-vs-8 gap is
   within run-to-run noise.
4. **Qwen3.8-27B GSQ-RCO IQ3_S is the best 27B here.** At 11.8 GB (Q4_K_M: ~17 GB) it decodes at 96 tok/s, ran Cline
   in 154 s (9/9, 5 issues) and keeps 75 tok/s at 100K. Likely cause: the dense model reads less memory per token,
   which outweighs the slower IQ dequantization. In pi it committed the local config folder.
5. **Flint is the fastest model in an agent, and the shallowest.** Cline in 63 s, 0.5 s to first token, but 4 and 1
   issues. It committed the local config folder and ignores `reasoning_effort: none` (5,665 thinking tokens on the
   long answer).
6. **Ternary Bonsai 2.5 27B is fast on Splash, but no better than the 27B GSQ file.** On Splash its 7.5 GB `PQ2_0`
   file decodes at 145 tok/s (160 wall-clock; llama.cpp: 31). It found 5 and 4 issues, as many as the 27B GSQ, but
   thinks at `xhigh` effort by default (the card says `low` is ignored), so its sessions take longer: Cline 268 s
   (GSQ: 154 s). Splash rejects the `Q2_0` file ("the rotation's one token table must be token_embd.weight in
   PQ2_0"); use `PQ2_0`.
7. **Kolibri 1.1 is not a coding-agent pick.** 69 tok/s on llama.cpp (no drafter), a perfect mini-eval with few
   tokens, and 16/18 on security, but 1–4 of 8 issues in the agent review, and it committed the local config folder
   in 3 of 4 sessions. The 36 GB Q3_K_M pushed swap to 5.9 GB; the 21 GB GSQ-RCO file fits easily but found 1–2
   issues.
8. **Ornith-1.5-122B is not worth it on 48 GB.** 44 tok/s with 58% of its experts in memory, 3 failed mini-eval
   tasks, 4 of 8 issues in both harnesses.
9. **pi-adapted beats DavidAU's TURBO-Fable** among the Qwen3.8-27B fine-tunes: 90 vs 21–24 tok/s, more checks and
   issues. TURBO-Fable is slow on Splash because it no longer matches the drafter ([runtimes](runtimes.md),
   finding 2). pi-adapted committed the local config folder in 3 of 4 sessions.
10. **Uncensored and security-tuned builds review no better** ([security-review](security-review.md)). RavenX found 0
   issues in the Cline review.
11. **Every model committed without asking** under auto-approve, and several committed a local config folder. Turn off
   command auto-approval on real projects, especially with abliterated models.
12. **The mini-eval does not rank models.** Nearly all score 9–10/10. It only shows that a fast setting doesn't
    break code; the agent session separates models.
13. **For real agent work, Flash-Next is the pick at 256K.** The 3-turn agent task already sent 40–77K tokens per
    request, so longer sessions need 128K or more. At a 250K prompt Flash-Next keeps 81% of its decode speed (104
    tok/s) and KAT-Ornith 62% (145 tok/s); the 27B models take 13–15 min to read the prompt. Flash-Next's
    full-attention layers attend to ~2,048 indexer-picked tokens instead of all of them
    ([long-context](long-context.md#why-flash-next-holds-up-model-structure)).
14. **Flash-Next keeps working at 213K tokens.** In the [long session](../../bench/long_session/README.md) (Rich
    14.3.4: read 9 modules, fix 4 real bugs, commit; pi on Splash, 256K context), both Flash-Next files fixed all 4
    bugs as judged by upstream's own regression tests, added tests, broke none, and committed cleanly:

    | Model | Session | Bugs fixed | Tests added | Largest prompt | Prompt from cache | Decode mean |
    |---|---|---|---|---|---|---|
    | Swift-1.5 Flash-Next Q2_0 | **1,202 s** | **4/4** | 23 | — | 97% | 86 tok/s |
    | ISTA Flash-Next Q2_0 | 1,367 s | **4/4** | 23 | 213K (TTFT 0.9 s, 90 tok/s) | 99% | 79 tok/s |

    Swift-1.5 (ukisai's coding- and agent-tuned Flash-Next, card: 63% fewer thinking tokens) was 12% faster here and
    decodes 15% faster at a 250K prompt (120 vs 104 tok/s); in Cline it found 7 of 8 issues with 9/9 checks. One run
    each. Its card calls Q2_0 experimental and recommends IQ2_XS (68 GB) for quality. Swift's largest prompt is not
    separable from its 250K test in the shared server log.
15. **LiveCodeBench (partial): the 32K answer limit is binding.** KAT-Ornith on the 51 problems of February 2025
    (release_v6, EvalScope 1.15.0, thinking on, temperature 0.6), stopped at 44: 22 passed. All 18 answers that hit
    the 32K limit failed, 13 of them hard problems; of the 26 that finished, 22 passed. A fair run needs a 64–96K
    answer limit. Raw data: [results/livecodebench](../../results/livecodebench/).

Before Splash (2026-11-23), the best agent setups were Inkling-2-Mini on a patched Strata (105–119 s per Cline
session) and Tiel-Coder on llama.cpp with MTP (142–168 s, 7 of 8 issues once). Those runs and the llama.cpp settings
that mattered (MTP n-max 1, a reasoning budget) are on the [archived agent-models page](../archive/2026-11-23-agent-models.md).

## Model sources

| Model | Repo (file) |
|---|---|
| KAT-Ornith-HERO fusion | `mradermacher/KAT-Ornith-HERO-35B-A3B-Fusion-i1-GGUF` (i1-Q4_K_M) |
| Tiel-Coder | `peculiar-ragdoll/Tiel-Coder-35B-A3B` collection (UD-Q4_K_XL GGUF) |
| KAT-Coder-V2.5-Dev | `bartowski/Kwaipilot_KAT-Coder-V2.5-Dev-GGUF` (Q4_K_M) |
| Qwen-AgentWorld | `unsloth/Qwen-AgentWorld-35B-A3B-GGUF` (UD-Q4_K_M) |
| Qwopus3.6-Coder | `Jackrong/Qwopus3.6-35B-A3B-Coder-MTP-GGUF` (Q4_K_M) |
| Qwen3.8-35B-A3B-Distill | `empero-ai/Qwen3.8-35B-A3B-Distill-GGUF` (Q4_K_M) |
| HauhauCS Aggressive | `HauhauCS/Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive` (Q4_K_M) |
| RavenX-CyberAgent | `deadbydawn101/RavenX-CyberAgent-Qwen3.6-35B-A3B-…-GGUF` (Q4_K_M) |
| Cyber-Tiel | `peculiar-ragdoll/Cyber-Tiel-Coder-35B-A3B-GGUF-MTP` (UD-Q4_K_XL) |
| Qwen3.8-Flash-Next | `ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF`, folder `Q2_0` (37.6 + 28.8 GB) |
| Qwen3.8-Flash-Next Coder | `ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-Coder-GGUF`, folder `IQ1_M` (29.6 + 28.8 GB) |
| Qwen3.8-27B GSQ-RCO | `ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF` (IQ3_S, 11.8 GB), drafter `incoai/Qwen3.8-27B-DFlash2` |
| Inkling-2-Mini | Unsloth's Inkling-2-Mini GGUF (UD-Q4_K_M, UD-IQ4_XS) |
| Ternary Bonsai 2.5 27B | `prism-ml/Ternary-Bonsai-2.5-27B-GGUF` (`PQ2_0-mtp` for Splash, `Q2_0-mtp` for llama.cpp), drafter `incoai/Qwen3.8-27B-DFlash2` |
| Kolibri 1.1 | `Aleph-Alpha/Kolibri-1.1-GGUF` (Q3_K_M, IQ2_XS-GSQ-RCO-2.25bpw); needs llama.cpp PR #32891 |
| Qwen3.8-27B-pi-adapted | requantized here from its published Q8_0 merge to Q4_K_M (no imatrix) |
| TURBO-Fable | DavidAU (Q4_K_M; the card recommends Q6 and calls Q4_K_M the minimum) |

Raw data: [results/](../../results/). First write-ups: [splash](../archive/2026-11-24-splash.md),
[model-sweep](../archive/2026-11-24-model-sweep.md).
