# Docs

## Findings (one question per page, current answer first)
- [models](findings/models.md): which local model for coding: everyday agent, thorough reviews, quick edits
- [runtimes](findings/runtimes.md): Splash vs llama.cpp vs Strata vs oMLX vs DSpine and others, same models
- [harnesses](findings/harnesses.md): Cline vs Claude Code vs pi vs OpenCode on the same model and task
- [long-context](findings/long-context.md): 100K on Splash, Inkling-2-Mini to 240K
- [security-review](findings/security-review.md): spotting planted flaws; do uncensored builds do better?
- [strata-prompt-cache](findings/strata-prompt-cache.md): Strata's Inkling prompt reuse, 0.2.19 → 0.2.20 (deep dive)

## Guides
- [splash](guides/splash.md): the fastest runtime, with launch scripts for the winning setups
- [agents](guides/agents.md): connecting Cline, Claude Code, pi and OpenCode to a local server
- [llama-cpp](guides/llama-cpp.md): Unsloth's llama.cpp fork, Tiel-Coder settings
- [strata](guides/strata.md): stock Strata for chat, the checkpoint engine for agents

## Reference
- [methodology](methodology.md): machine, metrics, agent grading, limits
- [journal](journal.md): what was done when, and open threads
- [archive](archive/): findings pages as written on the day, superseded by the pages above
