#!/bin/sh
# Inkling-2-Mini on Splash, thinking off by default (docs/findings/models.md): ~109 tok/s wall-clock.
#
#   MODEL=~/models/Inkling-2-Mini-UD-Q4_K_M.gguf DRAFT=~/models/drafts/Inkling-2-Mini-DFlash2 ./configs/splash/inkling.sh
# Model: Unsloth's Inkling-2-Mini GGUF (UD-Q4_K_M). Drafter: incoai/Inkling-2-Mini-DFlash2.
set -eu
MODEL="${MODEL:?set MODEL to the GGUF file}"
DRAFT="${DRAFT:?set DRAFT to the Inkling-2-Mini-DFlash2 folder}"
exec splash serve --model local/inkling --model-dir "$MODEL" --draft-model "$DRAFT" \
  --served-model-name "${NAME:-local}" --port "${PORT:-8000}" \
  --default-reasoning-effort none --max-context "${CTX:-128K}" \
  --language-only --idle-release off --max-cache-disk 4G --persistent-cache
