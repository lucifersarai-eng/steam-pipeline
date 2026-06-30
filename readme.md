# steam-pipeline

End-to-end gaming data pipeline built on public Steam APIs.

Ingests game, player, and review data from Steam, transforms it through a structured medallion architecture, and delivers a dashboard with KPIs and game similarity analysis based on review co-mentions.

---

## Architecture

```
Steam APIs (Spy / Store / Reviews)
     │
     ▼
[ingestion/]          ← HTTP requests, retry with backoff, rate limiting
     │
     ▼
[raw/]                ← raw JSON responses, timestamped
     │
     ▼
[transform/]           ← cleaning, typing, flattening
     │
     ▼
[silver/]              ← structured CSVs (games, review_summaries, reviews)
     │
     ▼
[gold/]                 ← aggregated KPIs and co-mention analysis
     │
     ▼
[dashboard.ipynb]       ← Jupyter Notebook with charts, rendered on GitHub
```

---

## Data Sources

| Source | Endpoint | Data |
|---|---|---|
| Steam Spy API | `/api.php` | Top games, owners, players, price |
| Steam Store API | `/api/appdetails` | Game metadata, genres, platforms, Metacritic score |
| Steam Reviews API | `/appreviews/{appid}` | Review summary, individual review texts, helpful votes |

---

## Stack

- **Python** — ingestion, transformation, and analysis logic (standard library + `requests`)
- **pandas** — loading and exploring CSVs in the dashboard
- **matplotlib** — static charts that render reliably inside GitHub
- **Jupyter Notebook** — dashboard delivery, viewable directly on GitHub

---

## Project Structure

```
steam-pipeline/
├── ingestion/
│   ├── steam_spy.py         # top games, players, owners
│   ├── steam_store.py       # game metadata
│   └── steam_reviews.py     # review summaries and top reviews
├── transform/
│   ├── silver_games.py      # clean game dimension
│   └── silver_reviews.py    # clean review summaries and texts
├── gold/
│   ├── gold_kpis.py         # top games by score/volume, genre stats
│   └── gold_comentions.py   # game co-mentions extracted from reviews
├── utils/
│   └── helpers.py           # rate limiting, retry logic, logging
├── examples/
│   ├── steamspy_sample.json # sample raw data
│   └── games_sample.csv     # sample silver data
├── dashboard.ipynb           # final dashboard with charts
├── main.py                   # orchestrates the full ingestion pipeline
├── requirements.txt
└── .gitignore
```

---

## Key Design Decisions

- **Medallion architecture (Raw → Silver → Gold)** — same pattern used in production data platforms; separates ingestion fidelity from analytical readiness
- **Rate limiting & retry logic** — Steam APIs are rate-limited; the ingestion layer handles backoff gracefully
- **Timestamped raw data** — every ingestion run is saved with a timestamp, creating an audit trail
- **Co-mentions stay in Gold, not Silver** — Silver preserves the original review texts unmodified; the extraction of game mentions is an analytical step that belongs in Gold, so it can be recomputed without re-ingesting data

---

## Dashboard

`dashboard.ipynb` renders directly on GitHub and includes:

- Overview of the 100-game dataset
- Top 20 games by % positive reviews (minimum 1,000 reviews)
- Top 20 games by total review volume
- Average positive ratio by genre
- Top 15 game pairs co-mentioned in reviews (similarity signal)

---

## Why This Project

This project replicates a production-style data pipeline using public gaming data from Steam. The APIs have the same characteristics as real production sources: rate limits, pagination, inconsistent schemas, and nested payloads. It's a hands-on way to practice data engineering fundamentals — ingestion, transformation, layered data modeling, and analysis — end to end.

---

## Status

- [x] Architecture defined
- [x] Steam Spy ingestion
- [x] Steam Store ingestion
- [x] Steam Reviews ingestion
- [x] Silver layer transformations
- [x] Gold KPI models
- [x] Gold co-mention analysis
- [x] Dashboard

*Pipeline complete — built end to end from API ingestion through dashboard delivery.*
