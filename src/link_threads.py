"""M8 v1: link threads to article edits.
Time window [first-1d, last+7d] plus a LINKING SCORE built from independent signals:
  +3 explicit diff/oldid link in the thread text (hard anchor, rare: ~3% of threads)
  +2 BRD ordering: an identity revert in the 3 days before the thread opened (revert -> discussion)
  +2 editor overlap >=2 between thread participants and in-window article editors (+1 if exactly 1)
  +2 an in-window edit summary citing the talk page
  +2 thread-title token appears in an in-window edit summary (section auto-summaries)
Confidence: high >=5, medium 3-4, low <=2. Post-thread stability as before (censored at now).
Causal caution: Wikipedia's Bold-Revert-Discuss norm means discussions typically FOLLOW reverts;
the score identifies a shared dispute episode, not a direction of causation."""
import re
from datetime import datetime, timedelta, timezone
from stability import SUMM, _ts

TALKREF=re.compile(r"דף השיחה|בדף שיחה|ראו שיחה|per talk|see talk",re.I)
DIFFLINK=re.compile(r"diff=\d+|oldid=\d+|מיוחד:הבדל|Special:Diff")
NOW=datetime.now(timezone.utc)
HEB=re.compile(r"[א-ת]{3,}")

def identity_flags(revs, window=50):
    rs=sorted(revs,key=_ts); seen={}; flags=[False]*len(rs)
    for i,r in enumerate(rs):
        h=r.get("sha1")
        if h in seen and i-seen[h]>1 and i-seen[h]<=window: flags[i]=True
        if h: seen[h]=i
    return rs,flags

def link(rs, flags, thread):
    dates=[c["date"] for c in thread["cmts"] if c["date"]]
    if not dates: return None
    t_open=datetime.fromisoformat(min(dates)).replace(tzinfo=timezone.utc)
    t0=t_open-timedelta(days=1)
    t1=datetime.fromisoformat(max(dates)).replace(tzinfo=timezone.utc)+timedelta(days=8)
    win=[(r,f) for r,f in zip(rs,flags) if t0<=_ts(r)<t1]
    after=[(r,f) for r,f in zip(rs,flags) if _ts(r)>=t1]
    nxt=next((r for r,f in after if f),None)
    end=datetime.fromisoformat(max(dates)).replace(tzinfo=timezone.utc)
    post=(_ts(nxt)-end).total_seconds()/86400 if nxt else (NOW-end).total_seconds()/86400
    # --- linking score ---
    parts={}
    txt="\n".join(c["text"] for c in thread["cmts"])
    parts["difflink"]=3 if DIFFLINK.search(txt) else 0
    brd=any(f and t_open-timedelta(days=3)<=_ts(r)<=t_open for r,f in zip(rs,flags))
    parts["brd"]=2 if brd else 0
    t_users={c["user"] for c in thread["cmts"] if c["user"]}
    w_users={r.get("user") for r,_ in win if r.get("user")}
    ov=len(t_users&w_users)
    parts["editors"]=2 if ov>=2 else (1 if ov==1 else 0)
    talkref=sum(1 for r,_ in win if TALKREF.search(r.get("comment","") or ""))
    parts["talkref"]=2 if talkref else 0
    toks=set(HEB.findall(thread["title"]))
    parts["section"]=2 if toks and any(toks & set(HEB.findall(r.get("comment","") or "")) for r,_ in win) else 0
    score=sum(parts.values())
    conf="high" if score>=5 else ("medium" if score>=3 else "low")
    return {"win_edits":len(win),"win_reverts":sum(f for _,f in win),"talkref":talkref,
            "post_days":round(post,1),"censored":nxt is None,
            "score":score,"conf":conf,"parts":parts,"editor_overlap":ov}
