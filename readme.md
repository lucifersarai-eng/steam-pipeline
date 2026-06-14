# steam-pipeline

End-to-end gaming data pipeline built on the Steam Web API.

Ingests game and player data from Steam, transforms it through a structured data model, and delivers a dashboard tracking player behavior, game performance, and revenue proxies — the same type of pipeline I build professionally in production.

---

## Architecture

```
Steam Web API
     │
     ▼
[ingestion.py]        ← HTTP requests, pagination, error handling
     │
     ▼
[raw/]                ← raw JSON responses, timestamped
     │
     ▼
[transform.py]        ← cleaning, typing, deduplication
     │
     ▼
[silver/]             ← structured tables (games, players, reviews)
     │
     ▼
[gold/]               ← aggregated models (KPIs, trends, rankings)
     │
     ▼
[dashboard]           ← Power BI / Looker Studio
```

---

## Data Sources

| Source | Endpoint | Data |
|---|---|---|
| Steam Store API | `/appdetails` | Game metadata, price, genres |
| Steam Spy API | `/app` | Player counts, revenue estimates, ratings |
| Steam Reviews API | `/reviews` | User reviews, sentiment, volume |

---

## Stack

- **Python** — ingestion, transformation logic
- **SQL** — data modelling (Silver/Gold layers)
- **Pandas / DuckDB** — local transformation and querying
- **Power BI / Looker Studio** — dashboard delivery

---

## Project Structure

```
steam-pipeline/
├── ingestion/
│   ├── steam_store.py       # game metadata ingestion
│   ├── steam_spy.py         # player and revenue data
│   └── steam_reviews.py     # reviews ingestion
├── transform/
│   ├── silver_games.sql     # clean game dimension
│   ├── silver_players.sql   # clean player metrics
│   └── silver_reviews.sql   # clean reviews
├── gold/
│   ├── gold_kpis.sql        # top games by player count, reviews, price
│   └── gold_trends.sql      # weekly player trend by genre
├── utils/
│   └── helpers.py           # rate limiting, retry logic, logging
├── notebooks/
│   └── exploration.ipynb    # EDA and model validation
├── requirements.txt
└── README.md
```

---

## Key Design Decisions

- **Medallion architecture (Raw → Silver → Gold)** — same pattern used in production; separates concerns between ingestion fidelity and analytical readiness
- **Rate limiting & retry logic** — Steam API has strict rate limits; ingestion layer handles backoff gracefully
- **Idempotent loads** — re-running the pipeline doesn't duplicate data
- **Schema validation** — type checks and null assertions at the Silver layer catch upstream API changes early

---

## Dashboard KPIs

- Top 50 games by concurrent players (7-day trend)
- Revenue proxy by genre and publisher
- Review sentiment score vs player retention
- Price vs rating distribution

---

## Why This Project

I work professionally with data pipelines in Databricks — this project replicates that work using public gaming data. The Steam API has the same characteristics as real production sources: rate limits, pagination, schema inconsistencies, and high-volume payloads. It's a natural bridge between my current stack and the gaming data engineering domain.

---

## Status

- [x] Architecture defined
- [X] Steam Store ingestion
- [ ] Steam Spy ingestion  
- [X] Silver layer transformations
- [ ] Gold KPI models
- [ ] Dashboard

*In progress — contributions welcome.*
