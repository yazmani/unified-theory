# Contributing

Most useful contributions:

1. **Results from another Mac** (M1–M5, any memory size) for models already here.
2. **A new model, runtime or harness** measured with the existing scripts.
3. **Better benchmarks**, especially a harder coding-quality set.

## Ground rules for a valid run

- One model server at a time. Record `sysctl vm.swapusage` before and after; discard or flag runs where swap grew.
- Record versions (runtime, engine, model file and quant) in `--notes` or the label.
- Put the machine in the result: chip, memory, macOS version, and anything heavy running (VMs, builds).
- Compare setups back to back under the same conditions.

## Adding results

```sh
make bench-speed URL=http://127.0.0.1:8000 MODEL=local LABEL=m3max-64g-splash-katornith-q4km
```

Label format: `[machine-]<engine>-<model/quant>-<options>` (see [results/README.md](results/README.md)). Then update
the matching page in `docs/findings/` and add a line to `docs/journal.md`. Where possible, build tables from the
JSON (`make summary`) instead of typing them.

## Privacy

Agent benchmarks run on real projects and can leak code or names. Before every commit:

- Keep project-specific files (sandbox copies, graders, transcripts) in `.local/`, which is gitignored.
- Write words that must never be published (project names, your name, client names) into `.local/private-terms`,
  one per line.
- Run `make hooks` once. The pre-commit hook then runs `tools/check_private.py`, which blocks home-directory paths,
  temp paths, e-mail addresses, local host names and your private terms.

## Code style

Python 3.11+, standard library only (`tokenizers` for the long-context scripts). Each script has a docstring with a
usage line, uses `argparse`, and writes one JSON result under `results/<category>/`. `make check` compiles all
scripts, runs ruff if installed, and runs the privacy check.
