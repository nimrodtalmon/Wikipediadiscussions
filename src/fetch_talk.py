"""Fetch talk pages (+archives) and article revision metadata for a seed list of he.wiki articles."""
import requests, json, sys, pathlib, time
API="https://he.wikipedia.org/w/api.php"
S=requests.Session(); S.headers.update({"User-Agent":"wiki-emotions/0.1 (BGU research; nimrodtalmon)"})
DATA=pathlib.Path(__file__).resolve().parent.parent/"data"

def q(**p):
    p.update(action="query",format="json",formatversion=2)
    time.sleep(0.15)
    for attempt in range(5):
        try:
            r=S.get(API,params=p,timeout=60); r.raise_for_status(); return r.json()
        except Exception as e:
            if attempt==4: raise
            time.sleep(5*2**attempt)
    

def resolve(title):
    r=q(titles=title,redirects=1); pg=r["query"]["pages"][0]
    return None if pg.get("missing") else pg["title"]

def subpages(prefix, ns):
    out=[]; cont={}
    while True:
        r=q(list="allpages",apprefix=prefix.split(":",1)[1]+"/",apnamespace=ns,aplimit=500,**cont)
        out+=[p["title"] for p in r["query"]["allpages"]]
        if "continue" in r: cont=r["continue"]
        else: return out

def revisions(title):
    revs=[]; cont={}
    while True:
        r=q(prop="revisions",titles=title,rvprop="ids|timestamp|user|size|comment|sha1",rvlimit=500,**cont)
        pg=r["query"]["pages"][0]
        if pg.get("missing"): return None
        revs+=pg.get("revisions",[])
        if "continue" in r: cont=r["continue"]
        else: return revs

def current_text(title):
    r=q(prop="revisions",titles=title,rvprop="content",rvslots="main",rvlimit=1)
    pg=r["query"]["pages"][0]
    return None if pg.get("missing") else pg["revisions"][0]["slots"]["main"]["content"]

def fetch(article):
    title=resolve(article)
    if not title: print("MISSING:",article); return
    talk="שיחה:"+title
    pages=[talk]+subpages(talk,1)
    rec={"article":title,"talk_pages":[],"article_revs":revisions(title)}
    for p in pages:
        txt=current_text(p)
        if txt is None: continue
        rec["talk_pages"].append({"title":p,"text":txt,"revs":revisions(p)})
    (DATA/(title.replace("/","_")+".json")).write_text(json.dumps(rec,ensure_ascii=False))
    print(f"{title}: {len(rec['talk_pages'])} talk page(s), {sum(len(t['revs'] or []) for t in rec['talk_pages'])} talk revs, {len(rec['article_revs'])} article revs")

if __name__=="__main__":
    for a in open(sys.argv[1],encoding="utf8").read().split("\n"):
        if a.strip(): fetch(a.strip())
