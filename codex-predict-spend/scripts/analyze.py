"""Codex arm: parse the ESTIMATE line from each run's first agent message and compare with actual usage."""
import csv, json, re, os, statistics as st
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
E = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); R = f"{E}/results"
RX = re.compile(r"ESTIMATE\s+total_tokens=([\d,]+)\s+output_tokens=([\d,]+)\s+model_calls=([\d,]+)")
rows = []
for r in csv.DictReader(open(f"{R}/runs.csv")):
    est, first = None, True
    for l in open(os.path.join(E, r["raw_jsonl"])):
        it = (json.loads(l).get("item") or {})
        if it.get("type") == "agent_message":
            m = RX.search(it.get("text", ""))
            if m: est = [int(x.replace(",", "")) for x in m.groups()]; break
            first = False
    a_tot, a_out, a_calls = int(r["total_tokens"]), int(r["output_tokens"]), int(r["model_calls"])
    rows.append(dict(task=r["task"], rep=r["rep"], passed=r["passed"], parsed=int(est is not None),
                     est_first_message=int(first), est_total=est and est[0], est_output=est and est[1], est_calls=est and est[2],
                     act_total=a_tot, act_output=a_out, act_reasoning=r["reasoning_output_tokens"], act_calls=a_calls,
                     ratio_total=est and round(a_tot / est[0], 3), ratio_output=est and round(a_out / est[1], 3),
                     ratio_calls=est and round(a_calls / est[2], 3), est_cost_usd=r["est_cost_usd"], wall_s=r["wall_s"]))
rows.sort(key=lambda x: (x["task"], x["rep"]))
with open(f"{R}/estimates.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
ok = [r for r in rows if r["parsed"]]
def lc(a, b): return float(np.corrcoef(np.log(a), np.log(b))[0, 1])
summ = dict(runs=len(rows), passed=sum(int(r["passed"]) for r in rows), parsed=len(ok),
            distinct_total_estimates=len({r["est_total"] for r in ok}))
for k in ("total", "output", "calls"):
    rr = [r[f"ratio_{k}"] for r in ok]
    summ[f"median_actual_over_est_{k}"] = round(st.median(rr), 3); summ[f"min_{k}"] = min(rr); summ[f"max_{k}"] = max(rr)
    summ[f"logcorr_{k}"] = round(lc([r[f"est_{k}"] for r in ok], [r[f"act_{k}"] for r in ok]), 3)
    summ[f"within_0.5x_2x_{k}"] = sum(0.5 <= x <= 2 for x in rr)
summ["mean_act_total_small"] = round(st.mean(r["act_total"] for r in ok if r["task"] != "SUITE14"))
summ["mean_est_cost_usd"] = round(st.mean(float(r["est_cost_usd"]) for r in rows), 4)
summ["mean_wall_s"] = round(st.mean(float(r["wall_s"]) for r in rows), 1)
with open(f"{R}/summary.csv", "w", newline="") as f:
    w = csv.writer(f); [w.writerow([k, v]) for k, v in summ.items()]
print(json.dumps(summ, indent=1))
fig, ax = plt.subplots(1, 3, figsize=(15, 4.6))
for i, (k, lab) in enumerate([("total", "total tokens"), ("output", "output tokens"), ("calls", "model calls")]):
    x = [r[f"est_{k}"] for r in ok]; y = [r[f"act_{k}"] for r in ok]
    c = ["tab:red" if r["task"] == "SUITE14" else "tab:blue" for r in ok]
    ax[i].scatter(x, y, c=c, alpha=.75)
    lo, hi = min(x + y) * .7, max(x + y) * 1.4
    ax[i].plot([lo, hi], [lo, hi], "k--", lw=1, label="perfect")
    ax[i].set_xscale("log"); ax[i].set_yscale("log"); ax[i].set_xlim(lo, hi); ax[i].set_ylim(lo, hi)
    from matplotlib.ticker import NullFormatter, FuncFormatter
    fmt = FuncFormatter(lambda v, _: f"{v/1000:g}K" if v >= 1000 else f"{v:g}")
    for A in (ax[i].xaxis, ax[i].yaxis):
        A.set_minor_formatter(NullFormatter()); A.set_major_formatter(fmt)
    if k == "total":
        ax[i].set_xticks([20e3, 30e3, 50e3, 70e3, 100e3]); ax[i].set_yticks([20e3, 30e3, 50e3, 70e3, 100e3])
    if k == "output":
        ax[i].set_xticks([200, 500, 1e3, 2e3, 5e3]); ax[i].set_yticks([200, 500, 1e3, 2e3, 5e3])
    if k == "calls":
        ax[i].set_xticks([3, 4, 6, 8, 10, 16, 20]); ax[i].set_yticks([3, 4, 6, 8, 10, 16, 20])
    ax[i].set_xlabel(f"Codex's estimate ({lab})"); ax[i].set_ylabel(f"actual ({lab})")
    ax[i].set_title(f"{lab}: median actual/est {summ[f'median_actual_over_est_{k}']}, log-r {summ[f'logcorr_{k}']}", fontsize=10)
ax[0].scatter([], [], c="tab:blue", label="single package"); ax[0].scatter([], [], c="tab:red", label="SUITE14 (14 pkgs)"); ax[0].legend(fontsize=8)
fig.suptitle("Can Codex (gpt-6.1-sol) predict its own spend? 22 runs, estimate given before reading any file")
fig.tight_layout(); fig.savefig(f"{R}/chart.png", dpi=110)
