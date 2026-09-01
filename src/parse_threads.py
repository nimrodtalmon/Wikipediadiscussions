"""Split fetched talk pages into threads; count signed comments and distinct editors per thread."""
import json, re, pathlib, csv
from collections import defaultdict
DATA=pathlib.Path(__file__).resolve().parent.parent/"data"
# he.wiki signature timestamp, e.g. "13:42, 5 במרץ 2019 (IST)" or "(IDT)"
SIG=re.compile(r"(\d{1,2}:\d{2}),?\s+(\d{1,2}\s+ב?[א-ת]+\s+\d{4})\s+\((?:IST|IDT|UTC)\)")
USER=re.compile(r"\[\[(?:משתמש|משתמשת|שיחת משתמש|שיחת משתמשת|User|User talk):([^|\]#/]+)")

def threads(text):
    parts=re.split(r"^==+\s*(.+?)\s*==+\s*$",text,flags=re.M)
    out=[]
    for i in range(1,len(parts),2):
        body=parts[i+1]
        sigs=SIG.findall(body); users=set(u.strip() for u in USER.findall(body))
        out.append({"title":parts[i],"chars":len(body),"comments":len(sigs),"editors":len(users),
                    "first":sigs[0][1] if sigs else "", "last":sigs[-1][1] if sigs else ""})
    return out

def main():
    rows=[]
    for f in sorted(DATA.glob("*.json")):
        rec=json.loads(f.read_text())
        for tp in rec["talk_pages"]:
            for t in threads(tp["text"]):
                rows.append({"article":rec["article"],"page":tp["title"],**t})
    with open(DATA/"threads.csv","w",newline="",encoding="utf8") as fh:
        w=csv.DictWriter(fh,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    agg=defaultdict(lambda:[0,0,0,0])
    for r in rows:
        a=agg[r["article"]]; a[0]+=1; a[1]+=r["comments"]; a[2]+=(r["comments"]>=5); a[3]+=(r["comments"]>=10)
    print(f"{'article':<28}{'threads':>8}{'comments':>10}{'>=5c':>6}{'>=10c':>7}")
    for k,v in sorted(agg.items(),key=lambda x:-x[1][1]): print(f"{k:<28}{v[0]:>8}{v[1]:>10}{v[2]:>6}{v[3]:>7}")
    T=[sum(v[i] for v in agg.values()) for i in range(4)]
    print(f"{'TOTAL':<28}{T[0]:>8}{T[1]:>10}{T[2]:>6}{T[3]:>7}")

if __name__=="__main__": main()
