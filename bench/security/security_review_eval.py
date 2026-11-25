#!/usr/bin/env python3
"""Security code-review check for any OpenAI-compatible server: does the model spot the planted vulnerability?

Defensive only. 18 short snippets with one planted flaw each (10 common, 8 subtler ones a quick skim misses),
plus 3 correct snippets where the right answer is "no real vulnerability" (catches false alarms). Graded by regex on the vulnerability name or its CWE id (rough, but identical for
every model). This measures security-analysis ability for a code-review harness -- it does NOT ask for, and does
not score, exploit code or attack payloads.

A model that refuses to review a snippet simply scores 0 on it (recorded as refused=True), which is itself a
useful signal when choosing a model for security review.

Only scores, times and token counts are saved, never the model's prose.

  python3 -I bench/security/security_review_eval.py --url http://127.0.0.1:8000 --label NAME [--extra JSON]
"""
import argparse, json, re, time, urllib.request
from pathlib import Path

# (name, language, snippet, accept-regex, refusal-is-wrong). One planted flaw each.
TASKS = [
    ("sqli", "python", '''@app.get("/user")
def user():
    name = request.args["name"]
    row = db.execute(f"SELECT id, email FROM users WHERE name = '{name}'").fetchone()
    return jsonify(row)''',
     r"sql\s*inject|CWE[- ]?89|parameteri[sz]e|prepared statement"),

    ("command_injection", "python", '''@app.post("/ping")
def ping():
    host = request.json["host"]
    return subprocess.check_output(f"ping -c 1 {host}", shell=True)''',
     r"command\s*inject|os command|CWE[- ]?78|shell=true|shell\s*inject"),

    ("path_traversal", "javascript", '''app.get("/files", (req, res) => {
  const p = path.join(__dirname, "uploads", req.query.name);
  res.sendFile(p);
});''',
     r"path\s*travers|directory\s*travers|CWE[- ]?22|\.\./|arbitrary file"),

    ("ssrf", "python", '''@app.post("/preview")
def preview():
    url = request.json["url"]
    r = requests.get(url, timeout=5)
    return {"body": r.text[:500]}''',
     r"ssrf|server.side request forgery|CWE[- ]?918|internal (service|network|metadata)"),

    ("insecure_deserialization", "python", '''@app.post("/session")
def load_session():
    data = base64.b64decode(request.cookies["session"])
    return {"user": pickle.loads(data)["user"]}''',
     r"deseriali[sz]|pickle|CWE[- ]?502|remote code exec|\bRCE\b|arbitrary code"),

    ("stored_xss", "javascript", '''app.get("/search", (req, res) => {
  res.send(`<h1>Results for ${req.query.q}</h1>`);
});''',
     r"\bxss\b|cross.site scripting|CWE[- ]?79|html (injection|escap)|saniti[sz]e"),

    ("jwt_unverified", "javascript", '''function auth(req, res, next) {
  const token = req.headers.authorization.split(" ")[1];
  req.user = jwt.decode(token).sub;   // decode, not verify
  next();
}''',
     r"not\s+verif|without\s+verif|no (signature|verification)|jwt\.verify|CWE[- ]?34[57]|CWE[- ]?287|forge"),

    ("hardcoded_secret", "go", '''const awsSecret = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

func newClient() *s3.Client {
    return s3.New(s3.Options{Credentials: creds.NewStatic("AKIAEXAMPLE", awsSecret, "")})
}''',
     r"hard.?cod|secret.*(in|into).*(source|code|repo)|CWE[- ]?798|embedded credential|leaked"),

    ("weak_hash", "python", '''def store_password(user, pw):
    digest = hashlib.md5(pw.encode()).hexdigest()
    db.save(user, digest)''',
     r"md5|weak hash|insecure hash|CWE[- ]?327|CWE[- ]?916|bcrypt|argon2|scrypt|no salt|unsalted"),

    ("idor", "python", '''@app.get("/invoice/<int:iid>")
@login_required
def invoice(iid):
    return Invoice.query.get(iid).as_json()   # no owner check''',
     r"idor|insecure direct object|CWE[- ]?639|CWE[- ]?285|authori[sz]ation|owner(ship)? check|access control"),

    # --- harder: subtler flaws a quick skim misses ---
    ("timing_compare", "python", '''def check_webhook(req):
    sig = hmac.new(SECRET, req.body, "sha256").hexdigest()
    if sig != req.headers["X-Signature"]:
        abort(401)''',
     r"timing|constant.time|compare_digest|CWE[- ]?208"),

    ("toctou", "python", '''def save_upload(path, data):
    if not os.path.exists(path):
        with open(path, "w") as f:   # runs as root
            f.write(data)''',
     r"toctou|time.of.check|race condition|CWE[- ]?367|symlink"),

    ("redos", "javascript", '''const EMAIL = /^([a-zA-Z0-9]+)*@example\\.com$/;
app.post("/signup", (req, res) => {
  if (!EMAIL.test(req.body.email)) return res.status(400).end();
  createUser(req.body);
});''',
     r"redos|regular expression denial|catastrophic backtrack|CWE[- ]?1333|exponential"),

    ("mass_assignment", "javascript", '''app.put("/me", auth, async (req, res) => {
  await User.updateOne({ _id: req.user.id }, req.body);
  res.json({ ok: true });
});''',
     r"mass.assign|over.?posting|CWE[- ]?915|isAdmin|role|privilege escalation|allow.?list|whitelist"),

    ("open_redirect", "python", '''@app.get("/login/done")
def done():
    return redirect(request.args.get("next", "/"))''',
     r"open redirect|unvalidated redirect|CWE[- ]?601|phishing"),

    ("xxe", "java", '''DocumentBuilderFactory f = DocumentBuilderFactory.newInstance();
Document doc = f.newDocumentBuilder().parse(request.getInputStream());
String name = doc.getElementsByTagName("name").item(0).getTextContent();''',
     r"\bxxe\b|xml external entit|CWE[- ]?611|external entit|disallow-doctype"),

    ("prototype_pollution", "javascript", '''function merge(dst, src) {
  for (const k in src) {
    if (typeof src[k] === "object") merge(dst[k] ??= {}, src[k]);
    else dst[k] = src[k];
  }
}
app.post("/prefs", (req, res) => { merge(userPrefs, req.body); res.end(); });''',
     r"prototype pollution|__proto__|CWE[- ]?1321|constructor\.prototype"),

    ("zip_slip", "python", '''def extract(upload, dest):
    with zipfile.ZipFile(upload) as z:
        for m in z.infolist():
            out = os.path.join(dest, m.filename)
            with open(out, "wb") as f:
                f.write(z.read(m))''',
     r"zip.?slip|path travers|directory travers|CWE[- ]?22|\.\./"),
]

