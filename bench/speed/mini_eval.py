#!/usr/bin/env python3
"""Tiny functional coding check (pass@1, greedy) for any OpenAI-compatible server.

Not a leaderboard: 10 hand-written Python tasks with hidden asserts, to catch a fast model that
writes broken code. Also records wall time and completion tokens per task (the cost of thinking).

  python3 -I bench/speed/mini_eval.py --url http://127.0.0.1:8092 --label NAME [--extra JSON]
"""
import argparse, json, re, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path

TASKS = [
    ("two_sum", "def two_sum(nums: list[int], target: int) -> tuple[int, int]:\n    \"\"\"Return indices (i, j), i < j, with nums[i] + nums[j] == target. Exactly one answer exists.\"\"\"",
     "assert two_sum([2,7,11,15],9)==(0,1)\nassert two_sum([3,2,4],6)==(1,2)\nassert two_sum([3,3],6)==(0,1)"),
    ("roman", "def to_roman(n: int) -> str:\n    \"\"\"Convert 1 <= n <= 3999 to a Roman numeral.\"\"\"",
     "assert to_roman(1994)=='MCMXCIV'\nassert to_roman(3999)=='MMMCMXCIX'\nassert to_roman(4)=='IV'\nassert to_roman(58)=='LVIII'"),
    ("merge_intervals", "def merge(intervals: list[list[int]]) -> list[list[int]]:\n    \"\"\"Merge overlapping closed intervals; return them sorted by start. Touching intervals ([1,2],[2,3]) merge.\"\"\"",
     "assert merge([[1,3],[2,6],[8,10],[15,18]])==[[1,6],[8,10],[15,18]]\nassert merge([[1,4],[4,5]])==[[1,5]]\nassert merge([])==[]\nassert merge([[5,7],[1,2]])==[[1,2],[5,7]]"),
    ("lru", "class LRUCache:\n    \"\"\"LRUCache(capacity). get(key) -> value or -1. put(key, value) evicts the least recently used key when full. Both O(1).\"\"\"",
     "c=LRUCache(2);c.put(1,1);c.put(2,2);assert c.get(1)==1;c.put(3,3);assert c.get(2)==-1;c.put(4,4);assert c.get(1)==-1;assert c.get(3)==3;assert c.get(4)==4"),
    ("parse_duration", "def parse_duration(s: str) -> int:\n    \"\"\"Parse strings like '1h30m', '45s', '2h', '1h2m3s', '90m' into total seconds. Raise ValueError on empty or invalid input (e.g. '', 'abc', '5x', 'h1').\"\"\"",
     "assert parse_duration('1h30m')==5400\nassert parse_duration('45s')==45\nassert parse_duration('1h2m3s')==3723\nassert parse_duration('90m')==5400\nfor bad in ['', 'abc', '5x', 'h1']:\n    try:\n        parse_duration(bad); raise SystemExit('no error for '+repr(bad))\n    except ValueError: pass"),
    ("topo", "def topo_sort(deps: dict[str, list[str]]) -> list[str]:\n    \"\"\"deps maps node -> nodes it depends on (which must come before it). Return an order containing every node mentioned (keys and values). Raise ValueError on a cycle.\"\"\"",
     "o=topo_sort({'a':['b','c'],'b':['c'],'c':[]});assert o.index('c')<o.index('b')<o.index('a')\no=topo_sort({'x':['y']});assert set(o)=={'x','y'} and o.index('y')<o.index('x')\ntry:\n    topo_sort({'a':['b'],'b':['a']}); raise SystemExit('no cycle error')\nexcept ValueError: pass"),
    ("flatten", "def flatten(obj: dict, sep: str = '.') -> dict:\n    \"\"\"Flatten nested dicts: {'a': {'b': 1}, 'c': 2} -> {'a.b': 1, 'c': 2}. Lists are values, not recursed. Empty nested dicts are dropped.\"\"\"",
     "assert flatten({'a':{'b':1,'c':{'d':2}},'e':3})=={'a.b':1,'a.c.d':2,'e':3}\nassert flatten({'a':[1,{'b':2}]})=={'a':[1,{'b':2}]}\nassert flatten({'a':{}})=={}\nassert flatten({'a':{'b':1}},sep='/')=={'a/b':1}"),
    ("rle", "def rle_encode(s: str) -> str:\n    \"\"\"Run-length encode: 'aaabccdddd' -> '3a1b2c4d'. Empty -> ''.\"\"\"\n\ndef rle_decode(s: str) -> str:\n    \"\"\"Inverse of rle_encode; counts may have several digits ('12a' -> 12 a's).\"\"\"",
     "assert rle_encode('aaabccdddd')=='3a1b2c4d'\nassert rle_encode('')==''\nassert rle_decode('12a1b')=='a'*12+'b'\nimport random\nfor _ in range(50):\n    t=''.join(random.choice('ab') for _ in range(random.randint(0,30)))\n    assert rle_decode(rle_encode(t))==t"),
    ("bank", "class Account:\n    \"\"\"Account(owner, balance=0). deposit(x) and withdraw(x) raise ValueError for x <= 0; withdraw raises ValueError if it would overdraw. transfer(other, x) moves money atomically (no change on error). history is a list of (kind, amount) tuples with kind in 'deposit','withdraw','transfer_out','transfer_in'.\"\"\"",
     "a=Account('a',100);b=Account('b')\na.transfer(b,30);assert a.balance==70 and b.balance==30\ntry:\n    a.transfer(b,1000); raise SystemExit('overdraw allowed')\nexcept ValueError: pass\nassert a.balance==70 and b.balance==30\nassert ('transfer_out',30) in a.history and ('transfer_in',30) in b.history\nfor f in (a.deposit,a.withdraw):\n    try:\n        f(0); raise SystemExit('zero allowed')\n    except ValueError: pass"),
    ("median_stream", "class MedianFinder:\n    \"\"\"add(num) and median() -> float over all numbers added so far, both O(log n) or better.\"\"\"",
     "m=MedianFinder()\nfor x,e in [(5,5.0),(15,10.0),(1,5.0),(3,4.0)]:\n    m.add(x); assert m.median()==e, (x, m.median())\nimport random,statistics\nm=MedianFinder();xs=[]\nfor _ in range(200):\n    v=random.randint(-1000,1000);xs.append(v);m.add(v)\n    assert abs(m.median()-statistics.median(xs))<1e-9"),
]


