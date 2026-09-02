"""M6: stability measures from article revision histories (v0).
Identity reverts: a revision whose sha1 equals an earlier revision's (within a window),
i.e. the page returned exactly to a previous state. Summary-based reverts as a secondary signal."""
import re
from datetime import datetime, timezone

SUMM=re.compile(r"שחזור|שוחזר|שיחזר|ביטול|בוטל|revert|undid|undo",re.I)
NOW=datetime.now(timezone.utc)

def _ts(r): return datetime.fromisoformat(r["timestamp"].replace("Z","+00:00"))

def analyze(revs, window=50):
    """revs: newest-first list from the API. Returns per-article stability summary."""
    rs=sorted(revs,key=_ts)  # oldest first
    n=len(rs)
    seen={}; identity=[]; summary=0
    for i,r in enumerate(rs):
        h=r.get("sha1")
        if h in seen and i-seen[h]>1 and i-seen[h]<=window: identity.append(i)
        if h: seen[h]=i
        if SUMM.search(r.get("comment","") or ""): summary+=1
    # edit wars: >=3 identity reverts within 48h of each other
    wars=0; streak=1
    for a,b in zip(identity,identity[1:]):
        if (_ts(rs[b])-_ts(rs[a])).total_seconds()<=48*3600: streak+=1
        else:
            if streak>=3: wars+=1
            streak=1
    if streak>=3: wars+=1
    # version lifetimes: gaps between consecutive edits (incl. gap from last edit to now)
    gaps=[(_ts(b)-_ts(a)).total_seconds()/86400 for a,b in zip(rs,rs[1:])]
    tail=(NOW-_ts(rs[-1])).total_seconds()/86400 if rs else 0
    alld=sorted(gaps+[tail])
    med=alld[len(alld)//2] if alld else 0
    return {"edits":n,"identity_reverts":len(identity),"summary_reverts":summary,
            "revert_rate":round(len(identity)/n,4) if n else 0,"war_episodes":wars,
            "median_version_days":round(med,2),"longest_stable_days":round(max(alld),1) if alld else 0,
            "current_version_days":round(tail,1),
            "first_edit":rs[0]["timestamp"][:10] if rs else "","last_edit":rs[-1]["timestamp"][:10] if rs else ""}
