"""Build docs/data/corpus.json for the GitHub Pages explorer from data/*.json."""
import json, re, pathlib
from parse_threads import threads as split_threads, SIG, USER
from emotion import score as emo_score
from stability import analyze as stab
from link_threads import identity_flags, link
from dynamics import dynamics
from collections import Counter
ROOT=pathlib.Path(__file__).resolve().parent.parent
MONTHS={m:i+1 for i,m in enumerate("ינואר פברואר מרץ אפריל מאי יוני יולי אוגוסט ספטמבר אוקטובר נובמבר דצמבר".split())}
def iso(d):
    m=re.match(r"(\d{1,2})\s+ב?([א-ת]+)\s+(\d{4})",d or "")
    return f"{m[3]}-{MONTHS.get(m[2],0):02d}-{int(m[1]):02d}" if m and m[2] in MONTHS else ""
def comments(body):
    """Segment a thread body into comments; tree via indentation."""
    out=[]; buf=[]; ind=0
    def flush(signed):
        nonlocal buf
        if not buf: return
        raw="\n".join(buf)
        us=USER.findall(raw); sg=SIG.findall(raw)
        out.append({"ind":ind,"user":us[-1].strip() if us else "","date":iso(sg[-1][1]) if sg else "","time":sg[-1][0] if sg else "","signed":signed,"text":raw,"emo":emo_score(raw)})
        buf=[]
    import re as _re
    for l in body.split("\n"):
        m=_re.match(r"^([:*#]+)",l); d=len(m.group(1)) if m else 0
        if not l.strip(): flush(False); continue
        if buf and d!=ind: flush(False)
        if not buf: ind=d
        buf.append(_re.sub(r"^[:*#]+\s?","",l))
        if SIG.search(l): flush(True)
    flush(False)
    # parent: nearest preceding with smaller indent
    for i,c in enumerate(out):
        c["parent"]=next((j for j in range(i-1,-1,-1) if out[j]["ind"]<c["ind"]),-1) if c["ind"]>0 else -1
    return out

def thread_bodies(text):
    parts=re.split(r"^==+\s*(.+?)\s*==+\s*$",text,flags=re.M)
    return [parts[i+1] for i in range(1,len(parts),2)]
Q=json.loads((ROOT/"data/quality.json").read_text()) if (ROOT/"data/quality.json").exists() else {}
PQ=json.loads((ROOT/"data/pair_quality.json").read_text()) if (ROOT/"data/pair_quality.json").exists() else {}
PAIRS=json.loads((ROOT/"data/pairs.json").read_text()) if (ROOT/"data/pairs.json").exists() else {}
seeds={l.strip():ring for ring in ("core","adjacent") for l in (ROOT/"data"/f"seed_{ring}.txt").read_text(encoding="utf8").splitlines() if l.strip()}
arts=[]
for f in sorted((ROOT/"data").glob("*.json")):
    if not f.name.endswith(".json") or f.name.startswith("scope_") or f.name in ("corpus.json","threads.csv","quality.json","analysis.json","pairs.json","pair_quality.json","validation_sample.csv"): continue
    rec=json.loads(f.read_text()); ths=[]
    for tp in rec["talk_pages"]:
        for meta,body in zip(split_threads(tp["text"]),thread_bodies(tp["text"])):
            ths.append({**meta,"first":iso(meta["first"]),"last":iso(meta["last"]),"page":tp["title"],"text":body.strip(),"cmts":comments(body.strip())})
    rs,flags=identity_flags(rec["article_revs"])
    for ti,t in enumerate(ths):
        t["link"]=link(rs,flags,t)
        _qv=Q.get(f"{rec['article']}::{ti}::{t['title']}"); t["q"]=_qv if _qv and "accuracy" in _qv else None
        t["dyn"]=dynamics(t["cmts"])
        _pk=f"{rec['article']}::{ti}::{t['title']}"
        _pq=PQ.get(_pk); _pr=PAIRS.get(_pk)
        _d={}
        if _pq: _d.update(better=_pq["better"],kept_acc=_pq["kept_acc"],discarded_acc=_pq["discarded_acc"])
        if _pr: _d.update(kept_by=_pr["kept_by"],discarded_by=_pr["discarded_by"])
        t["pq"]=_d if _d else None
    months=Counter(r["timestamp"][:7] for r in rs)
    m0=rs[0]["timestamp"][:7]; mN=__import__("time").strftime("%Y-%m")
    def _mrange(a,b):
        y,m=int(a[:4]),int(a[5:7]); out=[]
        while f"{y:04d}-{m:02d}"<=b: out.append(f"{y:04d}-{m:02d}"); m+=1; y,m=(y+1,1) if m>12 else (y,m)
        return out
    mm=_mrange(m0,mN)
    tl={"m0":m0,"edits":[months.get(m,0) for m in mm],"rev":[r["timestamp"][:10] for r,f in zip(rs,flags) if f]}
    arts.append({"title":rec["article"],"ring":seeds.get(rec["article"],"adjacent" if rec["article"] in seeds else "core"),
                 "talk_revs":sum(len(t["revs"] or []) for t in rec["talk_pages"]),"article_revs":len(rec["article_revs"]),
                 "archives":len(rec["talk_pages"])-1,"threads":ths,"stab":stab(rec["article_revs"]),"tl":tl})
out={"built":__import__("time").strftime("%Y-%m-%d %H:%M"),"articles":arts}
(ROOT/"site/corpus.json").write_text(json.dumps(out,ensure_ascii=False))
import re as _re, time as _time
stamp=str(int(_time.time()))
for fn in ("explorer.html","index.html","curate.html"):
    fp=ROOT/fn; h=fp.read_text()
    h=_re.sub(r"(site/(?:corpus|candidates)\.json\?v=)[0-9]*",r"\g<1>"+stamp,h)
    fp.write_text(h)
print(len(arts),"articles,",sum(len(a["threads"]) for a in arts),"threads,",round((ROOT/"site/corpus.json").stat().st_size/1e6,2),"MB")
