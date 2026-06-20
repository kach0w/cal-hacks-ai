# SafeStreets — backend

FastAPI app + Fetch.ai uAgent orchestrator + Redis + the two-stage Claude vision
pipeline + intervention/funding matching + last-mile routing.

```
src/safestreets/
  config.py            settings (env-driven)
  main.py              FastAPI app + CORS + router wiring

  api/                 HTTP surface
    routes.py            POST /analyze, SSE feed, GET intersection, POST submit, GET corridor
    schemas.py           request/response models

  models/              domain contracts (Pydantic) — the shared language of the system
    intersection.py      Intersection, ImageRef (with capture_date)
    condition.py         NamedZone, Confidence, ObservedCondition  (Stage 1 output)
    finding.py           FindingStatus, Corroboration, Finding      (Stage 2 output)
    intervention.py      Intervention
    funding.py           FundingProgram
    accountability.py    AccountabilityEvent
    analysis.py          AnalysisResult (the full bundle), ResidentSubmission

  orchestrator/        Fetch.ai uAgent — adaptive dispatch
    orchestrator.py      the uAgent (Fetch.ai track surface)
    dispatch.py          concurrent run + retry/backoff + signal-driven escalation
    messages.py          uAgent message models

  agents/              the workers
    structured_data.py   FARS + city open data
    news_agent.py        Browserbase news scrape
    council_311_agent.py Browserbase council PDF + 311 portal scrape
    image_fetcher.py     Google satellite + Street View (+ capture dates), resident override

  vision/              THE CORE
    stage1_blind.py      blind detection — imagery only, no community text
    stage2_corroborate.py independent corroboration -> CONFIRMED/CANDIDATE/REPORTED
    geometry.py          named zone -> deterministic marker placement
    prompts/             the two prompts (kept out of code)

  intervention/        finding -> action
    matcher.py           condition -> candidate intervention
    library.py           loads interventions.json
    funding_match.py     intervention -> SS4A/HSIP/state program
    data/                interventions.json, funding_programs.json

  render/
    annotate.py          numbered markers on the REAL image (PIL)
    concept.py           Midjourney concept illustration (SECONDARY, must be labeled)

  lastmile/            the half that actually changes outcomes
    ask.py               the specific costed request
    messenger.py         responsible official/body + next meeting + message draft
    coalition.py         aggregate corridor reports across residents
    accountability.py    "told in 2022, no action" — the durable record

  store/               Redis
    redis_client.py      async client singleton
    keys.py              key schema (lat/lng keying, TTLs)
    cache.py             JSON get/set helpers

  clients/             thin external API wrappers
    anthropic_client.py, browserbase_client.py, google_maps.py,
    nhtsa.py, socrata.py, midjourney.py
```

Run: `uvicorn safestreets.main:app --reload --app-dir src` (or `make backend` from repo root).
