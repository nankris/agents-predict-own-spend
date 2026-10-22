import csv, os, json, re, statistics as S
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = list(csv.DictReader(open(f"{D}/results/runs.csv"))); out=[]
RE = re.compile(r"ESTIMATE\s+total_tokens=([\d,_]+)\s+output_tokens=([\d,_]+)\s+model_calls=([\d,_]+)")
for r in rows:
    est=None
    for l in open(f"{D}/{r['raw_jsonl']}"):
        if not l.strip(): continue
        d=json.loads(l)
        if d.get("type")=="assistant":
            for c in d["message"].get("content",[]):
                if c.get("type")=="text":
                    m=RE.search(c["text"])
                    if m and est is None: est=[int(x.replace(",","").replace("_","")) for x in m.groups()]
        if est: break
    o=dict(model=r["cond"],task=r["task"],passed=r["passed"],est_total=est[0] if est else "",est_output=est[1] if est else "",est_calls=est[2] if est else "",
           act_total=int(r["total_tokens"]),act_output=int(r["output_tokens"]),act_calls=int(r["num_turns"]),est_cost_usd=r["est_cost_usd"])
    if est:
        o["ratio_total"]=round(o["act_total"]/est[0],2) if est[0] else ""; o["ratio_output"]=round(o["act_output"]/est[1],2) if est[1] else ""; o["ratio_calls"]=round(o["act_calls"]/est[2],2) if est[2] else ""
    out.append(o)
w=csv.DictWriter(open(f"{D}/results/estimates.csv","w"),fieldnames=["model","task","passed","est_total","act_total","ratio_total","est_output","act_output","ratio_output","est_calls","act_calls","ratio_calls","est_cost_usd"]); w.writeheader(); w.writerows(out)
summ=[]
for m in ("opus","haiku"):
    rs=[o for o in out if o["model"]==m and o["est_total"]!=""]
    def corr(a,b): return round(float(np.corrcoef(np.log(a),np.log(b))[0,1]),3) if len(set(a))>1 and len(set(b))>1 else ""
    summ.append(dict(model=m,n=len(rs),parsed=len(rs),passed=sum(o["passed"]=="True" for o in out if o["model"]==m),
        median_ratio_total=S.median(o["ratio_total"] for o in rs),min_ratio_total=min(o["ratio_total"] for o in rs),max_ratio_total=max(o["ratio_total"] for o in rs),
        median_ratio_output=S.median(o["ratio_output"] for o in rs),median_ratio_calls=S.median(o["ratio_calls"] for o in rs),
        logcorr_total=corr([o["est_total"] for o in rs],[o["act_total"] for o in rs]),logcorr_output=corr([o["est_output"] for o in rs],[o["act_output"] for o in rs])))
w=csv.DictWriter(open(f"{D}/results/summary.csv","w"),fieldnames=list(summ[0])); w.writeheader(); w.writerows(summ)
for s in summ: print(s)
fig,ax=plt.subplots(1,2,figsize=(12,5))
for i,(k,t) in enumerate((("total","total tokens"),("output","output tokens"))):
    for m,c in (("opus","#d1602a"),("haiku","#2e6da4")):
        rs=[o for o in out if o["model"]==m and o["est_total"]!=""]
        ax[i].scatter([o[f"est_{k}"] for o in rs],[o[f"act_{k}"] for o in rs],color=c,label=m)
    lo,hi=ax[i].get_xlim()[0],max(ax[i].get_xlim()[1],ax[i].get_ylim()[1]); 
    allv=[o[f"est_{k}"] for o in out if o["est_total"]!=""]+[o[f"act_{k}"] for o in out]
    mn,mx=min(allv)*0.7,max(allv)*1.4; ax[i].plot([mn,mx],[mn,mx],"k--",lw=0.8,label="perfect")
    ax[i].set_xscale("log"); ax[i].set_yscale("log"); ax[i].set_xlabel(f"self-estimate ({t})"); ax[i].set_ylabel(f"actual ({t})"); ax[i].legend(fontsize=8)
    ax[i].set_title(f"{t}: points above the line = underestimate")
    from matplotlib.ticker import NullFormatter; ax[i].xaxis.set_minor_formatter(NullFormatter()); ax[i].yaxis.set_minor_formatter(NullFormatter())
plt.suptitle("Can Claude Code predict its own spend? (11 tasks × opus/haiku)",fontsize=11); plt.tight_layout(); plt.savefig(f"{D}/results/chart.png",dpi=110)
