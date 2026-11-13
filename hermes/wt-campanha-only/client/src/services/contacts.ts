import { apiGet, apiPost, apiDelete } from "@/lib/api";
import type { Contact, MassCallJob } from "@/types/contacts";

export const getSessionContacts = (sid: string, query?: string) => {
  const q = query ? `?q=${encodeURIComponent(query)}` : "";
  return apiGet<{ contacts: Contact[] }>(`/api/sessions/${sid}/contacts${q}`).then((r) => r.contacts ?? []);
};

export const searchContacts = (name: string) =>
  apiGet<{ contacts: Contact[] }>(`/api/contacts/search?name=${encodeURIComponent(name)}`).then((r) => r.contacts ?? []);

export const startMassCall = (phones: string[], names: string[], sessionId?: string, delay?: number) =>
  apiPost<{ success: boolean; job: MassCallJob }>("/api/mass-call", {
    phones,
    names,
    session_id: sessionId ?? "",
    delay_between_s: delay ?? 5,
  });

export const getMassCallStatus = (id: string) => apiGet<MassCallJob>(`/api/mass-call/${id}`);

export const cancelMassCall = (id: string) => apiDelete(`/api/mass-call/${id}`);