def ask(url, prompt, extra, max_tokens):
    body = {"messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens, "temperature": 0, **(extra or {})}
    t = time.perf_counter()
    r = json.load(urllib.request.urlopen(urllib.request.Request(url.rstrip("/") + "/v1/chat/completions", json.dumps(body).encode(),
                                                                {"Content-Type": "application/json"}), timeout=1800))
    return r, time.perf_counter() - t


def extract(content):
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", content or "", re.S)
    return max(blocks, key=len) if blocks else (content or "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--extra", default=None)
    ap.add_argument("--max-tokens", type=int, default=8000)
    a = ap.parse_args()
    extra = json.loads(a.extra) if a.extra else None
    rows = []
    for name, sig, test in TASKS:
        prompt = f"Implement the following in Python. Return one complete ```python code block and nothing else.\n\n```python\n{sig}\n```"
        r, wall = ask(a.url, prompt, extra, a.max_tokens)
        content = r["choices"][0]["message"].get("content") or ""
        code = extract(content)
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(code + "\n\n" + test + "\nprint('PASS')\n")
        try:
            p = subprocess.run([sys.executable, "-I", f.name], capture_output=True, text=True, timeout=30)
            ok = p.returncode == 0 and "PASS" in p.stdout
            err = "" if ok else (p.stderr or p.stdout).replace(f.name, f"{name}.py")[-300:]   # no machine temp paths in results
        except subprocess.TimeoutExpired:
            ok, err = False, "timeout"
        Path(f.name).unlink(missing_ok=True)
        toks = r["usage"]["completion_tokens"]
        rows.append({"task": name, "pass": ok, "wall_s": wall, "completion_tokens": toks,
                     "finish": r["choices"][0]["finish_reason"], "err": err})
        print(f"{a.label:34s} {name:16s} {'PASS' if ok else 'FAIL'} {wall:6.1f}s tok={toks}", flush=True)
    s = {"label": a.label, "extra": extra, "when": time.strftime("%Y-%m-%d %H:%M:%S"),
         "passed": sum(r["pass"] for r in rows), "total": len(rows),
         "wall_s_total": sum(r["wall_s"] for r in rows), "tokens_total": sum(r["completion_tokens"] for r in rows), "rows": rows}
    print(f"== {a.label}: {s['passed']}/{s['total']} pass, {s['wall_s_total']:.0f}s total, {s['tokens_total']} tokens")
    out = Path(f"results/eval/eval-{a.label}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(s, indent=1))


if __name__ == "__main__":
    main()
