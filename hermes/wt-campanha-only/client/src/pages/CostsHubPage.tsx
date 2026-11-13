import { useState } from "react";
import { LayoutDashboard } from "lucide-react";
import { DashboardPage } from "@/pages/DashboardPage";
import { ROIPanel } from "@/pages/ROIPanel";
import { CostPage } from "@/pages/CostPage";
import { AnalyticsPage } from "@/pages/AnalyticsPage";

// CostsHubPage — UMA tela só (sem sub-abas). Faixa de destaque no topo com os 3
// números que importam LADO A LADO: ROI, Custo total e Economia total — com o ROI em
// evidência. Abaixo, empilhados: painel de ROI (detalhe), custos de IA e analytics.

export function CostsHubPage() {
  const [days, setDays] = useState(7);

  return (
    <div className="space-y-6 p-3 sm:p-6">
      <div className="flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-xl font-semibold">
          <LayoutDashboard className="h-5 w-5" /> Painel
        </h2>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="border border-border/50 rounded-xl px-3 py-1.5 text-sm bg-glass shadow-soft"
        >
          <option value={1}>Últimas 24h (1 dia)</option>
          <option value={7}>Últimos 7 dias</option>
          <option value={14}>Últimos 14 dias</option>
          <option value={30}>Últimos 30 dias</option>
          <option value={999}>Mais de 30 dias (Todos)</option>
        </select>
      </div>

      {/* Visão geral (absorve o antigo Dashboard) */}
      <DashboardPage />

      {/* Detalhe do valor gerado (ROI completo) */}
      <ROIPanel />

      {/* Custos por faixa (sem o duplicado do total) */}
      <CostPage hideTotalAndLimits={true} />

      {/* Métricas / conversão / A/B integradas (agora sem separação visual) */}
      <AnalyticsPage days={days} />
    </div>
  );
}
