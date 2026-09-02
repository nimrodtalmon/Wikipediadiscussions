"""M7a: LLM-based quality proxy for post-thread article versions.
For each rich thread (>=5 signed comments, dated): fetch the first article revision at/after the
thread window end, extract a relevant excerpt, and have an LLM rate it. Resumable; results in
data/quality.json (committed: expensive to regenerate). Requires ANTHROPIC_API_KEY.
This is a PROXY (M7a); expert validation on a subsample is M7b."""
import json, os, re, sys, pathlib, time
import requests
from datetime import datetime, timedelta, timezone
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from fetch_talk import q

ROOT=pathlib.Path(__file__).resolve().parent.parent
OUT=ROOT/"data/quality.json"
MODEL="claude-sonnet-4-6"

PROMPT="""אתם מעריכים איכות של קטע מערך ויקיפדיה בעברית בנושאי בריאות הנפש, כפי שנראה מיד אחרי דיון בדף השיחה.
כותרת הערך: {article}
נושא הדיון שהסתיים: {thread}
הקטע להערכה (מתוך גרסת הערך שלאחר הדיון):
---
{excerpt}
---
דרגו 1-7 (7 מיטבי) את הקטע עצמו, לא את הדיון: accuracy (נכונות קלינית/מדעית), sourcing (ביסוס במקורות), neutrality (ניסוח מאוזן). השיבו JSON בלבד:
{{"accuracy":n,"sourcing":n,"neutrality":n,"note":"נימוק במשפט"}}"""

def post_revision(article, after_iso):
    r=q(prop="revisions",titles=article,rvdir="newer",rvstart=after_iso,rvlimit=1,rvprop="ids|timestamp|content",rvslots="main")
    pg=r["query"]["pages"][0]; revs=pg.get("revisions")
    if not revs: return None
    return revs[0]

def excerpt(text, thread_title, size=4000):
    words=[w for w in re.findall(r"[א-ת]{3,}", thread_title)][:5]
    best=0
    for w in words:
        i=text.find(w)
        if i>=0: best=i; break
    s=max(0,best-size//4); return text[s:s+size]

def rate(payload):
    r=requests.post("https://api.anthropic.com/v1/messages",
        headers={"x-api-key":os.environ["ANTHROPIC_API_KEY"],"anthropic-version":"2023-06-01","content-type":"application/json"},
        json={"model":MODEL,"max_tokens":300,"messages":[{"role":"user","content":payload}]},timeout=120)
    r.raise_for_status()
    txt="".join(b.get("text","") for b in r.json()["content"])
    return json.loads(re.sub(r"^```json|```$","",txt.strip(),flags=re.M))

def main(budget=100):
    t0=time.time()
    done=json.loads(OUT.read_text()) if OUT.exists() else {}
    corpus=json.loads((ROOT/"site/corpus.json").read_text())
    for a in corpus["articles"]:
        for ti,t in enumerate(a["threads"]):
            key=f"{a['title']}::{t['page']}::{t['title']}"
            if key in done or t["comments"]<5 or not t.get("last"): continue
            if time.time()-t0>budget: OUT.write_text(json.dumps(done,ensure_ascii=False,indent=0)); print("budget"); return 3
            end=(datetime.fromisoformat(t["last"])+timedelta(days=8)).strftime("%Y-%m-%dT00:00:00Z")
            rev=post_revision(a["title"],end)
            if not rev: continue
            ex=excerpt(rev["slots"]["main"]["content"],t["title"])
            try:
                res=rate(PROMPT.format(article=a["title"],thread=t["title"],excerpt=ex))
                done[key]={**res,"revid":rev["revid"],"rev_ts":rev["timestamp"],"model":MODEL}
                print(f"{res['accuracy']}/{res['sourcing']}/{res['neutrality']}  {a['title'][:16]} :: {t['title'][:34]}")
            except Exception as e:
                print("FAIL",key[:60],e,file=sys.stderr)
    OUT.write_text(json.dumps(done,ensure_ascii=False,indent=0)); print(len(done),"rated"); return 0

if __name__=="__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv)>1 else 100))
