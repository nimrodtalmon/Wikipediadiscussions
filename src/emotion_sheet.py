"""Print comments of the N richest un-coded threads for LLM emotion coding (sitting tool)."""
import json,sys,re,pathlib
ROOT=pathlib.Path(__file__).resolve().parent.parent
d=json.loads((ROOT/"site/corpus.json").read_text())
done=set(json.loads((ROOT/"data/emotion_llm.json").read_text())) if (ROOT/"data/emotion_llm.json").exists() else set()
ths=[(a["title"],ti,t) for a in d["articles"] for ti,t in enumerate(a["threads"]) if t["comments"]>=5]
ths.sort(key=lambda x:-x[2]["comments"])
k=int(sys.argv[1]); cap=int(sys.argv[2]) if len(sys.argv)>2 else 260
shown=0
for art,ti,t in ths:
    if f"{art}::{ti}::0" in done: continue
    print(f"### {art}::{ti} — {t['title']} ({len(t['cmts'])} comments)")
    for ci,c in enumerate(t["cmts"]):
        txt=re.sub(r"\{\{[^}]*\}\}|\[\[[^\]]*\|","",c["text"]).replace("]]","").replace("'''","")
        txt=re.sub(r"\s+"," ",txt).strip()
        print(f"[{ci}] {c['user'] or '?'}: {txt[:cap]}")
    shown+=1
    if shown>=k: break
