# Guide: Splash on Apple Silicon

[Splash](https://github.com/incoai/splash) 1.7.2 is the fastest runtime measured here ([runtimes](../findings/runtimes.md)).
It is a Metal-only engine with kernels written per model family and a trained [DFlash 2](https://inco.ai/blog/dflash2/)
drafter for each family. It serves standard GGUF and MLX files.

```sh
brew install incoai/tap/splash
```

## Setups

| Use | Script | Model | Drafter |
|---|---|---|---|
| Fast agent, short tasks | [`configs/splash/kat-ornith-agent.sh`](../../configs/splash/kat-ornith-agent.sh) | `mradermacher/KAT-Ornith-HERO-35B-A3B-Fusion-i1-GGUF` (i1-Q4_K_M, 21.7 GB) | `incoai/Qwen3.6-35B-A3B-DFlash2` (1 GB) |
| Long agent sessions and reviews | [`configs/splash/flashnext-review.sh`](../../configs/splash/flashnext-review.sh) | `ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF`, folder `Q2_0` (66 GB) | `incoai/Qwen3.8-Flash-Next-DFlash2` (1.2 GB) |
| Inkling-2-Mini | [`configs/splash/inkling.sh`](../../configs/splash/inkling.sh) | Unsloth's Inkling-2-Mini GGUF (UD-Q4_K_M) | `incoai/Inkling-2-Mini-DFlash2` (0.9 GB) |

```sh
hf download incoai/Qwen3.6-35B-A3B-DFlash2 --local-dir ~/models/drafts/Qwen3.6-35B-A3B-DFlash2
MODEL=~/models/KAT-Ornith-HERO-35B-A3B-Fusion.i1-Q4_K_M.gguf DRAFT=~/models/drafts/Qwen3.6-35B-A3B-DFlash2 \
  ./configs/splash/kat-ornith-agent.sh
```

Swift-1.5 (`ukisai/Swift-1.5-Qwen3.8-Flash-Next-GSQ-RCO-GGUF`, folder-less `Q2_0` shards, 66.5 GB) runs with the
same script and drafter: set `MODEL` to its first shard. The Flash-Next Coder
(`ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-Coder-GGUF`, 58 GB) does too:
set `MODEL` to its first `IQ1_M` shard and `EXPERT_MEMORY=auto MAX_MEMORY=38G` (all its experts fit in memory).

The server listens on `http://127.0.0.1:8000/v1` (OpenAI API) and serves the model as `local`. Connect an agent:
[guides/agents](agents.md). Without `--model-dir`, `splash serve --model OWNER/REPO:VARIANT` downloads a model and
its drafter; `splash pi`, `splash opencode` and `splash claude` start a harness wired to the server.

## Flags that matter

| Flag | Why |
|---|---|
| `--draft-model` | the speed comes from the drafter: use the one for the model's family. A fine-tune far from its base (DavidAU's TURBO-Fable) drops to 1.7 accepted tokens per cycle and runs slower than llama.cpp |
| `--served-model-name NAME` | Splash rejects model names it doesn't serve. Cline's CLI over ACP always requests `gpt-4o`; serve under that name for it |
| `--thinking-token-budget 8192` | caps thinking per request for the Qwen3.6 and Flash-Next models; agent turns stay bounded |
| `--default-reasoning-effort none` | thinking off unless a request asks for it (Inkling, the Qwen3.8-27B fine-tunes) |
| `--expert-memory` / `--max-memory` | for MoE files larger than memory (Flash-Next): without them Splash tries to load every expert, swaps, then refuses to start. 20G / 36G worked on 48 GB |
| `--persistent-cache` | keeps the prompt cache across restarts; it only helps from the same working directory, because harnesses put it in the system prompt |
| `--idle-release off` | keeps the model loaded between agent turns |
| `--max-cache-disk 4G` | caps the SSD prompt cache |
| `--max-context 256K` | default in the KAT-Ornith and Flash-Next scripts. Both read a 250K prompt in ~4 min and decode at 145 / 104 tok/s there, with swap flat ([long-context](../findings/long-context.md)). Agent sessions already reached 40–77K tokens per request on a 3-turn task |

## Gotchas

- **One model at a time.** Check `sysctl vm.swapusage` before and after; a second model next to a loaded one can
  freeze a 48 GB Mac.
- One Inkling tool call came back as text once (`<|message_model|><|content_invoke_tool_json|>…`), so that turn
  ended without running it.
- The Ornith-trained drafter `jzinno/Ornith-1.5-35B-A3B-DFlash2` doesn't load in 1.7.2 (sliding window 4096, Splash
  expects 2048); the stock Qwen3.6-35B-A3B drafter serves the whole Ornith / Tiel family.
- The other Qwen3.6-35B-A3B models in [models](../findings/models.md) run with the same script and drafter; set
  `MODEL` to their GGUF.
