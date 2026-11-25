# unified-theory: common tasks. Run `make help`.
PY ?= python3
URL ?= http://127.0.0.1:8000
MODEL ?= local
LABEL ?= my-model

.PHONY: help check privacy lint summary bench-speed hooks

help:  ## list targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'

check: lint privacy  ## compile all scripts, lint (if ruff is installed), privacy check
	@$(PY) -m compileall -q bench tools && echo "compile: ok"

lint:  ## ruff, if installed
	@command -v ruff >/dev/null && ruff check bench tools || echo "lint: ruff not installed, skipped (pip install ruff)"

privacy:  ## fail if tracked files contain personal paths, e-mails, host names or .local/private-terms
	@$(PY) tools/check_private.py

summary:  ## print Markdown tables from results/
	@$(PY) tools/summarize.py

bench-speed:  ## decode + long answer + mini-eval against URL (model MODEL), saved under LABEL
	$(PY) -I bench/speed/oai_bench.py --url $(URL) --model $(MODEL) --label $(LABEL) --runs 2
	$(PY) -I bench/speed/long_answer.py --url $(URL) --label $(LABEL) --extra '{"model":"$(MODEL)"}'
	$(PY) -I bench/speed/mini_eval.py --url $(URL) --label $(LABEL) --extra '{"model":"$(MODEL)"}'
	$(PY) -I bench/speed/raw_decode.py --url $(URL) --model $(MODEL) --label $(LABEL)

hooks:  ## run the privacy check before every commit
	@git config core.hooksPath .githooks && echo "hooks: pre-commit privacy check enabled"
