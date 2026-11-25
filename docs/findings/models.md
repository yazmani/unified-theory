# Which local model for coding on a 48 GB Mac?

**Current answer (2026-11-25).** Every model below ran on [Splash](runtimes.md) 1.7.2, the fastest runtime here, on
an M5 Pro (20-core GPU) with 48 GB. Same prompts, graders and agent task for every row ([methodology](../methodology.md)).
How to run them: [guides/splash](../guides/splash.md).

| Use | Pick | Why |
|---|---|---|
| Everyday coding agent | **KAT-Ornith-HERO-35B-A3B** (i1-Q4_K_M, 21.7 GB) | 235 tok/s; the only fast model that found 6 of 8 issues in Cline in both runs (52–79 s) |
| Thorough review, time no object | **Qwen3.8-Flash-Next GSQ-RCO**: Q2_0 (66 GB, experts streamed from the SSD) or the expert-pruned Coder (58 GB, fits in memory) | Q2_0 found all 8 issues in both Cline runs; the Coder found 7 in Cline and in pi and scored 18/18 on the security check. Both 130 tok/s, 170–350 s per session |
| Dense 27B | **Qwen3.8-27B GSQ-RCO IQ3_S** (11.8 GB) | 96 tok/s, 154 s Cline · 9/9 · 5, and 75 tok/s at 100K: the best 27B setup here |
| Quick edits and commits | **Flint** or **Qwopus3.6-Coder** | 42–63 s Cline sessions, but only 1–4 issues found |
| If refusals get in the way | **HauhauCS Qwen3.6-35B-A3B Aggressive** | as good as the best coders on the [security check](security-review.md), 242 tok/s |
| Inkling-2-Mini | **UD-Q4_K_M** | same speed as UD-IQ4_XS (109 tok/s wall-clock), higher precision |

## Results

**Decode:** `bench/oai_bench.py`, 3 prompts × 2 runs, `reasoning_effort: none`. **Mini-eval:** 10 small Python
tasks. **Cline / pi:** the 3-turn agent session (*explain the changes → commit them → suggest improvements*): total
time · commit checks of 9 · real issues found of 8. **Security:** planted flaws found of 18 · clean snippets judged
clean of 3. **100K:** prefill / decode tok/s at 99K tokens of context · facts recalled of 8.
Two numbers in a cell are two runs.

### Qwen3.6-35B-A3B family (Ornith, Tiel and fine-tunes; drafter `Qwen3.6-35B-A3B-DFlash2`, thinking budget 8K)

| Model | Decode tok/s | Mini-eval | Cline | pi | Security | 100K |
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

| Model | Decode tok/s | Mini-eval | Cline | pi | 100K |
|---|---:|---|---|---|---|
| **Qwen3.8-Flash-Next GSQ-RCO Q2_0**, 20 GB expert store, thinking budget 8K | 129 (130 wall-clock) | 8/10 | 280 s · 7/9 · **8** | — | 1,196 / 127 · 8/8 |
| same, 14 GB expert store | 96 | 9/10 | 348 s · 9/9 · **8** | 204 s · 9/9 · 7 | — |
| **Qwen3.8-Flash-Next GSQ-RCO Coder** (256 of 512 experts, 58 GB, all in memory), thinking budget 8K | 124 (130 wall-clock) | 9/10 | 327 s · 8/9 · 7 | 171 s · 9/9 · 7 | 1,210 / 119 · 8/8 |
| Flint UD-Q4_K_XL (40B MoE, ~2.5B active), thinking budget 8K | 139 | 10/10 | **63 s** · 8/9 · 4 | 88 s · 9/9 · 1 | — |
| Inkling-2-Mini UD-IQ4_XS, thinking off | 101 (109–116 wall-clock) | 10/10 | 94 / 75 s · 9/9, 3/9† · 6, 6 | 60 s · 3/9‡ · 4 | 1,213 / 99 · 8/8 |
| Inkling-2-Mini UD-Q4_K_M, thinking off | 92 (109 wall-clock) | 10/10 | 72 s · 9/9 · 4 | 70 s · 9/9 · 6 | 1,218 / 96 · 8/8 |
| **Qwen3.8-27B GSQ-RCO IQ3_S** (11.8 GB), thinking off | 96 (107 wall-clock) | 9/10 | 154 s · 9/9 · 5 | 54 s · 8/9 · 5 | 512 / 75 · 8/8 |
| Qwen3.8-27B-pi-adapted Q4_K_M, thinking off | 90 | 10/10 | 228 / 169 s · 7/9, 8/9 · 4, 5 | 57 / 143 s · 7/9, 7/9 · 5, 5 | — |
| Qwen3.8-27B TURBO-Fable (DavidAU) Q4_K_M, thinking off | 21 | 10/10 | — | — | — |
| Ornith-1.5-122B UD-IQ3_XXS (49.5 GB), 24 GB expert store | 44 | 7/10 | 249 s · 9/9 · 4 | 141 s · 8/9 · 4 | — |

† Splash returned one tool call as text, so the commit turn ended without running it.
‡ The model stopped to ask for a git identity instead of setting one.

