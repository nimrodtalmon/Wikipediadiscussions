"""V0 smoke-test analysis over rich threads (>=5 signed comments).
Pipeline test only: every layer is v0 (lexicon emotions, window linking, LLM quality proxy).
Outputs data/analysis.json and prints a summary. Modular: reads only site/corpus.json."""
import json, math, pathlib, sys
from datetime import datetime
from scipy.stats import spearmanr, mannwhitneyu
ROOT=pathlib.Path(__file__).resolve().parent.parent
corpus=json.loads((ROOT/"site/corpus.json").read_text())

rows=[]
for a in corpus["articles"]:
    # article baseline: edits per day over lifetime
    n_ed=sum(a["tl"]["edits"]); n_days=max(len(a["tl"]["edits"])*30.4,1)
    base_rev=len(a["tl"]["rev"])/n_days  # reverts/day baseline
    for t in a["threads"]:
        if t["comments"]<5 or not t["link"]: continue
        n=len(t["cmts"]); e=lambda lab: sum(1 for c in t["cmts"] if c["emo"]["label"]==lab)
        first=datetime.fromisoformat(t["first"]); last=datetime.fromisoformat(t["last"])
        win_days=(last-first).days+9
        expected=base_rev*win_days
        rows.append(dict(article=a["title"],thread=t["title"],n=n,
            agg=e("agg")/n, con=e("con")/n, fru=e("fru")/n, any_agg=e("agg")>0,
            editors=t["editors"], win_days=win_days,
            win_rev=t["link"]["win_reverts"], excess_rev=t["link"]["win_reverts"]/expected if expected>0 else None,
            post_days=t["link"]["post_days"], censored=t["link"]["censored"],
            acc=t["q"]["accuracy"] if t.get("q") else None,
            hx=t["dyn"]["hostile_exit_share"] if t.get("dyn") else None,
            endc=t["dyn"]["ends_con"] if t.get("dyn") else None,
            cont=t["dyn"]["contagion_r"] if t.get("dyn") else None,
            src=t["q"]["sourcing"] if t.get("q") else None))
print(f"n={len(rows)} rich linked threads")

def sp(x,y,label):
    pairs=[(a,b) for a,b in zip(x,y) if a is not None and b is not None]
    if len(pairs)<8: print(f"{label}: n<8, skipped"); return None
    r,p=spearmanr(*zip(*pairs)); print(f"{label}: rho={r:+.2f} p={p:.3f} n={len(pairs)}")
    return dict(rho=round(r,3),p=round(p,4),n=len(pairs))
res={"n":len(rows),"note":"v0 smoke test; all measurement layers provisional","tests":{}}
A=lambda k:[r[k] for r in rows]
lp=[math.log10(r["post_days"]+1) for r in rows]
res["tests"]["agg_vs_excess_rev"]=sp(A("agg"),A("excess_rev"),"aggression share vs excess in-window reverts")
res["tests"]["agg_vs_post"]=sp(A("agg"),lp,"aggression share vs log post-stability")
res["tests"]["con_vs_post"]=sp(A("con"),lp,"conciliation share vs log post-stability")
res["tests"]["agg_vs_acc"]=sp(A("agg"),A("acc"),"aggression share vs quality (accuracy)")
res["tests"]["post_vs_acc"]=sp(lp,A("acc"),"log post-stability vs quality (accuracy)")
res["tests"]["editors_vs_post"]=sp(A("editors"),lp,"num editors vs log post-stability")
res["tests"]["hostile_exit_vs_post"]=sp(A("hx"),lp,"hostile-exit share vs log post-stability")
res["tests"]["hostile_exit_vs_acc"]=sp(A("hx"),A("acc"),"hostile-exit share vs quality (accuracy)")
res["tests"]["contagion_vs_post"]=sp(A("cont"),lp,"valence contagion (lag-1 r) vs log post-stability")
g1=[r["post_days"] for r in rows if r["endc"] and not r["censored"]]
g0=[r["post_days"] for r in rows if r["endc"] is False and not r["censored"]]
if len(g1)>=5 and len(g0)>=5:
    import statistics as st2
    u,p2=mannwhitneyu(g1,g0)
    print(f"post-stability, ends-conciliatory (med {st2.median(g1):.0f}d, n={len(g1)}) vs not (med {st2.median(g0):.0f}d, n={len(g0)}): U p={p2:.3f}")
    res["tests"]["endcon_post_mw"]=dict(p=round(p2,4),med_con=st2.median(g1),med_not=st2.median(g0),n1=len(g1),n0=len(g0))
# group test: any aggression vs none, on uncensored post_days
g1=[r["post_days"] for r in rows if r["any_agg"] and not r["censored"]]
g0=[r["post_days"] for r in rows if not r["any_agg"] and not r["censored"]]
if len(g1)>=5 and len(g0)>=5:
    u,p=mannwhitneyu(g1,g0)
    import statistics as st
    print(f"post-stability, agg-present (med {st.median(g1):.0f}d, n={len(g1)}) vs none (med {st.median(g0):.0f}d, n={len(g0)}): U p={p:.3f}")
    res["tests"]["anyagg_post_mw"]=dict(p=round(p,4),med_agg=st.median(g1),med_none=st.median(g0),n1=len(g1),n0=len(g0))
# article level: sentiment balance vs revert rate (n=18)
al=[]
for a in corpus["articles"]:
    cs=[c for t in a["threads"] for c in t["cmts"]]
    if not cs: continue
    bal=sum({"agg":-1,"fru":-0.5,"con":1}.get(c["emo"]["label"],0) for c in cs)/len(cs)
    al.append((bal,a["stab"]["revert_rate"]))
res["tests"]["article_balance_vs_revert"]=sp([x for x,_ in al],[y for _,y in al],"article sentiment balance vs revert rate")
(ROOT/"data/analysis.json").write_text(json.dumps(res,ensure_ascii=False,indent=1))
