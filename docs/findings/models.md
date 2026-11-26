# Which local model for coding on a 48 GB Mac?

**Answer as of 2026-11-26.** All models ran on [Splash](runtimes.md) 1.7.2 (1.7.3 where marked) on an M5 Pro (20-core GPU, 48 GB), with
the same prompts, graders and agent task ([methodology](../methodology.md)). Setup: [guides/splash](../guides/splash.md).

**How far to trust the quality numbers.** Speed differences of 2× or more repeat across runs. Quality numbers don't
yet: the issue counts come from one private project, graded by keywords, with 1–2 runs per setup, and the same build
has scored 3 then 5 issues, or 9/9 then 3/9 commit checks, in back-to-back runs. Treat differences of 1–2 issues,
or a single missed commit, as noise. The mini-eval, security check and long session are saturated (nearly every
model aces them). A public bug-fix suite with hidden upstream tests and repeated runs is being built to rank quality.

| Use | Pick | Why |
|---|---|---|
| Long agent sessions and thorough review | **Qwen3.8-Flash-Next**: Swift-1.5 Q2_0 (66.5 GB), ISTA Q2_0 (66 GB) or Coder (58 GB) | All 4 bugs fixed in the 213K-token long session (Swift-1.5 and ISTA Q2_0). Swift-1.5: 20 min for it, 120 tok/s at a 250K prompt. ISTA Q2_0: 23 min, 104 tok/s, 8 of 8 issues in both Cline runs. Coder: 7 of 8, 18/18 on security |
| Long sessions in the pi harness, fastest | **Qwen3.8-27B-pi-adapted** (Q4_K_M, 15 GB), thinking off | All 4 long-session bugs in 8.6 min, less than half Flash-Next's 20–23 min: far fewer steps (57 requests, 15K tokens written; Swift-1.5: 169, 106K). Trained for pi: the base 27B took 14.5 min and twice the requests. Reviews weaker: 4–5 of 8 issues. One run |
| Fast agent for short tasks | **KAT-Ornith-HERO-35B-A3B** (i1-Q4_K_M, 21.7 GB) | 235 tok/s. Only fast model with 6 of 8 issues in both Cline runs (52–79 s). 145 tok/s at a 250K prompt |
| Dense model, contexts under ~64K | **Qwen3.8-27B GSQ-RCO IQ3_S** (11.8 GB) | 96 tok/s, Cline 154 s with 5 issues, 75 tok/s at 100K; 13 min to read a 250K prompt. Ternary Bonsai 2.5 (7.5 GB) decodes faster (145 tok/s) and finds as many issues, but thinks longer: Cline 268 s |
| Quick edits and commits | **Flint** or **Qwopus3.6-Coder** | Cline sessions of 42–63 s, but 1–4 issues |
| Fewer refusals | **HauhauCS Qwen3.6-35B-A3B Aggressive** | 242 tok/s, security score equal to the best coders |
| Inkling-2-Mini | **Lucebox Inkling-2-Mini-Fast UD-Q8_K_XL** (22.9 GB), thinking on | A fine-tune that thinks about a quarter as long: Cline in 75–83 s instead of base's 361 s, mini-eval 10/10 in 38 s instead of 9/10 in 180 s. Q8 passed 9/9 commit checks in all 4 sessions, where the 4-bit builds skipped the commit in 4 of 10 (few runs: could be chance); reviews 4–5 of 8, no better than base. For chat, IQ4_NL-16GB is faster (142 vs 107 tok/s wall-clock) ([finding 16](#findings)) |

## Results

