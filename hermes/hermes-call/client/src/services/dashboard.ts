import { apiGet } from "@/lib/api";
import type { DashboardData } from "@/types/settings";

export async function fetchDashboard(range?: string): Promise<DashboardData> {
  const q = range ? `?range=${encodeURIComponent(range)}` : "";
  return apiGet<DashboardData>(`/api/dashboard${q}`);
}
