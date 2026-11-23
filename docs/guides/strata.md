# Guide: running Inkling-2-Mini on Strata

[Strata](https://github.com/Niko1221/Strata) is the fastest way to run Inkling-2-Mini on a Mac
([numbers](../findings/decode-speed.md)). Which setup to use depends on the client:

| Client | Use | Why |
|---|---|---|
| Chat, one-shot questions | **stock Strata 0.2.20** | thinking off: 66 tok/s, first token in under 0.5 s |
| Coding agents (anything that sends `tools`) | **checkpoint engine + 0.2.19 server** | prompt reuse works: ~3× faster sessions ([why](../findings/strata-prompt-cache.md)) |

## Stock Strata (chat)

```sh
strata update                     # 0.2.20 at the time of writing
strata install --family inkling-2-mini --model SQ-15 --yes   # ⚠ starts serving when done, see gotchas
strata launch --family inkling-2-mini --model sq-15 --context 32k --vision off --no-tui --yes
strata launch --stop
```

SQ-15 is the sweet spot: faster than SQ-20, no quality loss seen. SQ-10 is not faster in practice.

### Gotchas

- `strata install` downloads **and then starts serving** (and opens the web page). It never returns and keeps
  ~15–20 GB loaded. Combined with another model it can swap a 48 GB Mac into a freeze. Stop it before benchmarking.
- Model names are uppercase for `strata install` (`SQ-20`) and lowercase for `strata launch` (`sq-20`).
- Strata streams in a few large chunks: client-side chunk timing is meaningless; read `timings.predicted_per_second`.
- The signed engine folder is SHA-256 checked at start: a swapped binary there refuses to run. Custom engines go
  in a separate folder and are started with `strata serve --profile` (below).

## Agents: checkpoint engine + 0.2.19 server

Until the tools/thinking-block bug in 0.2.20 is fixed, this is the setup that keeps agents fast.

1. **Keep Control 0.1.65 (Strata 0.2.19).** `strata update` leaves old Control versions in
   `~/.local/share/strata/components/control/`.
2. **Build the engine with the checkpoint.** In a Strata checkout at `v0.2.19`, apply the engine diff posted on
   [#6627](https://github.com/Niko1221/Strata/issues/6627) and the reporting commit from
   [PR #6665](https://github.com/Niko1221/Strata/pull/6665), then:
   ```sh
   cmake -S engine/src/inkling2 -B build -DCMAKE_BUILD_TYPE=Release
   cmake --build build --target strata-inkling
   mkdir -p ~/.local/share/strata/custom/strata-inkling-ckpt
   cp build/strata-inkling ~/.local/share/strata/custom/strata-inkling-ckpt/
   ```
   (`metal/build_mac.sh` builds a standalone runner without `--serve`; use CMake.)
3. **Serve it** with [`configs/strata/inkling-agent.sh`](../../configs/strata/inkling-agent.sh):
   ```sh
   PORT=8091 CTX=131072 ./configs/strata/inkling-agent.sh
   ```
   It writes a serve profile and starts the 0.2.19 server with `STRATA_NO_HANDOVER=1` (otherwise the old Control
   hands over to the newest installed one).
4. **Check it:** in a multi-turn chat, follow-ups should report a growing `usage.prompt_tokens_details.cached_tokens`.

Then point your agent at `http://127.0.0.1:8091`: [guides/agents.md](agents.md).