| Column | Meaning |
|---|---|
| Decode | tok/s from `bench/speed/oai_bench.py`, 3 prompts × 2 runs, `reasoning_effort: none`. Wall-clock (`bench/speed/raw_decode.py`) in brackets where measured |
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
| Inkling-2-Mini UD-Q4_K_M, thinking on (Splash 1.7.3) | 92 (97) | 10/10 | 361 s · 9/9 · 5 | 211 s · 9/9 · 5 | — | — |
| **Inkling-2-Mini-Fast IQ4_NL** (Lucebox, 17.6 GB), thinking on (Splash 1.7.3) | 101 (122) | 10/10 | 102 s · 9/9 · **7** | 43 s · 3/9§ · 2 | — | — |
| same, thinking off | | | 58 s · 3/9§ · 5 | 35 s · 8/9 · 4 | — | — |
| **Inkling-2-Mini-Fast IQ4_NL-16GB** (all IQ4_NL, 15 GB), thinking on (Splash 1.7.3) | 122 (142) | 9/10 | 71 / 63 s · 9/9, 3/9§ · 3, 5 | 34 / 61 s · 3/9§, 9/9 · 4, 2 | — | — |
| same, thinking off | | | 37 s · 8/9 · 4 | 53 s · 8/9 · 3 | — | — |
| **Inkling-2-Mini-Fast UD-Q8_K_XL** (22.9 GB), thinking on (Splash 1.7.3) | 84 (107) | 10/10 | 83 / 75 s · 9/9, 9/9 · 4, 4 | 66 / 70 s · 9/9, 9/9 · 4, 5 | — | — |
| **Qwen3.8-27B GSQ-RCO IQ3_S** (11.8 GB), thinking off | 96 (107) | 9/10 | 154 s · 9/9 · 5 | 54 s · 8/9 · 5 | 16/18 · 3/3 | 512 / 75 · 8/8 |
| Ternary Bonsai 2.5 27B PQ2_0 (7.5 GB), thinking budget 8K | 145 (160) | 9/10 | 268 s · 9/9 · 5 | 176 s · 9/9 · 4 | 16/18 · 3/3 | 400 / 99 · 8/8 |
| Qwen3.8-27B (base, no adapter) Q4_K_M, thinking off | 85 | 10/10 | — | 64 s · 8/9 · 3 | — | — |
| Qwen3.8-27B-pi-adapted Q4_K_M, thinking off | 90 | 10/10 | 228 / 169 s · 7/9, 8/9 · 4, 5 | 57 / 143 s · 7/9, 7/9 · 5, 5 | — | — |
| Qwen3.8-27B-think-pi-adapted Q4_K_M, thinking budget 8K | 89 (99) | 10/10 | 245 s · 9/9 · 5 | 128 s · 9/9 · 4 | — | — |
| Qwen3.8-27B TURBO-Fable (DavidAU) Q4_K_M, thinking off | 21 | 10/10 | — | — | — | — |
| Ornith-1.5-122B UD-IQ3_XXS (49.5 GB), 24 GB expert store | 44 | 7/10 | 249 s · 9/9 · 4 | 141 s · 8/9 · 4 | — | — |

† Splash returned one tool call as text, so the commit turn ended without running it.
‡ The model stopped to ask for a git identity instead of setting one.
§ Answered the commit turn without committing.

Outside Splash, Qwen3.8-27B 4-bit with Tencent's DSpine drafter found the most issues at short context (Cline 166 s ·
9/9 · 7, pi 115 s · 8) but decoded at 18 tok/s at 100K ([runtimes](runtimes.md)).

Models Splash doesn't serve, on llama.cpp (thinking budget 8K, the model cards' sampling, `--min-p 0`):

| Model | Decode | Mini-eval | Cline | pi | Security | 100K |
|---|---:|---|---|---|---|---|
| Kolibri 1.1 (75B MoE, 3.4B active) Q3_K_M (36 GB), llama.cpp PR #32891 | 69 (69) | 10/10 | 337 s · 8/9 · 3 | 211 s · 8/9 · 4 | 16/18 · 3/3 | 584 / 49 · 8/8 |
| Kolibri 1.1 GSQ-RCO IQ2_XS (2.25 bpw, 21 GB), llama.cpp PR #32891 | 68 (67) | 10/10 | 309 s · 7/9 · 1 | 307 s · 9/9 · 2 | 16/18 · 3/3 | 614 / 48 · 8/8 |
| Ternary Bonsai 2.5 27B Q2_0 + MTP head (7.9 GB) | 31 (31) | 9/10 | 650 s · 9/9 · 4 | 244 s · 7/9 · 5 | 16/18 · 3/3 | 217 / 15 · 8/8 |

