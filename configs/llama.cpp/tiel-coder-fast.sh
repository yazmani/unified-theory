#!/bin/sh
# Tiel-Coder-35B-A3B UD-IQ4_XS + MTP: the fastest decode measured on the M5 Pro (~98 tok/s, ~18 GB).
# Best for chat and quick edits; for agents prefer tiel-coder-agent.sh (Q4_K_XL, reasoning budget).
#
#   MODEL=/path/to/Tiel-Coder-35B-A3B-MTP-UD-IQ4_XS.gguf ./configs/llama.cpp/tiel-coder-fast.sh
set -eu
SERVER="${LLAMA_SERVER:-$HOME/.unsloth/llama.cpp/build/bin/llama-server}"
MODEL="${MODEL:?set MODEL to the Tiel-Coder GGUF}"
exec "$SERVER" -m "$MODEL" --port "${PORT:-8092}" -c "${CTX:-32768}" -fa on --jinja -ngl 99 --spec-type draft-mtp
