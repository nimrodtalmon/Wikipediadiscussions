"""Build docs/data/corpus.json for the GitHub Pages explorer from data/*.json."""
import json, re, pathlib
from parse_threads import threads as split_threads, SIG
ROOT=pathlib.Path(__file__).resolve().parent.parent
MONTHS={m:i+1 for i,m in enumerate("ינואר פברואר מרץ אפריל מאי יוני יולי אוגוסט ספטמבר אוקטובר נובמבר דצמבר".split())}
def iso(d):
    m=re.match(r"(\d{1,2})\s+ב?([א-ת]+)\s+(\d{4})",d or "")
    return f"{m[3]}-{MONTHS.get(m[2],0):02d}-{int(m[1]):02d}" if m and m[2] in MONTHS else ""
def thread_bodies(text):
    parts=re.split(r"^==+\s*(.+?)\s*==+\s*$",text,flags=re.M)
    return [parts[i+1] for i in range(1,len(parts),2)]
seeds={l.strip():ring for ring in ("core","adjacent") for l in (ROOT/"data"/f"seed_{ring}.txt").read_text(encoding="utf8").splitlines() if l.strip()}
arts=[]
for f in sorted((ROOT/"data").glob("*.json")):
    if f.name=="corpus.json": continue
    rec=json.loads(f.read_text()); ths=[]
    for tp in rec["talk_pages"]:
        for meta,body in zip(split_threads(tp["text"]),thread_bodies(tp["text"])):
            ths.append({**meta,"first":iso(meta["first"]),"last":iso(meta["last"]),"page":tp["title"],"text":body.strip()})
    arts.append({"title":rec["article"],"ring":seeds.get(rec["article"],"adjacent" if rec["article"] in seeds else "core"),
                 "talk_revs":sum(len(t["revs"] or []) for t in rec["talk_pages"]),"article_revs":len(rec["article_revs"]),
                 "archives":len(rec["talk_pages"])-1,"threads":ths})
out={"built":__import__("datetime").date.today().isoformat(),"articles":arts}
(ROOT/"docs/data/corpus.json").write_text(json.dumps(out,ensure_ascii=False))
print(len(arts),"articles,",sum(len(a["threads"]) for a in arts),"threads,",round((ROOT/"docs/data/corpus.json").stat().st_size/1e6,2),"MB")
