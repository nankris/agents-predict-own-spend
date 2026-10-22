# Can a coding agent guess its own bill? Codex edition

Before each of 11 small bug-fix tasks I asked Codex one thing: "how many tokens, output tokens and model calls will this take?" It had to answer before opening a single file. Then it did the task, and I compared.

**It got the total roughly right and everything underneath it wrong.**

- Total tokens: it guessed about 45K for a typical one-file fix. The real number was about 60K. Median miss: it used 1.3× what it predicted. That's closer than I expected.
- Output tokens: it guessed 2,000–3,000. It wrote 200–600. A 7–8× overestimate, every single time.
- Model calls: it guessed 6–10. It used 4, almost every time, even on the 14-package task where it guessed 16.

So the "right" total is an accident of two errors cancelling: it imagines a lot of writing and many steps, and it forgets that every step re-sends a ~14K-token prompt of instructions and tool definitions. The cost of an agent run is mostly re-reading, not writing.

It also couldn't tell tasks apart. Across ten different one-file bugs, its guesses had basically no relationship to what they cost (log-correlation 0.25). Ask twice and you get a different guess: one task got 28K the first time and 65K the second.

The one thing it did know: a 14-package job costs more than a 1-file job. It guessed 90–95K; it used 95K.

Claude Opus and Haiku, on the same prompt, made the same output mistake (3–4× too high), but leaned slightly over on totals instead of under.

**Takeaway:** don't budget from an agent's self-estimate. A flat "≈60K tokens per small fix, mostly cached prefix" from your own logs beats it. All $ numbers are API-equivalent estimates (≈2.7¢ a run); Plus is a flat subscription.
