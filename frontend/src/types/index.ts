// Mirrors the backend Pydantic models so the wire format is typed end-to-end.

export type NamedZone =
  | "NW" | "NE" | "SW" | "SE"
  | "N_LEG" | "S_LEG" | "E_LEG" | "W_LEG" | "CENTER";

export type Confidence = "high" | "medium" | "low";
export type FindingStatus = "CONFIRMED" | "CANDIDATE" | "REPORTED";

export interface ObservedCondition {
  zone: NamedZone;
  observation: string;
  source_view: string;
  source_capture_date: string | null;
  confidence: Confidence;
  not_visually_confirmable: boolean;
}

export interface Corroboration {
  source: string;
  reference: string;
  excerpt: string | null;
  date: string | null;
}

export interface Intervention {
  key: string;
  name: string;
  trigger: string;
  cost_low: number | null;
  cost_high: number | null;
  cost_unit: string;
  evidence: string;
  feasibility_caveat: string;
  funding_program_keys: string[];
  disclaimer: string;
}

export interface Finding {
  condition: ObservedCondition;
  status: FindingStatus;
  corroboration: Corroboration[];
  intervention: Intervention | null;
  crash_count_intersection: number | null;
  crash_count_zone: number | null;
}

export interface AccountabilityEvent {
  intersection_id: string;
  date: string;
  source: string;
  summary: string;
  action_status: "no_action_recorded" | "action_recorded" | "unknown";
}

export interface ConceptRender {
  zone: string;
  observation: string;
  fix: string | null;
  before_url: string | null;
  after_url: string | null;
  label: string;
}

export interface RedditPost {
  subreddit: string;   // bare name; UI renders "r/<subreddit>"
  title: string;
  body: string;
}

export interface AnalysisResult {
  intersection: { id: string; address: string; lat: number; lng: number; images: any[] };
  findings: Finding[];
  accountability: AccountabilityEvent[];
  coalition_count: number;
  annotated_image_url: string | null;
  concept_image_url: string | null;
  renders: ConceptRender[];
  social_post: string | null;
  reddit_post: RedditPost | null;
  council_report: string | null;
}

export interface CouncilContact {
  name: string;
  email: string;
  district: string | null;
  role: string;
  source: string;
}

export interface CouncilEmailDraft {
  subject: string;
  body: string;
  recipients: CouncilContact[];
  eml_base64: string;   // base64 of a ready-to-send .eml (PDF attached) — desktop mail apps
  filename: string;     // .eml filename
  pdf_base64: string;   // standalone PDF, for manual attach on web Gmail/Outlook
  pdf_filename: string;
}

export interface ProgressEvent {
  agent: string;
  msg: string;
  [k: string]: unknown;
}
