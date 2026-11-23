# Guide: connecting coding agents to a local model

All four agents below were benchmarked against the same local server
([results](../findings/agent-harnesses.md)). Examples use Strata on `:8091` with model id `inkling-2-mini-sq-15`;
for llama-server use `:8092` (any model id works).

**Before you start:** make sure your server reuses the prompt across turns (check `cached_tokens` on a follow-up).
Without it every agent turn re-reads the whole conversation, which costs more than any harness choice.
On Strata that means the [agent setup](strata.md#agents-checkpoint-engine--0219-server), not stock 0.2.20.

## OpenCode (fastest in our runs)

Copy [`configs/agents/opencode.json`](../../configs/agents/opencode.json) to `~/.config/opencode/opencode.json`
(or point `OPENCODE_CONFIG` at it), then `opencode`. Headless:
`opencode run --dir . -m local/inkling-2-mini-sq-15 "your prompt"`. Pass `--dir` in scripts: OpenCode trusts `$PWD`.

## pi (best balance)

Copy [`configs/agents/pi-models.json`](../../configs/agents/pi-models.json) to `~/.pi/agent/models.json`, then
`pi --model local/inkling-2-mini-sq-15`. Headless: `pi -p "prompt"`, continue with `--continue`.

## Claude Code (most thorough)

```sh
set -a; . configs/agents/claude-code.env; set +a
claude
```
Both Strata and llama-server serve Anthropic's `/v1/messages`. Claude Code will log an unrecognized model and
assume a 1M context window; keep sessions within your server's context.

## Cline (VS Code extension or CLI)

Provider **OpenAI Compatible**, base URL `http://127.0.0.1:8091/v1`, API key `local`, model id
`inkling-2-mini-sq-15`, context window 131072, max output 16384. CLI: `cline auth -p openai-compatible -k local
-m inkling-2-mini-sq-15 -b http://127.0.0.1:8091/v1`.

## Safety

Every agent committed without asking when commands were auto-approved, and some committed local config folders.
Keep command auto-approval off on real projects, and avoid abliterated ("no refusals") models with auto-approve.