Engine stats per run (`tools/session_stats.py`; decode peak / token-weighted mean tok/s, prefix-cache hit):

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
   finding 2). pi-adapted committed the local config folder in 3 of 4 sessions. Its thinking counterpart, think-pi-adapted
   (released 2026-11-23), passed 9/9 checks in both harnesses but found no more issues (4–5 of 8).
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
14. **Every model tested fixed all 4 long-session bugs; the pi-trained 27B was fastest.** In the [long session](../../bench/long_session/README.md) (Rich
    14.3.4: read 9 modules, fix 4 real bugs, commit; pi on Splash, 256K context), all six models fixed all 4 bugs as
    judged by upstream's own regression tests, added tests, broke none, and committed only source and test files:

    | Model | Session | Bugs fixed | Tests added | Largest prompt | Prompt from cache | Decode mean |
    |---|---|---|---|---|---|---|
    | Qwen3.8-27B-pi-adapted Q4_K_M, thinking off | **515 s** | **4/4** | 4 | 107K (TTFT 0.8 s, 46 tok/s) | 98% | 53 tok/s |
    | KAT-Ornith-HERO-35B-A3B i1-Q4_K_M, thinking budget 8K | 566 s | **4/4** | 5 | 128K (TTFT 0.8 s, 109 tok/s) | 97% | 134 tok/s |
    | same, through oMLX + Splash | 754 s | **4/4** | 6 | 172K (TTFT 0.2 s, 109 tok/s) | 99% | 121 tok/s |
    | Qwen3.8-27B base (no adapter) Q4_K_M, thinking off | 872 s | **4/4** | 4 | 136K (TTFT 0.9 s, 47 tok/s) | 99% | 54 tok/s |
    | Qwen3.8-27B-think-pi-adapted Q4_K_M, thinking budget 8K | 1,037 s | **4/4** | 5 | 128K (TTFT 1.0 s, 43 tok/s) | 98% | 46 tok/s |
    | Swift-1.5 Flash-Next Q2_0 | 1,202 s | **4/4** | 7 | — | 97% | 86 tok/s |
    | ISTA Flash-Next Q2_0 | 1,367 s | **4/4** | 23 | 213K (TTFT 0.9 s, 90 tok/s) | 99% | 79 tok/s |

    The 27B models decode at half Flash-Next's speed at depth, yet finished first because they did less: pi-adapted
    made 57 requests and wrote 15K tokens, Swift-1.5 169 requests and 106K tokens. Both read all 9 modules in full;
    Flash-Next also read three related modules, which is why its context reached 213K. With 98% of each prompt
    reused, the 27B's slow prompt read (13 min at 250K) never came into play. pi-adapted was trained in pi, the
    harness used here; in Cline it took 169–228 s for the 3-turn task.

    **The adapter halves the steps, not the result.** The base Qwen3.8-27B, requantized the same way (Q8_0 to
    Q4_K_M), also fixed 4/4 but made 122 requests and 121 tool calls, against pi-adapted's 57 and 59, and took 872 s
    against 515 s. Decode speed was the same (54 vs 53 tok/s). In the 3-turn task the base found 3 of 8 issues and
    committed the local config folder; pi-adapted found 4–5.

    Swift-1.5 (ukisai's coding- and agent-tuned Flash-Next, card: 63% fewer thinking tokens) was 12% faster here and
    decodes 15% faster at a 250K prompt (120 vs 104 tok/s); in Cline it found 7 of 8 issues with 9/9 checks. One run
    each. Its card calls Q2_0 experimental and recommends IQ2_XS (68 GB) for quality. Swift's largest prompt is not
    separable from its 250K test in the shared server log. The task no longer separates models on quality: all six
    scored 4/4. KAT-Ornith, the fastest decoder, was second (566 s): fast tokens help when the steps stay few.
15. **LiveCodeBench (partial): the 32K answer limit is binding.** KAT-Ornith on the 51 problems of February 2025
    (release_v6, EvalScope 1.15.0, thinking on, temperature 0.6), stopped at 44: 22 passed. All 18 answers that hit
    the 32K limit failed, 13 of them hard problems; of the 26 that finished, 22 passed. A fair run needs a 64–96K
    answer limit. Raw data: [results/livecodebench](../../results/livecodebench/).
16. **Inkling-2-Mini-Fast keeps the answers and cuts the thinking.** Lucebox fine-tuned Inkling-2-Mini to reason
    concisely (card: half the tokens, 2× faster, same or better accuracy). On Splash 1.7.3 with thinking on, back to
    back on an idle Mac:

    | Thinking on | Base UD-Q4_K_M | Fast IQ4_NL | Fast IQ4_NL-16GB | Fast UD-Q8_K_XL |
    |---|---|---|---|---|
    | Wall-clock decode | 97 tok/s | 122 | 142 | 107 |
    | Mini-eval | 9/10 · 180 s · 27.3K tokens | 10/10 · 31 s · 3.8K | 10/10 · 26 s · 3.5K | 10/10 · 38 s · 3.8K |
    | Long answer (reasoning tokens) | 61 s (5,180) | 17 s (824) | 13 s (260) | 20 s (628) |
    | Cline | 361 s · 9/9 · 5 | 102 s · 9/9 · 7 | 71 / 63 s · 9/9, 3/9 · 3, 5 | 83 / 75 s · 9/9, 9/9 · 4, 4 |
    | pi | 211 s · 9/9 · 5 | 43 s · 3/9 · 2 | 34 / 61 s · 3/9, 9/9 · 4, 2 | 66 / 70 s · 9/9, 9/9 · 4, 5 |
    | Tokens written, whole first run | 90.7K | 25.1K | 23.4K | 22.7K |

    With thinking on, Fast runs agent sessions 3–6× faster than base and about as fast as base with thinking off
    (72 / 70 s). Base still reasons with `reasoning_effort: none` (1,557 tokens on the long answer; Fast: 134).
    Reviews didn't improve: 2–7 of 8 issues against base's 4–6. The 4-bit builds skipped the commit in 4 of 10
    sessions (thinking on or off, Cline and pi); base UD-Q4_K_M committed in all of its 4. UD-Q8_K_XL passed
    9/9 checks in all 4 of its sessions (two Cline, two pi), 4–5 issues each time, at 107 tok/s wall-clock and 66–83 s per
    session. That is a hint, not a result: 0 misses in 4 against 4 in 10 happens by chance about 1 time in 5
    (Fisher's exact test, p = 0.21). The all-IQ4_NL 16GB build is the fastest (142 tok/s) for chat and single
    answers. Base and IQ4_NL: one run each; 16GB and Q8: two agent runs.

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
| Inkling-2-Mini-Fast | `Lucebox/Inkling-2-Mini-Fast-GGUF` (UD-Q8_K_XL, IQ4_NL, IQ4_NL-16GB), drafter `incoai/Inkling-2-Mini-DFlash2` |
| Ternary Bonsai 2.5 27B | `prism-ml/Ternary-Bonsai-2.5-27B-GGUF` (`PQ2_0-mtp` for Splash, `Q2_0-mtp` for llama.cpp), drafter `incoai/Qwen3.8-27B-DFlash2` |
| Kolibri 1.1 | `Aleph-Alpha/Kolibri-1.1-GGUF` (Q3_K_M, IQ2_XS-GSQ-RCO-2.25bpw); needs llama.cpp PR #32891 |
| Qwen3.8-27B-pi-adapted | requantized here from its published Q8_0 merge to Q4_K_M (no imatrix) |
| Qwen3.8-27B (base) | `ggml-org/Qwen3.8-27B-GGUF`, requantized here from Q8_0 to Q4_K_M (no imatrix), as the adapters |
| Qwen3.8-27B-think-pi-adapted | `harness-hub/Qwen3.8-27B-think-pi-adapted-GGUF`, requantized here from its Q8_0 merge to Q4_K_M (no imatrix); the card recommends Q8_0 |
| TURBO-Fable | DavidAU (Q4_K_M; the card recommends Q6 and calls Q4_K_M the minimum) |

Raw data: [results/](../../results/). First write-ups: [splash](../archive/2026-11-24-splash.md),
[model-sweep](../archive/2026-11-24-model-sweep.md).
