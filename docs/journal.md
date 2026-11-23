# Journal

What was tried, in order, and where the write-up lives. New work gets a line here and its findings go into the
matching page under [findings/](findings/).

## 2026-11-22

- Benched Inkling-2-Mini on Strata 0.2.19 (SQ-10/15/20) against Unsloth's llama.cpp fork, plus Tiel-Coder-35B-A3B
  with MTP. → [decode-speed](findings/decode-speed.md)
- Learned the hard way to run one model at a time: an auto-serving `strata install` next to `llama-bench` swapped
  the Mac to 28 GB. → [methodology](methodology.md), [guides/strata](guides/strata.md)
- Long context at 30K / 120K / 240K: recall 8/8, but Strata re-read the whole prompt every turn.
  → [long-context](findings/long-context.md)
- Built TensorSharp from source: no Inkling on Mac, no gain for Tiel. → [tensorsharp](findings/tensorsharp.md)
- Wrote a server-side fix for Strata's Inkling re-reads, then measured the engine checkpoint posted on #6627, which
  won (8-turn session 333 s → 163 s). Added PR #6665's reporting. Found the tag-leak bug (#6675).
  → [strata-prompt-cache](findings/strata-prompt-cache.md)

## 2026-11-23

- Cline agent benchmark on a real 3-turn session: Inkling vs Tiel-Coder variants, MTP and reasoning-budget settings.
  → [agent-models](findings/agent-models.md)
- Strata 0.2.20: faster plain chat (thinking forced off), but agents ~3× slower (no reuse with tools).
  → [strata-prompt-cache §4](findings/strata-prompt-cache.md#4-strata-0220)
- Harness comparison: Cline, Claude Code, pi, OpenCode on the same model and task.
  → [agent-harnesses](findings/agent-harnesses.md)
- Repo restructured into findings / guides / configs, with a privacy check.
- Mixed setup (0.2.20 engine under the 0.2.19 server): 344 s, no better. Cause: 0.2.20 has prompt checkpoints for
  CUDA/CPU only, none on Metal. → [strata-prompt-cache §4](findings/strata-prompt-cache.md#4-strata-0220)
- Reported both 0.2.20 gaps upstream with a repro: [Niko1221/Strata#6904](https://github.com/Niko1221/Strata/issues/6904).

## Open threads

- [ ] Harder quality set (multi-file edits, SWE-style tasks) to pick a quality winner, not just a speed winner.
- [ ] LM Studio (MLX engine) and mlx-lm on the same models.
- [ ] More models: Qwen3-Coder-30B-A3B, a dense ~27B as a quality reference.
- [ ] The harness comparison on Tiel-Coder (llama.cpp).
- [ ] Re-run the decode table with no VM running, to measure what it cost.
- [ ] Tiel-Coder MTP `--spec-draft-n-max` sweep beyond 1 and 3.
- [ ] Memory-bandwidth roofline: GB read per token vs measured tok/s, to see the headroom left.
