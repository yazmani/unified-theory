# Guide: llama.cpp (Unsloth fork) on Apple Silicon

Unsloth's llama.cpp fork (b12588 at the time of writing, installed by Unsloth Studio in `~/.unsloth/llama.cpp`) is
the best general runtime measured here. Homebrew's llama.cpp 0.7.0 was behind it (no `inkling2` architecture).

## Tiel-Coder-35B-A3B (Qwen-family MoE, MTP head built in)

| Use | Quant | Script | Measured |
|---|---|---|---|
| Fastest decode (chat, quick edits) | UD-IQ4_XS (18.1 GB) | [`configs/llama.cpp/tiel-coder-fast.sh`](../../configs/llama.cpp/tiel-coder-fast.sh) | ~98 tok/s |
| Coding agents | UD-Q4_K_XL (22.7 GB) | [`configs/llama.cpp/tiel-coder-agent.sh`](../../configs/llama.cpp/tiel-coder-agent.sh) | 57–61 tok/s, most issues found in reviews |

```sh
MODEL=~/models/tiel/Tiel-Coder-35B-A3B-MTP-UD-Q4_K_XL.gguf ./configs/llama.cpp/tiel-coder-agent.sh
```

What matters, from [agent-models](../findings/agent-models.md):

- `--spec-type draft-mtp --spec-draft-n-max 1 --spec-draft-p-min 0.0`: n-max 1 beat 3 (61 vs 47 tok/s, acceptance
  0.87 vs 0.64).
- `--reasoning-budget 8192`: without it one agent turn thought for 668 s.
- Agentic sampling from the model card: `--temp 0.6 --top-p 0.95 --top-k 20 --min-p 0`.
- `-ctk q8_0 -ctv q8_0` keeps a 128K KV cache affordable on 48 GB.
- llama.cpp's prompt cache works out of the box for multi-turn and agents.

## Inkling-2-Mini on llama.cpp

Works (`inkling2` arch), at ~30 tok/s, or 36 with the DSpark drafter (`--spec-type draft-dspark --spec-draft-n-max 3`
with the `dspark-Inkling-2-Mini-Q8_0.gguf` drafter). Strata is 1.6–1.9× faster on Mac. Set
`"chat_template_kwargs": {"reasoning_effort": "none"}` per request unless you want long hidden thinking: the
template's default effort is 0.9.

## Kernel baseline

```sh
~/.unsloth/llama.cpp/build/bin/llama-bench -m MODEL.gguf -p 512 -n 128 -r 3 -fa 1
```
