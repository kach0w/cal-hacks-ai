# SafeStreets

A multi-agent system that reads an intersection — crash records, 311 complaints, local
news, council minutes, and satellite + Street View imagery — identifies the specific
physical conditions causing harm, and routes each finding to the action that gets it
fixed: the ask, the matching grant program, the responsible official, and an
accountability record of whether the city ever responded.

This repo is the implementation scaffold for the design described in
`safestreets_v3_design_doc.md`. Configs and data contracts are written; the harder
pieces are stubbed with clear interfaces so the team can parallelize.

> Built for UC Berkeley AI Hackathon 3.0.

---

## The core idea in one diagram

```
address ──> orchestrator (Fetch.ai uAgent, adaptive dispatch)
              ├─ structured data agent   (FARS, city open data)
              ├─ news agent              (Browserbase scrape)
              ├─ council/311 agent       (Browserbase scrape)
              ├─ image fetcher           (Google satellite + Street View + dates)
              └─ resident submissions    (current photos fill data deserts)
                        │
                     Redis  (cache + coalition reports + accountability log)
                        │
   Stage 1: BLIND VISION (Claude, imagery only) ── observed conditions + confidence
                        │
   Stage 2: CORROBORATION (independent match)   ── CONFIRMED / CANDIDATE / REPORTED
                        │
   intervention + funding agent (Claude) ── candidate fix + SS4A/HSIP match + messenger
                        │
   output: annotated REAL image + last-mile packet + one-pager
```

The two design decisions that make this defensible (and which the code structure
protects):

1. **Blind-then-corroborate.** Stage 1 never sees the complaint text, so "seen" and
   "reported by residents" are two independent signals. See `vision/stage1_blind.py`
   and `vision/stage2_corroborate.py`.
2. **Named-geometry placement, not raw pixels.** Claude assigns conditions to named
   zones (NW corner, N leg, ...); the renderer maps zones to marker positions
   deterministically. A marker can't land on the wrong corner. See `vision/geometry.py`.

---

## Layout

```
backend/   FastAPI + Fetch.ai uAgents + Redis + Claude vision pipeline (Python)
frontend/  Vite + React + TypeScript + Tailwind + Mapbox GL
```

See `backend/README.md` and `frontend/README.md` for module-by-module detail.

---

## Quick start

Prereqs: Docker (for Redis), Python 3.11+, Node 18+.

```bash
# 1. secrets
cp .env.example .env            # fill in API keys

# 2. Redis
make redis-up                   # docker compose up -d redis

# 3. backend
make backend                    # installs deps, runs FastAPI on :8000

# 4. frontend (separate terminal)
make frontend                   # installs deps, runs Vite on :5173

# 5. (optional) preload the demo intersection so the demo is reliable
make demo-seed
```

---

## Keys you need

| Key | Used by | Where |
|---|---|---|
| `ANTHROPIC_API_KEY` | vision, intervention, last-mile | console.anthropic.com |
| `BROWSERBASE_API_KEY` / `BROWSERBASE_PROJECT_ID` | news + council/311 agents | browserbase.com |
| `GOOGLE_MAPS_API_KEY` | image fetcher (Static Maps + Street View) | Google Cloud console |
| `SOCRATA_APP_TOKEN` | city open data (optional, raises rate limits) | data portal dev settings |
| `MIDJOURNEY_API_KEY` | concept illustration (optional, secondary) | provider-dependent |
| `MAPBOX_TOKEN` (frontend) | map selector | mapbox.com |

---

## A known decision point: Stagehand

The design names **Browserbase + Stagehand** for scraping. Stagehand is TypeScript-first.
This scaffold keeps the backend in Python and uses the Browserbase Python SDK in the
scraping agents. If you want Stagehand specifically, split the news/council agents into
a small Node sidecar and have the Python orchestrator call it over HTTP. The agent
interfaces in `agents/` are written so either choice drops in without touching the rest
of the pipeline.

---

## Build-plan mapping (from the design doc)

| Day 1 | Files |
|---|---|
| FARS + one city portal + imagery with dates | `clients/nhtsa.py`, `clients/socrata.py`, `clients/google_maps.py`, `agents/` |
| Stage 1 blind vision + correct placement | `vision/stage1_blind.py`, `vision/geometry.py` |
| Stage 2 corroboration | `vision/stage2_corroborate.py` |
| intervention + funding match | `intervention/` |
| frontend annotated real image | `frontend/src/components/AnnotatedImage.tsx` |

| Day 2 | Files |
|---|---|
| adaptive orchestration | `orchestrator/` |
| live agent feed (SSE) | `api/routes.py`, `frontend/src/hooks/useAnalysis.ts`, `AgentFeed.tsx` |
| last-mile packet + one-pager | `lastmile/`, `OnePagerExport.tsx` |
| resident submissions | `agents/image_fetcher.py` (supersede), `ResidentSubmit.tsx` |
| stretch: coalition, concept render | `lastmile/coalition.py`, `render/concept.py` |
