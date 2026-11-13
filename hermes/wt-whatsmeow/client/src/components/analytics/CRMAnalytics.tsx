import { Card } from "@/components/ui/card";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { Sparkles, TrendingUp, DollarSign, Clock, Bot, User, GitBranch, LayoutGrid } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useState, useEffect } from "react";
import { apiGet } from "@/lib/api";

// Analytics CRM — reconstruído fiel à golden v0.2.1 (componente sOe).
// Dados reais vêm de /api/analytics/crm/{kpis,win-loss,funnel,heatmap}; sem dado,
// mostra zeros/vazios (não inventa números).

const FUNNEL_COLORS = ["#3b82f6", "#0ea5e9", "#14b8a6", "#10b981", "#059669", "#047857"];

function brl(n: number) {
  return (n || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function CRMAnalytics({ onFilterClick }: { onFilterClick?: (type: "stage" | "source", value: string) => void }) {
  const [funnelData, setFunnelData] = useState<any[]>([]);
  const [winLossData, setWinLossData] = useState<any[]>([]);
  const [lossReasons, setLossReasons] = useState<{ reason: string; percent: number }[]>([]);
  const [kpis, setKpis] = useState({
    revenue: "R$ 0", ticket: "R$ 0", timeToClose: "0h",
    avgEffort: "—", leadsWaiting: 0, forecast: "R$ 0",
  });
  const [revenueChange, setRevenueChange] = useState<number | null>(null);
  const [heatmapCells, setHeatmapCells] = useState<{ day: number; hour: number; n: number }[]>([]);

  useEffect(() => {
    (async () => {
      try {
        const [kpi, wl, fn, hm] = await Promise.all([
          apiGet<any>("/api/analytics/crm/kpis").catch(() => null),
          apiGet<any>("/api/analytics/crm/win-loss").catch(() => null),
          apiGet<any>("/api/analytics/crm/funnel").catch(() => null),
          apiGet<any>("/api/analytics/crm/heatmap").catch(() => null),
        ]);
        if (kpi) {
          const ttcDays = Number(kpi.time_to_close || 0);
          const ttc = ttcDays <= 0 ? "—"
            : ttcDays < 1 ? `${Math.round(ttcDays * 24)}h`
            : `${ttcDays.toFixed(1)} dias`;
          const effort = Number(kpi.avg_effort || 0);
          setKpis({
            revenue: brl(kpi.revenue || 0),
            ticket: brl(kpi.ticket || 0),
            timeToClose: ttc,
            avgEffort: effort > 0 ? `${effort.toFixed(1)}x` : "—",
            leadsWaiting: kpi.leads_waiting || 0,
            forecast: brl(kpi.forecast || 0),
          });
          setIaClosed(Number(kpi.revenue || 0) - Number(kpi.human_revenue || 0));
          setHumanClosed(Number(kpi.human_revenue || 0));
          const prev = Number(kpi.prev_revenue || 0);
          if (prev > 0) {
            setRevenueChange(((Number(kpi.revenue || 0) - prev) / prev) * 100);
          } else if (Number(kpi.revenue || 0) > 0) {
            setRevenueChange(100);
          }
        }
        if (wl?.win_loss) setWinLossData(wl.win_loss);
        if (wl?.loss_reasons) {
          setLossReasons(wl.loss_reasons.map((r: any) => ({ reason: r.name, percent: Math.round(r.value) })));
        }
        if (fn?.funnel) {
          setFunnelData(fn.funnel.map((s: any, i: number) => ({ name: s.name, value: s.value, fill: FUNNEL_COLORS[i % FUNNEL_COLORS.length] })));
        }
        if (hm?.cells) {
          setHeatmapCells(hm.cells);
        }
      } catch {
        /* sem dados ainda — mostra zeros/vazios, não inventa números */
      }
    })();
  }, []);

  const [iaClosed, setIaClosed] = useState(0);
  const [humanClosed, setHumanClosed] = useState(0);
  const days = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];

  const flowData = funnelData;
  const winLoss = winLossData;

  return (
    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10 mt-4">
      {/* Copilot Insight */}
      <Card className="p-4 bg-primary/5 border-primary/20 shadow-glow flex items-start gap-4">
        <div className="p-3 bg-primary/20 rounded-full text-primary shrink-0 mt-1">
          <Sparkles className="w-5 h-5" />
        </div>
        <div>
          <h3 className="font-bold text-primary flex items-center gap-2 mb-1">
            Hipercool Copilot
            <Badge variant="outline" className="text-[9px] h-4 bg-background border-primary/30 text-primary">Insight</Badge>
          </h3>
          <p className="text-sm text-foreground/80 leading-relaxed">
            {lossReasons.length > 0 ? (
              <>Seu maior motivo de perda é <strong>{lossReasons[0].reason}</strong> ({lossReasons[0].percent}% dos descartes). Considere um follow-up focado nesse ponto para recuperar leads parados.</>
            ) : (
              <>Ainda não há dados suficientes de fechamento/perda para gerar um insight. Conforme seus leads avançarem no funil, mostro aqui onde você está perdendo vendas e o que ajustar.</>
            )}
          </p>
        </div>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-4 auto-rows-[minmax(120px,auto)]">
        {/* Receita Gerada */}
        <Card className="col-span-1 md:col-span-4 p-5 bg-glass border-border/50 shadow-soft flex flex-col justify-between relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
            <DollarSign className="w-24 h-24 text-emerald-500" />
          </div>
          <div className="relative z-10">
            <div className="flex items-center gap-2 mb-2 text-muted-foreground">
              <DollarSign className="w-4 h-4 text-emerald-500" />
              <span className="text-xs font-bold uppercase tracking-wider">Receita Gerada</span>
            </div>
            <p className="text-4xl font-bold text-emerald-500">{kpis.revenue}</p>
          </div>
          <div className="mt-4 flex items-center gap-2 text-sm font-medium relative z-10" style={{ color: revenueChange !== null ? (revenueChange >= 0 ? "rgb(16 185 129 / 0.8)" : "rgb(239 68 68 / 0.8)") : "rgb(161 161 170 / 0.6)" }}>
            <TrendingUp className="w-4 h-4" /> {revenueChange !== null ? `${revenueChange >= 0 ? "+" : ""}${Math.round(revenueChange)}% vs mês anterior` : "Sem dados do mês anterior"}
          </div>
        </Card>

        {/* Velocidade (Time-to-Close) */}
        <Card className="col-span-1 md:col-span-4 p-5 bg-glass border-border/50 shadow-soft flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2 text-muted-foreground">
              <Clock className="w-4 h-4 text-amber-500" />
              <span className="text-xs font-bold uppercase tracking-wider">Velocidade (Time-to-Close)</span>
            </div>
            <p className="text-4xl font-black font-mono tracking-tighter">{kpis.timeToClose}</p>
          </div>
          <p className="text-xs text-muted-foreground mt-4">Média de tempo da entrada do lead até o "Ganho".</p>
        </Card>

        {/* Origem do Fechamento */}
        <Card className="col-span-1 md:col-span-4 p-5 bg-glass border-border/50 shadow-soft flex flex-col justify-between">
          <div className="flex items-center gap-2 mb-4 text-muted-foreground">
            <GitBranch className="w-4 h-4 text-blue-500" />
            <span className="text-xs font-bold uppercase tracking-wider">Origem do Fechamento</span>
          </div>
          <div className="space-y-4">
            <div onClick={() => onFilterClick?.("source", "ia")} className={onFilterClick ? "cursor-pointer hover:bg-primary/5 rounded-lg p-1 -m-1 transition-colors" : ""}>
              <div className="flex justify-between text-sm font-bold mb-1">
                <span className="flex items-center gap-1.5"><Bot className="w-4 h-4 text-primary" /> IA (Piloto)</span>
                <span>{brl(iaClosed)}</span>
              </div>
              <div className="w-full bg-primary/10 h-2 rounded-full overflow-hidden">
                <div className="bg-primary h-full rounded-full" style={{ width: `${iaClosed + humanClosed > 0 ? (iaClosed / (iaClosed + humanClosed)) * 100 : 0}%` }} />
              </div>
            </div>
            <div onClick={() => onFilterClick?.("source", "humano")} className={onFilterClick ? "cursor-pointer hover:bg-muted/30 rounded-lg p-1 -m-1 transition-colors" : ""}>
              <div className="flex justify-between text-sm font-bold mb-1 text-muted-foreground">
                <span className="flex items-center gap-1.5"><User className="w-4 h-4" /> Humano</span>
                <span>{brl(humanClosed)}</span>
              </div>
              <div className="w-full bg-muted h-2 rounded-full overflow-hidden">
                <div className="bg-muted-foreground/50 h-full rounded-full" style={{ width: `${iaClosed + humanClosed > 0 ? (humanClosed / (iaClosed + humanClosed)) * 100 : 0}%` }} />
              </div>
            </div>
          </div>
        </Card>

        {/* Fluxo de Leads (Sankey Flow) */}
        <Card className="col-span-1 md:col-span-8 p-5 bg-glass border-border/50 shadow-soft h-[300px] flex flex-col relative overflow-hidden group">
          <div className="flex items-center justify-between mb-4 relative z-10">
            <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-sky-500" /> Fluxo de Leads (Sankey Flow)
            </h4>
          </div>
          <div className="flex-1 w-full relative z-10">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={flowData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }} onClick={(e: any) => { if (e?.activePayload?.[0]?.payload?.name && onFilterClick) onFilterClick("stage", e.activePayload[0].payload.name); }} style={{ cursor: onFilterClick ? "pointer" : undefined }}>
                <defs>
                  <linearGradient id="colorFlow" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.1} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={10} tickLine={false} axisLine={false} />
                <YAxis stroke="hsl(var(--muted-foreground))" fontSize={10} tickLine={false} axisLine={false} hide />
                <Tooltip cursor={{ fill: 'hsl(var(--muted)/0.1)' }} contentStyle={{ backgroundColor: 'hsl(var(--background))', borderColor: 'hsl(var(--border))', borderRadius: '12px', fontSize: '12px' }} />
                <Area type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorFlow)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Heatmap de Conversão — FIX #7: grade era 100% decorativa (todas as células fixas
            em bg-muted/40, sem endpoint). Marcado como "Em breve" pra não parecer um gráfico
            real vazio (o que fazia o dono achar "fake"). Quando o backend expor
            /api/analytics/crm/heatmap, alimentar as células com a intensidade real. */}
        <Card className="col-span-1 md:col-span-4 p-5 bg-glass border-border/50 shadow-soft h-[300px] flex flex-col">
          <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-2 mb-4">
            <LayoutGrid className="h-4 w-4 text-rose-500" /> Heatmap de Conversão
            <Badge variant="outline" className="text-[8px] h-4 bg-background border-amber-500/30 text-amber-500 ml-auto">Em breve</Badge>
          </h4>
          <div className="flex-1 w-full flex flex-col gap-1.5 justify-center">
            <div className="flex gap-2 text-[9px] text-muted-foreground mb-1 ml-6">
              <span className="flex-1 text-center">00h</span>
              <span className="flex-1 text-center">12h</span>
              <span className="flex-1 text-center">23h</span>
            </div>
            {days.map((day, di) => {
              const maxN = Math.max(1, ...heatmapCells.map(c => c.n));
              return (
                <div key={day} className="flex items-center gap-1.5 h-full">
                  <span className="text-[10px] font-bold text-muted-foreground w-5">{day}</span>
                  <div className="flex flex-1 gap-1 h-full">
                    {Array.from({ length: 12 }).map((_, hi) => {
                      const hourStart = hi * 2;
                      const count = heatmapCells.filter(c => c.day === di && (c.hour === hourStart || c.hour === hourStart + 1)).reduce((s, c) => s + c.n, 0);
                      const intensity = count > 0 ? Math.max(0.15, count / maxN) : 0;
                      return (
                        <div
                          key={hi}
                          className="flex-1 rounded-[2px]"
                          style={{ backgroundColor: count > 0 ? `rgba(239, 68, 68, ${intensity})` : "hsl(var(--muted) / 0.4)" }}
                          title={count > 0 ? `${day} ${hourStart}h-${hourStart + 2}h: ${count} conversão(ões)` : `${day} ${hourStart}h-${hourStart + 2}h: sem dados`}
                        />
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </Card>

        {/* Taxa de Vitória + Motivos de Perda */}
        <Card className="col-span-1 md:col-span-12 p-5 bg-glass border-border/50 shadow-soft grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="flex flex-col items-center justify-center border-b md:border-b-0 md:border-r border-border/50 pb-6 md:pb-0">
            <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-4 w-full text-center">Taxa de Vitória</h4>
            <div className="h-[140px] w-[140px] relative">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={winLoss} innerRadius={50} outerRadius={70} paddingAngle={2} dataKey="value" stroke="none">
                    {winLoss.map((s: any, i: number) => (
                      <Cell key={`cell-${i}`} fill={s.color} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: 'hsl(var(--background))', borderColor: 'hsl(var(--border))', borderRadius: '8px', fontSize: '12px' }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-3xl font-black">
                  {(() => {
                    const won = Number(winLoss.find((d: any) => d.name === "Ganhos")?.value || 0);
                    const lost = Number(winLoss.find((d: any) => d.name === "Perdas")?.value || 0);
                    const total = won + lost;
                    return total > 0 ? Math.round((won / total) * 100) : 0;
                  })()}%
                </span>
              </div>
            </div>
          </div>

          <div className="md:col-span-2 flex flex-col justify-center">
            <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-4">Motivos de Perda (Descartes)</h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-4">
              {lossReasons.map((reason, i) => (
                <div key={i} className="flex flex-col gap-1.5 hover:bg-muted/30 p-2 rounded-lg transition-colors cursor-default">
                  <div className="flex justify-between text-sm">
                    <span className="font-bold text-foreground/80">{reason.reason}</span>
                    <span className="text-destructive font-bold">{reason.percent}%</span>
                  </div>
                  <div className="w-full bg-destructive/10 h-2 rounded-full overflow-hidden shadow-inner">
                    <div className="bg-destructive h-full rounded-full shadow-glow" style={{ width: `${reason.percent}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
