# Inspiration

Every city has streets everyone knows are dangerous — the corner where cars don't yield, the crosswalk no one can see at night. The data to prove it exists: crash records, 311 complaints, local news, council minutes. But it's scattered across a dozen portals, and turning it into something a city will actually act on — the specific fix, the grant that pays for it, the official to email — takes hours of expert work.

We built SafeStreets to do that in one click: drop a pin on any street and get a complete, fundable, ready-to-send case for fixing it.

---

# What makes it different

**Blind-then-corroborate.** Our vision model never sees the community data. Claude diagnoses hazards from satellite + Street View imagery alone — then a separate pass checks those findings against real crash, 311, news, and council records. So "seen" and "reported" are two independent signals, not a model agreeing with itself. Every finding comes out labeled CONFIRMED / CANDIDATE / REPORTED, and the label is trustworthy.

**It can't point at the wrong corner.** Each hazard is assigned to a named zone (NW corner, north leg, crosswalk) and mapped to a marker deterministically — no raw-pixel guessing, no marker drifting onto the wrong street.

**It finishes the job.** Most tools stop at "here's a problem." SafeStreets hands you the fix, the grant that funds it, the official to contact, a before/after render of the fixed street, and a ready-to-send council letter — the whole last mile.

---

# What it does

Drop a pin on the map. SafeStreets then:

- **Sees the hazard** — Claude reads satellite + Street View imagery, blind to any community data, and localizes dangers to named zones.
- **Proves it** — an independent pass corroborates each finding against real crash, 311, news, and council data → CONFIRMED / CANDIDATE / REPORTED.
- **Routes the fix** — matches each finding to a concrete intervention and the funding program that pays for it (SS4A / HSIP / state grants).
- **Closes the last mile** — numbered markers on the real satellite image, a council letter, a shareable social post, an accountability record, and before/after Gemini renders of the street with the fix applied.

---

# How we built it

**Vision (Claude Haiku):** a two-stage pipeline — blind detection, then independent corroboration — with deterministic named-zone → marker placement drawn onto the real satellite image. Built with Claude Code.

**Browserbase:** the data that has no clean API — JS-rendered local news and council-agenda PDFs — reached with real headless browsers. California crash data (CCRS) and city 311 records stay on fast open-data APIs. Choosing the right tool per source kept the pipeline fast and reliable.

**Redis as shared memory:** more than a cache — the pipeline's shared state, persisting the accountability log, coalition counts, and per-location evidence across agents. Two-layer caching (raw scrape + full analysis, separately keyed) means repeat queries are instant and a bad first run never poisons future results.

**Frontend:** React + TypeScript + Tailwind + Mapbox GL, in a retro pixel aesthetic (Press Start 2P / VT323). A live SSE agent feed shows the pipeline's stages in real time as it runs.

---

# Challenges we ran into

**Keeping the two signals independent.** It would've been easy to let the model peek at complaints; we firewalled the blind pass on purpose, because that firewall is the product's credibility.

**The most useful data has no clean API.** News and council agendas live in JS-rendered pages and PDFs. Browserbase let us drive real browsers to reach them while crashes and 311 stayed on APIs — choosing the right tool per source mattered more than raw scraping volume.

**Matching is deceptively hard.** Naive substring matching let "vision" match "pro-vision" and "king" (from MLK Way) match "par*king*." We moved to whole-word, geocoded matching and forward-geocoded true intersections to precise coordinates.

**Cache poisoning.** When the SSE stream and the POST /analyze hit simultaneously on first load, both race to fetch community data. If one finishes first with empty results (rate limit, timeout), those empty results would get cached and poison every subsequent run. The fix: only write to cache when there's real data, and if your own fetch came back empty, check whether the concurrent stream saved something better in the meantime.

---

# What we learned

**Independence is the feature.** Firewalling the blind pass is what turns "seen and reported" into a credible signal instead of a circular one. The architecture had to protect that separation from the start — it couldn't be bolted on later.

**The last mile is the hard part.** Finding data is easy; turning it into the exact ask, grant, and person who can fix it is the work that actually moves a city.

**Right tool per source.** APIs for what has them, Browserbase for what doesn't, Redis to hold it all together — that's what makes a multi-agent pipeline affordable and demo-reliable.
