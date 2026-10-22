# Can Codex predict its own token spend? (Codex counterpart)

**Question.** Ask the agent, before it starts, how many tokens and model calls the task will take. How close is it? Codex CLI counterpart of [`claude-predict-own-spend`](../claude-predict-own-spend/) (same tasks, same estimate prompt).

**Short answer (this build, these tasks).** 22/22 runs passed and every run gave a parseable `ESTIMATE` line as its first message. Codex (gpt-6.1-sol) was **roughly right on total tokens, way off on output, and couldn't tell tasks apart**:
- **Total tokens: slight underestimate.** Median actual/estimate **1.30** (range 0.90–2.51); 19/22 within 0.5–2×. It guessed 28K–65K for the single-package tasks, which all cost 58K–85K. Log-correlation 0.57 overall, but that's almost all the "one package vs 14 packages" split (SUITE14 guesses of 90K/95K were within 6% of the actual 95K). **Among the 10 single-package tasks the log-correlation was 0.25.**
- **Output tokens: ~7.6× overestimate.** It guessed 1,800–3,000 output tokens per small task; actual was 214–628 (median actual/estimate **0.13**, 0/22 within 2×). On SUITE14: guessed 6–7K, used ~1.3K.
- **Model calls: ~1.7× overestimate.** Guessed 6–10 (16 for SUITE14); actual was 4 in 20 of 22 runs (5 in two), including SUITE14, where Codex batch-fixed all 14 packages in 4 calls. Log-correlation 0.07.
- **Not repeatable.** The same task got different guesses on the two reps in 6 of 11 cases, e.g. T06/T09 got 28K then 65K (or vice versa).

Same direction as the Claude arm for output (both overestimate it 3–8×), opposite for total tokens (Claude Opus/Haiku slightly *over*estimated total; Codex slightly *under*). Codex's per-run fixed prefix (~13–15K tokens re-sent on each of 4 calls) is what it seems to miss.

## Setup
- Codex CLI `codex-cli 0.162.1`, model `gpt-6.1-sol`, default reasoning effort, ChatGPT Plus login. Headless `codex exec --json --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox -C <fresh temp copy>` via the shared harness (`scripts/harness/run_one.py`), one fresh session per run.
- Prompt = `scripts/preamble.txt` (identical to the Claude arm: "Before you do anything else, write one line in exactly this format … `ESTIMATE total_tokens=<N> output_tokens=<N> model_calls=<N>` — where total_tokens is everything this task will consume across all your model calls (all input context re-sent on each call, including system prompt and tool definitions, plus output) …") + ` Task: ` + the task prompt. The estimate is the model's first output, before it has opened any file.
- Tasks (11, same as the Claude arm): 10 single packages from `SUITE14` (N01_median, N02_duration, N03_csv, T02_duplicate, T05_stale, T06_neardup, T07_multihunk, T08_insert, T09_delete, T10_replace_all; "Make `node test.js` pass by fixing the code. Do not edit test.js.") + the whole `SUITE14` dir (14 packages, `scripts/suite_prompt.txt`, pass = `node run_all.js`). 2 reps each = 22 runs, 3 at a time, 2026-10-14 20:10–20:13 UTC (2026-10-15 01:40–01:43 IST).
- Pass = check command exits 0 and no `test.js` changed (hash check).
- Actual = the session rollout's cumulative `total_token_usage` (input incl. cached + output), `output_tokens` (includes the few reasoning tokens), and the number of model responses (`token_count` events).
- Cost: gpt-6.1-sol API list price $2.00/M uncached input, $0.10/M cached, $10.00/M output (https://developers.openai.com/api/docs/models/gpt-6.1-sol, checked 2026-10-14). **API-equivalent estimates only; Plus is a flat subscription.** Mean $0.027 per run.

## Exact commands
```bash
# activate a Python environment with matplotlib and numpy; Codex CLI on PATH
scripts/driver.sh scripts/jobs.txt 3 results/driver.log
python scripts/analyze.py
```

## Results
| | Runs | Pass | Parsed | actual/estimate median (range) | within 0.5–2× | log-corr (all 22) | log-corr (10 small tasks only) |
|---|---|---|---|---|---|---|---|
| Total tokens | 22 | 22 | 22 | 1.30 (0.90–2.51) | 19/22 | 0.57 | 0.25 |
| Output tokens | | | | 0.13 (0.09–0.28) | 0/22 | 0.76 | −0.02 |
| Model calls | | | | 0.60 (0.25–0.67) | 19/22 | 0.07 | 0.30 |

Mean actual total on single-package tasks: 63.1K tokens. Mean wall 18.8 s. Per-run estimates vs actuals: `results/estimates.csv`. Chart: `results/chart.png` (estimate vs actual, log-log, SUITE14 in red).

Comparison with the Claude arm (from `../claude-predict-own-spend/README.md`, same tasks/prompt, 1 run per task):

| Model | actual/est total | actual/est output | actual/est calls | log-corr total |
|---|---|---|---|---|
| Codex gpt-6.1-sol (this repo, 22 runs) | 1.30 | 0.13 | 0.60 | 0.57 |
| Claude Opus 5.5 (11 runs) | 0.87 | 0.27 | 0.75 | 0.74 |
| Claude Haiku 5.5 (11 runs) | 1.22 | 0.41 | 0.62 | 0.40 |

## Caveats
- The estimate is a blind guess before reading files; an "after reading the code" estimate might do better. Not tested.
- Small, homogeneous tasks: the actual range is narrow (58K–95K), which caps how much any predictor can show. The total-token correlation is mostly one big-vs-small distinction.
- 2 reps per task; estimates varied between reps, so the medians are more meaningful than any single run.
- Asking for the estimate adds a few output tokens per run (a default arm with no estimate, from my [compression vs code edits study](https://github.com/nankris/compression-vs-code-edits), averaged 61.1K total / 293 output on similar tasks vs 63.1K / 345 here).
- Other Codex runs (from my [diffs vs full files study](https://github.com/nankris/diffs-vs-full-files)) used the same account in the same minutes; rate-limit percentages in `runs.csv` include them.

## Files
- `scripts/preamble.txt`, `scripts/suite_prompt.txt`, `scripts/jobs.txt`, `scripts/driver.sh`, `scripts/analyze.py`, `scripts/harness/` (copy of the shared harness and fixtures)
- `results/runs.csv` (one row per run), `results/estimates.csv`, `results/summary.csv`, `results/chart.png`, `results/driver.log`, `results/raw/*.jsonl` (raw `codex exec --json` streams)
