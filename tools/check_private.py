#!/usr/bin/env python3
"""Fail if tracked (or staged) files contain private information, before anything leaves this machine.

Checks every file git tracks plus what is staged, for:
  - home-directory paths with a user name (/Users/<name>/, /home/<name>/) and temp/scratch paths
  - e-mail addresses (GitHub no-reply addresses are allowed)
  - local host names (*.local, *.lan)
  - every term listed in `.local/private-terms` (one per line, case-insensitive, `#` comments). That file is gitignored,
    so the words you want to keep private are never committed themselves.

  python3 tools/check_private.py          # exit 1 and list hits
  make hooks                              # run it automatically before every commit
"""
import re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATTERNS = {
    "home path": re.compile(r"/(?:Users|home)/(?!runner\b|USER\b|you\b|<)[A-Za-z0-9._-]+/"),
    "temp path": re.compile(r"/private/(?:tmp|var)/|/var/folders/"),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@(?!users\.noreply\.github\.com)(?!anthropic\.com\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "host name": re.compile(r"\b[A-Za-z0-9-]+\.(?:lan|local)\b(?!/)"),
}
SKIP = {"tools/check_private.py"}


def tracked_files():
    out = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout
    return [f for f in out.split("\0") if f and f not in SKIP]


def private_terms():
    p = ROOT / ".local" / "private-terms"
    if not p.exists():
        return []
    return [t.strip().lower() for t in p.read_text().splitlines() if t.strip() and not t.lstrip().startswith("#")]


def main():
    terms, hits = private_terms(), []
    for f in tracked_files():
        path = ROOT / f
        if not path.is_file():
            continue
        try:
            text = path.read_text("utf-8")
        except UnicodeDecodeError:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            low = line.lower()
            for name, rx in PATTERNS.items():
                if rx.search(line):
                    hits.append((f, n, name, rx.search(line).group(0)))
            for t in terms:
                if t in low:
                    hits.append((f, n, "private term", "<from .local/private-terms>"))
    for f, n, kind, what in hits:
        print(f"{f}:{n}: {kind}: {what}")
    if hits:
        print(f"\n{len(hits)} possible leak(s). Fix them, or adjust the pattern if it is a false positive.", file=sys.stderr)
        sys.exit(1)
    print(f"privacy check: clean ({len(terms)} private terms checked)")


if __name__ == "__main__":
    main()
