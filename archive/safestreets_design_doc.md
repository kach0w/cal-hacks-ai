# SafeStreets — Hackathon Design Doc
**UC Berkeley AI Hackathon 3.0 · June 21–22, 2025**

---

## 1. Overview

Every city knows which intersections are dangerous. What they don't have is a fast, evidence-backed answer to the question: **what exactly should we do about it, and what will it cost?**

**SafeStreets** is a multi-agent system that ingests crash records, 311 complaints, local news, and city infrastructure data across multiple cities simultaneously — then produces specific, costed, intervention recommendations a community advocate or city traffic engineer can act on immediately. It doesn't just identify risk. It prescribes fixes, ranks them by cost-effectiveness, and generates a ready-to-present report for a city council meeting.

### The reframe: who actually uses this

The primary user is **not** a city bureaucrat. It's the person who has to pressure the city into action:

- A parent whose child was hit at an intersection, preparing for a city council meeting next Tuesday
- A community organizer building a case for infrastructure funding in an underserved neighborhood
- A local journalist investigating why a particular corridor has killed three pedestrians in two years
- A Vision Zero coordinator who needs to justify their top-10 priority list to the mayor's office

These users have urgency, a specific ask, and no access to the analytical infrastructure cities use internally. SafeStreets gives them a professional-grade evidence package in 90 seconds.

### What makes it different

Existing tools (city Vision Zero dashboards, NHTSA crash viewers) show you where crashes happened. They stop there. SafeStreets answers the next three questions no existing tool addresses together:

1. **Why** is this intersection dangerous? (contributing factors: signal timing, sight lines, speed, pedestrian volume)
2. **What** should be done? (ranked interventions with evidence from comparable cities)
3. **What will it cost and what's the projected impact?** (cost estimates + reduction percentages from peer-reviewed research)

### Prize tracks

| Sponsor | How |
|---|---|
| **Browserbase** | Fleet of agents scraping local news, city council minutes, and non-API city data portals simultaneously |
| **Fetch.ai** | Multi-agent orchestration: separate uAgents for data ingestion, risk scoring, intervention matching, and report generation |
| **Anthropic** | Claude for narrative synthesis, intervention reasoning, and report generation; social impact track |
| **Redis** | Intersection risk score caching; per-city data caching to avoid redundant API calls |
| **Deepgram** | Voice input: "Show me the most dangerous intersections for pedestrians in Oakland" |

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          USER INPUT                             │
│   City + neighborhood  │  Mode  │  Voice (Deepgram optional)    │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│               ORCHESTRATOR (Fetch.ai uAgent)                    │
│   Decomposes city into data tasks, spawns specialist agents     │
└───┬──────────────┬───────────────┬──────────────┬──────────────┘
    │              │               │              │
    ▼              ▼               ▼              ▼
┌────────┐  ┌──────────┐  ┌─────────────┐  ┌──────────────┐
│Structured│ │Browserbase│ │Browserbase  │  │Browserbase   │
│Data Agent│ │News Agent │ │Council Agent│  │311 Agent     │
│          │ │           │ │             │  │              │
│NHTSA FARS│ │Local news │ │City council │  │311 complaint │
│City APIs │ │crash      │ │meeting      │  │scrape for    │
│Vision    │ │reports    │ │minutes re:  │  │traffic/road  │
│Zero DBs  │ │(last 2yr) │ │road safety  │  │complaints    │
└────┬─────┘ └─────┬─────┘ └──────┬──────┘  └──────┬───────┘
     │             │              │                 │
     └─────────────┴──────────────┴─────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│              RISK SCORING AGENT (Fetch.ai uAgent)               │
