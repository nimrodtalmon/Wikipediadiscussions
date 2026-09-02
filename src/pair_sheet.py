"""Print compact rating sheets for unrated revert pairs: metadata + unified diff of the two excerpts."""
import json,sys,difflib,pathlib
ROOT=pathlib.Path(__file__).resolve().parent.parent
pairs=json.loads((ROOT/"data/pairs.json").read_text())
done=json.loads((ROOT/"data/pair_quality.json").read_text())
todo=[k for k in pairs if k not in done]
s,e=int(sys.argv[1]),int(sys.argv[2])
print(f"TODO {len(todo)}")
for k in todo[s:e]:
    p=pairs[k]
    print("="*80); print(k); print(f"kept_by={p['kept_by']}  discarded_by={p['discarded_by']}")
    ka,da=p["kept_excerpt"],p["discarded_excerpt"]
    if ka==da: print("[identical excerpts — diff not localized]"); continue
    diff=list(difflib.unified_diff(da.splitlines(),ka.splitlines(),lineterm="",n=1))[2:]
    out="\n".join(diff)[:1600]
    print(out if out.strip() else "[no line-level diff in excerpt]")
