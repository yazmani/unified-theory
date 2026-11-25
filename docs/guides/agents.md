# Guide: connecting coding agents to a local model

All four agents below were benchmarked against the same local servers ([results](../findings/harnesses.md)). The
configs in [`configs/agents/`](../../configs/agents/) point at a [Splash](splash.md) server on `:8000` serving the
model as `local`. For another server, change the base URL and model id: Strata's agent setup listens on `:8091`
with model id `inkling-2-mini-sq-15`, llama-server on `:8092` accepts any id.

**Before you start:** make sure your server reuses the prompt across turns (check `cached_tokens` on a follow-up).
Without it every agent turn re-reads the whole conversation, which costs more than any harness choice. Splash and
llama.cpp do it by default; on Strata it needs the [agent setup](strata.md#agents-checkpoint-engine--0219-server).

## pi (fastest on Splash)

Copy [`configs/agents/pi-models.json`](../../configs/agents/pi-models.json) to `~/.pi/agent/models.json`, then
`pi --model local/local`. Headless: `pi -p "prompt"`, continue with `--continue`.

## OpenCode

Copy [`configs/agents/opencode.json`](../../configs/agents/opencode.json) to `~/.config/opencode/opencode.json`
(or point `OPENCODE_CONFIG` at it), then `opencode`. Headless: `opencode run --dir . -m local/local "your prompt"`.
Pass `--dir` in scripts: OpenCode trusts `$PWD`. It sends the largest prompts of the four.

## Claude Code (most thorough on Strata)

```sh
set -a; . configs/agents/claude-code.env; set +a
claude
```
Splash, Strata and llama-server serve Anthropic's `/v1/messages`. Claude Code will log an unrecognized model and
assume a 1M context window; keep sessions within your server's context.

## Cline (VS Code extension or CLI)

Provider **OpenAI Compatible**, base URL `http://127.0.0.1:8000/v1`, API key `local`, model id `local`, context
window 131072, max output 16384. CLI: `cline auth -p openai-compatible -k local -m local -b http://127.0.0.1:8000/v1`.
The CLI over ACP requests the model `gpt-4o` whatever you configure, so for it start Splash with `NAME=gpt-4o`.

## Safety

Every agent committed without asking when commands were auto-approved, and some committed local config folders.
Keep command auto-approval off on real projects, and avoid abliterated ("no refusals") models with auto-approve.
