"""Build docs/data/corpus.json for the GitHub Pages explorer from data/*.json."""
import json, re, pathlib
from parse_threads import threads as split_threads, SIG, USER
from emotion import score as emo_score
from stability import analyze as stab
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
seeds={l.strip():ring for ring in ("core","adjacent") for l in (ROOT/"data"/f"seed_{ring}.txt").read_text(encoding="utf8").splitlines() if l.strip()}
arts=[]
for f in sorted((ROOT/"data").glob("*.json")):
    if not f.name.endswith(".json") or f.name.startswith("scope_") or f.name in ("corpus.json","threads.csv"): continue
    rec=json.loads(f.read_text()); ths=[]
    for tp in rec["talk_pages"]:
        for meta,body in zip(split_threads(tp["text"]),thread_bodies(tp["text"])):
            ths.append({**meta,"first":iso(meta["first"]),"last":iso(meta["last"]),"page":tp["title"],"text":body.strip(),"cmts":comments(body.strip())})
    arts.append({"title":rec["article"],"ring":seeds.get(rec["article"],"adjacent" if rec["article"] in seeds else "core"),
                 "talk_revs":sum(len(t["revs"] or []) for t in rec["talk_pages"]),"article_revs":len(rec["article_revs"]),
                 "archives":len(rec["talk_pages"])-1,"threads":ths,"stab":stab(rec["article_revs"])})
out={"built":__import__("datetime").date.today().isoformat(),"articles":arts}
(ROOT/"site/corpus.json").write_text(json.dumps(out,ensure_ascii=False))
print(len(arts),"articles,",sum(len(a["threads"]) for a in arts),"threads,",round((ROOT/"site/corpus.json").stat().st_size/1e6,2),"MB")