# Clean snippets: correct code. A good reviewer says there is no serious vulnerability instead of inventing one.
CLEAN = [
    ("clean_param_sql", "python", '''@app.get("/me/orders")
@login_required
def my_orders():
    rows = db.execute("SELECT id, total FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT 50",
                      (current_user.id,)).fetchall()
    return jsonify([dict(r) for r in rows])'''),
    ("clean_subprocess", "python", '''ALLOWED = {"api.internal.example.com", "db.internal.example.com"}

def health_check(host: str) -> bool:
    """Called by our scheduler with hosts from ALLOWED only; not exposed over HTTP."""
    if host not in ALLOWED:
        raise ValueError("unknown host")
    return subprocess.run(["ping", "-c", "1", host], capture_output=True, timeout=5).returncode == 0'''),
    ("clean_hash", "python", '''def store_password(user, pw):
    db.save(user, bcrypt.hashpw(pw.encode(), bcrypt.gensalt(rounds=12)))'''),
]
# A clean verdict: the answer says plainly there is no real vulnerability (not just "no SQL injection").
CLEAN_OK = re.compile(r"\bno (significant |serious |obvious |major |real |critical |apparent |exploitable )?"
                      r"(security )?(vulnerabilit|issue|flaw|problem)|not vulnerable|"
                      r"\b(is|looks|appears) (secure|safe)\b|nothing (exploitable|to fix)", re.I)

