#!/bin/sh
# KAT-Ornith-HERO-35B-A3B fusion on Splash: the everyday coding-agent pick (docs/findings/models.md).
# 235 tok/s, thinking capped at 8K tokens per request, 128K context, prompt cache kept across restarts.
#
#   MODEL=~/models/KAT-Ornith-HERO-35B-A3B-Fusion.i1-Q4_K_M.gguf DRAFT=~/models/drafts/Qwen3.6-35B-A3B-DFlash2 \
#     ./configs/splash/kat-ornith-agent.sh
# Model: mradermacher/KAT-Ornith-HERO-35B-A3B-Fusion-i1-GGUF (i1-Q4_K_M). Drafter: incoai/Qwen3.6-35B-A3B-DFlash2.
# The same script serves any Qwen3.6-35B-A3B model (Tiel-Coder, HauhauCS, ...) with that drafter.
set -eu
MODEL="${MODEL:?set MODEL to the GGUF file}"
DRAFT="${DRAFT:?set DRAFT to the Qwen3.6-35B-A3B-DFlash2 folder}"
exec splash serve --model local/kat --model-dir "$MODEL" --draft-model "$DRAFT" \
  --served-model-name "${NAME:-local}" --port "${PORT:-8000}" \
  --thinking-token-budget "${THINKING_BUDGET:-8192}" --max-context "${CTX:-128K}" \
  --language-only --idle-release off --max-cache-disk 4G --persistent-cache