Off Splash, the most thorough short-context setup was Qwen3.8-27B 4-bit with Tencent's DSpine drafter: 90 tok/s,
Cline 166 s · 9/9 · **7**, pi 115 s · **8**, but 18 tok/s at 100K ([runtimes](runtimes.md)).

Session stats over each model's whole run (decode peak / token-weighted mean, prefix-cache hit), from
`bench/session_stats.py`: KAT-Ornith 320 / 205 tok/s, 67%; Tiel 337 / 160, 88%; KAT-Coder 327 / 182, 62%;
AgentWorld 315 / 178, 74%; Qwopus 398 / 284, 63%; Distill 352 / 195, 67%; HauhauCS 333 / 220, 73%; RavenX 426 / 296,
69%; Cyber-Tiel 291 / 149, 81%.

## Findings

1. **KAT-Ornith-HERO is the everyday pick.** Tiel-Coder is a fine-tune of Ornith-1.5-35B-A3B, so every Ornith-35B
   model runs on the same Splash drafter. KAT-Ornith-HERO (a merge of KAT-Coder-V2.5, Ornith-1.5 and HERO-35B-A3B)
   is faster and more thorough than Tiel. In pi it was quick (26–35 s) but found 3 issues and committed the local
   config folder. The others in the family are as fast or faster but find 1–4 issues; Qwen's own AgentWorld found 1
   in each harness.
2. **Qwen3.8-Flash-Next is the most thorough model, and it fits by streaming.** The 66 GB Q2_0 file decodes at 96
   tok/s with 42% of its routed experts in a 14 GB store and 129 tok/s with 61% in 20 GB; the 28.8 GB n-gram table
   streams from the SSD too. It found all 8 issues in both Cline runs, a first on this task, but writes more, so
   sessions take 4–5× longer. Run 2 left the new files out of the commit (7/9).
3. **The Flash-Next Coder ties Q2_0 at a smaller size.** ISTA-DASLab removed half of the routed experts, keeping the
   ones that code, tool use and vision need. All 24.6 GB of its experts fit in memory, so it needs no
   `--expert-memory` cap, but it isn't faster: 130 tok/s wall-clock for both. It found 7 of 8 issues in Cline and in
   pi (Q2_0: 8 and 7), ran pi faster (171 vs 204 s), and scored 18/18 on the security check (Q2_0: 17;
   AgentWorld also 18). One Cline run each so far, so the 7-vs-8 gap is within noise.
4. **Flint is the fastest model in an agent, but shallow.** 63 s in Cline and 0.5 s to first token, but 4 and 1 issues
   found, it committed the local config folder, and it ignores `reasoning_effort: none` (5,665 thinking tokens on the
   long answer).
5. **Ornith-1.5-122B doesn't pay for its size on 48 GB.** 44 tok/s with 58% of its experts in memory, 3 logic-bug
   failures on the mini-eval, 4 of 8 issues in both harnesses: slower than Flash-Next and less thorough.
6. **ISTA-DASLab's GSQ-RCO IQ3_S is the best Qwen3.8-27B here.** At 11.8 GB (against ~17 GB for Q4_K_M) it decodes
   at 96 tok/s (107 wall-clock), ran Cline in 154 s with 9/9 and 5 issues and pi in 54 s, and holds 75 tok/s at 100K,
   where DSpine's 4-bit 27B drops to 18. The smaller file reads less memory per token, which outweighs the extra
   cost of decoding IQ formats on this dense model. In pi it committed the local config folder.
7. **Of the Qwen3.8-27B fine-tunes, pi-adapted wins**: 90 vs 21–24 tok/s, more checks and issues. DavidAU's
   TURBO-Fable is slow on Splash because it no longer matches the drafter ([runtimes](runtimes.md) finding 2). Both
   27Bs are dense, so long agent turns cost more than on the 35B-A3B MoEs. pi-adapted committed the local config
   folder in 3 of 4 sessions.
8. **Uncensored and security-tuned builds don't review code better** ([security-review](security-review.md)).
   RavenX, despite its branding, found 0 issues in the Cline review.
9. **Every model committed without asking** under auto-approve, and several committed a local config folder. Keep
   command auto-approval off on real projects, especially with abliterated models.
10. **The mini-eval is too easy to rank models** (almost everything 9–10/10). It only shows a fast setting doesn't
   write broken code; the agent session separates models.

Before Splash (2026-11-23), Inkling-2-Mini on a patched Strata (105–119 s per Cline session) and Tiel-Coder on
llama.cpp with MTP (142–168 s, 7 of 8 issues once) were the best agent setups; see the
[archived agent-models page](../archive/2026-11-23-agent-models.md) for those runs and the llama.cpp settings that
mattered (MTP n-max 1, a reasoning budget).

## Models

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
| Qwen3.8-27B-pi-adapted | requantized here from its published Q8_0 merge to Q4_K_M (no imatrix) |
| TURBO-Fable | DavidAU (Q4_K_M; the card recommends Q6 and calls Q4_K_M the minimum) |

Raw data: [results/](../../results/). The pages these results first appeared on:
[splash](../archive/2026-11-24-splash.md), [model-sweep](../archive/2026-11-24-model-sweep.md).
