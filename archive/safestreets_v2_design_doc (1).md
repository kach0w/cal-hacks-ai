# SafeStreets — Hackathon Design Doc v2
**UC Berkeley AI Hackathon 3.0 · June 21–22, 2025**

---

## 1. Overview

Every city knows which intersections are dangerous. What they can't answer fast is: **what exactly is physically wrong, and what needs to change?**

**SafeStreets** is a multi-agent system that takes an intersection, pulls crash records, 311 complaints, local news, and city data — then reads the actual street using satellite and Street View imagery to identify the specific physical conditions causing harm. It produces a marked-up top-down view of the intersection with annotated fix recommendations grounded in real community data.

It doesn't show you a risk score. It shows you the bush that's been in three 311 complaints since 2021 and is still there.

### The reframe: who actually uses this

The primary user is the person who has to pressure the city into action:

- A parent whose child was hit at an intersection, preparing for a city council meeting next Tuesday
- A community organizer building a case for infrastructure funding in an underserved neighborhood
- A local journalist investigating why a particular corridor has killed three pedestrians in two years
- A Vision Zero coordinator who needs to justify their top priority list to the mayor's office

These users don't need another dashboard. They need a tool that looks at the street, tells them exactly what's wrong, and gives them something concrete to point at.

### What makes it different

Every existing tool — city Vision Zero dashboards, NHTSA crash viewers — tells you a number. SafeStreets shows you the street and says: *here, that thing, fix that.*

A city engineer looks at the annotated output and immediately knows whether it's right. A parent looks at it and finally has a visual answer to why this keeps happening. Not statistics — a picture with an arrow pointing at the obstruction that's been killing people.

### Prize tracks

| Sponsor | How |
|---|---|
| **Fetch.ai** | Orchestrator uAgent dispatches and manages the fleet of Browserbase scraping agents; coordinates the full analysis pipeline |
| **Browserbase** | Scrapes local news, city council minutes, and 311 portals — spawned and controlled by the Fetch.ai orchestrator |
| **Anthropic** | Claude for street image analysis, intervention reasoning, and annotation generation; social impact track |
| **Redis** | Caches and stores all scraped data, vision analysis results, and intersection risk profiles; keyed by lat/lng with TTL |
| **Midjourney** | Generates photorealistic before/after renderings of the intersection with proposed fixes applied |

---

## 2. Core Concept: Street Vision Analysis

The central innovation is using Claude's vision capability to read a street the way a traffic engineer would on a site visit — except cross-referenced against why people have actually been getting hurt there.

### Input pipeline

1. User submits an intersection (address or map click)
2. Fetch.ai orchestrator spawns Browserbase agents to pull crash data, 311 complaints, news reports, council minutes — stores all results in Redis
3. System fetches Google Maps Static API satellite image (top-down) + Street View images (4 cardinal directions)
4. Claude receives: the satellite image, Street View images, and the aggregated community data from Redis
5. Claude identifies physical conditions contributing to crashes and maps them to specific locations on the top-down view
6. Midjourney generates a before/after rendering: the current intersection vs. the intersection with the top recommended fixes applied

### What the vision analysis looks for

Claude is prompted to identify physical infrastructure conditions visible in imagery, cross-referenced against complaint and crash data:

| Condition | Detection signal | Data corroboration |
|---|---|---|
| Missing or faded crosswalk markings | Satellite imagery | 311 complaints about "unmarked crossing" |
| Vegetation obstructing sightlines | Street View corners | News reports citing "visibility issues" |
| No curb extension / parking blocking view | Satellite geometry | Crash reports: right-turn conflicts |
| Missing stop bar setback | Satellite imagery | Crash reports: vehicles in crosswalk |
| No pedestrian signal or LPI | Street View | 311 complaints about signal timing |
| Narrow sidewalk / no buffer | Satellite measurement | Pedestrian crash density |
| Poor lighting conditions | Street View | Night crash clustering |
| High-speed approach geometry | Satellite road width | Speed cited in crash reports |

### Annotation output

The primary output is the satellite image annotated with 3–5 numbered fix markers, each grounded in both what the vision model sees and what the community data confirms:

