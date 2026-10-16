# #020 Can Claude Code predict its own spend?

**Question.** Ask the agent, before it starts, how many tokens and model calls the task will take. How close is it?

**Short answer.** 11 tasks × 2 models = 22 runs, all passed, all gave a parseable estimate. Both models **over**-estimated, not under (the cited result says models underestimate). **Opus 5.5 answered "60,000 total / 1,500 output / 4 calls" for all 10 small tasks** — an anchor that happened to land within 0.86–1.43× of actual total tokens, while output was overestimated ~3.7× (median actual/estimate 0.27) and calls by 1.3×. On the bigger 14-package task it guessed 400K and used 99K (4× over). **Haiku 5.5** varied its guesses (60K/120K/250K) but they didn't track reality: actual/estimate 0.57–1.72, log-correlation 0.40 for total tokens (≈ the cited 0.39) and 0.22 for output. Opus's log-correlation was 0.74 total / 0.86 output, but almost all of that comes from one big-vs-small distinction (it gave only two distinct estimates).

## Setup
- Claude Code 2.1.300, Pro; `--model opus` (claude-opus-5-5) and `--model haiku` (claude-haiku-5-5), default effort; headless `claude -p … --output-format stream-json --verbose --dangerously-skip-permissions --strict-mcp-config --no-session-persistence`, fresh fixture copy per run.
- Prompt = `scripts/preamble.txt` ("Before you do anything else, write one line … `ESTIMATE total_tokens=<N> output_tokens=<N> model_calls=<N>` — total_tokens is everything this task will consume across all your model calls (all input re-sent each call, incl. system prompt and tool definitions, plus output) …") + the task. The estimate is made before the model has seen the files.
- Tasks: 10 single packages (N01_median, N02_duration, N03_csv, T02_duplicate, T05_stale, T06_neardup, T07_multihunk, T08_insert, T09_delete, T10_replace_all; "Make `node test.js` pass…") + SUITE14 (14 packages, #010 prompt). 2 at a time, 2026-10-14 ~20:06–20:08 UTC.
- Actual = Claude's `usage` (input + cache write + cache read + output), `output_tokens`, `num_turns`. Est. $ (`total_cost_usd`) is in `results/runs.csv` — **API-equivalent estimate; Pro isn't billed per token.**

## Exact commands
```bash
source /workspace/tools/setup.sh
scripts/harness/driver_cc.sh scripts/jobs.txt 2 results/driver.log
/workspace/tools/mlenv/bin/python scripts/analyze.py
```

## Results
| Model | Runs | actual/estimate, total tokens (median, range) | actual/estimate, output | actual/estimate, calls | log-corr total | log-corr output |
|---|---|---|---|---|---|---|
| Opus 5.5 | 11 | 0.87 (0.25–1.43) | 0.27 | 0.75 | 0.74 | 0.86 |
| Haiku 5.5 | 11 | 1.22 (0.57–1.72) | 0.41 | 0.62 | 0.40 | 0.22 |

Per-run estimates vs actuals: `results/estimates.csv`. Chart (`results/chart.png`): estimate vs actual, log-log, both models.

## Caveats
- The estimate is a pre-task guess with no file contents; a "after reading the code" estimate might do better.
- Opus's small-task accuracy is an anchor (the same number every time), not a prediction; with only two distinct guesses its correlation is not meaningful.
- Small, homogeneous tasks: the actual range is narrow (51K–141K), which caps how much a predictor can show.
- Asking for the estimate itself adds a few output tokens per run.
