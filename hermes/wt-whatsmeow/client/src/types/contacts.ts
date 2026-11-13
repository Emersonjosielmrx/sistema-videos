export interface Contact {
  jid: string;
  phone: string;
  name: string;
  push_name: string;
  business_name: string;
  is_group: boolean;
}

export interface MassCallJob {
  id: string;
  phones: string[];
  names: string[];
  session_id: string;
  status: "pending" | "running" | "done" | "cancelled" | "failed";
  progress: number;
  total: number;
  results: MassCallResult[];
  delay_between_s: number;
}

export interface MassCallResult {
  phone: string;
  name: string;
  status: string;
  duration_ms: number;
}
