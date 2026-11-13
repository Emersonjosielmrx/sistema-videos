import { useEffect, useState } from "react";
import { Activity, PhoneCall, Radio, Zap, Clock, Heart, DollarSign, Users, Download, AlertTriangle, ArrowRight, BrainCircuit, Filter, FileText, ShieldAlert, Ear, Globe2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { fetchDashboard } from "@/services/dashboard";
import { apiGet } from "@/lib/api";
import { logError } from "@/lib/log";
import { setView } from "@/stores/navigation";
import type { DashboardData } from "@/types/settings";
import { cn } from "@/lib/utils";
import { FirstStepsCard } from "@/components/onboarding/FirstStepsCard";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";

function StatCard({ icon: Icon, label, value, sub, chartData, chartColor = "#10b981", className }: { icon: React.ElementType; label: string; value: string | number; sub?: string; chartData?: number[]; chartColor?: string; className?: string }) {
  const cId = "grad-" + Math.random().toString(36).substring(2, 9);
  return (
    <Card className={cn("relative overflow-hidden bg-glass border border-border/50 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl p-5 flex flex-col justify-between group", className)}>
      <div className="absolute top-0 right-0 w-24 h-24 bg-primary/10 rounded-full blur-2xl -mr-8 -mt-8 transition-transform group-hover:scale-150"></div>
      <div className="relative z-10 flex items-start justify-between">
        <div>
          <div className="inline-flex rounded-xl bg-primary/15 p-2.5 mb-4 shadow-glow">
            <Icon className="h-5 w-5" style={{ color: chartColor }} />
          </div>
          <p className="text-sm font-medium text-muted-foreground">{label}</p>
        </div>
      </div>
      <div className="mt-2 relative z-10 flex items-end justify-between">
        <div>
          <p className="text-3xl font-bold tracking-tight">{value}</p>
          {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
        </div>
        {chartData && (
          <div className="w-24 h-12 ml-4 -mb-2 shrink-0">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData.map((val, i) => ({ val, i }))}>
                <defs>
                  <linearGradient id={cId} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={chartColor} stopOpacity={0.4}/>
                    <stop offset="95%" stopColor={chartColor} stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <Area type="monotone" dataKey="val" stroke={chartColor} strokeWidth={2} fillOpacity={1} fill={`url(#${cId})`} isAnimationActive={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </Card>
  );
}

function CircularProgress({ value, label, sub }: { value: number; label: string; sub?: string }) {
  const radius = 38;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (value / 100) * circumference;

  return (
    <Card className="col-span-12 md:col-span-3 lg:col-span-3 bg-glass border border-border/50 p-5 flex flex-col items-center justify-center transition-all duration-300 hover:-translate-y-1 hover:shadow-xl group relative overflow-hidden">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-32 h-32 bg-primary/5 rounded-full blur-xl group-hover:bg-primary/10 transition-colors"></div>
      <div className="relative w-28 h-28 flex items-center justify-center">
        <svg className="w-full h-full transform -rotate-90">
          <circle cx="56" cy="56" r={radius} stroke="currentColor" strokeWidth="8" fill="transparent" className="text-muted/30" />
          <circle 
            cx="56" 
            cy="56" 
            r={radius} 
            stroke="currentColor" 
            strokeWidth="8" 
            fill="transparent" 
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            className="text-primary transition-all duration-1000 ease-out drop-shadow-[0_0_8px_rgba(16,185,129,0.5)]" 
          />
        </svg>
        <div className="absolute flex flex-col items-center justify-center">
          <span className="text-2xl font-bold">{value}%</span>
        </div>
      </div>
      <div className="text-center mt-4 z-10">
        <p className="text-sm font-medium text-muted-foreground">{label}</p>
        {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
      </div>
    </Card>
  );
}

// mapeia o filtro do select pro range do backend
const rangeParam = (r: string) => (r === "7dias" ? "7d" : r === "mes" ? "30d" : r === "sempre" ? "all" : r === "1dia" ? "1d" : "today");

type FeedItem = { id: string; msg: string; phone: string; time: string; type: string };

function relTime(iso: string): string {
  const d = new Date(iso).getTime();
  if (isNaN(d)) return "";
  const diff = Math.floor((Date.now() - d) / 60000);
  if (diff < 1) return "agora";
  if (diff < 60) return `${diff} min`;
  if (diff < 1440) return `${Math.floor(diff / 60)}h`;
  return `${Math.floor(diff / 1440)}d`;
}

export function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [totalTranscripts, setTotalTranscripts] = useState(0);
  const [dateRange, setDateRange] = useState("hoje");
  const [healthStatus] = useState("ok");
  const [feedEvents, setFeedEvents] = useState<FeedItem[]>([]);
  // FIX P0-008 (2026-07-25): antes fetchDashboard().catch(() => {}) engolia o
  // erro, data ficava null, e o render abaixo mostrava <Skeleton /> pra sempre.
  // Agora tracking de loading + error distintos; se erro, mostra estado
  // honesto com botão "Tentar de novo" em vez de pulsar eternamente.
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Live Feed REAL: últimas ligações transcritas (número, resumo/classificação, quando).
  const loadFeed = () => {
    apiGet<{ transcripts: any[] }>("/api/transcripts?limit=8")
      .then((r) => {
        // Deriva o tipo do evento da classificação/interesse REAL da ligação.
        const items = (r.transcripts ?? []).map((t: any): FeedItem => {
           const cls = String(t.classificacao || "").toLowerCase();
           let type = "info";
           if (t.interested || cls.includes("interess")) type = "success";
           else if (cls.includes("sem_interesse") || cls.includes("errado") || cls.includes("recus")) type = "warn";
           const msg = (t.resumo && t.resumo.trim())
             ? t.resumo.trim()
             : t.classificacao
               ? `Ligação classificada: ${t.classificacao}`
               : "Ligação transcrita";
           return {
             id: t.id,
             msg,
             phone: t.number || "—",
             time: relTime(t.created_at),
             type,
           };
        });
        setFeedEvents(items);
      })
      .catch(() => setFeedEvents([]));
  };

  const loadDashboard = async () => {
    setLoading(true);
    setError(null);
    try {
      const d = await fetchDashboard(rangeParam(dateRange));
      setData(d);
    } catch (e: any) {
      // FIX P0-008: mostra erro real em vez de skeleton infinito.
      setError(e?.message || "Erro ao carregar dashboard");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
    apiGet<{ transcripts: any[] }>("/api/transcripts?limit=1000")
      .then(r => setTotalTranscripts(r.transcripts?.length || 0))
      .catch(logError("/api/transcripts"));
    loadFeed();

    const interval = setInterval(() => {
      loadDashboard();
      loadFeed();
    }, 10000);
    return () => clearInterval(interval);
  }, [dateRange]);

  if (loading && !data) {
    return (
      <div className="p-6 space-y-6">
        <div className="h-8 w-48 bg-muted rounded-md animate-pulse"></div>
        <div className="grid grid-cols-12 gap-4">
          {[1,2,3,4].map(i => <div key={i} className="col-span-12 sm:col-span-6 lg:col-span-3 h-36 bg-muted rounded-2xl animate-pulse"></div>)}
        </div>
      </div>
    );
  }

  if (error && !data) {
    // FIX P0-008: estado de erro honesto com ação de retry.
    return (
      <div className="p-6 space-y-4">
        <FirstStepsCard />
        <div className="flex items-center gap-3 text-amber-500">
          <AlertTriangle className="h-6 w-6" />
          <h2 className="text-xl font-semibold">Não foi possível carregar o dashboard</h2>
        </div>
        <p className="text-sm text-muted-foreground">{error}</p>
        <Button onClick={loadDashboard} variant="outline" className="gap-2">
          Tentar de novo
        </Button>
      </div>
    );
  }

  // FIX P0-008: TS narrowing — após os 2 returnsAbove, se chegou aqui data é
  // não-null (loading=false && error=null && data preenchido). Mas TS não
  // infere sozinho, então asserção explícita.
  if (!data) return null;

  const avgSec = Math.round(data.calls.avg_duration_ms / 1000);
  const avgDisplay = avgSec > 60 ? `${Math.floor(avgSec / 60)}m${avgSec % 60}s` : `${avgSec}s`;
  const answerRate = Math.round(data.calls.answer_rate * 100);

  // Funil REAL (agregado de campaign_results pelo backend). Sem dado → zeros.
  const funil = {
    mailing: data.funnel?.attempts ?? 0, // "base" = tentativas (schema não tem mailing original)
    tentativas: data.funnel?.attempts ?? 0,
    atendidas: data.funnel?.answered ?? 0,
    engajadas: data.funnel?.engaged ?? 0,
    leads: data.funnel?.leads ?? 0,
  };

  // baseCalls = tentativas reais no recorte (ou histórico de transcrições como piso).
  const baseCalls = funil.tentativas > 0 ? funil.tentativas : totalTranscripts;
  // Minutos por ligação: usa a duração média REAL quando existe; 6 min só como estimativa inicial.
  const minPorLigacao = data.calls.avg_duration_ms > 0 ? data.calls.avg_duration_ms / 60000 : 6;
  const minutosTotais = baseCalls * minPorLigacao;
  const custoPorHumanoHora = (2500 / 176) * 1.7;
  const economiaTotal = (minutosTotais / 60) * custoPorHumanoHora;
  // Custo REAL de IA no mês (BRL) vindo do backend; fallback à estimativa antiga.
  const custoIA = data.cost?.ai_brl_month ?? baseCalls * 0.45;
  const roiLiquido = economiaTotal - custoIA;
  const humanosNecessarios = baseCalls > 0 ? Math.max(1, Math.ceil(minutosTotais / (8 * 22 * 60))) : 0;

  // Custos por Etapa (custo real / conversões reais de cada etapa)
  const cpa = funil.atendidas > 0 ? custoIA / funil.atendidas : 0;
  const cpe = funil.engajadas > 0 ? custoIA / funil.engajadas : 0;
  const cpl = funil.leads > 0 ? custoIA / funil.leads : 0;

  function brl(n: number) {
    return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
  }
  function horas(min: number) {
    if (min === 0) return '0min';
    if (min < 60) return `${Math.round(min)}min`;
    return `${(min / 60).toFixed(1)}h`;
  }
  // Conversão real entre duas etapas do funil (b/a). 0 quando não há base.
  function pct(a: number, b: number) {
    return a > 0 ? Math.round((b / a) * 100) : 0;
  }
  // Custo médio real por ligação da base (custo total de IA / ligações).
  const custoPorLig = baseCalls > 0 ? custoIA / baseCalls : 0;

  // Sparklines reais dos buckets da API (timeseries). Fallback pra array derivado.
  const tsCalls = (data.timeseries ?? []).map(b => b.calls);
  const tsAnswered = (data.timeseries ?? []).map(b => b.answered);
  const sparkCalls = tsCalls.length >= 2 ? tsCalls : [0, baseCalls];
  const sparkAnswered = tsAnswered.length >= 2 ? tsAnswered : [0, funil.atendidas];
  const sparkCumCalls = sparkCalls.reduce<number[]>((acc, v) => { acc.push((acc[acc.length - 1] ?? 0) + v); return acc; }, []);

  return (
    <div className="space-y-6 p-4 sm:p-6 max-w-7xl mx-auto overflow-x-hidden">
      {/* Primeiros passos (caminho principal para começar; some quando tudo estiver feito) */}
      <FirstStepsCard />

      {/* Alerta de Saúde do Sistema */}
      {healthStatus === 'warn' && (
        <div className="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded-xl flex items-center gap-3">
          <AlertTriangle className="h-5 w-5" />
          <div className="flex-1">
             <p className="text-sm font-bold">Taxa de atendimento em queda livre</p>
             <p className="text-xs">A taxa de atendimento nas últimas 2 horas está abaixo de 10%. Revise a qualidade do mailing.</p>
          </div>
        </div>
      )}

      {/* Hero Banner Dashboard (Compacto) */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary/10 via-background to-background border border-primary/20 p-4 sm:p-5 shadow-glow mb-4">
        <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
          <img src="/hermesLogo.png" alt="Hermes Call Logo" className="w-32 h-auto object-contain rounded-full" onError={(e) => { e.currentTarget.style.display = 'none'; }} />
        </div>
        <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Zap className="h-4 w-4 text-primary" />
              <h2 className="text-xl sm:text-2xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-br from-primary to-emerald-400 drop-shadow-sm">
                Visão Geral da Operação
              </h2>
            </div>
            <p className="text-sm text-muted-foreground">
              Acompanhe em tempo real o desempenho de todos os seus agentes.
            </p>
          </div>
          <Badge className="bg-primary/10 text-primary border-primary/20 shrink-0 w-fit">
            Sistema Operante
          </Badge>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <h3 className="text-xl font-bold tracking-tight text-foreground/80">Métricas de Valor e Economia</h3>
        <div className="flex items-center gap-2 self-start sm:self-auto flex-wrap">
          <div className="relative">
             <Filter className="w-3 h-3 absolute left-2.5 top-2 text-muted-foreground pointer-events-none" />
             <select 
                value={dateRange} 
                onChange={(e) => setDateRange(e.target.value)}
                className="bg-background border border-border/50 text-xs rounded-full pl-7 pr-3 py-1 text-muted-foreground outline-none focus:ring-1 focus:ring-primary/50 cursor-pointer h-7 appearance-none"
             >
                <option value="hoje">Hoje</option>
                <option value="1dia">Últimas 24h (1 dia)</option>
                <option value="7dias">Últimos 7 dias</option>
                <option value="mes">Este mês (30 dias)</option>
                <option value="sempre">Mais de 30 dias (Todos)</option>
             </select>
          </div>
          <Button variant="outline" size="sm" className="h-7 rounded-full text-xs px-3 bg-background" onClick={() => window.print()}>
            <Download className="w-3 h-3 mr-1.5" /> Exportar Relatório
          </Button>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-semibold shrink-0 h-7">
            <Zap className="w-3 h-3" /> ROI em Tempo Real
          </div>
        </div>
      </div>

      {/* Grid Carrossel no Mobile */}
      <div className="flex sm:grid sm:grid-cols-12 gap-4 md:gap-6 overflow-x-auto snap-x snap-mandatory pb-4 sm:pb-0 scroll-smooth -mx-4 sm:mx-0 px-4 sm:px-0">
        <StatCard className="snap-center w-[85vw] sm:w-auto shrink-0 col-span-12 sm:col-span-6 lg:col-span-3" icon={DollarSign} label="Economia Bruta" value={brl(economiaTotal)} sub="Mão de obra + encargos" chartData={sparkCumCalls.map(v => v * 6 / 60 * custoPorHumanoHora)} chartColor="#10b981" />
        <StatCard className="snap-center w-[85vw] sm:w-auto shrink-0 col-span-12 sm:col-span-6 lg:col-span-3" icon={BrainCircuit} label="Custo da IA" value={brl(custoIA)} sub="Telefonia, Tokens e TTS" chartData={sparkCumCalls.map(v => v * custoPorLig)} chartColor="#ef4444" />
        <StatCard className="snap-center w-[85vw] sm:w-auto shrink-0 col-span-12 sm:col-span-6 lg:col-span-3" icon={Heart} label="ROI Líquido" value={brl(roiLiquido)} sub="Retorno real gerado" chartData={sparkCumCalls.map(v => v * 6 / 60 * custoPorHumanoHora - v * custoPorLig)} chartColor="#10b981" />
        <StatCard className="snap-center w-[85vw] sm:w-auto shrink-0 col-span-12 sm:col-span-6 lg:col-span-3" icon={Users} label="Atendentes Subtit." value={humanosNecessarios} sub="Pessoas poupadas" chartData={sparkCumCalls.map(v => Math.max(1, Math.ceil(v * 6 / 480)))} chartColor="#8b5cf6" />
      </div>

      <div className="flex items-center justify-between pt-2">
        <h3 className="text-xl font-bold tracking-tight text-foreground/80">Métricas Operacionais</h3>
      </div>

      <div className="flex sm:grid sm:grid-cols-12 gap-4 md:gap-6 overflow-x-auto snap-x snap-mandatory pb-4 sm:pb-0 scroll-smooth -mx-4 sm:mx-0 px-4 sm:px-0">
        <StatCard className="snap-center w-[85vw] sm:w-auto shrink-0 col-span-12 sm:col-span-6 lg:col-span-3" icon={Activity} label="Ligações (Histórico)" value={baseCalls} sub="Conversas totais" chartData={sparkCalls} chartColor="#ec4899" />
        <StatCard className="snap-center w-[85vw] sm:w-auto shrink-0 col-span-12 sm:col-span-6 lg:col-span-3" icon={PhoneCall} label="Em Ligação" value={data.calls.active} sub="Neste exato momento" chartData={sparkAnswered} chartColor="#0ea5e9" />
        <StatCard className="snap-center w-[85vw] sm:w-auto shrink-0 col-span-12 sm:col-span-6 lg:col-span-3" icon={Clock} label="Tempo Economizado" value={horas(minutosTotais)} sub={data.calls.avg_duration_ms > 0 ? `~${avgDisplay} por ligação (média real)` : "~6min por ligação (estimativa)"} chartData={sparkCumCalls.map(v => Math.round(v * 6))} chartColor="#eab308" />
        <CircularProgress value={answerRate} label="Taxa de Atendimento" sub="Ligações bem sucedidas" />
      </div>

      {/* Linha Extra: Funil, Distribuição e Feed */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 pt-4">
        {/* Gráfico Principal */}
        <Card className="col-span-1 md:col-span-7 p-5 bg-glass border border-border/50">
           <div className="flex items-center justify-between mb-6">
             <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Volume Acumulado <span className="normal-case font-normal text-[0.65rem] opacity-60">(total acumulado no período)</span></h3>
           </div>
           <div className="h-[250px] w-full">
             <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={(data.timeseries ?? []).length >= 2
                  ? data.timeseries!.reduce<{ time: string; calls: number }[]>((acc, b) => {
                      acc.push({ time: b.bucket.slice(11) || b.bucket.slice(5), calls: (acc[acc.length - 1]?.calls ?? 0) + b.calls });
                      return acc;
                    }, [])
                  // Sem série suficiente: só início e total reais (antes inventava uma curva 08h–18h).
                  : [{ time: 'início', calls: 0 }, { time: 'agora', calls: baseCalls }]}>
                  <defs>
                    <linearGradient id="colorCalls" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                  <XAxis dataKey="time" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#09090b', borderColor: '#27272a', borderRadius: '8px' }} />
                  <Area type="monotone" dataKey="calls" stroke="#10b981" strokeWidth={3} fillOpacity={1} fill="url(#colorCalls)" />
                </AreaChart>
             </ResponsiveContainer>
           </div>
        </Card>

        {/* Funil & Sentimentos */}
        <div className="col-span-1 md:col-span-5 grid grid-rows-2 gap-6">
           <Card className="p-4 bg-glass border border-border/50 flex flex-col justify-center relative overflow-visible">
             <div className="flex justify-between items-center mb-2">
               <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Jornada do Lead (Funil)</h3>
               <Badge variant="outline" className="text-[0.6rem] bg-primary/5 text-primary">Hoje</Badge>
             </div>
             
             {/* Funil Visual Expandido (5 Etapas) */}
             <div className="flex justify-between items-center relative mt-4">
                {/* Linha de conexão */}
                <div className="absolute top-6 left-6 right-6 h-1 bg-gradient-to-r from-border via-blue-500/30 to-primary/50 -z-10 rounded-full" />
                
                {/* 1. Mailing */}
                <div className="flex flex-col items-center gap-1.5 group cursor-pointer w-14">
                  <div className="bg-background border-2 border-muted w-10 h-10 rounded-full flex items-center justify-center font-bold text-xs group-hover:scale-110 transition-transform">{funil.mailing}</div>
                  <span className="text-[0.65rem] font-medium text-muted-foreground">Mailing</span>
                </div>

                {/* Drop-off Mailing -> Tentativas (mesma base: tentativas discadas) */}
                <div className="flex flex-col items-center group relative -mt-6">
                  <span className="text-[0.55rem] font-bold text-muted-foreground bg-background px-1 rounded-sm border border-border/50 mb-0.5">{pct(funil.mailing, funil.tentativas)}%</span>
                  <ArrowRight className="w-3 h-3 text-muted-foreground opacity-40" />
                  <div className="absolute -bottom-8 bg-card border border-border/50 rounded-lg p-2 text-[0.6rem] w-32 shadow-xl opacity-0 group-hover:opacity-100 transition-opacity z-20 pointer-events-none text-center">
                    <strong className="block mb-1">Discadas</strong>
                    {funil.tentativas} de {funil.mailing}
                  </div>
                </div>

                {/* 2. Tentativas */}
                <div className="flex flex-col items-center gap-1.5 group cursor-pointer w-14">
                  <div className="bg-background border-2 border-slate-500 w-12 h-12 rounded-full flex items-center justify-center font-bold text-slate-300 group-hover:scale-110 transition-transform">{funil.tentativas}</div>
                  <span className="text-[0.65rem] font-medium text-muted-foreground">Tentativas</span>
                  <span className="text-[0.55rem] text-muted-foreground opacity-80" title="Custo Médio da Base">{brl(custoPorLig)}/Lig</span>
                </div>

                {/* Drop-off Tentativas -> Atendidas */}
                <div className="flex flex-col items-center group relative -mt-6">
                  <span className="text-[0.55rem] font-bold text-blue-400 bg-background px-1 rounded-sm border border-blue-500/30 mb-0.5">{pct(funil.tentativas, funil.atendidas)}%</span>
                  <ArrowRight className="w-3 h-3 text-blue-500 opacity-40" />
                  <div className="absolute -bottom-8 bg-card border border-border/50 rounded-lg p-2 text-[0.6rem] w-32 shadow-xl opacity-0 group-hover:opacity-100 transition-opacity z-20 pointer-events-none text-center">
                    <strong className="block mb-1">Atenderam</strong>
                    {funil.atendidas} de {funil.tentativas}
                  </div>
                </div>

                {/* 3. Atendidas */}
                <div className="flex flex-col items-center gap-1.5 group cursor-pointer w-14">
                  <div className="bg-background border-2 border-blue-500 w-12 h-12 rounded-full flex items-center justify-center font-bold text-blue-400 group-hover:scale-110 transition-transform shadow-[0_0_10px_rgba(59,130,246,0.1)]">{funil.atendidas}</div>
                  <span className="text-[0.65rem] font-medium text-muted-foreground">Atendidas</span>
                  <span className="text-[0.55rem] text-blue-400 font-medium" title="Custo Por Atendimento">CPA: {brl(cpa)}</span>
                </div>

                {/* Drop-off Atendidas -> Engajadas */}
                <div className="flex flex-col items-center group relative -mt-6">
                  <span className="text-[0.55rem] font-bold text-indigo-400 bg-background px-1 rounded-sm border border-indigo-500/30 mb-0.5">{pct(funil.atendidas, funil.engajadas)}%</span>
                  <ArrowRight className="w-3 h-3 text-indigo-500 opacity-40" />
                  <div className="absolute -bottom-8 bg-card border border-border/50 rounded-lg p-2 text-[0.6rem] w-32 shadow-xl opacity-0 group-hover:opacity-100 transition-opacity z-20 pointer-events-none text-center">
                    <strong className="block mb-1">Engajaram</strong>
                    {funil.engajadas} de {funil.atendidas}
                  </div>
                </div>

                {/* 4. Engajadas */}
                <div className="flex flex-col items-center gap-1.5 group cursor-pointer w-14">
                  <div className="bg-background border-2 border-indigo-500 w-12 h-12 rounded-full flex items-center justify-center font-bold text-indigo-400 group-hover:scale-110 transition-transform shadow-[0_0_10px_rgba(99,102,241,0.15)]">{funil.engajadas}</div>
                  <span className="text-[0.65rem] font-medium text-muted-foreground">Engajadas</span>
                  <span className="text-[0.55rem] text-indigo-400 font-medium" title="Custo Por Engajamento">CPE: {brl(cpe)}</span>
                </div>

                {/* Drop-off Engajadas -> Leads */}
                <div className="flex flex-col items-center group relative -mt-6">
                  <span className="text-[0.55rem] font-bold text-primary bg-background px-1 rounded-sm border border-primary/30 mb-0.5">{pct(funil.engajadas, funil.leads)}%</span>
                  <ArrowRight className="w-3 h-3 text-primary opacity-40" />
                  <div className="absolute -bottom-8 bg-card border border-border/50 rounded-lg p-2 text-[0.6rem] w-32 shadow-xl opacity-0 group-hover:opacity-100 transition-opacity z-20 pointer-events-none text-center">
                    <strong className="block mb-1">Viraram lead</strong>
                    {funil.leads} de {funil.engajadas}
                  </div>
                </div>

                {/* 5. Leads */}
                <div className="flex flex-col items-center gap-1.5 group cursor-pointer w-14">
                  <div className="bg-primary border-2 border-primary w-14 h-14 rounded-full flex items-center justify-center font-black text-primary-foreground group-hover:scale-110 transition-transform shadow-[0_0_20px_rgba(16,185,129,0.4)] text-lg">{funil.leads}</div>
                  <span className="text-[0.65rem] font-bold text-primary">LEADS</span>
                  <span className="text-[0.55rem] text-primary font-bold bg-primary/10 px-1 rounded-sm" title="Custo Por Lead">CPL: {brl(cpl)}</span>
                </div>
             </div>
           </Card>

           <Card className="p-5 bg-glass border border-border/50 flex flex-row items-center gap-4">
              {(() => {
                // Distribuição de sentimento REAL vinda do backend (data.sentiment,
                // agregado de call_transcripts.classificacao). Sem dado → estado honesto.
                const palette = ["#10b981", "#f59e0b", "#3b82f6", "#ef4444", "#8b5cf6", "#64748b"];
                const slices = (data.sentiment ?? []).filter((s) => s.value > 0);
                const totalSent = slices.reduce((acc, s) => acc + s.value, 0);
                return (
                  <>
                    <div className="flex-1">
                      <h3 className="mb-2 text-sm font-semibold uppercase tracking-wider text-muted-foreground">Sentimentos</h3>
                      {totalSent === 0 ? (
                        <p className="text-xs text-muted-foreground py-4">Sem ligações classificadas neste período.</p>
                      ) : (
                        <ul className="space-y-2 text-xs font-medium">
                          {slices.map((s, i) => (
                            <li key={s.name} className="flex justify-between items-center">
                              <span className="flex items-center gap-2"><div className="w-2 h-2 rounded-full" style={{ backgroundColor: palette[i % palette.length] }} /> {s.name}</span>
                              {Math.round((s.value / totalSent) * 100)}%
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                    {totalSent > 0 && (
                      <div className="w-28 h-28 shrink-0">
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie data={slices} dataKey="value" nameKey="name" innerRadius={25} outerRadius={45} paddingAngle={2}>
                              {slices.map((_, i) => <Cell key={i} fill={palette[i % palette.length]} />)}
                            </Pie>
                            <Tooltip contentStyle={{ backgroundColor: 'rgba(0,0,0,0.8)', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff' }} />
                          </PieChart>
                        </ResponsiveContainer>
                      </div>
                    )}
                  </>
                );
              })()}
           </Card>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 pt-0 md:pt-2">
        {/* Audit & Compliance Log */}
        <Card className="p-5 bg-glass border border-border/50 flex flex-col">
           <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
             <ShieldAlert className="h-4 w-4 text-primary" /> Feed de Auditoria & Compliance <Badge variant="outline" className="ml-2 bg-primary/10 text-primary">Tempo Real</Badge>
           </h3>
           <div className="flex-1 space-y-2 overflow-y-auto custom-scrollbar pr-2 max-h-[300px]">
             {feedEvents.length === 0 ? (
               <div className="flex flex-col items-center justify-center py-10 text-center text-muted-foreground">
                 <ShieldAlert className="h-8 w-8 opacity-20 mb-2" />
                 <p className="text-sm">Nenhum evento de segurança recente.</p>
               </div>
             ) : (
               feedEvents.map((evt) => (
                  <div key={evt.id} className="group flex gap-3 items-center border border-border/20 bg-background/30 rounded-xl p-3 hover:bg-muted/40 transition-colors">
                    <div className={cn("h-2.5 w-2.5 rounded-full shrink-0", evt.type === 'success' ? 'bg-primary shadow-[0_0_8px_rgba(16,185,129,0.8)]' : evt.type === 'warn' ? 'bg-destructive shadow-[0_0_8px_rgba(239,68,68,0.8)]' : 'bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.8)]')} />
                    <div className="flex-1 min-w-0 flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                      <div>
                        <p className="text-[0.85rem] font-medium leading-tight">{evt.msg}</p>
                        <p className="text-[0.75rem] text-muted-foreground mt-0.5">Sessão: {evt.phone} • {evt.time}</p>
                      </div>
                      <Button variant="ghost" size="sm" onClick={() => setView("transcripts")} className="hidden sm:flex h-8 gap-1 opacity-0 group-hover:opacity-100 transition-opacity text-xs">
                        <FileText className="h-3 w-3" /> Investigar Log
                      </Button>
                    </div>
                 </div>
               ))
             )}
           </div>
        </Card>
      </div>

      <div className="pt-2 pb-6">
        <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
          <Globe2 className="h-4 h-4" /> Provedores Ativos na Sua Conta
        </h3>
        <p className="text-xs text-muted-foreground mb-4">Quem está respondendo por você agora — STT/LLM/TTS configurados nas suas Settings.</p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
           <Card className="p-4 bg-glass border border-border/50">
             <div className="flex items-center gap-2 mb-4">
                <Ear className="w-4 h-4 text-sky-500" />
                <h4 className="font-bold text-sm">Ouvir (STT)</h4>
             </div>
             <div className="text-sm font-semibold">{data.services.voice.stt_provider || "Não configurado"}</div>
             <p className="text-xs text-muted-foreground mt-1">Habilite e escolha em Voz & STT nas configurações.</p>
           </Card>

           <Card className="p-4 bg-glass border border-border/50">
             <div className="flex items-center gap-2 mb-4">
                <BrainCircuit className="w-4 h-4 text-emerald-500" />
                <h4 className="font-bold text-sm">Pensar (LLM)</h4>
             </div>
             <div className="text-sm font-semibold">{data.services.ai.provider || "—"}{data.services.ai.model ? ` · ${data.services.ai.model}` : ""}</div>
             <p className="text-xs text-muted-foreground mt-1">{data.services.ai.enabled ? "IA ativa" : "IA desativada"} — ajuste em Credenciais IA.</p>
           </Card>

           <Card className="p-4 bg-glass border border-border/50">
             <div className="flex items-center gap-2 mb-4">
                <Radio className="w-4 h-4 text-amber-500" />
                <h4 className="font-bold text-sm">Falar (TTS)</h4>
             </div>
             <div className="text-sm font-semibold">{data.services.voice.enabled ? "Sintetizador configurado" : "Não configurado"}</div>
             <p className="text-xs text-muted-foreground mt-1">A configuração detalhada por provedor entra em Voz & STT.</p>
           </Card>
        </div>
      </div>
    </div>
  );
}
