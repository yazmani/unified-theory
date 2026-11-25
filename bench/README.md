# bench/

Every script talks to an **OpenAI-compatible server** (Splash, llama-server, Strata, LM Studio, ...) and writes
one JSON file under `results/`. Pure standard library except where noted. Run from the repo root.

| Folder | Script | Measures | Output |
|---|---|---|---|
| `speed/` | `oai_bench.py` | decode tok/s (engine counter), TTFT, wall time, visible-output rate over `prompts.json` | `results/decode/` |
| | `long_answer.py` | wall time to one complete long answer (8000 max tokens), hidden reasoning size | `results/long-answer/` |
| | `mini_eval.py` | 10 Python tasks with hidden asserts (pass@1): a broken-code smoke test | `results/eval/` |
| | `raw_decode.py` | wall-clock decode from one non-streamed request (catches servers that stream in bursts) | `results/raw-decode/` |
| `agents/` | `cline_bench.py` + `acp_client.py` | Cline CLI over ACP on a real multi-turn task, in a sandbox copy | `results/agents/cline/` |
| | `harness_bench.py` | the same task through Claude Code, pi or OpenCode | `results/agents/harness/` |
| | `grade_template.py` | template for your private agent-task grader | — |
| `long_session/` | | a public 6-turn agent session on Rich 14.3.4 that grows past 100K tokens: four real bugs, graded with upstream's regression tests ([README](long_session/README.md)) | `results/agents/long-session/` |
| `context/` | `long_context.py` | prefill/decode at depth and needle recall on a code haystack (needs `tokenizers`) | `results/long-context/` |
| | `longctx_multiturn.py` | 3-turn chat over a ~120K dump: is the prompt reused? (needs `tokenizers`) | `results/long-context/` |
| | `agent_session.py` | 8-turn coding chat over pasted source files: per-turn read time and cached tokens | `results/sessions/` |
| `security/` | `security_review_eval.py` | spots planted vulnerabilities in 18 snippets, false alarms on 3 clean ones (defensive review only) | `results/security/` |

Whole-run engine stats from a Splash server log (decode peak/mean, prefill, cache hit, TTFT) come from
`tools/session_stats.py`, written to `results/engine-stats/`.

## Quick start

```sh
# speed (start your server first; one model at a time, check swap before and after).
# Splash and Strata reject unknown model names: pass the served name (--model, or "model" in --extra).
python3 -I bench/speed/oai_bench.py --url http://127.0.0.1:8000 --model local --label my-model --runs 2
python3 -I bench/speed/long_answer.py --url http://127.0.0.1:8000 --label my-model --extra '{"model":"local"}'
python3 -I bench/speed/mini_eval.py --url http://127.0.0.1:8000 --label my-model --extra '{"model":"local"}'
python3 -I bench/speed/raw_decode.py --url http://127.0.0.1:8000 --model local --label my-model

# thinking settings go in --extra (merged into the request body)
python3 -I bench/speed/mini_eval.py --url http://127.0.0.1:8000 --label my-model-nothink \
  --extra '{"model":"local","reasoning_effort":"none"}'

# security review (defensive: spot planted flaws)
python3 -I bench/security/security_review_eval.py --url http://127.0.0.1:8000 --label my-model --extra '{"model":"local"}'

# whole-run engine stats from a Splash log
python3 -I tools/session_stats.py splash-server.log --label my-model

# long context (pip install tokenizers, or use a venv)
python3 bench/context/long_context.py --url http://127.0.0.1:8000 --label my-model --tokens 100000 \
  --tokenizer path/to/tokenizer.json --extra '{"model":"local"}'
```

`make bench-speed URL=... MODEL=... LABEL=...` runs the first four in one go; `make summary` prints tables from `results/`.

## Agent benchmarks on your own project

1. Pick a repo with uncommitted work; copy it to `.local/agent-bench/template/` and remove its git remote.
2. Write a grader from `agents/grade_template.py` into `.local/agent-bench/grade.py`.
3. Install the harness CLIs you want (`npm i cline @earendil-works/pi-coding-agent opencode-ai` in
   `.local/tools/`; Claude Code from its installer).
4. Run:
   ```sh
   CLINE_BIN=.local/tools/node_modules/.bin/cline python3 -I bench/agents/cline_bench.py --label my-run \
     --base-url http://127.0.0.1:8091/v1 --model MODEL_ID --template .local/agent-bench/template \
     --private-out .local/agent-bench/runs --metrics-out results/agents/cline/cline-my-run.json
   python3 -I bench/agents/harness_bench.py --harness pi --bin .local/tools/node_modules/.bin/pi --label pi-my-run \
     --base-url http://127.0.0.1:8091 --model MODEL_ID --template .local/agent-bench/template \
     --private-out .local/agent-bench/runs --metrics-out results/agents/harness/harness-pi-my-run.json
   python3 -I .local/agent-bench/grade.py .local/agent-bench/runs/my-run
   ```
   Transcripts (which contain your code) stay in `--private-out`; only timing and counts go to `results/`.

Run harnesses from a neutral folder, never from inside another repo: some agents (OpenCode) trust `$PWD`.
