"""M8 v0: link each thread to article edits by time window.
Window: [first comment date - 1d, last comment date + 7d].
Outputs per thread: edits and identity-reverts in window, edits whose summary cites the talk page,
and post-thread stability: days from thread end to the next identity revert (censored at 'now')."""
import re
from datetime import datetime, timedelta, timezone
from stability import SUMM, _ts

TALKREF=re.compile(r"דף השיחה|בדף שיחה|ראו שיחה|per talk|see talk",re.I)
NOW=datetime.now(timezone.utc)

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
    t0=datetime.fromisoformat(min(dates)).replace(tzinfo=timezone.utc)-timedelta(days=1)
    t1=datetime.fromisoformat(max(dates)).replace(tzinfo=timezone.utc)+timedelta(days=8)  # end of +7d
    win=[(r,f) for r,f in zip(rs,flags) if t0<=_ts(r)<t1]
    after=[(r,f) for r,f in zip(rs,flags) if _ts(r)>=t1]
    nxt=next((r for r,f in after if f),None)
    end=datetime.fromisoformat(max(dates)).replace(tzinfo=timezone.utc)
    post=( _ts(nxt)-end ).total_seconds()/86400 if nxt else (NOW-end).total_seconds()/86400
    return {"win_edits":len(win),"win_reverts":sum(f for _,f in win),
            "talkref":sum(1 for r,_ in win if TALKREF.search(r.get("comment","") or "")),
            "post_days":round(post,1),"censored":nxt is None}
