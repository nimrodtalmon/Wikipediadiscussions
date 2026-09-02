"""M4: comment-level emotion. Two implementations share one output schema:
    {"label": "agg"|"con"|"fru"|"neu", "s": intensity 0..1}
plus VALENCE (used by dynamics): con=+1, agg=-1, fru=-0.5, neu=0.

Implementation A — lexicon (data/lexicon.csv; columns: category, phrase). Editable by anyone.
  score = phrase occurrences per category (+ "!!" and "??" count toward aggression);
  intensity = occurrences per 1000 characters; label = argmax if intensity >= THRESH else "neu".
Implementation B — LLM coding (data/emotion_llm.json, keyed "article::thread_index::comment_index"),
  produced in rating sittings; same schema. Missing entries fall back to nothing (explorer shows A)."""
import csv, re, json, pathlib
ROOT=pathlib.Path(__file__).resolve().parent.parent
VALENCE={"con":1.0,"agg":-1.0,"fru":-0.5,"neu":0.0}
CAT={"aggression":"agg","conciliation":"con","exhaustion":"fru"}
THRESH=0.8

def load_lexicon(path=ROOT/"data/lexicon.csv"):
    lex={"agg":[],"con":[],"fru":[]}
    with open(path,encoding="utf8") as f:
        for r in csv.DictReader(f):
            k=CAT.get(r["category"].strip())
            if k and r["phrase"].strip(): lex[k].append(r["phrase"].strip())
    return lex
LEX=load_lexicon()

def score_lexicon(text):
    t=text.replace("״",'"'); n=max(len(t),1)
    raw={k:sum(t.count(w) for w in ws) for k,ws in LEX.items()}
    raw["agg"]+=t.count("!!")+0.5*len(re.findall(r"\?\?+",t))
    per={k:v*1000/n for k,v in raw.items()}
    best=max(raw,key=lambda k:(raw[k],per[k]))
    if raw[best]==0 or per[best]<THRESH: return {"label":"neu","s":0}
    return {"label":best,"s":min(round(per[best]/3,2),1)}

def load_llm(path=ROOT/"data/emotion_llm.json"):
    return json.loads(path.read_text()) if path.exists() else {}

score=score_lexicon  # backward-compatible name
