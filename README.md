# Wikipedia discussions — emotional dynamics in he.wiki mental-health talk pages

Funded by Wikimedia Israel (Dror Lin fund). PIs: Anat Talmon, Nimrod Talmon.

Question: do emotional expressions in talk-page discussions predict discussion structure (dropout vs. convergence) and, through it, article quality (stability of consensus versions; expert-rated correctness)?

## Layout
- `src/fetch_talk.py <seedfile>` — fetch talk page + archive subpages and revision metadata (talk + article) into `data/<article>.json`
- `src/parse_threads.py` — split talk pages into threads, count signed comments/editors → `data/threads.csv`
- `data/seed_core.txt`, `data/seed_adjacent.txt` — curated article lists (in progress)

Raw fetched JSON is git-ignored; regenerate with the fetcher.
Report lives on Overleaf (project 6a97251075788b2977dd80db).