PROMPT = ("You are reviewing code for security. If this {lang} snippet has a security vulnerability, name the most "
          "serious one: its class and CWE id if you know it, in one or two sentences. If it has no real security "
          "vulnerability, say so plainly.\n\n```{lang}\n{code}\n```")

REFUSAL = re.compile(r"\b(I can('|no)?t|I am (unable|not able)|I won'?t|cannot assist|can'?t help|not able to help|"
                     r"against my|unable to assist)\b", re.I)


def ask(url, prompt, extra, max_tokens):
    body = {"messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens,
            "temperature": 0, **(extra or {})}
    t = time.perf_counter()
    req = urllib.request.Request(url.rstrip("/") + "/v1/chat/completions", json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=1800))
    msg = r["choices"][0]["message"]
    text = (msg.get("content") or "")
    usage = r.get("usage", {})
    return text, usage.get("completion_tokens", 0), time.perf_counter() - t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--extra", default=None)
    ap.add_argument("--max-tokens", type=int, default=16000)
    ap.add_argument("--out", default=None, help="results json (default results/security/sec-LABEL.json)")
    ap.add_argument("--dump", default=None, help="also write every answer to this file (keep it outside the repo)")
    a = ap.parse_args()
    extra = json.loads(a.extra) if a.extra else None
    rows, hits, refusals, toks, wall = [], 0, 0, 0, 0.0
    dump = []
    empty = 0
    for name, lang, code, rx, *_ in TASKS:
        text, ct, w = ask(a.url, PROMPT.format(lang=lang, code=code), extra, a.max_tokens)
        # grade on the visible answer only (strip any <think> block)
        answer = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
        refused = bool(REFUSAL.search(answer)) and not re.search(rx, answer, re.I)
        empty += not answer.strip()
        hit = bool(re.search(rx, answer, re.I))
        hits += hit; refusals += refused; toks += ct; wall += w
        dump.append(f"## {name} hit={hit}\n{answer.strip()}\n")
        rows.append({"task": name, "hit": hit, "refused": refused, "completion_tokens": ct, "wall_s": round(w, 1)})
        print(f"{a.label} {name:24} {'HIT ' if hit else 'miss'}{' REFUSED' if refused else ''} "
              f"{w:5.1f}s {ct} tok", flush=True)
    clean_ok = 0
    for name, lang, code in CLEAN:
        text, ct, w = ask(a.url, PROMPT.format(lang=lang, code=code), extra, a.max_tokens)
        answer = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
        ok = bool(CLEAN_OK.search(answer))
        empty += not answer.strip()
        clean_ok += ok; toks += ct; wall += w
        dump.append(f"## {name} clean_ok={ok}\n{answer.strip()}\n")
        rows.append({"task": name, "clean_ok": ok, "completion_tokens": ct, "wall_s": round(w, 1)})
        print(f"{a.label} {name:24} {'ok  ' if ok else 'FALSE ALARM'} {w:5.1f}s {ct} tok", flush=True)
    if a.dump:
        Path(a.dump).write_text("\n".join(dump))
    out = Path(a.out or f"results/security/sec-{a.label}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    basic = sum(r.get("hit", False) for r in rows[:10])
    summary = {"found": hits, "total": len(TASKS), "found_basic": basic, "found_subtle": hits - basic,
               "subtle_total": len(TASKS) - 10, "clean_ok": clean_ok, "clean_total": len(CLEAN),
               "refused": refusals, "empty_answers": empty, "wall_s_total": round(wall, 1), "tokens_total": toks}
    out.write_text(json.dumps({"label": a.label, "extra": extra, "when": time.strftime("%Y-%m-%d %H:%M:%S"),
                               "summary": summary, "rows": rows}, indent=1))
    print(f"== {a.label}: found {hits}/{len(TASKS)} (basic {basic}/10, subtle {hits - basic}/{len(TASKS) - 10}), "
          f"clean {clean_ok}/{len(CLEAN)}, refused {refusals}, empty {empty}, {round(wall)}s, saved {out}")


if __name__ == "__main__":
    main()
