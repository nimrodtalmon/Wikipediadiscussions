"""M7a extension: pairwise quality around the pivotal in-window revert.
Motivation: rating only the surviving version cannot detect wrongful reverts -- a good edit
reverted by an aggressive (wrong) editor who bullies the author into silence. For each rich
thread with an in-window identity revert, take the FIRST such revert R: the KEPT version is R
itself; the DISCARDED version is the revision just before R. Extract the changed region
(difflib, largest differing block +-400 chars) from both, for side-by-side quality rating.
Output: data/pairs.json (excerpts + who reverted whom); ratings go to data/pair_quality.json."""
import json, sys, pathlib, difflib
from datetime import datetime, timedelta, timezone
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from fetch_talk import q
from link_threads import identity_flags
from stability import _ts
ROOT=pathlib.Path(__file__).resolve().parent.parent

def content(article, revid):
    r=q(prop="revisions",titles=article,rvstartid=revid,rvlimit=1,rvprop="ids|content|user|timestamp",rvslots="main")
    pg=r["query"]["pages"][0]; rv=pg["revisions"][0]
    sl=rv.get("slots",{}).get("main",{})
    if "content" not in sl: return None,None,None  # suppressed/deleted revision text
    return sl["content"], rv.get("user",""), rv["timestamp"]

def changed_region(a,b,ctx_lines=6):
    """Line-level diff (char-level is quadratic on 200KB pages); largest changed block +- context lines."""
    la,lb=a.splitlines(),b.splitlines()
    sm=difflib.SequenceMatcher(None,la,lb,autojunk=False)
    best=None
    for tag,i1,i2,j1,j2 in sm.get_opcodes():
        if tag=="equal": continue
        size=max(i2-i1,j2-j1)
        if best is None or size>best[0]: best=(size,i1,i2,j1,j2)
    if not best: return a[:800],b[:800]
    _,i1,i2,j1,j2=best
    ka="\n".join(la[max(0,i1-ctx_lines):i2+ctx_lines])
    da="\n".join(lb[max(0,j1-ctx_lines):j2+ctx_lines])
    return ka,da

def main(limit=999):
    raw={}
    for f in (ROOT/"data").glob("*.json"):
        if f.stem in ("scope_ck","scope_rows","pairs","quality","pair_quality","analysis","threads"): continue
        try: j=json.loads(f.read_text())
        except Exception: continue
        if "talk_pages" in j: raw[f.stem]=j
    corpus=json.loads((ROOT/"site/corpus.json").read_text())
    out=json.loads((ROOT/"data/pairs.json").read_text()) if (ROOT/"data/pairs.json").exists() else {}
    made=0
    for a in corpus["articles"]:
        rec=raw.get(a["title"].replace("/","_"))
        if not rec: continue
        rs,flags=identity_flags(rec["article_revs"])
        for ti,t in enumerate(a["threads"]):
            key=f"{a['title']}::{ti}::{t['title']}"
            if key in out or t["comments"]<5 or not t.get("link") or t["link"]["win_reverts"]<1: continue
            if made>=limit: break
            d0=datetime.fromisoformat(min(c["date"] for c in t["cmts"] if c["date"])).replace(tzinfo=timezone.utc)-timedelta(days=1)
            d1=datetime.fromisoformat(max(c["date"] for c in t["cmts"] if c["date"])).replace(tzinfo=timezone.utc)+timedelta(days=8)
            piv=None
            for i,(r,f) in enumerate(zip(rs,flags)):
                if f and d0<=_ts(r)<d1: piv=i; break
            if piv is None or piv==0: continue
            kept_txt,kept_u,kept_ts=content(a["title"],rs[piv]["revid"])
            disc_txt,disc_u,_=content(a["title"],rs[piv-1]["revid"])
            if kept_txt is None or disc_txt is None: continue
            ka,da=changed_region(kept_txt,disc_txt)
            out[key]={"kept_rev":rs[piv]["revid"],"kept_by":kept_u,"kept_ts":kept_ts,
                      "discarded_rev":rs[piv-1]["revid"],"discarded_by":disc_u,
                      "kept_excerpt":ka[:2200],"discarded_excerpt":da[:2200]}
            made+=1
            (ROOT/"data/pairs.json").write_text(json.dumps(out,ensure_ascii=False))
            print(f"{len(out)} {key[:50]}",flush=True)
    (ROOT/"data/pairs.json").write_text(json.dumps(out,ensure_ascii=False))
    print(len(out),"pairs extracted")

if __name__=="__main__": main(int(sys.argv[1]) if len(sys.argv)>1 else 999)
