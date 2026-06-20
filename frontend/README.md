# SafeStreets — frontend

Vite + React + TypeScript + Tailwind + Mapbox GL.

```
src/
  main.tsx, App.tsx, index.css
  types/index.ts        mirrors the backend domain models
  api/client.ts         fetch wrapper + EventSource for the live agent feed
  lib/geometry.ts       named zone -> screen coords (mirror of backend geometry.py)
  hooks/
    useAnalysis.ts        subscribes to the SSE agent feed
    useIntersection.ts    fetches a cached analysis result
  components/
    MapView.tsx           Mapbox selector (entry point, not the deliverable)
    AgentFeed.tsx         the 'wow moment' — live investigative-report log
    AnnotatedImage.tsx    the hero — markers on the REAL satellite image
    MarkerDetail.tsx      click-to-expand: observation, corroboration, fix, funding
    ConfidenceBadge.tsx   CONFIRMED / CANDIDATE / REPORTED
    LastMilePanel.tsx     ask / money / messenger / coalition / accountability
    ConceptToggle.tsx     labeled Midjourney concept (secondary, always labeled)
    ResidentSubmit.tsx    photo + description submission
    OnePagerExport.tsx    structured template export for council
```

Components are typed stubs. When you flesh out the UI, that's the moment to apply real
visual design — this scaffold deliberately leaves styling open.

Run: `npm install && npm run dev` (or `make frontend` from repo root).
