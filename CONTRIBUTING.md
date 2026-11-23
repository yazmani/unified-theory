# Contributing

Thanks for helping map what runs well on Apple Silicon. The most useful contributions:

1. **Results from another Mac** (M1–M5, any memory size) for models already here.
2. **A new model, runtime or harness** measured with the existing scripts.
3. **Better benchmarks**, especially a harder coding-quality set.

## Ground rules for a valid run

- One model server at a time. Check `sysctl vm.swapusage` before and after; discard runs where swap grew.
- Record versions (runtime, engine, model file and quant) in `--notes` or the label.
- Put the machine in the result: chip, memory, macOS version, and anything heavy running (VMs, builds).
- Compare setups back to back under the same conditions.

## Adding results

```sh
make bench-speed URL=http://127.0.0.1:8092 LABEL=m3max-64g-tiel-iq4xs-mtp
```

Label format: `[machine-]<engine>-<model/quant>-<options>` (see [results/README.md](results/README.md)). Then add
or update the matching page in `docs/findings/` and a line in `docs/journal.md`. Keep tables generated from the
JSON (`make summary`) rather than typed by hand where you can.

## Privacy

Agent benchmarks run on real projects, so they can leak code or names. Before every commit:

- Keep project-specific files (sandbox copies, graders, transcripts) in `.local/`, which is gitignored.
- Write words that must never be published (project names, your name, client names) into `.local/private-terms`,
  one per line.
- Run `make hooks` once: a pre-commit hook then runs `tools/check_private.py`, which blocks home-directory paths,
  temp paths, e-mail addresses, local host names and your private terms.

## Code style

Python 3.11+, standard library first (`tokenizers` only for the long-context scripts). Each script: a docstring with
a usage line, `argparse`, one JSON result under `results/<category>/`. `make check` compiles everything, runs ruff if
installed, and runs the privacy check.
