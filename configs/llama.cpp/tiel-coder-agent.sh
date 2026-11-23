#!/bin/sh
# Tiel-Coder-35B-A3B (UD-Q4_K_XL, MTP head inside the GGUF) for coding agents, on Unsloth's llama.cpp fork.
# Settings from docs/findings/agent-models.md: MTP n-max 1, the model card's agentic sampling, and a reasoning
# budget (without it one agent turn thought for 11 minutes).
#
#   MODEL=~/models/tiel/Tiel-Coder-35B-A3B-MTP-UD-Q4_K_XL.gguf ./configs/llama.cpp/tiel-coder-agent.sh
set -eu
SERVER="${LLAMA_SERVER:-$HOME/.unsloth/llama.cpp/build/bin/llama-server}"
MODEL="${MODEL:?set MODEL to the Tiel-Coder GGUF}"
exec "$SERVER" -m "$MODEL" --port "${PORT:-8092}" \
  -c "${CTX:-131072}" -fa on -ctk q8_0 -ctv q8_0 --jinja -ngl 99 \
  --temp 0.6 --top-p 0.95 --top-k 20 --min-p 0 \
  --spec-type draft-mtp --spec-draft-n-max 1 --spec-draft-p-min 0.0 \
  --reasoning-budget "${REASONING_BUDGET:-8192}" --reasoning-budget-message "Proceed to final answer."
