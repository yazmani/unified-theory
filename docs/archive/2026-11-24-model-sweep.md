# Qwen3.6-35B coding models, security review, oMLX and DSpine

> **Archived snapshot.** Kept as measured on that date; the current answer is in [models](../findings/models.md), [runtimes](../findings/runtimes.md), [harnesses](../findings/harnesses.md) and [security-review](../findings/security-review.md).

**Measured:** 2026-11-24, M5 Pro (20-core GPU) 48 GB, plugged in. Same prompts, graders and agent task as the other
findings ([methodology](../methodology.md)). Raw data: [results/](../../results/).

Tiel-Coder, the fastest model in [splash](2026-11-24-splash.md), is a fine-tune of Ornith-1.5-35B-A3B, which is itself a
Qwen3.6-35B-A3B. Every model in that family runs on Splash's existing `Qwen3.6-35B-A3B-DFlash2` drafter at 175–245 tok/s,
so this page sweeps the family: coding fine-tunes, uncensored and security-tuned builds, and two other Mac runtimes
that people call fast (oMLX, and Tencent's DSpine drafter for Qwen3.8-27B).

## Results

All Splash rows: Q4 GGUF, `Qwen3.6-35B-A3B-DFlash2` drafter, thinking budget 8K, 128K context. "Cline" and "pi" are the
3-turn agent session: time, 9 commit checks, real issues found of 8 ([agent-models](2026-11-23-agent-models.md)). Security: the
new [security review check](#security-review-check). 100K: prefill / decode tok/s at 99K tokens of context, and how
many of 8 facts hidden in it the model recalled.

| Model | Engine | Decode tok/s | Mini-eval | Cline | pi | Security | 100K prefill / decode, recall |
|---|---|---:|---|---|---|---|---|
| **KAT-Ornith-HERO fusion** | Splash | 235 | 9/10 | **79 / 52 s · 8/9, 9/9 · 6, 6** | 26 / 35 s · 3, 3 | 17/18 · 3/3 | 1,757 / 160 · 8/8 |
| Tiel-Coder (Ornith fine-tune) | Splash | 191 | 9/10 | 101 / 94 s · 9/9, 8/9 · 6, 2 | 36 s · 4 | 17/18 · 3/3 | 1,756 / 187 · 8/8 |
| Kwaipilot KAT-Coder-V2.5-Dev | Splash | 206 | 9/10 | 82 s · 9/9 · 4 | 32 s · 3 | 17/18 · 3/3 | 1,755 / 180 · 8/8 |
| Qwen-AgentWorld-35B-A3B | Splash | 220 | 9/10 | 73 s · 9/9 · 1 | 36 s · 1 | **18/18** · 3/3 | 1,783 / 199 · 8/8 |
| Qwopus3.6-35B-A3B-Coder | Splash | **244** | 9/10 | **45 s** · 8/9 · 3 | 48 s · 1 | 16/18 · 3/3 | 1,753 / 190 · 8/8 |
| Qwen3.8-35B-A3B-Distill (empero) | Splash | 229 | 9/10 | 86 s · 8/9 · 3 | 31 s · 2 | 16/18 · 2/3 | 1,756 / 171 · 8/8 |
| HauhauCS Aggressive (uncensored) | Splash | 242 | 9/10 | 50 s · 8/9 · 4 | 40 s · 2 | 17/18 · 3/3 | 1,770 / **223** · 8/8 |
| RavenX-CyberAgent (security-tuned) | Splash | 174 | 10/10 | 42 s · 7/9 · 0 | 21 s · 2 | 17/18 · 3/3 | — |
| Cyber-Tiel (abliterated Tiel) | Splash | 194 | 9/10 | 88 s · 8/9 · 5 | 42 s · 5 | 17/18 · 3/3 | 1,769 / 206 · 8/8 |
| Tiel-Coder oQ4e-MTP | **oMLX** 0.8.3 | 126 | 9/10 | 85 s · 8/9 · 5 | 44 s · 3 | 18/18 · 3/3 | 1,451 / 112 · 8/8 |
| Inkling-2-Mini oQ4e-mtp, effort 0 | **oMLX** 0.8.3 | 55* | 10/10 | 370 s · 9/9 · 6 | 86 s · 4 | 17/18 · 3/3 | 682 / 24 · 8/8 |
| Qwen3.8-27B 4-bit + DSpine, T=0.6 | **dspine-hybrid-mlx** 0.4.0 | 90 | 10/10 | 166 s · 9/9 · **7** | 115 s · **8** | 17/18 · 3/3 | 416 / 18 · 8/8 |

\* Wall-clock (`bench/raw_decode.py`, non-streamed). The streamed benchmark reported 261 tok/s for this row: oMLX
releases Inkling's tokens in bursts, so the first-to-last-token window looked short. oMLX's own log agrees with 55.
The other oMLX and DSpine rows match between the two methods (Tiel 117 vs 126, DSpine 87 vs 90).

Session stats over each model's whole run (decode peak / token-weighted mean, prefix-cache hit), from
`bench/session_stats.py`: KAT-Ornith 320 / 205 tok/s, 67%; Tiel 337 / 160, 88%; KAT-Coder 327 / 182, 62%;
AgentWorld 315 / 178, 74%; Qwopus 398 / 284, 63%; Distill 352 / 195, 67%; HauhauCS 333 / 220, 73%; RavenX 426 / 296,
69%; Cyber-Tiel 291 / 149, 81%. Prefill on Splash peaks at 3,600–3,900 tok/s and holds ~1,760 tok/s at 99K.
Swap stayed under 7 GB for every Splash run.

## Findings

1. **KAT-Ornith-HERO is still the everyday pick.** It is the only fast model that found 6 of 8 issues in Cline in both
   runs. The other coders are as fast or faster (Qwopus 244 tok/s, a 45 s Cline session) but find 1–4 issues; Qwen's
   own AgentWorld found 1 in each harness.
2. **All Qwen3.6-35B models handle 100K of context well on Splash.** Every one recalled 8/8 facts at 99K tokens, with
   ~56 s of prefill (1,760 tok/s) and **160–223 tok/s decode at that depth**: the linear-attention layers barely slow
   down. A dual RTX 5070 Ti user reported 5,400–6,400 tok/s prefill and 184 tok/s decode at 103K on Basalt: about 3×
   our prefill (bandwidth), but the same decode.
3. **Uncensored and security-tuned builds don't review code better.** On the security check every model found 16–18
   of 18 planted flaws and nobody refused (the check is defensive). HauhauCS Aggressive matches the best coders there,
   runs at 242 tok/s and has the fastest decode at 100K, so it's a reasonable pick if refusals ever get in the way;
   RavenX, despite its security branding, found 0 issues in the Cline review and was the slowest of the batch.
4. **Splash beats oMLX on both models.** Tiel: 191 vs 126 tok/s (187 vs 112 at 100K). Inkling: 116 vs 55 tok/s
   wall-clock, and 682 / 24 tok/s at 100K on oMLX. oMLX's MTP is worth +24% (55 vs 44 tok/s with it off). In agent
   turns oMLX also throttles prefill under its memory guard and stores the prompt cache of this hybrid model in
   2,048-token blocks, so each turn re-reads 5–9K tokens at ~700 tok/s.
5. **oMLX needs thinking turned off on the server for agent work.** `chat_template_kwargs.enable_thinking=false`
   doesn't reach Inkling, and harness requests carry no thinking settings. Setting `"chat_template_kwargs":
   {"reasoning_effort": 0.0}` in oMLX's per-model settings took the Cline session from 532 s / 4 issues / pi 3/9 checks
   to 370 s / 6 issues / 9/9.
6. **DSpine is the most thorough short-context setup, but slow at depth.** Tencent's drafter for Qwen3.8-27B (the
   Mac support was merged upstream as [Tencent/DSpine#3](https://github.com/Tencent/DSpine/pull/3); the server comes
   from [dspine-hybrid-mlx](https://github.com/internet-projects/dspine-hybrid-mlx)) decodes at 90 tok/s here (its
   README shows 186 on an M5 Max, twice our bandwidth) and found 7 issues in Cline and 8 in pi. But 100K took 238 s of
   prefill and decoded at 18 tok/s, and memory peaked at ~37 GB (swap rose to ~10 GB).
7. **Don't run DSpine greedy.** Its server defaults to temperature 0, and in Cline one request looped for 32,000
   tokens until the turn timed out. With Qwen's sampling (`--temperature 0.6 --top-p 0.95 --top-k 20`) the same
   session took 166 s.

## Harnesses on Inkling: Splash vs oMLX

Same 3-turn session, same model (Inkling-2-Mini, thinking off), each harness against each engine. Time · commit checks
· issues found of 8.

| Engine (wall-clock decode) | Cline | OpenCode | Claude Code | pi |
|---|---|---|---|---|
| **Splash** (116 tok/s) | 75–94 s · 9/9 · 6 | 139 s · 9/9 · **6** | 139 s · 9/9 · 4 | **49 s** · 9/9 · 4 |
| oMLX, MTP (55 tok/s) | 370 s · 9/9 · 6 | 268 s · 8/9 · 5 | 168 s · 9/9 · 4 | 86 s · 9/9 · 4 |

- **The harness matters 2–5×, the engine on top of that.** pi is the fastest on both engines; Cline is the slowest on
  oMLX. Splash is faster in every harness (1.2–4×).
- **OpenCode is no longer the fastest.** It was on Strata ([agent-harnesses](../findings/harnesses.md), 66 s), but it sends
  the largest prompts (223–323K prompt tokens over the session, against 53K for pi), so on engines with fast decode
  and working prompt reuse pi wins. OpenCode and Cline found the most issues (6).

## Security review check

`bench/security_review_eval.py`: 18 short snippets with one planted flaw each, 10 common (SQL and command injection,
path traversal, SSRF, pickle, XSS, unverified JWT, hard-coded key, MD5 passwords, IDOR) and 8 subtler (timing-unsafe
compare, TOCTOU, ReDoS, mass assignment, open redirect, XXE, prototype pollution, zip slip), plus 3 correct snippets
where the right answer is "no real vulnerability". Graded by regex on the vulnerability class or CWE. It measures
whether a model can spot flaws in a review; it doesn't ask for exploit code. A first version had clean snippets with
real gaps (no login check, pinging any host a user supplies) and a 4,000-token cap that cut off long thinking; both
were fixed before the numbers above.

## Setup

```sh
# oMLX (foreground only, settings in a throwaway --base-path; the model dir is symlinked as "gpt-4o" for Cline)
brew tap jundot/omlx https://github.com/jundot/omlx
xcodebuild -downloadComponent MetalToolchain        # needed for --with-custom-kernel on current Xcode
brew install jundot/omlx/omlx --with-custom-kernel
omlx serve --model-dir DIR --base-path TMP --port 8000 --headless
#   per-model settings in TMP/model_settings.json, e.g.
#   {"version": 3, "models": {"gpt-4o": {"mtp_enabled": true, "chat_template_kwargs": {"reasoning_effort": 0.0}}}}

# DSpine on Qwen3.8-27B (MLX)
pip install "dspine-hybrid-mlx[fast] @ git+https://github.com/internet-projects/dspine-hybrid-mlx.git@v0.4.0"
dspine-hybrid-serve --target mlx-community/Qwen3.8-27B-4bit --draft netprojects/Qwen3.8-27B-DSpine-b16-MLX \
  --fast --temperature 0.6 --top-p 0.95 --top-k 20 --port 8000
```

Models: `mradermacher/KAT-Ornith-HERO-35B-A3B-Fusion-i1-GGUF` (i1-Q4_K_M),
`bartowski/Kwaipilot_KAT-Coder-V2.5-Dev-GGUF` (Q4_K_M), `unsloth/Qwen-AgentWorld-35B-A3B-GGUF` (UD-Q4_K_M),
`Jackrong/Qwopus3.6-35B-A3B-Coder-MTP-GGUF` (Q4_K_M), `empero-ai/Qwen3.8-35B-A3B-Distill-GGUF` (Q4_K_M),
`HauhauCS/Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive` (Q4_K_M),
`deadbydawn101/RavenX-CyberAgent-Qwen3.6-35B-A3B-Opus-4.7-OpenMythos-Pentester-BugHunter-RATH-GGUF` (Q4_K_M),
`peculiar-ragdoll/Cyber-Tiel-Coder-35B-A3B-GGUF-MTP` (UD-Q4_K_XL), `peculiar-ragdoll/Tiel-Coder-35B-A3B-MLX-oQ4e-MTP`,
`mlx-community/Inkling-2-Mini-oQ4e-mtp`, `mlx-community/Qwen3.8-27B-4bit` + `netprojects/Qwen3.8-27B-DSpine-b16-MLX`.
