import { apiGet } from "@/lib/api";

export type CampaignSummary = {
  id: string;
  session_id: string;
  kind: string;
  name: string;
  total: number;
  audio_ms: number;
  created_at: string;
  finished_at?: string | null;
  completed: number;
  answered: number;
  no_answer: number;
  failed: number;
  avg_listen_pct: number;
  full_listen_count: number;
};

export type CampaignResult = {
  campaign_id: string;
  number: string;
  name?: string;
  jid?: string;
  call_id?: string;
  status: string;
  duration_ms: number;
  audio_ms: number;
  listen_pct: number;
  reply?: string;
  interested: boolean;
  created_at: string;
};

export const listCampaigns = (limit = 50) =>
  apiGet<{ campaigns: CampaignSummary[] }>(`/api/campaigns?limit=${limit}`).then((r) => r.campaigns ?? []);

export type ResultFilters = {
  order?: "listen" | "duration" | "status";
  minListen?: number;
  interested?: boolean;
};

export const getCampaignResults = (id: string, f: ResultFilters = {}) => {
  const p = new URLSearchParams();
  if (f.order) p.set("order", f.order);
  if (f.minListen) p.set("min_listen", String(f.minListen));
  if (f.interested) p.set("interested", "true");
  const q = p.toString();
  return apiGet<{ results: CampaignResult[] }>(`/api/campaigns/${id}/results${q ? "?" + q : ""}`).then(
    (r) => r.results ?? [],
  );
};
