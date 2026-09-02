# Wikipedia discussions — emotional dynamics in Hebrew-Wikipedia mental-health talk pages

Funded by Wikimedia Israel (Dror Lin fund). PIs: Anat Talmon (HUJI), Nimrod Talmon (BGU).
Question: do emotions in talk-page discussions predict discussion structure and, through it,
article quality — stability (versions survive) and correctness (versions are right)?

Site: https://nimrodtalmon.github.io/Wikipediadiscussions/ (homepage → `method.html` → `explorer.html`)
Report: Overleaf project 6a97251075788b2977dd80db (compiled copy in `site/report.pdf`).

## Pipeline (each module a pure function of the previous)
| # | Module | Code | Status |
|---|--------|------|--------|
| 1 | Corpus + fetch | `src/scope_candidates.py` (ranking, internal), `src/fetch_talk.py` | seed of 18 articles |
| 2 | Segmentation (threads, comments, reply tree) | `src/parse_threads.py`, `build_site.comments()` | v1 |
| 3 | Comment emotion — A lexicon (`data/lexicon.csv`), B LLM (`data/emotion_llm.json`) | `src/emotion.py`, `src/emotion_sheet.py` | complete (1,220 comments) |
| 4 | Discussion dynamics | `src/dynamics.py` | v0 |
| 5 | Article stability | `src/stability.py` | v0 |
| 6 | Version quality — LLM rater; samples A (`data/quality.json`) and B pairs (`src/pair_quality.py`, `data/pair_quality.json`) | `src/llm_quality.py` | v0 |
| 7 | Linking threads ↔ edits | `src/link_threads.py` | v1 (score) |
| 8 | Analysis | `src/analysis.py {lex|llm}` → `data/analysis_*.json` | smoke test |

`src/build_site.py` runs 2–7 over fetched data and writes `site/corpus.json` for the site.

## Workflow
```
python3 src/fetch_talk.py data/seed_core.txt      # fetch (raw JSON is git-ignored)
python3 src/build_site.py                         # rebuild site data (+cache-busting)
python3 src/analysis.py llm                       # analysis on the LLM implementation
```
Raw article data is never committed; coded/rated files under `data/` are.