```
[1] Extend curb on northwest corner
    Seen: No curb extension; parking extends to crosswalk line
    Data: 3 of 5 pedestrian strikes occurred at this corner
    Fix: Curb extension removes 2 parking spots, eliminates blind spot
    Cost: $10,000–30,000 | Impact: −40% right-turn conflicts

[2] Clear vegetation on southeast corner
    Seen: Mature shrubs obscure pedestrian visibility at 3ft height
    Data: SF Chronicle, March 2023 — witness cited "couldn't see anyone"
    Fix: Trim to below 30 inches per NACTO sight-line standard
    Cost: $500–2,000/year maintenance | Impact: immediate

[3] Repave crosswalk markings (north leg)
    Seen: Faded to near-invisible in satellite imagery
    Data: 311 complaint #2847221, July 2022 — "crosswalk completely gone"
    Fix: High-visibility ladder markings
    Cost: $2,000–5,000 | Impact: −30% pedestrian conflicts at unmarked crossings

[4] Add Leading Pedestrian Interval
    Seen: Standard concurrent-phase signal, no LPI
    Data: 4 pedestrian strikes during turning movements
    Fix: 7-second LPI head start for pedestrians
    Cost: $115/year | Impact: −33% pedestrian injury (Columbia/Nature Cities 2024)
```

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          USER INPUT                             │
│                   Address / map click                           │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│               ORCHESTRATOR (Fetch.ai uAgent)                    │
│   Dispatches Browserbase agents + image fetcher in parallel     │
└───┬──────────────┬───────────────┬──────────────┬──────────────┘
    │              │               │              │
    │   [Fetch.ai dispatches all Browserbase agents below]        │
    ▼              ▼               ▼              ▼
┌────────┐  ┌──────────┐  ┌─────────────┐  ┌──────────────┐
│Structured│ │Browserbase│ │Browserbase  │  │ Image Fetcher│
│Data Agent│ │News Agent │ │Council/311  │  │              │
│          │ │           │ │Agent        │  │Google Maps   │
│NHTSA FARS│ │Local news │ │Council mins │  │Static API    │
│City APIs │ │crash      │ │311 portals  │  │(satellite)   │
│Vision    │ │reports    │ │             │  │Street View   │
│Zero DBs  │ │(last 2yr) │ │             │  │API (4 dirs)  │
└────┬─────┘ └─────┬─────┘ └──────┬──────┘  └──────┬───────┘
     │             │              │                 │
     └─────────────┴──────────────┴─────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    REDIS (cache + store)                         │
│                                                                 │
│  Stores: scraped news/311/council data (keyed by intersection)  │
│  Stores: structured crash records from city APIs                │
│  Caches: vision analysis results (lat/lng key, 24h TTL)         │
│  Caches: intervention recommendations per intersection          │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│              VISION ANALYSIS AGENT (Claude)                     │
│                                                                 │
│  Receives: satellite image + 4 Street View images +             │
│            aggregated crash/complaint/news data from Redis      │
│                                                                 │
│  Outputs: structured list of physical conditions with           │
│           location coordinates on the satellite image,          │
│           matched to community data signals                     │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│           INTERVENTION AGENT (Claude)                           │
│                                                                 │
│  Maps identified conditions → evidence-based interventions      │
│  Pulls cost estimates + peer-reviewed impact data               │
│  Ranks by cost-effectiveness                                    │
│  Writes results back to Redis                                   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│              ANNOTATION + RENDER AGENT                          │
│                                                                 │
│  Claude: generates numbered overlay annotations on satellite    │
│  Midjourney: before/after photorealistic street rendering       │
│             with top recommended fixes applied                  │
│                                                                 │
│  Side output (optional): city council complaint document        │
└─────────────────────────────────────────────────────────────────┘
```

### Component table

| Component | Technology | Responsibility |
|---|---|---|
| Orchestrator | Fetch.ai uAgent | Dispatches and manages all Browserbase scraping agents; coordinates full pipeline |
| Structured data agent | Python + REST | NHTSA FARS, city open data, Vision Zero APIs |
| News agent | Browserbase + Stagehand | Local news crash reports — spawned by Fetch.ai orchestrator |
| Council/311 agent | Browserbase + Stagehand | Council minutes + 311 portals — spawned by Fetch.ai orchestrator |
| Image fetcher | Google Maps Static API + Street View API | Satellite top-down + 4-direction street-level images |
| Redis | Redis | Caches and stores all scraped data, crash records, vision results, and intervention plans keyed by lat/lng |
| Vision analysis agent | Claude (vision) | Identifies physical conditions in imagery, reads from Redis |
| Intervention agent | Claude | Maps conditions to evidence-based fixes; writes results to Redis |
| Annotation + render agent | Claude + Midjourney | Annotated satellite overlay + photorealistic before/after rendering |
| Frontend | React + TypeScript + Mapbox GL | Map interface, intersection detail, annotated output, before/after view |

---

## 4. Data Sources

### Structured APIs

**NHTSA FARS** — Fatal crash data 2010–present by state, year, coordinates.

```
GET https://crashviewer.nhtsa.dot.gov/CrashAPI/crashes/GetCaseList
  ?states=6&fromYear=2020&toYear=2024&format=json