│                                                                 │
│  Per-intersection composite score from:                         │
│  · Crash frequency + severity (fatalities weighted 10x)         │
│  · Crash trend (worsening vs improving)                         │
│  · Vulnerable road user involvement (pedestrian/cyclist flag)   │
│  · Complaint density (311 + news mentions)                      │
│  · Infrastructure gap signals (no crosswalk, no signal, etc.)   │
│                                                                 │
│  Output: ranked list of top 20 intersections with score + flags │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│           INTERVENTION AGENT (Claude + Redis)                   │
│                                                                 │
│  For each high-risk intersection:                               │
│  · Match contributing factors → intervention library            │
│  · Pull comparable city case studies from Redis cache           │
│  · Generate ranked recommendations with costs + evidence        │
│                                                                 │
│  Intervention library (evidence-based):                         │
│  · Leading Pedestrian Interval: $115/yr, −33% pedestrian injury │
│  · Speed camera: $~50k install, −21% fatal crashes              │
│  · Curb extensions (bulb-outs): $10–30k, improved sight lines   │
│  · Raised crosswalk: $15–50k, reduces vehicle speed             │
│  · Pedestrian refuge island: $20–60k, reduces crossing distance │
│  · Left-turn signal phase: $5–15k, reduces turning conflicts    │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│              REPORT AGENT (Claude + Fetch.ai uAgent)            │
│                                                                 │
│  Generates three output formats:                                │
│  · Interactive map (live, in browser)                           │
│  · Council brief (PDF-ready, 2-page format)                     │
│  · Full evidence report (all intersections, all sources cited)  │
└─────────────────────────────────────────────────────────────────┘
```

### Component table

| Component | Technology | Responsibility |
|---|---|---|
| Orchestrator | Fetch.ai uAgent | Decomposes city into tasks, spawns and manages specialist agents |
| Structured data agent | Python + REST | NHTSA FARS API, city open data portals, Vision Zero APIs |
| News agent | Browserbase + Stagehand | Scrapes local news for crash reports, investigative pieces |
| Council agent | Browserbase + Stagehand | City council meeting minutes mentioning road safety |
| 311 agent | Browserbase + Stagehand | City 311 portals without clean APIs (smaller cities) |
| Risk scoring agent | Fetch.ai uAgent | Composite intersection risk scoring and ranking |
| Intervention agent | Claude + Redis | Matches risk factors to evidence-based interventions |
| Report agent | Claude + Fetch.ai uAgent | Generates map, council brief, full evidence report |
| Intersection cache | Redis | Risk scores keyed by lat/lng, 24h TTL |
| Frontend | React + TypeScript + Mapbox GL | Live map, intersection detail cards, report download |
| Voice input | Deepgram STT | Natural language city/neighborhood queries |

---

## 3. Data Sources

### Structured APIs (reliable, no scraping needed)

**NHTSA FARS (Fatality Analysis Reporting System)**
Free public API. Returns fatal crash data from 2010 onwards by state, year, and location. Endpoints include `/crashes/GetCaseList` filtered by state + year range + coordinates. Covers all fatal motor vehicle crashes nationally. JSON output.
```
GET https://crashviewer.nhtsa.dot.gov/CrashAPI/crashes/GetCaseList
  ?states=6         # California FIPS code
  &fromYear=2020
  &toYear=2024
  &format=json
