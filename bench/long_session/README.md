# Long agent session: four real Rich bugs in one conversation

Tests whether a model keeps working well as an agent session grows past 100K tokens of context. The project is
[Rich](https://github.com/Textualize/rich) at v14.3.4, before four bugs that upstream fixed in v15.0.0. Everything
is public, so results can be compared across machines.

One session, six turns, each continuing the last ([`turns.json`](turns.json)):

1. Read nine core modules in full (~90K tokens) and explain how `Console.print` produces output.
2. Fix: an empty `console.print(end="!")` writes a newline (upstream PR #4075).
3. Fix: `Text.from_ansi` drops newlines (#4076).
4. Fix: `FileProxy` doesn't pass on `isatty` (#4077).
5. Fix: inline code in a Markdown table cell loses its highlighting (#4079).
6. Run the whole suite and commit.

The grader runs, for each bug, the regression test upstream added in v15.0.0. The agent never sees it. The grader
also runs the agent's final test suite (unmodified 14.3.4 passes all 952 tests) and checks the commit.

```sh
sh bench/long_session/setup_rich.sh .local/agent-bench/long-session        # template + pinned test venv
python3 -I bench/harness_bench.py --harness pi --bin PATH/TO/pi --label my-run --base-url http://127.0.0.1:8000 \
  --model local --template .local/agent-bench/long-session/template --private-out /tmp/agent-runs \
  --metrics-out results/agents/long-session/longsess-my-run.json --context 262144 \
  --turns bench/long_session/turns.json --timeout 3600
python3 -I bench/long_session/grade.py /tmp/agent-runs/my-run/ws .local/agent-bench/long-session/upstream
```

Checked both ways: the template scores 0 of 4 and upstream's v15.0.0 fixes score 4 of 4. The test venv pins
Pygments 2.19.2 from Rich's lock file, because newer Pygments changes highlight colours and fails 7 tests.

Limits: the bugs are small, and models trained after April 2026 may have seen the fixes. What this tests is
whether the model stays accurate deep into a long session, not whether it can solve hard bugs.