```

**City open data portals**
- Chicago: `data.cityofchicago.org` — traffic crash dataset, Socrata API
- NYC: Vision Zero View via NYC Open Data, intersection-level
- SF: `data.sfgov.org` — 311 cases + traffic crash data, updated nightly
- DC: `opendata.dc.gov` — Vision Zero Safety dataset
- 100+ additional cities: Socrata Open Data API standard

**Google Maps imagery**
- Static Maps API: satellite top-down, configurable zoom (zoom 19–20 for intersection detail)
- Street View Static API: 4 cardinal directions at the intersection, 640×640px

### Browserbase scraping targets

**Local news** — crash reports contain information not in official databases: witness accounts, contributing factors police reports miss, specific physical descriptions of the scene. Stagehand `extract()` on local news sites for crash-related articles by location and date range.

**City council meeting minutes** — leading indicator. When a community has complained enough, the intersection appears in minutes before a fatality. Many cities post PDFs; Stagehand handles PDF extraction via browser rendering.

**311 portals without APIs** — smaller cities have web interfaces but no API. Stagehand scrapes complaint categories: broken signals, missing crosswalks, sight-line obstructions, speeding complaints, vegetation blocking signs.

---

## 5. Vision Analysis: Claude Prompt Design

The vision analysis agent receives a structured prompt combining imagery and community data:

```
You are analyzing an intersection for physical infrastructure conditions 
contributing to pedestrian and cyclist crashes.

You have:
- 1 satellite top-down image of the intersection
- 4 Street View images (N/S/E/W approaches)
- Crash data: [N crashes, breakdown by type, locations, years]
- 311 complaints: [list of relevant complaints with dates]
- News reports: [excerpts mentioning physical conditions]
- Council mentions: [relevant references]

Your task:
1. Identify 3–5 specific physical conditions visible in the imagery
   that are likely contributing to crashes
2. For each condition, note:
   - Exact location (which corner, which leg, which approach)
   - What you see in the image that indicates the problem
   - Which community data points corroborate this observation
   - The specific intervention that addresses it
   - Estimated cost range and projected impact from the intervention library

Return as structured JSON with pixel coordinates on the satellite image
for annotation placement.

Do not invent conditions not visible in the imagery.
Do not recommend interventions not corroborated by at least one data source.
```

The constraint — *do not invent conditions not visible in the imagery* — is the key guardrail. Every annotation is defensible because it's grounded in both what the model sees and what residents have reported.

---

## 6. Intervention Library

| Intervention | Trigger condition | Cost estimate | Evidence |
|---|---|---|---|
| Leading Pedestrian Interval (LPI) | Pedestrian crashes at signalized intersection; turning conflicts | $115/yr | −33% pedestrian injury (Columbia/Nature Cities 2024); −46–71% ped-vehicle crashes (NACTO) |
| Speed camera | Speeding cited in crash reports; school zone proximity | $50k install | −21% fatal crashes (NYC DOT longitudinal, ScienceDirect 2025) |
| Curb extension (bulb-out) | Parking blocking sightline; right-turn conflicts | $10–30k | Reduces crossing distance; forces vehicle speed reduction |
| Raised crosswalk | Mid-block or high-volume crossing | $15–50k | Reduces vehicle speeds; increases driver yielding |
| Pedestrian refuge island | Wide multilane crossing; long exposure time | $20–60k | Reduces exposure time; allows staged crossing |
| Left-turn signal phase | Left-turn conflicts in crash data | $5–15k | Eliminates permitted left-turn conflicts with pedestrians |
| High-visibility crosswalk markings | Faded or absent markings visible in satellite | $2–5k | High visibility; effective near schools and transit |
| Vegetation clearance | Shrubs/trees obstructing sightlines in Street View | $500–2k/yr | Immediate; addresses NACTO 30-inch sight-line standard |
| Stop bar setback | Vehicles stopping in crosswalk visible in imagery | $1–3k | Removes vehicle encroachment on pedestrian space |
| RRFB beacon | Uncontrolled crossing; mid-block | $15–40k | −47% pedestrian crashes at uncontrolled crossings (FHWA) |

---

## 7. Frontend

**Stack:** React + TypeScript + Tailwind + Mapbox GL JS

### Views

**Map interface (entry point)**
Mapbox GL map. Users click any intersection or type an address. Markers show previously analyzed intersections colored by severity. This is the selector, not the deliverable.

**Live agent feed (the wow moment)**
Triggered on intersection selection. A side panel shows agents working in real time — not a loading spinner, but a live log that reads like investigative reporting:

```
Fetch.ai orchestrator dispatching agents...
  → Browserbase News Agent: scraping SF Chronicle for crash reports
  → Browserbase Council Agent: reading city council minutes
  → Browserbase 311 Agent: pulling complaint history
  → Structured Data Agent: querying NHTSA FARS

