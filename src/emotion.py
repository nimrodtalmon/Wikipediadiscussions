"""Crude lexicon-based emotion coding for Hebrew talk-page comments.
Categories follow the proposal: aggression, conciliation, frustration/exhaustion; else neutral.
v0 placeholder — to be replaced by LLM/manual coding once the taxonomy is fixed with Anat."""
import re

AGG=["שטויות","שטות","מגוחך","בושה","שקר","שקרן","הזוי","מביך","חוצפה","זבל","גועל","מניפולצי",
     "צביעות","בור ","עם הארץ","תתבייש","הבל","אין לך מושג","ונדליזם","וונדליזם","השחתה","מטומטם",
     "אידיוט","דביל","טיפש","הזיה","קשקוש","פייק","דמגוגי","עזות מצח","שערורי","מזעזע","חצוף",
     "אל תעז","איך אתה מעז","מי אתה בכלל","בערות","נלעג","עלוב","מגמתי","מוטה","תעמולה","סילוף"]
CON=["מסכים","מסכימה","צודק","צודקת","תודה","מקבל את","בסדר גמור","מצוין","רעיון טוב","אין בעיה",
     "מקובל עלי","נשמע טוב","פשרה","מתנצל","סליחה","בהחלט","נכון מאוד","אתה צודק","את צודקת",
     "שכנעת","אשנה","תיקנתי","קיבלתי","הסכמה","מברך","יפה מאוד","עבודה יפה","כל הכבוד","אשמח","אנא","בבקשה"]
FRU=["נמאס","שוב פעם","כמה פעמים","עייפתי","מיותר","אין טעם","ויתרתי","חבל על הזמן","לא משנה",
     "עזבו","התעייפתי","מתיש","אין עם מי לדבר","חוזר על עצמו","במעגלים","לא מוביל לשום","אותו דבר שוב",
     "בפעם המי יודע כמה","הרמתי ידיים","מייאש","אבסורד"]

def _hits(text,lst): return sum(text.count(w) for w in lst)

def score(text):
    t=text.replace("״",'"')
    n=max(len(t),1)
    agg=_hits(t,AGG)+t.count("!!")+len(re.findall(r"[א-ת]!{1}",t))*0.2
    con=_hits(t,CON)
    fru=_hits(t,FRU)
    q=len(re.findall(r"\?\?+",t))  # ?? often rhetorical/hostile
    agg+=q*0.5
    raw={"agg":agg,"con":con,"fru":fru}
    per={k:v*1000/n for k,v in raw.items()}  # per-1000-chars intensity
    best=max(raw,key=lambda k:(raw[k],per[k]))
    if raw[best]==0 or per[best]<0.8: return {"label":"neu","s":0}
    return {"label":best,"s":min(round(per[best]/3,2),1)}
