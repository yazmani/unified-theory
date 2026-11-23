#!/usr/bin/env python3
"""A coding-assistant style session: real source files pasted once (~N tokens), then follow-up requests on the same
conversation. Records each turn's wall time, prompt read time, cached tokens and answer length.

  python3 -I bench/agent_session.py URL LABEL [TARGET_TOKENS]

Source files come from a TensorSharp checkout (https://github.com/zhongkaifu/TensorSharp): set TENSORSHARP_DIR,
default ../../TensorSharp next to this repo.
"""
import json, os, sys, time, urllib.request
from pathlib import Path

url, label = sys.argv[1], sys.argv[2]
target_chars = int(sys.argv[3] if len(sys.argv) > 3 else 30000) * 3     # ~3 chars per token for code
# Neutral code (C# from the TensorSharp checkout next to this repo). Code about a model's own control tokens is avoided:
# Strata's Inkling output parser mangles answers that quote Inkling's <|...|> tokens (see INSIGHTS.md).
root = Path(os.environ.get("TENSORSHARP_DIR") or Path(__file__).resolve().parent.parent.parent / "TensorSharp")
files = ["TensorSharp.Chat/ConversationTranscriptStore.cs", "TensorSharp.Chat/ModelLifecycleService.cs",
         "TensorSharp.Chat/ChatHistoryPreparer.cs", "TensorSharp.Runtime/ChatProtocol.cs"]
dump, used = "", []
for f in files:
    p = root / f
    if not p.exists():
        continue
    txt = p.read_text("utf-8", "replace")
    if len(dump) + len(txt) > target_chars:
        txt = txt[: max(0, target_chars - len(dump))]
    dump += f"\n### file: {f}\n```csharp\n{txt}\n```\n"
    used.append(f)
    if len(dump) >= target_chars:
        break

turns = [
    "Here is part of a C# codebase.\n" + dump + "\nSummarize in 5 bullets what ConversationTranscriptStore.cs does.",
    "In ModelLifecycleService.cs, what happens when a model fails to load? Quote the relevant lines.",
    "Write an xUnit test for one public method of ChatHistoryPreparer. Show only the test class.",
    "Refactor the longest method in ConversationTranscriptStore.cs into two smaller methods. Show only the new code.",
    "Is there a thread-safety risk anywhere in these files? Answer in at most 5 sentences.",
    "List three types in ChatProtocol.cs and say in one line each what they are for.",
    "Which of these four files would you split first, and why? Two sentences.",
    "Write a one-paragraph commit message for the refactor you proposed earlier.",
]


def call(msgs):
    t = time.perf_counter()
    r = json.load(urllib.request.urlopen(urllib.request.Request(url + "/v1/chat/completions", json.dumps(
        {"messages": msgs, "max_tokens": 4000, "temperature": 0}).encode(), {"Content-Type": "application/json"}), timeout=3600))
    return r, time.perf_counter() - t


msgs, rows = [], []
for i, q in enumerate(turns, 1):
    msgs.append({"role": "user", "content": q})
    r, w = call(msgs)
    c = r["choices"][0]["message"].get("content") or ""
    msgs.append({"role": "assistant", "content": c})
    t = r.get("timings") or {}
    row = {"turn": i, "wall_s": w, "prompt_tokens": r["usage"]["prompt_tokens"],
           "cached": (r["usage"].get("prompt_tokens_details") or {}).get("cached_tokens"),
           "prompt_ms": t.get("prompt_ms"), "completion_tokens": r["usage"]["completion_tokens"],
           "finish": r["choices"][0]["finish_reason"], "answer_chars": len(c)}
    rows.append(row)
    print(f"{label} turn{i}: {w:6.1f}s prompt={row['prompt_tokens']} cached={row['cached']} read={(row['prompt_ms'] or 0)/1000:6.1f}s "
          f"gen={row['completion_tokens']} finish={row['finish']} chars={len(c)}", flush=True)
total = sum(r["wall_s"] for r in rows)
follow = sum(r["wall_s"] for r in rows[1:])
read_follow = sum((r["prompt_ms"] or 0) for r in rows[1:]) / 1000
print(f"== {label}: total {total:.0f}s, follow-ups {follow:.0f}s (of which prompt reading {read_follow:.0f}s)")
Path("results/sessions").mkdir(parents=True, exist_ok=True)
Path(f"results/sessions/session-{label}.json").write_text(json.dumps({"label": label, "files": used, "rows": rows,
                                                             "total_s": total, "followups_s": follow}, indent=1))
