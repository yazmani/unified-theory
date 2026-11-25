#!/bin/sh
# Qwen3.8-Flash-Next GSQ-RCO Q2_0 (66 GB) on a 48 GB Mac with Splash: the most thorough reviewer here
# (docs/findings/models.md). Routed experts beyond --expert-memory stream from the SSD; without the two memory caps
# Splash tries to load every expert and swaps.
#
#   MODEL=~/models/flashnext/Q2_0/Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-00001-of-00002.gguf \
#   DRAFT=~/models/drafts/Qwen3.8-Flash-Next-DFlash2 ./configs/splash/flashnext-review.sh
# Model: ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF, folder Q2_0 (both shards). Drafter: incoai/Qwen3.8-Flash-Next-DFlash2.
set -eu
MODEL="${MODEL:?set MODEL to the first Q2_0 shard}"
DRAFT="${DRAFT:?set DRAFT to the Qwen3.8-Flash-Next-DFlash2 folder}"
exec splash serve --model local/flashnext --model-dir "$MODEL" --draft-model "$DRAFT" \
  --served-model-name "${NAME:-local}" --port "${PORT:-8000}" \
  --expert-memory "${EXPERT_MEMORY:-20G}" --max-memory "${MAX_MEMORY:-36G}" \
  --thinking-token-budget "${THINKING_BUDGET:-8192}" --max-context "${CTX:-128K}" \
  --language-only --idle-release off --max-cache-disk 4G
