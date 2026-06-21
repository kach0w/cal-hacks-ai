# Inspiration

There's an intersection near our campus where someone almost gets hit every week. Everyone knows it's dangerous. The city probably knows too. But nothing happens.

We looked into why — turns out the data to prove it is all there (crash records, 311 complaints, news articles, council minutes) but it's spread across like 12 different government websites. And even if you find it all, you still have to write the letter, find the right official, figure out which grant pays for the fix. That's hours of work most people aren't going to do.

So we built SafeStreets. Drop a pin, get the whole case in one click.

---

# What makes it different

**The AI looks at the street before it looks at any complaints.** We made Claude analyze satellite and Street View photos without showing it any community data first. Then separately, we check if what it saw matches real crash reports and 311 complaints. That way "the camera spotted it" and "residents reported it" are actually two separate signals — not the model just agreeing with itself. We thought this was important for the results to actually be trustworthy.

**It can't point at the wrong corner.** Instead of using pixel coordinates (which drift), we made Claude assign hazards to named zones like "NW corner" or "north crosswalk." The markers snap to the right spot every time.

**It finishes the job.** Most tools just tell you there's a problem. SafeStreets gives you the specific fix, which grant program funds it, who to email, a before/after render of what the street would look like, and a letter you can actually send.

---

# What it does

```
pin drop → grab crash data, 311, news, street view (all at once)
         → claude looks at photos, spots hazards (no peeking at complaints)
         → cross-check findings against the community data
         → match each hazard to a fix + the grant that pays for it
         → spit out a tweet, a council letter, before/after renders
```

---

# How we built it

**Claude (Haiku)** runs the two-stage vision pipeline. First pass is blind — images only. Second pass sees the community data and corroborates. We used Claude Code to build most of it.

**Browserbase** handles the data sources that don't have clean APIs — local news sites and council agenda PDFs that need a real browser to load. Crash records and 311 stay on regular open data APIs.

**Redis** caches everything per intersection. Two layers: raw scraped data and the full analysis result. Only writes to cache when agents actually returned something — otherwise a bad first run would poison every reload.

**Frontend** is React + Mapbox with a retro pixel aesthetic. There's a live feed that shows what each agent is doing as it runs.

---

# Challenges

**Keeping the two signals actually independent.** It would've been so easy to just show the model the complaints and let it run. We had to be pretty disciplined about the firewall because that's the whole point — if the model just reads the complaints and says "yep looks dangerous," that's not really two signals.

**Government data is a mess.** News and council documents live in JS-rendered pages and PDFs that normal scrapers can't reach. Browserbase saved us there. And even the "clean" APIs (crash records, 311) each have totally different schemas.

**Substring matching is a nightmare.** We had bugs where "king" matched "parking" and "vision" matched "provision" when searching crash records near MLK Way. Had to switch to whole-word matching and actually geocode intersections to real coordinates.

**Race condition in the cache.** The live agent feed and the analysis request both hit the server at the same time on first load. If the analysis request finished first with empty data (rate limit, timeout), those empty results would get cached and break every subsequent load. Fix was to only cache when there's real data, and check if the other concurrent request saved something better.

---

# What we learned

The blind-then-corroborate thing sounds like an implementation detail but it's actually the whole product. If you skip it, you just have a scraper with a chatbot on top.

The last mile is genuinely hard. Getting the data is the easy part. Turning it into the exact letter, to the exact person, with the exact grant number — that's what actually gets streets fixed.

Pick the right tool per data source. Some things have APIs. Some need a real browser. Don't force one approach for everything.
