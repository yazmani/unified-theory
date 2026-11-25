#!/bin/sh
# Build the long-session template: Rich (github.com/Textualize/rich) at v14.3.4, before four bugs fixed in v15.0.0,
# as a fresh one-commit repo (no future history to peek at) with a test venv in .venv (gitignored by Rich).
#   sh bench/long_session/setup_rich.sh DEST      e.g. .local/agent-bench/long-session
# DEST/template is the agent's workspace template; DEST/upstream is the full clone the grader reads hidden tests from.
set -eu
DEST=${1:?usage: setup_rich.sh DEST}
mkdir -p "$DEST"
DEST=$(cd "$DEST" && pwd)
[ -d "$DEST/upstream" ] || git clone -q --filter=blob:none https://github.com/Textualize/rich.git "$DEST/upstream"
rm -rf "$DEST/template"; mkdir "$DEST/template"
git -C "$DEST/upstream" archive v14.3.4 | tar -x -C "$DEST/template"
cd "$DEST/template"
git init -q -b main
git add -A
git -c user.name=dev -c user.email=dev commit -qm "Rich 14.3.4"
python3 -m venv .venv
.venv/bin/pip install -q --disable-pip-version-check pytest==8.4.2 pygments==2.19.2 markdown-it-py==3.0.0 attrs typing-extensions   # pins from poetry.lock (Pygments changes highlight colours)
.venv/bin/python -m pytest tests -q -p no:cacheprovider 2>&1 | tail -1
