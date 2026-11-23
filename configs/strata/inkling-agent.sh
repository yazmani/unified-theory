#!/bin/sh
# Serve Inkling-2-Mini for coding agents with working prompt reuse:
# a strata-inkling engine built with the prompt checkpoint from Niko1221/Strata#6627 (+ PR #6665 reporting),
# under the Strata 0.2.19 server (Control 0.1.65). See docs/guides/strata.md.
#
#   PORT=8091 CTX=131072 ./configs/strata/inkling-agent.sh
#
# Every path can be overridden; defaults match a standard Strata install.
set -eu
ENGINE="${INKLING_ENGINE:-$HOME/.local/share/strata/custom/strata-inkling-ckpt/strata-inkling}"
CONTROL="${STRATA_CONTROL:-$HOME/.local/share/strata/components/control/0.1.65}"
MODEL="${INKLING_MODEL:-$HOME/Documents/Strata/models/inkling-2-mini/Inkling-2-Mini-SQ-15.strata}"
TOKENIZER="${INKLING_TOKENIZER_DIR:-$HOME/Documents/Strata/packs/inkling-2-mini-sq-15/tokenizer}"
NAME="${MODEL_NAME:-inkling-2-mini-sq-15}"
CTX="${CTX:-131072}"
PORT="${PORT:-8091}"
LOG="${LOG:-${TMPDIR:-/tmp}/inkling-agent.engine.log}"

for f in "$ENGINE" "$CONTROL/strata.py" "$MODEL" "$TOKENIZER"; do
  [ -e "$f" ] || { echo "missing: $f (see docs/guides/strata.md)" >&2; exit 1; }
done

PROFILE="$(mktemp "${TMPDIR:-/tmp}/inkling-agent.XXXXXX")"
ARGS="[\"--native\", \"$MODEL\", \"--max-context\", \"$CTX\"]"
cat > "$PROFILE" <<EOF
{
 "exe": "$ENGINE", "args": $ARGS, "args_written": $ARGS, "args_derived": $ARGS,
 "cwd": "$CONTROL", "tokenizer": "$TOKENIZER", "model_name": "$NAME", "arch": "inkling2_loop",
 "log": "$LOG", "lib_dirs": [], "port": $PORT, "drafting": "dspark", "parallel": 1, "backend": "metal",
 "host": "127.0.0.1", "open_browser": false
}
EOF

# STRATA_NO_HANDOVER=1: without it the 0.2.19 strata.py hands over to a newer installed Control (0.2.20),
# whose prompt suffix breaks reuse for tool-using clients.
STRATA_NO_HANDOVER=1 exec "$CONTROL/python/bin/python3" "$CONTROL/strata.py" serve --profile "$PROFILE" --port "$PORT"
