import { apiGet, apiPost, apiDelete } from "@/lib/api";
import type { MassMessageJob, StartMassMessageRequest } from "@/types/massmsg";

export async function startMassMessage(req: StartMassMessageRequest): Promise<MassMessageJob> {
  return apiPost("/api/mass-message", req);
}

export async function getMassMessageStatus(id: string): Promise<MassMessageJob> {
  return apiGet(`/api/mass-message/${id}`);
}

export async function cancelMassMessage(id: string): Promise<{ ok: boolean }> {
  await apiDelete(`/api/mass-message/${id}`);
  return { ok: true };
}