```

**City open data portals (major cities have clean APIs)**
- Chicago: `data.cityofchicago.org` — full traffic crash dataset updated continuously, Socrata API
- NYC: Vision Zero View Data via NYC Open Data, intersection-level aggregation
- SF: `data.sfgov.org` — 311 cases + traffic crash data, updated nightly
- DC: `opendata.dc.gov` — Vision Zero Safety dataset with public-facing API
- Austin, Portland, Philadelphia: all have Vision Zero dashboards with downloadable datasets

These cover the demo cities. For the "fleet of agents" scale angle, the Socrata Open Data API standard is shared across 100+ US city portals — one integration covers most major cities.

### Browserbase scraping targets (no clean API)

**Local news** — the most unique data source. Crash reports in local news contain information not in official databases: witness accounts, contributing factors police reports miss, community reaction, history of complaints at that location. Stagehand `extract()` on local news sites (SF Chronicle, Chicago Tribune, local TV stations) for crash-related articles by location.

**City council meeting minutes** — gold signal. When a community has complained about an intersection enough times, it appears in council minutes. This is the "pre-crash" signal: intersections under community complaint before a fatality occurs. Many cities post PDFs; Stagehand handles PDF extraction via browser rendering.

**311 portals without APIs** — smaller cities have 311 web interfaces but no API. Stagehand scrapes complaint categories related to traffic: broken signals, missing crosswalks, sight-line obstructions, speeding complaints.

---

## 4. Risk Scoring Model

Each intersection gets a composite score (0–100) built from five weighted components:

```python
def intersection_risk_score(intersection: dict) -> float:
    # Component 1: Crash severity (40% weight)
    severity = (
        intersection["fatalities"] * 10 +
        intersection["serious_injuries"] * 3 +
        intersection["minor_injuries"] * 1
    ) / intersection["years_of_data"]

    # Component 2: Trend direction (20% weight)
    # positive = worsening, negative = improving
    trend = linear_regression_slope(intersection["crashes_by_year"])

    # Component 3: Vulnerable road user flag (20% weight)
    vru = (
        intersection["pedestrian_crashes"] +
        intersection["cyclist_crashes"]
    ) / max(intersection["total_crashes"], 1)

    # Component 4: Community signal density (10% weight)
    community = (
        intersection["news_mentions"] * 2 +
        intersection["complaints_311"] +
        intersection["council_mentions"] * 3
    )

    # Component 5: Infrastructure gap (10% weight)
    # derived from Claude analysis of news + council text
    gap = intersection.get("infrastructure_gap_score", 0)

    return normalize(
        severity * 0.4 +
        trend * 0.2 +
        vru * 0.2 +
        community * 0.1 +
        gap * 0.1
    )
```

The **trend component** is what makes this genuinely predictive rather than retrospective — an intersection with 3 crashes last year and 8 this year scores higher than one with a stable 6 crashes/year. Most city dashboards don't surface this.

The **community signal** component is the novel data layer. An intersection appearing in council minutes three times in two years is a leading indicator. Official crash data is a lagging indicator.

---

## 5. Intervention Library

Every recommendation is grounded in peer-reviewed research. The intervention agent matches intersection risk factors to the appropriate countermeasure:

| Intervention | Trigger condition | Cost estimate | Evidence |
|---|---|---|---|
| Leading Pedestrian Interval (LPI) | Pedestrian crashes at signalized intersection | $115/intersection/year | 33% reduction in pedestrian injury (Columbia, Nature Cities 2024); 46–71% reduction in ped-vehicle crashes (NACTO) |
| Speed camera | Speeding cited in crash reports; school zone proximity | $50k install | 21% reduction in fatal crashes (NYC DOT longitudinal study); effective on arterial roads |
| Curb extension (bulb-out) | Sight-line issues; high pedestrian volume | $10–30k | Reduces crossing distance; forces vehicle speed reduction at turn |
| Raised crosswalk | Mid-block crossing; high pedestrian volume | $15–50k | Reduces vehicle speeds; increases driver yielding |
| Pedestrian refuge island | Wide multilane crossing | $20–60k | Reduces exposure time; allows staged crossing |
| Left-turn signal phase | Left-turn conflicts in crash data | $5–15k | Eliminates permitted left-turn conflicts with pedestrians |
| High-visibility crosswalk markings | Unmarked or faded crosswalk | $2–5k | Low cost, high visibility; effective near schools and transit |
| Rectangular rapid-flash beacon (RRFB) | Uncontrolled crossing; mid-block | $15–40k | 47% reduction in pedestrian crashes at uncontrolled crossings (FHWA) |

The intervention agent prompt instructs Claude to:
1. Identify the top 2–3 contributing factors from the crash and complaint data
2. Match those factors to the intervention library
3. Rank by cost-effectiveness ratio (projected injury reduction / cost)
4. Pull 1–2 real-world comparable city case studies from the hardcoded intervention library
5. Generate a plain-English justification a non-engineer can present at a council meeting

---

## 6. Fetch.ai Agent Design

Five uAgents registered on Agentverse, communicating via Fetch.ai Chat Protocol:

**`OrchestratorAgent`**
Receives the city + neighborhood input. Decomposes into parallel tasks: which structured APIs to query, which Browserbase scraping jobs to spawn, which date ranges to cover. Dispatches tasks to specialist agents. Collects results and triggers the risk scorer.

**`DataIngestionAgent`**
Handles all structured API calls: NHTSA FARS, city open data portals. Returns normalized intersection-level crash records. Registers on Agentverse so other projects can reuse the data layer — this is the "Search and Discover" feature Fetch.ai judging specifically rewards.

**`RiskScoringAgent`**
Receives normalized crash + complaint data. Runs the composite scoring model. Returns ranked intersection list with score components broken out. Stores scores in Redis.

**`InterventionAgent`**
Receives a high-risk intersection profile. Checks Redis cache for previously scored similar intersections. Calls Claude to generate ranked recommendations. Returns structured intervention plan with costs and evidence citations.

**`ReportAgent`**
Receives full analysis output. Calls Claude to generate three artifacts: the map data payload, the council brief narrative, and the full evidence report. Handles formatting and export.

Agent communication example:
```python
from uagents import Agent, Context, Model

