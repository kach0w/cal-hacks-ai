# SafeStreets

**SafeStreets** is a multi-agent AI system that analyzes dangerous intersections and turns raw data into civic action. Pick any point on a map — SafeStreets reads crash records, 311 complaints, local news, Street View imagery, and council minutes, then produces a costed fix, a matching federal grant, a council letter, and a social media post ready to send.

Built for UC Berkeley AI Hackathon 3.0.

---

## How it works

```
map click ──▶ orchestrator (Fetch.ai adaptive dispatch)
                 ├─ crash data agent      (CCRS / city open data via Socrata)
                 ├─ 311 complaints agent  (Browserbase scrape)
                 ├─ news agent            (Browserbase scrape)
                 └─ image fetcher         (Google Street View + Satellite)
                          │
                       Redis  (24h cache per intersection)
                          │
    Stage 1 · BLIND VISION     Claude sees only images — no community text
    (what the camera sees)     → observed conditions with confidence scores
                          │
    Stage 2 · CORROBORATION    Independent match against crash/311/news records
    (two separate signals)     → CONFIRMED / CANDIDATE / REPORTED findings
                          │
    Stage 3 · INTERVENTION     Condition → costed fix → SS4A / HSIP grant match
                          │
    Stage 4 · LAST MILE        Single Claude call → tweet + council letter
                          │
    Stage 5 · CONCEPT RENDER   Gemini image edit: before → after (background)
```

**Two design decisions that make this defensible:**

1. **Blind-then-corroborate** — Stage 1 never sees complaint text, so "camera spotted" and "residents reported" are genuinely independent signals. A finding marked CONFIRMED means two independent sources agree.

2. **Named-zone geometry** — Claude assigns conditions to named zones (NW corner, N leg, …) rather than pixel coordinates. The renderer maps zones to marker positions deterministically. A marker can't land on the wrong corner.

---

## Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.11, FastAPI, Fetch.ai uAgents |
| AI | Claude Haiku (vision + text), Gemini Flash (image editing) |
| Data | CCRS crash records, Browserbase scraping, Google Maps API |
| Cache | Redis (24h per intersection, scrape + analysis split) |
| Frontend | Vite + React + TypeScript + Tailwind + Mapbox GL JS |

---

## Quick start

**Prerequisites:** Docker, Python 3.11+, Node 18+

```bash
# 1. Copy and fill in secrets
cp .env.example .env

# 2. Start Redis
make redis-up

# 3. Backend (terminal 1)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src uvicorn safestreets.main:app --reload --reload-dir src

# 4. Frontend (terminal 2)
cd frontend
npm install && npm run dev
```

Open http://localhost:5173 — click any intersection on the map.

---

## Environment variables

Create a `.env` file at the repo root:

```bash
# Required
ANTHROPIC_API_KEY=...
GOOGLE_MAPS_API_KEY=...         # Street View + Static Maps (server-restricted)
MAPBOX_TOKEN=...                # frontend map (set in frontend/.env as VITE_MAPBOX_TOKEN)

# Recommended
GOOGLE_AI_API_KEY=...           # Gemini before/after concept renders
BROWSERBASE_API_KEY=...         # 311 + news scraping
BROWSERBASE_PROJECT_ID=...

# Optional
SOCRATA_APP_TOKEN=...           # raises rate limits on city open data portals
CLAUDE_VISION_MODEL=claude-haiku-4-5-20251001
CLAUDE_TEXT_MODEL=claude-haiku-4-5-20251001
DEMO_CITY=Berkeley              # default city for data scoping
REDIS_URL=redis://localhost:6379/0
```

---

## Project layout

```
backend/
  src/safestreets/
    api/              HTTP routes (POST /analyze, SSE /analyze/stream, GET /intersection)
    orchestrator/     Fetch.ai uAgent + adaptive dispatch + Redis caching
    agents/           crash data, 311, news, image fetcher
    vision/           Stage 1 blind pass + Stage 2 corroboration (the core)
    intervention/     condition → fix → grant matching
    lastmile/         tweet, council letter, Reddit post generation
    render/           Gemini before/after concept image editing
    models/           shared Pydantic contracts
    store/            Redis client + key schema
    clients/          thin wrappers: Anthropic, Google Maps, Browserbase, Socrata

frontend/
  src/
    components/       MapboxMap, MarkerDetail, AgentFeed, LastMilePanel, ConceptRenders
    hooks/            useAnalysis (SSE feed), useIntersection (polling)
    api/              client.ts — typed fetch wrappers
    types/            mirrors backend Pydantic models

data/
  alameda_intersections.geojson   5,024 Alameda County dangerous intersections (CCRS-sourced)
```

---

## Caching behavior

Two-layer cache in Redis:

| Key | What | TTL |
|---|---|---|
| `ss:scrape:{lat}:{lng}` | Raw community data (crash/311/news/images) | 24h |
| `ss:vision:{lat}:{lng}` | Full analysis result + concept renders | 24h |

Both layers only write when they have real data — an analysis run where agents returned empty results is never cached, so the next request retries cleanly.

---

## Makefile shortcuts

```bash
make redis-up      # start Redis via Docker
make redis-down    # stop Redis
make backend       # install + run backend on :8000
make frontend      # install + run frontend on :5173
make test          # run backend tests
```
