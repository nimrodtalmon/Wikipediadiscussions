"""Print rating-ready excerpts for rich threads [start:end) by global index."""
import json,sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from llm_quality import post_revision, excerpt
from datetime import datetime,timedelta
corpus=json.load(open(pathlib.Path(__file__).parent.parent/"site/corpus.json"))
done=set(json.load(open(pathlib.Path(__file__).parent.parent/"data/quality.json")))
jobs=[]
for a in corpus["articles"]:
    for ti,t in enumerate(a["threads"]):
        k=f"{a['title']}::{ti}::{t['title']}"
        if t["comments"]>=5 and t.get("last") and k not in done: jobs.append((a["title"],ti,t))
jobs.sort(key=lambda j:(j[0],j[1]))
s,e=int(sys.argv[1]),int(sys.argv[2])
print(f"TOTAL_JOBS {len(jobs)}")
for art,ti,t in jobs[s:e]:
    end=(datetime.fromisoformat(t["last"])+timedelta(days=8)).strftime("%Y-%m-%dT00:00:00Z")
    rev=post_revision(art,end)
    if not rev: print(f"@@KEY {art}::{ti}::{t['title']}\n@@NOREV"); continue
    ex=excerpt(rev["slots"]["main"]["content"],t["title"],1300)
    print(f"@@KEY {art}::{ti}::{t['title']}\n@@REV {rev['revid']} {rev['timestamp']}\n@@THREAD {t['title']}\n{ex}\n")