class IntersectionTask(Model):
    city: str
    neighborhood: str
    lat: float
    lng: float
    radius_miles: float

class RiskProfile(Model):
    intersection_id: str
    address: str
    risk_score: float
    crash_count: int
    pedestrian_flag: bool
    trend: str           # "worsening" | "stable" | "improving"
    community_signals: list[str]
    top_contributing_factors: list[str]

# Orchestrator dispatches to risk scorer
@orchestrator.on_message(model=IntersectionTask)
async def handle_task(ctx: Context, sender: str, task: IntersectionTask):
    crash_data = await query_structured_apis(task)
    scraped_data = await run_browserbase_agents(task)
    merged = merge_and_deduplicate(crash_data, scraped_data)
    await ctx.send(risk_scorer.address, merged)
```

---

## 7. The Scalability Angle

The demo story that wins: **one query, multiple cities, fleet of agents.**

Input: *"Compare the 5 most dangerous pedestrian corridors in Oakland, San Jose, and Fresno."*

What fires:
- 3 city open data API calls (simultaneous)
- 9 Browserbase sessions (3 cities × local news + council minutes + 311)
- Risk scorer runs on all three cities in parallel
- Intervention agent generates recommendations for top 5 intersections per city
- Report agent produces a cross-city comparison

The frontend shows a live dashboard: agents spawning, sources completing, risk scores populating on the map in real time. Three cities' worth of infrastructure intelligence in under 2 minutes.

This is the scalability argument made *visible*, not just claimed. Judges watch 12 simultaneous data streams converge into a ranked, actionable map. That's the wow moment.

Browserbase is the right tool here specifically because the scraping targets (local news, council minutes, 311 portals) have inconsistent or nonexistent APIs across cities — exactly the problem Browserbase's managed browser infrastructure with Stagehand's AI-native extraction is built to solve.

---

## 8. Frontend

**Stack:** React + TypeScript + Tailwind + Mapbox GL JS

### Views

**Live agent dashboard (the wow moment)**
Full-screen view showing the fleet of agents working: each Browserbase session represented as a card with source name, status (scraping / processing / complete), and a live count of data points ingested. As agents complete, risk scores begin populating on the map. This view runs for ~90 seconds at the start of the demo.

**Risk map**
Mapbox GL map with intersection markers colored by risk score (green → yellow → red). Click any intersection for the detail panel. Filter controls: pedestrian crashes only, date range, severity threshold.

**Intersection detail panel**
- Risk score breakdown (5 components, visualized)
- Crash timeline (bar chart by year — shows trend)
- Source log (which news articles, 311 complaints, council minutes contributed)
- Ranked intervention recommendations with cost estimates and evidence links
- "Export to council brief" button

**Compare mode**
Side-by-side city comparison. Same risk map interface, split-screen. Used for the multi-city demo moment.

**Council brief export**
Two-page PDF-ready layout: executive summary, top 3 intersections with photos (pulled via Street View API), intervention recommendations with costs, evidence citations. Designed to be handed directly to a city council member.

---

## 9. Build Plan

### Saturday (day 1)

| Time | Goal |
|---|---|
| 9am–11am | NHTSA FARS API + one city open data portal (Chicago, best API) working end-to-end |
| 11am–1pm | Risk scoring model + basic map rendering with real data |
| 1pm–3pm | Browserbase news scraper (Stagehand) for one city |
| 3pm–5pm | Claude intervention agent + intervention library prompt |
| 5pm–7pm | Basic React map frontend with intersection detail panel |

**End of day 1 goal:** One city, real data, risk map renders, one intersection has intervention recommendations. Everything else is additive.

### Sunday (day 2)

| Time | Goal |
|---|---|
| 9am–10am | Fetch.ai uAgents setup: Orchestrator + DataIngestion wired together |
| 10am–11am | Multi-city parallel execution (add SF + Oakland) |
| 11am–12pm | Live agent dashboard UI (the wow visualization) |
| 12pm–1pm | Council brief PDF export |
| 1pm–2pm | Redis caching layer (risk scores + API responses) |
| 2pm–3pm | Deepgram voice input (if time) |
| 3pm–4pm | Demo polish, edge cases, README, Devpost |

---

## 10. Demo Script (2 minutes)

1. **Voice input:** "Find the most dangerous pedestrian intersections in Oakland and San Jose."
2. **Agent dashboard fires.** Show 8 sessions spawning — NHTSA, city portals, local news, 311. Data points ticking up. (~45 seconds)
3. **Map populates.** Red markers appear. Point out the highest-risk intersection in Oakland.
4. **Click the intersection.** Show the detail panel: risk score 87/100, 4 pedestrian fatalities in 3 years, worsening trend, 12 community complaints, 2 council meeting mentions.
5. **Scroll to interventions.** "Claude recommends: Leading Pedestrian Interval ($115/year, 33% reduction in pedestrian injury, already proven at 2,951 NYC intersections), plus curb extension on the northwest corner where sight lines are obstructed per 3 news reports."
6. **Hit "Export council brief."** Show the 2-page PDF. "This is what a parent brings to the city council meeting on Tuesday."
7. **Switch to compare mode.** San Jose map populates alongside Oakland. "Same query, two cities, 90 seconds."

---

## 11. References

- NHTSA FARS API: https://crashviewer.nhtsa.dot.gov/CrashAPI
- Chicago crash data (Socrata): https://data.cityofchicago.org/Transportation/Traffic-Crashes-Crashes/85ca-t3if
- NYC Vision Zero open data: https://data.cityofnewyork.us/widgets/v7f4-yzyg
- SF 311 open data: https://data.sfgov.org/City-Infrastructure/311-Cases/vw6y-z8j6
- DC Vision Zero Safety API: https://opendata.dc.gov/datasets/vision-zero-safety/api
- LPI effectiveness (Columbia / Nature Cities, 2024): 33% reduction in pedestrian injury at 6,003 NYC intersections
- LPI cost-effectiveness (NACTO): $115/intersection/year, 46–71% crash reduction
- Speed camera effectiveness (NYC longitudinal, ScienceDirect 2025): 21% reduction in fatal crashes
- Browserbase Stagehand v3: https://www.browserbase.com/blog/stagehand-v3
- Fetch.ai uAgents quickstart: https://uagents.fetch.ai/docs/quickstart
- Fetch.ai Agentverse: https://agentverse.ai
