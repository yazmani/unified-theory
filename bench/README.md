# bench/

Every script talks to an **OpenAI-compatible server** (Strata, llama-server, LM Studio, TensorSharp, ...) and writes
one JSON file under `results/`. Pure standard library except where noted. Run from the repo root.

| Script | Measures | Output |
|---|---|---|
| `oai_bench.py` | decode tok/s (engine counter), TTFT, wall time, visible-output rate over `prompts.json` | `results/decode/` |
| `long_answer.py` | wall time to one complete long answer (8000 max tokens), hidden reasoning size | `results/long-answer/` |
| `mini_eval.py` | 10 Python tasks with hidden asserts (pass@1): a broken-code smoke test | `results/eval/` |
| `raw_decode.py` | wall-clock decode from one non-streamed request (catches servers that stream in bursts) | `results/decode/raw-*` |
| `security_review_eval.py` | spots planted vulnerabilities in 18 snippets, false alarms on 3 clean ones (defensive review only) | `results/security/` |
| `session_stats.py` | whole-run engine stats from a Splash server log: decode peak/mean, prefill, cache hit, TTFT | `results/sessions/` |
| `long_context.py` | prefill/decode at depth and needle recall on a code haystack (needs `tokenizers`) | `results/long-context/` |
| `longctx_multiturn.py` | 3-turn chat over a ~120K dump: is the prompt reused? (needs `tokenizers`) | `results/long-context/` |
| `agent_session.py` | 8-turn coding chat over pasted source files: per-turn read time and cached tokens | `results/sessions/` |
| `cline_bench.py` + `acp_client.py` | Cline CLI over ACP on a real multi-turn task, in a sandbox copy | `results/agents/cline/` |
| `harness_bench.py` | the same task through Claude Code, pi or OpenCode | `results/agents/harness/` |
| `examples/grade_template.py` | template for your private agent-task grader | — |

## Quick start

```sh
# speed (start your server first; one model at a time, check swap before and after)
python3 -I bench/oai_bench.py --url http://127.0.0.1:8092 --label my-model --runs 2
python3 -I bench/long_answer.py --url http://127.0.0.1:8092 --label my-model
python3 -I bench/mini_eval.py --url http://127.0.0.1:8092 --label my-model

# thinking settings go in --extra (merged into the request body)
python3 -I bench/mini_eval.py --url http://127.0.0.1:8092 --label my-model-nothink \
  --extra '{"chat_template_kwargs":{"reasoning_effort":"none"}}'

# long context (pip install tokenizers, or use a venv)
python3 bench/long_context.py --url http://127.0.0.1:8091 --label my-model --tokens 120000 \
  --tokenizer path/to/tokenizer.json
```

`make bench-speed URL=... LABEL=...` runs the first three in one go; `make summary` prints tables from `results/`.

## Agent benchmarks on your own project

1. Pick a repo with uncommitted work; copy it to `.local/agent-bench/template/` and remove its git remote.
2. Write a grader from `examples/grade_template.py` into `.local/agent-bench/grade.py`.
3. Install the harness CLIs you want (`npm i cline @earendil-works/pi-coding-agent opencode-ai` in
   `.local/tools/`; Claude Code from its installer).
4. Run:
   ```sh
   CLINE_BIN=.local/tools/node_modules/.bin/cline python3 -I bench/cline_bench.py --label my-run \
     --base-url http://127.0.0.1:8091/v1 --model MODEL_ID --template .local/agent-bench/template \
     --private-out .local/agent-bench/runs --metrics-out results/agents/cline/cline-my-run.json
   python3 -I bench/harness_bench.py --harness pi --bin .local/tools/node_modules/.bin/pi --label pi-my-run \
     --base-url http://127.0.0.1:8091 --model MODEL_ID --template .local/agent-bench/template \
     --private-out .local/agent-bench/runs --metrics-out results/agents/harness/harness-pi-my-run.json
   python3 -I .local/agent-bench/grade.py .local/agent-bench/runs/my-run
   ```
   Transcripts (which contain your code) stay in `--private-out`; only timing and counts go to `results/`.

Run harnesses from a neutral folder, never from inside another repo: some agents (OpenCode) trust `$PWD`.
