# Professor Research Mapper — Design Doc
**UC Berkeley AI Hackathon 3.0 · June 21–22, 2025**

---

## 1. Overview

**Professor Research Mapper** is a two-agent system that automates the most tedious part of academic networking: researching professors before reaching out. A student enters a professor's name and university; the system returns a structured one-pager covering their research focus, tech stack, open projects, and fit score — then automatically drafts a personalized cold email and manages the follow-up workflow.

The system is composed of two distinct agents with a clean handoff:

1. **Research Agent** — powered by Browserbase + Stagehand, scrapes 4+ sources in parallel, synthesizes with Claude
2. **Workflow Agent** — powered by Fetch.ai uAgents, handles email sequencing, follow-up scheduling, paper monitoring, and deadline tracking

### Target users

| Mode | Who | Primary need |
|---|---|---|
| **Undergrad** | First-time lab seekers | Understand what a lab does; get a first email out |
| **Senior / MS** | PhD applicants | Find PIs whose research direction aligns with thesis |
| **Post-bac** | Seeking research positions | Identify labs actively hiring; move fast |

### Prize tracks targeted

| Sponsor | How |
|---|---|
| **Browserbase** | Core scraping infrastructure; Stagehand for AI-native extraction |
| **Fetch.ai** | Multi-agent workflow orchestration via uAgents + Agentverse |
| **Anthropic** | Claude for synthesis + fit scoring; education track |
| **Redis** | Professor profile caching; vector search for paper similarity |
| **Deepgram** | Voice input to kick off searches |

---

## 2. System Architecture

```
┌──────────────────────────────────────────────────────────┐
│                        USER INPUT                        │
│     Professor name + school  │  Mode  │  Background      │
└───────────────────┬──────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────┐
│              RESEARCH AGENT (Browserbase)                │
│                                                          │
│  Planning Agent (Claude)                                 │
│  └─ decides sources, constructs URLs                     │
│                                                          │
│  Parallel scrapers (Stagehand v3):                       │
│  ├── Lab page        → projects, open roles, students    │
│  ├── Google Scholar  → papers, h-index, recency          │
│  ├── Semantic Scholar → topic tags, co-authors           │
│  └── GitHub          → repos, languages, activity        │
│                                                          │
│  Claude synthesis → research summary + fit score         │
│  Redis cache      → keyed by name+school, 72h TTL        │
└───────────────────┬──────────────────────────────────────┘
                    │  structured profile JSON
                    ▼
┌──────────────────────────────────────────────────────────┐
│           WORKFLOW AGENT (Fetch.ai uAgents)              │
│                                                          │
│  EmailSequencerAgent  → stagger outreach across profs    │
│  EmailGeneratorAgent  → mode-aware cold email drafts     │
│  PaperMonitorAgent    → watch for new publications       │
│  DeadlineTrackerAgent → PhD program deadline surfacing   │
│  PipelineTrackerAgent → status per professor             │
└──────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────┐
│                        OUTPUTS                           │
│  Professor one-pager  │  Compare mode  │  Email drafts   │
│  Outreach dashboard   │  Follow-up queue                 │
└──────────────────────────────────────────────────────────┘
```

### Component responsibilities

| Component | Technology | Responsibility |
|---|---|---|
| Planning agent | Claude (claude-sonnet-4-6) | Decides which sources exist for a given professor, constructs target URLs |
| Lab page scraper | Stagehand `extract()` | Projects, open roles, current students, funding |
| Scholar scraper | Stagehand + Browserbase stealth | Papers (last 3 years), h-index, top co-authors |
| Semantic Scholar scraper | Stagehand / REST API fallback | Topic tags, research area clustering, influential citations |
| GitHub scraper | Stagehand `extract()` | Repos, primary languages, README content, commit recency |
| Data aggregator | Python | Deduplication and merging across sources |
| Synthesis | Claude (claude-sonnet-4-6) | Research summary, fit score, cold email angle |
| Profile cache | Redis | `prof:{name_slug}:{school_slug}` → profile JSON, 72h TTL |
| EmailSequencerAgent | Fetch.ai uAgent | Enforces outreach pacing rules, manages send queue |
| EmailGeneratorAgent | Fetch.ai uAgent + Claude | Mode-aware cold email drafts, follow-up hooks |
| PaperMonitorAgent | Fetch.ai uAgent + Semantic Scholar | Polls for new publications daily, triggers reply hooks |
| DeadlineTrackerAgent | Fetch.ai uAgent + Browserbase | Scrapes PhD program deadlines, surfaces urgency |
| PipelineTrackerAgent | Fetch.ai uAgent | Stateful status tracker per professor |
| Frontend | React + TypeScript + Tailwind | Search, one-pager, compare mode, outreach dashboard |
| Voice input | Deepgram STT | Optional voice search kickoff |

### Agent handoff

The two agents communicate via Fetch.ai's Chat Protocol. When the Research Agent completes a profile, it sends a `ProfileHandoff` message to the Workflow Agent on Agentverse:

```python
class ProfileHandoff(Model):
    professor_name: str
    school: str
    profile_json: str
    user_mode: str  # "undergrad" | "ms" | "postbac"
```

This clean boundary means the Research Agent is stateless and reusable; the Workflow Agent owns all persistence and scheduling.
