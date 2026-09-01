"""Crawl he.wiki category trees around mental health, score articles by talk-page activity, write site/candidates.json."""
import json, pathlib, sys, time
from concurrent.futures import ThreadPoolExecutor
from fetch_talk import q, subpages
ROOT=pathlib.Path(__file__).resolve().parent.parent
ROOTS=["קטגוריה:בריאות הנפש","קטגוריה:הפרעות נפשיות והתנהגותיות","קטגוריה:פסיכיאטריה","קטגוריה:פסיכולוגיה קלינית",
       "קטגוריה:פסיכולוגיה","קטגוריה:מיניות האדם","קטגוריה:מגדר","קטגוריה:אלימות","קטגוריה:התמכרות","קטגוריה:סמים",
       "קטגוריה:פסיכותרפיה","קטגוריה:רגשות","קטגוריה:התאבדות","קטגוריה:טראומה","קטגוריה:הפרעות אכילה","קטגוריה:אוטיזם"]
SKIP=("סרטים","סרט ","פסיכיאטרים","פסיכולוגים","ספרים","ספר ","אנשים","אישים","סדרות","שירים","אלבומים","רומנים","מחזות","שחקנים",
      "זמרים","סופרים","משוררים","יוצרים","להקות","משחקי","דמויות","יצירות","עיתונאים","ארגונים","מוסדות","בתי חולים","חברות ","קורבנות",
      "פרסים","כתבי עת","אוניברסיט","מלחמ","רצח","פשע","עבריינ","ילידי","נפטרים","בוגרי","טכנולוגיה","מדינות","לפי מדינה","לפי שנה","נשים ")
DEPTH=2; MIN_TALK=2000

def members(cat):
    out=[]; cont={}
    while True:
        r=q(list="categorymembers",cmtitle=cat,cmlimit=500,cmtype="page|subcat",**cont)
        out+=r["query"]["categorymembers"]
        if "continue" in r: cont=r["continue"]
        else: return out

CRAWL_CK=None  # set in main
def crawl(budget):
    t0=time.time()
    if CRAWL_CK.exists(): st=json.loads(CRAWL_CK.read_text())
    else: st={"arts":{},"seen":{},"frontier":[[r,0,r] for r in ROOTS]}
    arts,seen,frontier=st["arts"],st["seen"],st["frontier"]
    ex=ThreadPoolExecutor(6)
    while frontier and time.time()-t0<budget:
        batch=[]; 
        while frontier and len(batch)<6:
            c=frontier.pop(0)
            if c[0] not in seen: seen[c[0]]=c[2]; batch.append(c)
        for (cat,d,path),ms in zip(batch,ex.map(lambda b:members(b[0]),batch)):
            for m in ms:
                if m["ns"]==0: arts.setdefault(m["title"],path)
                elif m["ns"]==14 and d<DEPTH and not any(s in m["title"] for s in SKIP):
                    frontier.append([m["title"],d+1,path+" › "+m["title"].split(":",1)[1]])
        CRAWL_CK.write_text(json.dumps({"arts":arts,"seen":seen,"frontier":frontier},ensure_ascii=False))
    print(f"crawl: {len(seen)} cats, {len(arts)} arts, {len(frontier)} frontier left",file=sys.stderr)
    return (arts,seen) if not frontier else (None,None)

def talk_sizes(titles):
    out={}
    for i in range(0,len(titles),50):
        r=q(prop="info",titles="|".join("שיחה:"+t for t in titles[i:i+50]))
        for p in r["query"]["pages"]:
            if not p.get("missing"): out[p["title"][5:]]=p["length"]
    return out

def rev_count(title):
    # capped at 500 (one API page) — enough for ranking
    r=q(prop="revisions",titles=title,rvprop="ids",rvlimit=500); pg=r["query"]["pages"][0]
    return 0 if pg.get("missing") else len(pg.get("revisions",[]))

CK=ROOT/"data/scope_ck.json"
if __name__=="__main__":
    CRAWL_CK=ROOT/"data/scope_crawl_ck.json"
    BUDGET=int(sys.argv[1]) if len(sys.argv)>1 else 100
    T0=time.time()
    if CK.exists():
        ck=json.loads(CK.read_text()); arts=ck["arts"]; sizes=ck["sizes"]
        print("resume:",len(arts),"articles cached",file=sys.stderr)
    else:
        arts,cats=crawl(BUDGET)
        if arts is None: sys.exit(3)  # crawl not finished; rerun
        sizes=talk_sizes(list(arts))
        CK.write_text(json.dumps({"arts":arts,"sizes":sizes},ensure_ascii=False))
    cand=sorted([t for t,s in sizes.items() if s>=MIN_TALK],key=lambda t:-sizes[t])[:800]
    print(len(cand),"candidates (top by talk bytes)",file=sys.stderr)
    seeds=set(l.strip() for ring in ("core","adjacent") for l in (ROOT/"data"/f"seed_{ring}.txt").read_text(encoding="utf8").splitlines() if l.strip())
    done=json.loads((ROOT/"data/scope_rows.json").read_text()) if (ROOT/"data/scope_rows.json").exists() else {}
    rows=list(done.values())
    todo=[t for t in cand if t not in done]
    def work(t):
        arch=subpages("שיחה:"+t,1); revs=rev_count("שיחה:"+t)+sum(rev_count(a) for a in arch)
        return t,{"title":t,"path":arts[t],"talk_bytes":sizes[t],"archives":len(arch),"talk_revs":revs,"seed":t in seeds}
    ex=ThreadPoolExecutor(3); i=0
    for t,row in ex.map(work,todo):
        done[t]=row; rows.append(row); i+=1
        if i%25==0:
            (ROOT/"data/scope_rows.json").write_text(json.dumps(done,ensure_ascii=False))
            print(f"{len(done)}/{len(cand)}",file=sys.stderr)
            if time.time()-T0>BUDGET:
                print("budget hit",file=sys.stderr); sys.exit(3)
    (ROOT/"data/scope_rows.json").write_text(json.dumps(done,ensure_ascii=False))
    rows.sort(key=lambda r:-r["talk_revs"])
    (ROOT/"site/candidates.json").write_text(json.dumps({"built":time.strftime("%Y-%m-%d"),"min_talk_bytes":MIN_TALK,"roots":ROOTS,"rows":rows},ensure_ascii=False))
    print(len(rows),"candidates written")
