# Strata + Inkling-2-Mini: the prompt-cache saga (0.2.19 → 0.2.20)

Multi-turn chats and agents are only fast if each follow-up reuses the already-read conversation. On Strata, for
Inkling-2-Mini, that was broken in 0.2.19 and is broken in a different way in 0.2.20. This page is the whole story,
with the numbers. Upstream threads: [#6627](https://github.com/Niko1221/Strata/issues/6627),
[PR #6665](https://github.com/Niko1221/Strata/pull/6665), [#6675](https://github.com/Niko1221/Strata/issues/6675).

**TL;DR (2026-11-23)**

| Use | Best setup | Why |
|---|---|---|
| Agents (Cline, Claude Code, pi, OpenCode) | **0.2.19 server + engine with the #6627 checkpoint** | Only setup where prompt reuse works with tools: ~3× faster sessions |
| Plain chat, one-shot questions | **stock 0.2.20** | Thinking forced off: 66 tok/s, first token in 0.2–0.4 s |

How to run each: [guides/strata.md](../guides/strata.md).

## 1. Strata 0.2.19: every turn re-read the whole conversation

From source (`engine/src/inkling2/ink_serve.h`, engine 0.1.65): Strata's documented prompt caching
(`docs/PROMPT_CACHE_TAIL.md`, `--prompt-cache` checkpoints) belongs to the main `strata-engine`. Inkling runs in the
separate `strata-inkling` engine, whose only reuse is a per-slot append-only check: it resumes only if the new
prompt starts with **every** token the slot holds, including the hidden thinking it generated. Strata strips that
thinking from the reply, so a client can never send it back, and the engine never resumes. Measured: 0 resumes in
every run; a 120K follow-up took 204 s.

## 2. Two fixes, measured on the same 8-turn coding session

`bench/agent_session.py`: 4 C# files (~24K tokens) pasted once, then 7 follow-ups. SQ-15, 64K context.

| | Release engine | Unmodified source build | **Engine checkpoint (#6627)** | Server-side splice (ours) |
|---|---|---|---|---|
| Whole session | 333 s | 332 s | **163 s (−51%)** | 239 s |
| Follow-ups | 304 s | 303 s | **133 s** | 210 s |
| Prompt re-reading in follow-ups | 152 s | 160 s | **4 s** | 26 s |
| Follow-ups resumed | 1/7 | 1/7 | **7/7** | 6/7 |

- **Server-side splice** (our first attempt, local branch, now retired): the server kept the engine's own tokens
  for the last reply (thinking included) and swapped them back into the next prompt so the slot matched. On a
  120K 3-turn chat it cut turn 2 from 294 s to 12 s. It can't splice after a reply that was cut off.
- **Engine checkpoint** (diff posted on #6627 by its author, Metal + `ink_serve.h`): when a prompt has been read, the
  engine saves the slot's SWA ring KV, ShortConv state and DSpark state. A follow-up that contains the previous
  prompt resumes from there. The model input is unchanged and it also resumes after cut-off replies. **It beat our
  splice, so we switched to it.**
- **PR #6665's reporting commit** makes the engine report reused tokens, so `cached_tokens` is real
  (23,891 → 26,753 on follow-ups) and DSpark counters show up in `timings`.
- Outputs at temperature 0 differ from a cold read after a few dozen characters (chunk-boundary numerics), as the
  #6627 author also reports.
- Build: `cmake -S engine/src/inkling2 -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build --target strata-inkling`.
  `metal/build_mac.sh` builds a standalone runner without `--serve`.

## 3. Separate bug: answers that quote Inkling's own tags leak the thinking (#6675)

The model writes `<|message_model|>` and `<|end_message|>` as **ordinary text tokens** when it talks about them.
A token probe on the unmodified server showed the real special ids only at the structural positions, but
`InklingDialect` matches tag *strings* in decoded text: a plain-text `<|message_model|>` inside the thinking closes
the channel early and the rest of the thinking is emitted as content. Fix direction: tell a sampled special id from
the same characters written as text. Still open in 0.2.20.

## 4. Strata 0.2.20

`strata update` → Control 0.1.66, Inkling engine 0.1.66. What changed for Inkling:

- **#6627 closed, but not for Macs:** the engine's prompt-end checkpoint (`save_prompt_checkpoint` /
  `restore_prompt_checkpoint`) is implemented for **CUDA and CPU only**. The Metal backend (like HIP and SYCL) keeps
  the default that returns `false`, so on Apple Silicon there is no checkpoint at all. `DONE` now reports drafts and
  reused tokens.
- **Thinking is always off.** The server appends `<|message_model|><|content_text|>` (no tools) or an empty thinking
  block `<|message_model|><|content_thinking|><|end_message|>` (with tools). No request option turns it back on.

**Plain chat: much faster, slightly less accurate**

| Bench | 0.2.19 SQ-15 (thinking) | 0.2.20 SQ-15 (no thinking) |
|---|---|---|
| Decode tok/s, median of 3 prompts | 58.0 | **65.9** (refactor prompt 90.9) |
| Wall time, 6 requests | 124.9 s | **42.8 s** |
| Time to first token | 3.7–25 s | **0.2–0.4 s** |
| 10-task Python eval | 10/10, 145 s | 9/10, **35 s** |

**Agents: ~3× slower.** Every agent sends `tools`, so every prompt ends with the empty thinking block. The chat
template never renders that block back into history, so the next prompt diverges right there and the engine
re-reads everything (~1,000 tok/s, 10–20 s per request at 10–20K tokens).

| Cline, same 3-turn session ([details](agent-models.md)) | Total | Prompt reuse |
|---|---|---|
| stock 0.2.20, 2 runs | 330 / 341 s | 0 of 15–16 requests |
| 0.2.20 + chat-template workaround from the #6627 thread | 719 s | 5 of 17; one request ran to 32,000 hidden tokens (517 s) |
| checkpoint engine under the 0.2.20 server | 281 s | 0 of 14 (the mismatch is in the prompt text) |
| 0.2.20 engine under the 0.2.19 server | 344 s | 5 of 17 (no Metal checkpoint; only exact-prefix hits) |
| **checkpoint engine + 0.2.19 server** | **105 / 113 / 119 s** | 85–88% of prompt tokens |

**Why plain chat still reuses on 0.2.20 (Mac):** with thinking off, the slot holds exactly the prompt plus the
visible reply, so the next prompt extends it and the old exact-prefix path matches. No checkpoint is involved.
With tools, the forced empty thinking block breaks that exact match too, and there is no checkpoint to fall back
on. Two separate upstream gaps, both needed for agents on a Mac: Metal checkpoint support, and a prompt suffix
that the next turn's history reproduces.

The same happens with Claude Code, pi and OpenCode: 0 cached tokens on 0.2.20, 2.5–5.7× slower
([agent-harnesses.md](agent-harnesses.md)). Upstream fix needed: render the empty thinking block back for
tool-using assistant turns, or stop appending it.