[News Agent] SF Chronicle, March 14 2023 — stored to Redis
Witness cited "couldn't see anyone until too late" — sightline flag

[311 Agent] Complaint #2847221, July 2022 — stored to Redis
"Crosswalk is completely gone, paint faded years ago"

[Council Agent] June 2022 council minutes — stored to Redis
Corridor mentioned twice — no recorded action taken

Fetching satellite + Street View imagery...
Running street vision analysis...
Generating before/after rendering...
```

This runs for ~60–90 seconds. The output feels earned because the user watched the system build the case.

**Annotated intersection view (the deliverable)**
The satellite image with numbered overlay annotations. Each marker is clickable — expands to show: what was seen, which data source corroborates it, the specific fix, cost estimate, projected impact. The image is shareable via URL permalink.

**Before/after rendering (the Midjourney output)**
Side-by-side view: current Street View photo of the intersection on the left, Midjourney-generated photorealistic rendering on the right showing the intersection after the top fixes are applied — curb extensions built out, crosswalk repainted, vegetation cleared, LPI signal installed. This is the image someone brings to a city council meeting. Not a diagram. A photo of what it could look like.

**Intersection detail panel**
Alongside the annotated image:
- Summary: N crashes in Y years, trend direction (worsening / stable / improving)
- Source log: every news article, 311 complaint, council mention that contributed
- Fix list: ranked by cost-effectiveness
- Comparable city card: one real-world example where the top fix was implemented and worked

**Side output: council complaint document**
A secondary button — not the primary CTA. Generates a one-page document with: the annotated intersection image, the top 3 fixes with costs, the data sources cited, and a signature block. Designed to be attached to a written public comment or handed across a table. Not AI-generated prose — structured data formatted into a template.

---

## 8. The Demo Script (2 minutes)

1. **Open with a real story.** Pull a documented fatal crash from NHTSA FARS — a real intersection, a real date. "On March 14, 2023, a pedestrian was killed crossing International Blvd at 35th Ave in Oakland. That person's family is presenting to the city council Tuesday. They typed this address into SafeStreets."

2. **Click the intersection.** Agent feed fires. Read two or three lines aloud as they populate — the Fetch.ai orchestrator dispatching Browserbase agents, the news quote landing in Redis, the 311 complaint, the council mention with no action. Let the silence after "no recorded action taken" land.

3. **Annotated image appears.** Four numbered markers on the satellite view. "This is what a traffic engineer sees on a site visit. SafeStreets sees it in 90 seconds."

4. **Click marker 1.** "Northwest corner — no curb extension. Parking extends to the crosswalk line, creating a blind spot. Three of the five pedestrian strikes happened at this corner. A curb extension removes two parking spots and costs $15,000."

5. **Click marker 2.** "Southeast corner — mature shrubs at eye level, visible right here in Street View. A resident reported this in a 311 complaint in July 2022. The shrubs are still there."

6. **Show the before/after.** Switch to the Midjourney rendering. Left side: the intersection today. Right side: the same intersection with the curb extension built, crosswalk repainted, vegetation cleared. "This is what it looks like after. Not a diagram — a photo of what it could be. This is the image you put on slide one of your council presentation."

7. **Hit 'Export for council meeting.'** Show the one-pager. "The annotated satellite view, the before/after, the top 3 fixes with costs and citations. Not AI opinion — what the street looks like, what residents have been reporting for two years, and what it costs to fix."

---

## 9. Build Plan

### Saturday (day 1)

| Time | Goal |
|---|---|
| 9am–11am | NHTSA FARS + one city open data portal working end-to-end; Google Maps Static + Street View images fetching for a test intersection |
| 11am–1pm | Claude vision analysis prompt: satellite + Street View → structured condition list with pixel coordinates |
| 1pm–3pm | Browserbase news scraper (Stagehand) for one city; 311 scraper; Redis storing all scraped results |
| 3pm–5pm | Intervention matching: condition list → ranked fixes with costs; results written to Redis |
| 5pm–7pm | Frontend: map + annotated image overlay rendering with click-to-expand markers |

**End of day 1 goal:** One real intersection, real imagery, real data in Redis, annotated output renders with at least 2 grounded fix markers.

### Sunday (day 2)

| Time | Goal |
|---|---|
| 9am–10am | Fetch.ai uAgents: Orchestrator dispatching Browserbase agents, results flowing through Redis |
| 10am–11am | Live agent feed UI — real-time log showing Fetch dispatch + Browserbase agents completing |
| 11am–12pm | Midjourney before/after: Street View photo → prompt engineering → photorealistic fix rendering |
| 12pm–1pm | Before/after UI view; council complaint document export (one-pager template with annotated image + before/after) |
| 1pm–2pm | Multi-intersection support; Redis cache hit path for repeat queries |
| 2pm–3pm | Comparable city cards; source log in detail panel; demo intersection selection from NHTSA data |
| 3pm–4pm | Demo polish, README, Devpost |

---

## 10. Why This Wins

**Against the "data labeler" critique:** every other tool stops at identifying the problem. SafeStreets identifies the physical cause visible in the actual street — grounded in what residents have been reporting, not just what crash records show.

**Against the "AI slop" critique:** every annotation is grounded in real imagery and real community data. The prompt explicitly forbids inventing conditions not visible or not corroborated. The output is defensible because you can see the thing it's pointing at.

**The Midjourney angle:** the before/after rendering is the emotional core of the demo. A city council member can look at a photo of what their intersection could be. That's not a diagram or a report — it's a vision. No one has paired photorealistic infrastructure rendering with real crash data before.

**The Anthropic social impact angle:** the gap being closed is access to traffic engineering expertise. A city with a Vision Zero team can do site visits and produce this analysis in-house. A community in an underserved neighborhood cannot. SafeStreets closes that gap in 90 seconds.

**The Fetch.ai angle:** Fetch.ai is doing exactly what it's built for — orchestrating a fleet of heterogeneous agents with clear dispatch, coordination, and result aggregation. The Browserbase agents are meaningless without the orchestrator managing their parallel execution and passing results downstream.

**The Browserbase angle:** the scraped data layer — local news, council minutes, 311 portals — is what turns a generic infrastructure recommendation into a grounded, locally-specific finding. That's exactly the unstructured, non-API web data Browserbase is built for.

**The Redis angle:** every piece of data in the pipeline flows through Redis — scraped content, crash records, vision results, intervention plans. It's not just a cache; it's the shared memory that lets agents hand off to each other without re-fetching. Repeat queries on the same intersection are instant.

---

## 11. References

- NHTSA FARS API: https://crashviewer.nhtsa.dot.gov/CrashAPI
- Google Maps Static API: https://developers.google.com/maps/documentation/maps-static
- Google Street View Static API: https://developers.google.com/maps/documentation/streetview
- Chicago crash data (Socrata): https://data.cityofchicago.org/Transportation/Traffic-Crashes-Crashes/85ca-t3if
- NYC Vision Zero open data: https://data.cityofnewyork.us/widgets/v7f4-yzyg
- SF 311 open data: https://data.sfgov.org/City-Infrastructure/311-Cases/vw6y-z8j6
- DC Vision Zero Safety API: https://opendata.dc.gov/datasets/vision-zero-safety/api
- LPI effectiveness (Columbia / Nature Cities, 2024): 33% reduction in pedestrian injury at 6,003 NYC intersections
- LPI cost-effectiveness (NACTO): $115/intersection/year, 46–71% crash reduction
- Speed camera effectiveness (NYC longitudinal, ScienceDirect 2025): 21% reduction in fatal crashes
- RRFB effectiveness (FHWA): 47% reduction in pedestrian crashes at uncontrolled crossings
- Browserbase Stagehand v3: https://www.browserbase.com/blog/stagehand-v3
- Fetch.ai uAgents quickstart: https://uagents.fetch.ai/docs/quickstart
- Midjourney API: https://docs.midjourney.com
