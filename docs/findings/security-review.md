# Can a local model review code for security flaws? Do uncensored builds do it better?

**Current answer (2026-11-25):** any good coder does it well, and uncensored or security-tuned builds don't do it
better. Every model tested found 16–18 of 18 planted flaws, and none refused.

## The check

`bench/security_review_eval.py` asks the model to review 21 short snippets:

- **10 common flaws:** SQL injection, command injection, path traversal, SSRF, insecure deserialization (pickle),
  stored XSS, unverified JWT, hard-coded secret, unsalted MD5 passwords, IDOR.
- **8 subtler flaws:** timing-unsafe comparison, TOCTOU, ReDoS, mass assignment, open redirect, XXE, prototype
  pollution, zip slip.
- **3 correct snippets** where the right answer is "no real vulnerability" (an owner-scoped query behind a login, a
  subprocess call with a fixed allow-list, bcrypt with 12 rounds).

Answers are graded by regex on the vulnerability class or CWE; empty answers and refusals are counted. It measures
whether a model can spot flaws in a review, and asks for no exploit code. A first version had "clean" snippets with
real gaps and a 4,000-token cap that cut off long thinking; both were fixed before the numbers below.

## Results

| Model | Runtime | Flaws found (of 18) | Clean judged clean (of 3) |
|---|---|---|---|
| Qwen3.8-Flash-Next GSQ-RCO Coder | Splash | **18** | 3 |
| Qwen-AgentWorld-35B-A3B | Splash | **18** | 3 |
| Tiel-Coder oQ4e-MTP | oMLX | **18** | 3 |
| KAT-Ornith-HERO fusion | Splash | 17 | 3 |
| Tiel-Coder UD-Q4_K_XL | Splash | 17 | 3 |
| Kwaipilot KAT-Coder-V2.5-Dev | Splash | 17 | 3 |
| HauhauCS Aggressive (uncensored) | Splash | 17 | 3 |
| RavenX-CyberAgent (security-tuned) | Splash | 17 | 3 |
| Cyber-Tiel (abliterated) | Splash | 17 | 3 |
| Inkling-2-Mini oQ4e-mtp | oMLX | 17 | 3 |
| Qwen3.8-27B 4-bit + DSpine | dspine-hybrid-mlx | 17 | 3 |
| Qwen3.8-Flash-Next GSQ-RCO Q2_0 | Splash | 17 | 3 |
| Qwen3.8-27B GSQ-RCO IQ3_S | Splash | 16 | 3 |
| Qwopus3.6-35B-A3B-Coder | Splash | 16 | 3 |
| Qwen3.8-35B-A3B-Distill | Splash | 16 | 2 |

## Findings

1. **The check doesn't separate good coders**: 16–18 of 18 for every model. Every model found all 10 common flaws;
   the misses were all among the 8 subtler ones. A harder set (multi-file context, flaws that need data-flow reasoning) is an open thread.
2. **No refusals anywhere**, so uncensored builds have nothing to unlock on a defensive review. HauhauCS Aggressive
   matches the best coders, runs at 242 tok/s and has the fastest decode at 100K, so it's a reasonable pick if
   refusals ever get in the way.
3. **Security branding means little.** RavenX-CyberAgent scored like everyone else here and found 0 of 8 real issues
   in the Cline code review ([models](models.md)).
4. **Abliterated models are a risk in agents** with auto-approved commands; they were no better at coding either.

Raw data: [results/security](../../results/security/). Answers are dumped outside the repo with `--dump`.
