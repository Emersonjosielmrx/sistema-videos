import { Contact } from "./contacts";

export interface MassMessageResult {
  phone: string;
  name: string;
  status: "sent" | "failed" | "skipped";
  error?: string;
}

export interface MassMessageJob {
  id: string;
  user_id: string;
  session_id: string;
  message: string;
  media_url?: string;
  contacts: Contact[];
  status: "pending" | "running" | "completed" | "cancelled" | "failed";
  progress: number;
  total: number;
  results: MassMessageResult[];
  delay_between: number;
  created_at: string;
}

export interface StartMassMessageRequest {
  sessionId: string;
  message: string;
  media_url?: string;
  delay_between: number;
  contacts: Contact[];
  /** Quem nunca conversou com a linha recebe os botões "Tenho interesse" / "Bloquear". */
  first_contact_buttons?: boolean;
}
