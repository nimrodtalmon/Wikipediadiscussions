"""M5 v0: per-thread discussion-dynamics measures.
All measures operate on the ordered comment list (M3 output) with v0 emotion labels (M4),
so they inherit both layers' noise; constructs and thresholds await joint revision.

Measures:
  valence series  : agg=-1, fru=-0.5, con=+1, neu=0 per comment
  contagion_r     : lag-1 Pearson correlation of the valence series (emotional contagion proxy)
  agg_lift        : P(next is aggressive | current aggressive) / P(aggressive)  (>1 = aggression breeds aggression)
  hostile_exits   : participants who were recently active, then never spoke again after another
                    editor's aggressive comment (within 3 turns before it); share of participants
  duel_len        : longest strictly-alternating run between two editors (ping-pong signature)
  top_share       : share of comments by the most active editor (concentration)
  ends_con        : thread's last 3 comments contain conciliation and no aggression (convergence proxy)
"""
VAL={"agg":-1.0,"fru":-0.5,"con":1.0,"neu":0.0}

def _pearson(x,y):
    n=len(x)
    if n<3: return None
    mx=sum(x)/n; my=sum(y)/n
    sx=sum((a-mx)**2 for a in x)**.5; sy=sum((b-my)**2 for b in y)**.5
    if sx==0 or sy==0: return None
    return sum((a-mx)*(b-my) for a,b in zip(x,y))/(sx*sy)

def dynamics(cmts):
    n=len(cmts)
    if n<3: return None
    lab=[c["emo"]["label"] for c in cmts]
    users=[c["user"] for c in cmts]
    val=[VAL[l] for l in lab]
    out={}
    out["contagion_r"]=_pearson(val[:-1],val[1:])
    p_agg=lab.count("agg")/n
    trans=sum(1 for i in range(n-1) if lab[i]=="agg" and lab[i+1]=="agg")
    n_agg_nonlast=sum(1 for i in range(n-1) if lab[i]=="agg")
    out["agg_lift"]=round((trans/n_agg_nonlast)/p_agg,2) if n_agg_nonlast>=2 and p_agg>0 else None
    # hostile exits
    last={}; 
    for i,u in enumerate(users):
        if u: last[u]=i
    participants=set(last)
    victims=set()
    for j,l in enumerate(lab):
        if l!="agg": continue
        aggressor=users[j]
        for u,li in last.items():
            if u==aggressor or li>j: continue
            if any(users[k]==u for k in range(max(0,j-3),j)):  # recently active
                victims.add(u)
    out["hostile_exit_share"]=round(len(victims)/len(participants),2) if participants else None
    out["hostile_exits"]=len(victims)
    # duel
    best=cur=1
    for i in range(1,n):
        pair={users[i-1],users[i]}
        if users[i] and users[i-1] and users[i]!=users[i-1] and (cur==1 or pair==prev_pair):
            cur+=1; prev_pair=pair
        else:
            cur=2 if users[i] and users[i-1] and users[i]!=users[i-1] else 1
            prev_pair={users[i-1],users[i]}
        best=max(best,cur)
    out["duel_len"]=best
    counts={}
    for u in users:
        if u: counts[u]=counts.get(u,0)+1
    out["top_share"]=round(max(counts.values())/sum(counts.values()),2) if counts else None
    tail=lab[-3:]
    out["ends_con"]="con" in tail and "agg" not in tail
    return out
