# I asked Claude Code to guess its own token bill first. It guessed "60,000" every time.

*Draft. Tech in General experiment #020. 22 headless Claude Code runs, 2026-10-15 IST.*

Before each task, the agent had to write one line: how many total tokens, output tokens and model calls it expected. Then it did the task. 11 tasks, Opus 5.5 and Haiku 5.5.

**Opus said 60,000 / 1,500 / 4 for all ten small tasks.** That's roughly right for total tokens (actual 52–86K), because Claude Code's ~16K-token system prompt sent 3–4 times lands right about there. But it guessed 3–4× too much output, and on the one big task it guessed 400K and used 99K.

**Haiku changed its guesses, and they didn't track anything.** It was off by 0.6× to 1.7×, with a correlation of 0.40 to the real number (the published figure is 0.39).

**Both overestimated output, not under.** The common claim is that models underestimate their usage. Here they consistently thought they'd write more than they did.

**Takeaway.** Don't use the agent's own guess as a budget. Measure a few runs and use those — on Claude Code, cost per task is very repeatable (see #010b).

*Token counts from Claude Code's usage output; cost figures are API-equivalent estimates, Pro isn't billed per token.*
