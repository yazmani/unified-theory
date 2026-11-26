#!/bin/sh
# Inkling-2-Mini-Fast on Splash, thinking on (docs/findings/models.md, finding 16): Cline sessions of 66-83 s, all commit
# checks passed in 4 of 4 sessions, 107 tok/s wall-clock. For chat, the IQ4_NL-16GB file decodes at 142 tok/s.
#
#   MODEL=~/models/Inkling-2-Mini-Fast-UD-Q8_K_XL.gguf DRAFT=~/models/drafts/Inkling-2-Mini-DFlash2 ./configs/splash/inkling.sh
# Model: Lucebox/Inkling-2-Mini-Fast-GGUF (UD-Q8_K_XL, 22.9 GB). Drafter: incoai/Inkling-2-Mini-DFlash2.
# Base Inkling-2-Mini (Unsloth UD-Q4_K_M) thinks 4-6x longer: run it with EFFORT=none.
set -eu
MODEL="${MODEL:?set MODEL to the GGUF file}"
DRAFT="${DRAFT:?set DRAFT to the Inkling-2-Mini-DFlash2 folder}"
exec splash serve --model local/inkling --model-dir "$MODEL" --draft-model "$DRAFT" \
  --served-model-name "${NAME:-local}" --port "${PORT:-8000}" \
  ${EFFORT:+--default-reasoning-effort "$EFFORT"} --max-context "${CTX:-128K}" \
  --language-only --idle-release off --max-cache-disk 4G --persistent-cache
