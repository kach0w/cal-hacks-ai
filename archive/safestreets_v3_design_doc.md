# SafeStreets — Hackathon Design Doc v3
**UC Berkeley AI Hackathon 3.0 · June 21–22, 2026**

> Changes from v2: blind-then-corroborate vision pipeline (kills the confirmation-bias problem), named-geometry annotation placement (kills the pixel-coordinate failure), honest precision on crash attribution, the *last mile* — funding match, the right messenger, and accountability tracking — plus a participatory thin-data mode so the tool works where it's actually needed.

---

## 1. Overview

Every city knows which intersections are dangerous. What they can't answer fast is: **what exactly is physically wrong, what would fix it, and who has to be pushed to pay for it?**

**SafeStreets** is a multi-agent system that takes an intersection, pulls crash records, 311 complaints, local news, and city data — then reads the actual street using satellite and Street View imagery to identify the specific physical conditions causing harm. It produces a marked-up top-down view of the intersection with annotated fix recommendations grounded in real community data — and then hands the user the things that actually move a fix from "known problem" to "funded project": the specific ask, the matching grant program, the official responsible, and a durable record of whether the city ever responded.

It doesn't show you a risk score. It shows you the bush that's been in three 311 complaints since 2021 and is still there — and then it shows you which council member to email, which federal safety grant pays for clearing it, and the fact that the city was already told in 2022 and did nothing.

### The thing v2 got wrong, and v3 fixes

The honest critique of the original concept: **identifying the problem was never the bottleneck.** Cities employ engineers who can do a site read. The 311 complaint already documented the faded crosswalk. The council minutes already named the corridor. The bush is still there because fixing it competes with a thousand other line items for a constrained budget and limited political attention — all of which is *downstream* of diagnosis.

A tool that stops at "here's what's wrong" automates the half that was already cheap. So v3 is built around the half that's expensive: **turning a finding into an action a city is accountable for.** Diagnosis is the hook. The last mile is the product.

### The reframe: who actually uses this

The primary user is the person who has to pressure the city into action:

- A parent whose child was hit at an intersection, preparing for a city council meeting next Tuesday
- A community organizer building a case for infrastructure funding in an underserved neighborhood
- A local journalist investigating why a particular corridor has killed three pedestrians in two years
- A Vision Zero coordinator who needs to justify their top priority list to the mayor's office

These users don't need another dashboard. They need a tool that looks at the street, tells them exactly what's wrong, tells them what to *ask for and who to ask*, and gives them a record the city can't quietly bury.

### What makes it different

Every existing tool — city Vision Zero dashboards, NHTSA crash viewers — tells you a number. SafeStreets shows you the street and says: *here, that thing, fix that — here's the grant that pays for it, here's who to email, and here's proof they already knew.*

Three things make the output trustworthy enough to act on:

1. **Grounded, not generated.** The hero deliverable is the *real* satellite and Street View imagery with annotations on it — every marker traceable to a specific visual observation and an independent corroborating record. Where we show a rendering of a proposed fix, it is clearly labeled as an illustration, never presented as a photo of the site.
2. **The model is kept honest by design.** Vision runs *blind* to the complaint text first, then corroboration is matched separately, so "seen" and "reported by residents" are two genuinely independent signals — not the model agreeing with text it was handed.
3. **It closes the loop.** Diagnosis is wired straight into the ask, the money, the messenger, and the accountability record.

### Prize tracks

| Sponsor | How |
|---|---|
| **Fetch.ai** | Orchestrator uAgent does *adaptive* dispatch — escalates deeper scraping when early signals are strong, retries/falls back on source failures, and decides which data sources to query based on what's found. Not a static fan-out. |
| **Browserbase** | Scrapes local news, city council minutes, and 311 portals *without APIs* — exactly the unstructured web data with no clean endpoint. Spawned and managed by the Fetch.ai orchestrator. |
| **Anthropic** | Claude for the two-stage street vision analysis (blind detection → corroboration), intervention reasoning with feasibility caveats, the ask/messenger generation, and annotation. Social impact track. |
| **Redis** | Caches and stores scraped data, crash records, vision results, and intervention plans keyed by lat/lng with TTL — and persists the cross-resident coalition reports and the accountability log. |
| **Midjourney** | Generates a clearly-labeled *concept illustration* of a proposed fix as an optional, secondary aid — never the primary, never presented as the real site. |

---

## 2. Core Concept: Two-Stage Street Vision Analysis

The central innovation is using Claude's vision capability to read a street the way a traffic engineer would on a site visit — cross-referenced against why people have actually been getting hurt there. The critical design choice is *how* that cross-referencing happens, because done naively it manufactures false confidence.

### Why two stages (the credibility fix)

If you hand a vision model the satellite image **and** the text "311 complaint: crosswalk completely gone" in the same prompt and ask "what do you see," you have primed it to confirm a faded crosswalk whether or not the image actually shows one. "Seen" and "corroborated" are then the same source wearing two hats — and the whole "this isn't AI slop" claim collapses under any judge who notices.

So vision and corroboration are split:

- **Stage 1 — Blind visual pass.** Claude receives *only* the imagery (satellite + 4 Street View). No crash data, no complaints, no news. It returns the physical conditions it can actually observe, each with a confidence level and a named-zone location. It is explicitly instructed to report uncertainty and to omit anything not visible.
- **Stage 2 — Independent corroboration.** A separate step matches each blindly-observed condition against the crash/311/news/council data pulled in parallel. Each finding is then labeled:
  - **CONFIRMED** — seen in imagery *and* independently corroborated by community data (the strong, defensible findings)
  - **CANDIDATE** — seen in imagery but not yet corroborated (worth a look, flagged as such)
  - **REPORTED** — present in community data but not visually confirmable from available imagery (e.g., signal timing, or a condition only visible from an angle Street View doesn't cover)

The demo line writes itself: *"The model flagged this corner before it ever saw the complaint. Then the complaint confirmed it."*

### Localization: named geometry, not raw pixels (the placement fix)

Vision-language models are unreliable at returning accurate pixel coordinates, and a marker that lands on the wrong corner destroys the entire "you can see the thing it's pointing at" value prop. So we never ask Claude for raw pixels.

Instead we establish a **canonical intersection frame** from the satellite geometry — the four corners (NW/NE/SW/SE), the four legs (N/S/E/W approaches), and the center box. Claude assigns each condition to a *named zone*; the renderer maps named zones to marker positions deterministically from the known image geometry. Optional finer placement uses a coarse labeled grid, gated by confidence. If Claude's zone assignment for a condition is inconsistent between the satellite and the Street View it was also shown, the finding is flagged for quick human confirmation rather than silently guessing. Wrong-but-confident placement is the failure we engineer out.

### Imagery currency (the "is the bush still there" fix)

Street View can be years stale, which means a confident "the shrubs are still there" might be describing a 2019 photo of shrubs cleared in 2023. Every image carries its **capture date**, shown on the output. When imagery is old, the finding is badged accordingly — and the user (or a resident, see §4) can submit a current photo that supersedes the stale Street View for that zone.

### Input pipeline

1. User submits an intersection (address or map click); optionally attaches a current photo or observation
2. Fetch.ai orchestrator adaptively dispatches Browserbase agents + the image fetcher; stores all results in Redis
3. System fetches Google Maps Static API satellite image (top-down) + Street View images (4 cardinal directions), with capture dates
4. **Stage 1:** Claude receives imagery only → blind condition list with named-zone locations + confidence
5. **Stage 2:** observed conditions are matched independently against crash/311/news/council data → CONFIRMED / CANDIDATE / REPORTED
6. Intervention + funding agent maps conditions → candidate fixes (with feasibility caveats) → matching grant programs → responsible official
7. Output renders on the *real* imagery; Midjourney concept illustration generated as a clearly-labeled secondary aid

### What the vision analysis looks for

Claude is prompted in Stage 1 to identify physical infrastructure conditions visible in imagery; corroboration in Stage 2 is matched separately:

| Condition | Detection signal (Stage 1, blind) | Corroboration (Stage 2, independent) |
|---|---|---|
| Missing or faded crosswalk markings | Satellite imagery | 311 complaints about "unmarked crossing" |
| Vegetation obstructing sightlines | Street View corners | News reports citing "visibility issues" |
| No curb extension / parking blocking view | Satellite geometry | Crash reports: right-turn conflicts |
| Missing stop bar setback | Satellite imagery | Crash reports: vehicles in crosswalk |
| No pedestrian signal or LPI | Street View | 311 complaints about signal timing (REPORTED — not visually confirmable) |
| Narrow sidewalk / no buffer | Satellite measurement | Pedestrian crash density |
| Poor lighting conditions | Street View (limited — flag low confidence) | Night crash clustering |
| High-speed approach geometry | Satellite road width | Speed cited in crash reports |

### Annotation output

The primary output is the *real* satellite image annotated with 3–5 numbered fix markers placed by named zone, each labeled with its confidence tier and grounded in both what the vision model saw and what the community data independently confirms:

```
[1] CONFIRMED · Extend curb on northwest corner
    Seen (blind pass, high confidence): No curb extension; parking extends to crosswalk line
    Corroborated: 5 pedestrian crashes recorded at this intersection (2020–2024);
                  crash narratives cite right-turn conflicts. (Crash data is
                  intersection-level; corner attribution shown only where the
                  source record includes it.)
    Candidate fix: Curb extension — removes ~2 parking spots, shortens crossing,
                   slows turning vehicles. Feasibility check needed: drainage,
                   ADA ramp placement, transit stop. Confirm with a licensed engineer.
    Cost: $10,000–30,000 | Evidence: shorter crossing distance + lower turn speeds
    Funding: eligible project type under SS4A Implementation + state HSIP

[2] CONFIRMED · Clear vegetation on southeast corner
    Seen (blind pass, high confidence): Mature shrubs obscure pedestrian visibility
                                        (Street View, captured 2024-08)
    Corroborated: SF Chronicle, March 2023 — witness cited "couldn't see anyone"
    Candidate fix: Trim to below 30 inches per NACTO sight-line standard
    Cost: $500–2,000/year maintenance | Evidence: immediate sight-line restoration
    Funding: routine maintenance — no grant needed; the ask is a work order

[3] CONFIRMED · Repave crosswalk markings (north leg)
    Seen (blind pass, medium confidence): Markings faded in satellite; flagged for
                                          field confirmation
    Corroborated: 311 complaint #2847221, July 2022 — "crosswalk completely gone"
    Candidate fix: High-visibility ladder markings
    Cost: $2,000–5,000 | Funding: SS4A Implementation; HSIP

[4] REPORTED · Add Leading Pedestrian Interval (not visually confirmable)
    Seen: Standard concurrent-phase signal visible; LPI status not determinable from imagery
    Corroborated: 311 complaints on signal timing; turning-movement crashes in record
    Candidate fix: 7-second LPI head start for pedestrians
    Cost: $115/year | Evidence: −33% pedestrian injury (Columbia/Nature Cities 2024)
    Funding: extremely low cost — the ask is a signal retiming request, not a grant
```

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          USER INPUT                             │
│        Address / map click  (+ optional resident photo)         │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│            ORCHESTRATOR (Fetch.ai uAgent) — ADAPTIVE            │
│  Dispatches agents; retries/falls back on source failure;       │
│  escalates deeper scraping when early signals are strong        │
└───┬──────────────┬───────────────┬──────────────┬──────────────┘
    ▼              ▼               ▼              ▼
┌────────┐  ┌──────────┐  ┌─────────────┐  ┌──────────────┐
│Structured│ │Browserbase│ │Browserbase  │  │ Image Fetcher│
│Data Agent│ │News Agent │ │Council/311  │  │ Google Maps  │
│FARS/City │ │(last 2yr) │ │Agent        │  │ + Street View│
│APIs/VZ DB│ │           │ │(PDF/portal) │  │ (+ capture   │
│          │ │           │ │             │  │   dates)     │
└────┬─────┘ └─────┬─────┘ └──────┬──────┘  └──────┬───────┘
     │             │              │                 │
     │        ┌────┴────┐         │                 │
     │        │ Resident│         │                 │
     │        │ submissions│      │                 │
     │        └────┬────┘         │                 │
     └─────────────┴──────────────┴─────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    REDIS (cache + shared store)                 │
│  Scraped news/311/council (intersection-keyed) · crash records  │
│  Vision results (lat/lng, 24h TTL) · interventions · funding    │
│  Cross-resident COALITION reports · ACCOUNTABILITY log          │
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│        STAGE 1 — BLIND VISION PASS (Claude, imagery only)      │
│  No community text. Observed conditions + named-zone location   │
│  + confidence. Reports uncertainty; omits the non-visible.      │
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│        STAGE 2 — CORROBORATION (independent matching)          │
│  Match observed conditions ↔ crash/311/news/council            │
│  Label: CONFIRMED · CANDIDATE · REPORTED                        │
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│        INTERVENTION + FUNDING AGENT (Claude)                   │
│  Conditions → candidate fixes (+ feasibility/ADA caveats)       │
│  → matching grant programs (SS4A / HSIP / state)               │
│  → responsible official/body → ranked by cost-effectiveness     │
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│              OUTPUT + LAST-MILE PACKET                          │
│  Grounded annotated REAL image (named-zone markers, confidence, │
│  imagery dates) · The Ask · The Money · The Messenger ·         │
│  Accountability record · one-pager export                       │
│  Optional: clearly-labeled Midjourney concept illustration      │
└─────────────────────────────────────────────────────────────────┘
```

### Component table

| Component | Technology | Responsibility |
|---|---|---|
| Orchestrator | Fetch.ai uAgent | Adaptive dispatch, retry/fallback, signal-driven escalation across scraping agents |
| Structured data agent | Python + REST | NHTSA FARS, city open data, Vision Zero APIs (intersection-level precision) |
| News agent | Browserbase + Stagehand | Local news crash reports — spawned by orchestrator |
| Council/311 agent | Browserbase + Stagehand | Council minutes (PDF) + 311 portals without APIs |
| Image fetcher | Google Static Maps + Street View | Satellite top-down + 4-direction street-level images, with capture dates |
| Resident submissions | Upload + intake | Current photos / observations that supersede stale imagery and fill data deserts |
| Redis | Redis | Cache + shared store; coalition reports; accountability log |
| Vision agent (Stage 1) | Claude (vision) | Blind condition detection, named-zone localization, confidence |
| Corroboration (Stage 2) | Claude + logic | Independent matching of observed conditions to community data |
| Intervention + funding agent | Claude | Candidate fixes, feasibility caveats, grant matching, responsible official |
| Render + concept agent | Renderer + Midjourney | Annotated real image (hero) + labeled concept illustration (secondary) |
| Frontend | React + TypeScript + Mapbox GL | Map, detail panel, annotated output, last-mile packet, coalition view |

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

> **Precision discipline.** Crash and 311 records are geocoded to the intersection or road segment, not the corner. We display attribution at the granularity the source actually supports and only claim corner-level precision when the underlying record contains it. Inventing "3 of 5 strikes at the NW corner" from intersection-level data is exactly the fabricated rigor a city engineer spots instantly — so we don't.

**Google Maps imagery**
- Static Maps API: satellite top-down, zoom 19–20 for intersection detail, capture date surfaced
- Street View Static API: 4 cardinal directions, 640×640px, capture date surfaced

### Browserbase scraping targets

**Local news** — crash reports contain witness accounts and physical scene descriptions official databases miss. Stagehand `extract()` on local news for crash articles by location and date range.

**City council meeting minutes** — a leading indicator: when a community has complained enough, the intersection appears in minutes before a fatality. Many cities post PDFs; Stagehand handles PDF extraction via browser rendering. These minutes also feed the accountability log (§9).

**311 portals without APIs** — smaller cities have web interfaces but no API. Stagehand scrapes complaint categories: broken signals, missing crosswalks, sight-line obstructions, speeding, vegetation.

### Resident-submitted observations (the equity fix)

The uncomfortable truth about a data-driven civic tool: it works *best where it's needed least.* Well-resourced cities have clean open-data portals, current Street View, digitized 311, and functioning local news. The underserved neighborhoods and small municipalities this tool claims to serve are exactly where Street View is stale, 311 is a phone line, the local paper folded, and there is no open data.

So residents are a first-class data source. A user can attach a current photo and a short description of what's wrong. That submission (1) supersedes stale Street View for the relevant zone, (2) provides ground truth where no scraped data exists, and (3) aggregates with other residents' reports into a coalition case (§9). In a data desert, the tool degrades gracefully to *imagery + national FARS + resident reports* rather than failing — and the participation itself is the point: it organizes constituents, which is the actual lever on political will.

### Funding-program data

A small curated dataset of the major safety-funding mechanisms, used by the intervention agent to match a fix to the money that could pay for it (§9):

- **SS4A** (Safe Streets and Roads for All) — USDOT discretionary grants for data-driven fatality/serious-injury reduction. *Note: FY2026 is the program's fifth and final guaranteed round under the IIJA authorization (expires Sept 30, 2026); only local/regional/Tribal governments may apply, not individuals.* This shapes the feature: the tool tells a resident the program, the eligibility, and whether their city has a qualifying Action Plan — so they can pressure the city to apply, which is the real lever.
- **HSIP** (Highway Safety Improvement Program) — the standing, state-administered FHWA formula program for data-driven safety projects. The durable backbone, independent of SS4A's uncertain future.
- **State and regional programs** — many states and MPOs run their own safety set-asides; extensible per city.

---

## 5. Vision Analysis: Claude Prompt Design

Two prompts, deliberately separated so corroboration is independent of detection.

### Stage 1 — blind detection (imagery only, no community data)

```
You are analyzing an intersection for physical infrastructure conditions
that affect pedestrian and cyclist safety. You have ONLY images.

You have:
- 1 satellite top-down image of the intersection
- 4 Street View images (N/S/E/W approaches), each with a capture date

You DO NOT have crash data or complaints. Do not speculate about them.

Your task:
1. Identify 3–6 physical conditions you can actually SEE that plausibly
   affect safety.
2. For each, return:
   - named_zone: one of {NW, NE, SW, SE} corner, {N, S, E, W} leg, or CENTER
   - observation: what in the image indicates it
   - source_view: satellite | streetview_<dir>, and the capture date
   - confidence: high | medium | low
3. If a commonly-relevant condition CANNOT be determined from imagery
   (e.g., signal phasing, lighting at night), say so explicitly with
   confidence: low and mark not_visually_confirmable: true.

Return structured JSON keyed by named_zone.

Hard rules:
- Do NOT report conditions you cannot see.
- Prefer "uncertain" over a confident guess.
- Do NOT output pixel coordinates. Use named_zone only.
```

### Stage 2 — independent corroboration (matching, separate call)

```
You are matching independently-observed physical conditions against
community evidence. You did not generate the observations.

You have:
- observed_conditions: [Stage 1 JSON]
- crash_data: [N crashes, types, years; precision: intersection-level]
- complaints_311: [list with dates/categories]
- news: [excerpts mentioning physical conditions]
- council: [relevant references + dates]

For each observed condition, assign:
- status: CONFIRMED (observed AND independently corroborated)
         | CANDIDATE (observed, no corroboration found)
         | REPORTED (in community data, not visually confirmable)
- corroboration: which specific record(s) support it, with dates
- Respect data precision. If crash data is intersection-level, do not
  assert corner-level attribution.

Return structured JSON. Do not upgrade confidence beyond what the
evidence supports.
```

The split is the guardrail. Detection can't be talked into seeing what the text described, because at detection time there is no text. Every CONFIRMED finding is two independent signals; everything weaker is honestly labeled as weaker.

---

## 6. Intervention Library

Candidate interventions — explicitly framed as options to discuss with a licensed engineer, not verdicts. Each carries a feasibility note and a funding match.

| Intervention | Trigger condition | Cost | Evidence | Feasibility caveat | Funding |
|---|---|---|---|---|---|
| Leading Pedestrian Interval (LPI) | Ped crashes / turning conflicts at signal | $115/yr | −33% ped injury (Columbia/Nature Cities 2024); −46–71% (NACTO) | Requires signalized intersection | SS4A; HSIP; often just a retiming request |
| Speed camera | Speeding cited; school-zone proximity | $50k install | −21% fatal crashes (NYC longitudinal, 2025) | State enabling law required; politically sensitive | SS4A (varies by NOFO priorities) |
| Curb extension (bulb-out) | Parking blocks sightline; right-turn conflicts | $10–30k | Shorter crossing; slower turns | Check drainage, ADA ramps, transit stops | SS4A Implementation; HSIP |
| Raised crosswalk | Mid-block / high-volume crossing | $15–50k | Lower speeds; more yielding | Not on primary transit/emergency routes | SS4A; HSIP |
| Pedestrian refuge island | Wide multilane crossing | $20–60k | Less exposure; staged crossing | Needs roadway width; utility conflicts | SS4A; HSIP |
| Left-turn signal phase | Left-turn conflicts in crash data | $5–15k | Eliminates permitted-turn conflicts | Signal controller capacity | SS4A; HSIP |
| High-visibility crosswalk markings | Faded/absent markings in satellite | $2–5k | High visibility near schools/transit | Repaint cycle; material choice | SS4A; HSIP; maintenance |
| Vegetation clearance | Shrubs/trees blocking sightlines (Street View) | $500–2k/yr | Immediate; NACTO 30-inch standard | Ownership (city vs private property) | Maintenance work order |
| Stop bar setback | Vehicles in crosswalk in imagery | $1–3k | Removes encroachment | Repaint; minor | Maintenance; HSIP |
| RRFB beacon | Uncontrolled / mid-block crossing | $15–40k | −47% ped crashes uncontrolled (FHWA) | Power/visibility; warrant check | SS4A; HSIP |

---

## 7. Honest Output & Trust

The credibility of this project lives or dies on whether the output is defensible. The rules:

**The hero is the real image.** The primary deliverable is the actual satellite + Street View imagery with named-zone markers on it. Every marker expands to: the blind observation and its confidence, the independent corroborating record, the candidate fix with its feasibility caveat, cost, evidence, funding match, and the imagery capture date. You can see the thing it points at — on the real street.

**Confidence is always visible.** CONFIRMED / CANDIDATE / REPORTED is shown on every finding. The tool never launders a guess into a fact.

**Concept renders are labeled as concepts.** The Midjourney before/after is demoted from "the emotional core" to an optional, clearly-watermarked *illustration* — because a photorealistic AI image of a street that doesn't quite match the real one, presented to a city council as "what it could look like," is the exact "AI slop" failure this project exists to avoid. The honest primary "after" is a simple annotated overlay drawn on the real photo (a sketched curb extension, a repainted crosswalk). If a concept render is shown, it reads: *"Illustrative concept — not a photo of this site."*

**Expertise is bounded.** Every recommendation carries: *"Candidate intervention. Real designs must account for drainage, utilities, ADA, transit, and right-of-way not visible in imagery. Confirm with a licensed traffic engineer."* For a social-impact tool, overconfident civic AI that misdirects scarce funds is a harm, not a feature.

---

## 8. The Last Mile: From Finding to Funded

This is the section that makes SafeStreets a tool that changes outcomes rather than a tool that produces a prettier complaint. For the top fixes, the system assembles:

**The Ask.** The specific, costed request, in the language a city understands: *"Install a 7-second LPI on the north leg signal. Estimated $115/year. Addresses turning-movement conflicts documented in 4 crashes since 2020."*

**The Precedent.** One real comparable city where this fix was implemented and worked — the "if Oakland can do it" card.

**The Money.** The matching funding mechanism, with eligibility framed correctly: which program pays for this class of project (SS4A Implementation, HSIP, or a state set-aside), and — crucially — that *the city, not the resident, applies.* So the actionable ask becomes "ask whether our corridor is in the city's SS4A Action Plan," which is a far sharper lever than a generic plea.

**The Messenger.** The body or official responsible for this decision (city traffic engineer, DOT, the relevant council member's office) and the next public meeting where it can be raised — plus a ready-to-send message and a public-comment-ready one-pager.

**Coalition mode.** Multiple residents reporting the same corridor aggregate into a single collective case: *"7 residents have flagged this corridor since 2023."* Political will is a numbers game; the tool does the organizing math.

**Accountability tracking.** The durable record. The system logs when a corridor was raised — in council minutes, in 311, in a SafeStreets submission — and whether action followed. "Corridor mentioned twice — no recorded action taken" stops being a buried line in a PDF and becomes a visible, citable, shareable fact. Turning institutional silence into an on-the-record signal is the single most direct pressure the tool can apply on the bottleneck that actually keeps the bush in place.

---

## 9. Frontend

**Stack:** React + TypeScript + Tailwind + Mapbox GL JS

### Views

**Map interface (entry point).** Mapbox GL map. Click any intersection or type an address; optionally attach a current photo. Markers show previously analyzed intersections colored by severity, with corridor clustering for coalition cases. This is the selector, not the deliverable.

**Live agent feed (the wow moment).** A side panel shows agents working in real time — not a spinner, but a live log that reads like investigative reporting, now with the blind-then-corroborate beat made explicit:

```
Fetch.ai orchestrator dispatching agents (adaptive)...
  → Browserbase News Agent: scraping SF Chronicle for crash reports
  → Browserbase Council Agent: reading city council minutes
  → Browserbase 311 Agent: pulling complaint history
  → Structured Data Agent: querying NHTSA FARS
  → Image Fetcher: satellite + Street View (captured 2024-08)

[Stage 1 · blind vision] No complaint text loaded.
  NW corner: no curb extension, parking to crosswalk line — HIGH
  SE corner: shrubs obscuring sightline (Street View 2024-08) — HIGH

[Stage 2 · corroboration]
  NW corner → 5 crashes at intersection, right-turn conflicts → CONFIRMED
  SE corner → SF Chronicle 2023, "couldn't see anyone" → CONFIRMED
  Signal timing → 311 complaints, turning crashes → REPORTED (not visible)

[Accountability] June 2022 council minutes — corridor named, no action recorded
```

This runs ~60–90 seconds. The output feels earned because the user watched the system build the case — *and* watched the model commit to what it saw before it knew what residents reported.

**Annotated intersection view (the deliverable).** The real satellite image with named-zone markers, each badged CONFIRMED/CANDIDATE/REPORTED and clickable to expand: observation + confidence, corroborating source, fix + feasibility caveat, cost, evidence, funding match, imagery date. Shareable via URL permalink.

**Last-mile packet panel.** The Ask, the Precedent, the Money, the Messenger, plus the coalition count and the accountability record. The most important panel in the product.

**Concept illustration (optional, labeled).** The annotated real-photo overlay as the honest "after"; the Midjourney render available behind a clearly-marked "illustrative concept" toggle.

**Council complaint one-pager (export).** Structured data into a template — not AI prose: the annotated real image, the top 3 fixes with costs and citations, the funding match, the named messenger, the accountability record, and a signature block. Designed to be attached to a written public comment or handed across a table.

---

## 10. Demo Script (2 minutes)

1. **Open with a real story.** Pull a documented fatal crash from NHTSA FARS — a real intersection, a real date. "On March 14, 2023, a pedestrian was killed crossing International Blvd at 35th Ave in Oakland. That person's family is presenting to the city council Tuesday. They typed this address into SafeStreets."

2. **Click the intersection.** Agent feed fires. Read the Stage 1 / Stage 2 split aloud — *"watch this: the model is looking at the street with no complaint data. It flags the shrubs on the southeast corner. Now — only now — we bring in the records, and a resident reported those exact shrubs in 2022."* Let the independence land; it's the credibility moment.

3. **Annotated image appears.** Numbered markers on the *real* satellite view, badged CONFIRMED. "This is what a traffic engineer sees on a site visit. SafeStreets saw it in 90 seconds — and it's pointing at the real street, with the dates on the imagery."

4. **Click marker 1.** "Northwest corner — no curb extension, parking to the crosswalk line. Five pedestrian crashes at this intersection, narratives cite right-turn conflicts. A curb extension costs $15,000 — and it's exactly the project type SS4A and HSIP fund."

5. **The last mile.** Open the packet. "Here's who decides this — the city traffic engineer and the District 5 council office. Here's the ready-to-send message. And here's the record: the city was told about this corridor in June 2022 and took no action. That's not an accusation. That's the minutes."

6. **Show the honest 'after.'** The overlay on the real photo. "Not an AI fantasy of a different street — the actual intersection with the fix drawn on it. If you want a fuller rendering, here's a concept illustration, clearly labeled as a concept."

7. **Hit 'Export for council meeting.'** The one-pager: real annotated image, top 3 fixes with costs and citations, funding match, named messenger, accountability record. "What the street looks like, what residents reported for two years, what it costs, who pays, who decides — and proof they already knew."

---

## 11. Build Plan

De-risked: Day 1 nails the credibility loop on a few *real* intersections in one city. Day 2 adds the last-mile features and clearly-labeled stretch goals. Be honest in the demo about what is pre-cached.

### Saturday (day 1) — the credibility loop

| Time | Goal |
|---|---|
| 9am–11am | NHTSA FARS + one city open-data portal end-to-end; Static Maps + Street View fetching (with capture dates) for 2–3 real test intersections |
| 11am–1pm | **Stage 1 blind vision**: imagery-only → named-zone condition list + confidence. Get placement *correct* on the real intersections — this is the highest-risk item; spend the time here |
| 1pm–2:30pm | **Stage 2 corroboration**: independent matching → CONFIRMED/CANDIDATE/REPORTED; precision discipline on crash attribution |
| 2:30pm–4:30pm | Intervention + funding match (SS4A/HSIP) with feasibility caveats; results to Redis |
| 4:30pm–7pm | Frontend: map + annotated *real* image with named-zone markers, confidence badges, click-to-expand |

**End of day 1 goal:** 2–3 real intersections, real imagery with dates, real data in Redis, annotated output on the real image with correctly-placed CONFIRMED markers.

### Sunday (day 2) — the last mile + polish

| Time | Goal |
|---|---|
| 9am–10am | Fetch.ai uAgents: adaptive orchestration (retry/fallback, signal-driven escalation), results through Redis |
| 10am–11am | Live agent feed UI — show the Stage 1 → Stage 2 split and the accountability line |
| 11am–12pm | Browserbase scrapers (news, 311, council PDF) for the demo city; accountability log from council minutes |
| 12pm–1pm | **Last-mile packet**: The Ask / Money / Messenger; one-pager export (template with real annotated image) |
| 1pm–2pm | Resident submission intake (photo supersedes stale Street View); Redis cache-hit path for repeat queries |
| 2pm–3pm | *Stretch (clearly labeled):* coalition/corridor aggregation; Midjourney concept illustration toggle; second city |
| 3pm–4pm | Demo polish, README, Devpost |

---

## 12. Why This Matters

**It closes the half that was actually hard.** Diagnosis was never the bottleneck — cities already know. SafeStreets wires diagnosis straight into the ask, the matching grant, the responsible official, and an on-the-record accountability trail. That's the half that moves a fix from "known problem" to "funded project."

**It's honest enough to be trusted.** Blind-then-corroborate grounding means CONFIRMED findings are two independent signals, not a model agreeing with text it was handed. Annotations sit on the real street, with imagery dates. Renderings are labeled as renderings. Recommendations are bounded by "confirm with a licensed engineer." A city engineer can look at the output and see why it's defensible — and a skeptical judge can't dismiss it as slop.

**It works where it's needed, not only where it's easy.** Resident submissions and graceful degradation to imagery + national data + community reports keep the tool useful in the news-desert, no-API-311, stale-imagery neighborhoods that need it most — and the participation itself organizes the constituents who are the real lever on political will.

**The technical bet is the right one.** The hard, valuable problem — reading a street and grounding it against why people get hurt there, then routing it to action — is exactly what a multi-agent vision system can do that a dashboard cannot. The complexity lives where it belongs: the two-stage grounding and the last-mile routing, not a fifth scraper.

**Sponsor fit, honestly stated.** Browserbase scrapes the API-less web that turns a generic recommendation into a locally-specific finding. Fetch.ai orchestrates a heterogeneous agent fleet with real adaptive dispatch. Redis is the shared store *and* the persistent memory for coalitions and accountability. Claude does the reasoning that requires judgment. Midjourney contributes a clearly-bounded illustration. Each is there because the problem needs it.

---

## 13. References

- NHTSA FARS API: https://crashviewer.nhtsa.dot.gov/CrashAPI
- Google Maps Static API: https://developers.google.com/maps/documentation/maps-static
- Google Street View Static API: https://developers.google.com/maps/documentation/streetview
- Chicago crash data (Socrata): https://data.cityofchicago.org/Transportation/Traffic-Crashes-Crashes/85ca-t3if
- NYC Vision Zero open data: https://data.cityofnewyork.us/widgets/v7f4-yzyg
- SF 311 open data: https://data.sfgov.org/City-Infrastructure/311-Cases/vw6y-z8j6
- DC Vision Zero Safety API: https://opendata.dc.gov/datasets/vision-zero-safety/api
- LPI effectiveness (Columbia / Nature Cities, 2024): 33% reduction in pedestrian injury at 6,003 NYC intersections
- LPI cost-effectiveness (NACTO): ~$115/intersection/year
- Speed camera effectiveness (NYC longitudinal, ScienceDirect 2025): 21% reduction in fatal crashes
- RRFB effectiveness (FHWA): 47% reduction in pedestrian crashes at uncontrolled crossings
- SS4A grant program (USDOT): https://www.transportation.gov/grants/SS4A — FY2026 is the fifth and final guaranteed round under IIJA (authorization expires Sept 30, 2026); local/regional/Tribal governments apply
- HSIP (FHWA Highway Safety Improvement Program): https://highways.dot.gov/safety/hsip — standing, state-administered, data-driven safety funding
- Browserbase Stagehand v3: https://www.browserbase.com/blog/stagehand-v3
- Fetch.ai uAgents quickstart: https://uagents.fetch.ai/docs/quickstart
- Midjourney API: https://docs.midjourney.com
