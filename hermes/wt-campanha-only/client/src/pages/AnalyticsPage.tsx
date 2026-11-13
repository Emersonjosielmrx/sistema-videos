import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { getAnalytics, getWeeklyReport } from "@/services/security";
import { getCallAnalytics, type CallAnalytics } from "@/services/broadcast";
import { PhoneCall, PhoneMissed, XCircle, Ear, Star, Clock, Megaphone } from "lucide-react";
import { apiGet } from "@/lib/api";
import type { DailyStat, WeeklyReport } from "@/types/security";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

type CampaignConversion = {
  campaign_id: string;
  total: number;
  interested: number;
  callback: number;
  not_interested: number;
  wrong_number: number;
  conversion_pct: number;
};

type VariantConversion = {
  variant: string;
  total: number;
  interested: number;
  conversion_pct: number;
};


function fmtDuration(sec: number) {
  if (sec < 60) return `${sec}s`;
  const m = Math.floor(sec / 60);
  if (m < 60) return `${m}min ${sec % 60}s`;
  return `${Math.floor(m / 60)}h ${m % 60}min`;
}

export function AnalyticsPage({ days = 7 }: { days?: number }) {
  const [daily, setDaily] = useState<DailyStat[]>([]);
  const [, setAvgMs] = useState(0);
  const [, setReport] = useState<WeeklyReport | null>(null);
  const [calls, setCalls] = useState<CallAnalytics | null>(null);
  const [conv, setConv] = useState<CampaignConversion[]>([]);
  const [variants, setVariants] = useState<VariantConversion[]>([]);
  const [costPerCall, setCostPerCall] = useState(0);
  const [, setHourly] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getAnalytics(days).catch(() => ({ daily: [], hourly: [], avg_response_ms: 0 })),
      getWeeklyReport().catch(() => null),
      getCallAnalytics().catch(() => null),
      apiGet<{ campaigns: CampaignConversion[]; variants: VariantConversion[]; total_cost_brl: number; total_calls: number }>("/api/analytics/conversion").catch(() => ({ campaigns: [], variants: [], total_cost_brl: 0, total_calls: 0 })),
    ])
      .then(([analytics, weekly, callStats, conversion]) => {
        setDaily(analytics.daily || []);
        setAvgMs(analytics.avg_response_ms || 0);
        setHourly(analytics.hourly || []);
        setReport(weekly);
        setCalls(callStats);
        setConv(conversion.campaigns ?? []);
        setVariants(conversion.variants ?? []);
        setCostPerCall(conversion.total_calls > 0 ? conversion.total_cost_brl / conversion.total_calls : 0);
      })
      .catch(() => toast.error("Erro ao carregar analytics"))
      .finally(() => setLoading(false));
  }, [days]);

  if (loading) {
    return <div className="flex items-center justify-center h-64">Carregando...</div>;
  }

  return (
    <div className="space-y-6 pt-2">

      {/* Métricas de CAMPANHAS DE CHAMADA (o que a dona pediu) */}
      <div>
        <h2 className="text-lg font-semibold flex items-center gap-2 mb-3">
          <Megaphone className="h-5 w-5 text-primary" /> Campanhas de Chamada
        </h2>
        {calls && calls.total_calls > 0 ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <MetricCard icon={PhoneCall} tint="text-sky-500" label="Ligações" value={calls.total_calls} sub={`${calls.total_campaigns} campanhas`} />
            <MetricCard icon={Ear} tint="text-amber-500" label="Escuta média" value={`${calls.avg_listen_pct}%`} sub={`${calls.full_listen} ouviram tudo`} />
            <MetricCard icon={Star} tint="text-emerald-500" label="Interessados" value={calls.interested} sub="disseram sim" />
            <MetricCard icon={Clock} tint="text-primary" label="Tempo total ouvido" value={fmtDuration(calls.total_listen_sec)} sub="soma de todos" />
            <MetricCard icon={PhoneMissed} tint="text-orange-500" label="Não atenderam" value={calls.no_answer} sub="" />
          </div>
        ) : (
          <Card><CardContent className="py-8 text-center text-muted-foreground text-sm">
            Nenhuma campanha de chamada ainda. Dispare uma pela aba Contatos → Ligar em Massa → Campanha com áudio.
          </CardContent></Card>
        )}
      </div>

      <Separator />

      {/* Summary cards removidos pois já estão lá em cima no CostHubPage (Total, Tempo de resposta, etc) */}

      <Separator />

      {/* 1. Funil de Conversão Resumido (Substitui Tabela de Campanhas) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="flex flex-col">
          <CardHeader><CardTitle>Funil de Conversão Geral</CardTitle></CardHeader>
          <CardContent className="flex-1">
            {conv.length === 0 ? (
              <div className="flex h-full items-center justify-center text-sm text-muted-foreground pb-4">
                Ainda não há conversões registradas nestes {days} dias.
              </div>
            ) : (
              <div className="space-y-4 pt-2">
                {(() => {
                  const tot = conv.reduce((acc, c) => acc + c.total, 0);
                  const interested = conv.reduce((acc, c) => acc + c.interested, 0);
                  const callbacks = conv.reduce((acc, c) => acc + c.callback, 0);
                  const notInterested = conv.reduce((acc, c) => acc + c.not_interested, 0);
                  const totalCost = conv.reduce((acc, c) => acc + (c.total * costPerCall), 0);
                  
                  return (
                    <>
                      <div className="flex justify-between items-center bg-muted/50 p-3 rounded-lg border">
                        <div className="text-sm font-medium">1. Total de Ligações</div>
                        <div className="font-bold text-lg">{tot}</div>
                      </div>
                      <div className="flex justify-between items-center bg-muted/50 p-3 rounded-lg border ml-2 sm:ml-4">
                        <div className="text-sm font-medium flex items-center gap-2"><Ear className="h-4 w-4 text-primary shrink-0" /> <span className="truncate">2. Atendidas (Ouviram)</span></div>
                        <div className="font-bold text-lg shrink-0">{calls?.answered ?? 0}</div>
                      </div>
                      <div className="flex justify-between items-center bg-green-500/10 border-green-500/30 p-3 rounded-lg border ml-4 sm:ml-8">
                        <div className="text-sm font-medium text-green-600 dark:text-green-500 flex items-center gap-2"><Star className="h-4 w-4 shrink-0" /> <span className="truncate">3. Interessados (Hot Leads)</span></div>
                        <div className="font-bold text-lg text-green-600 dark:text-green-500 shrink-0">{interested} <span className="text-xs font-normal opacity-70">({tot > 0 ? Math.round((interested/tot)*100) : 0}%)</span></div>
                      </div>
                      <div className="flex justify-between items-center bg-sky-500/10 border-sky-500/30 p-3 rounded-lg border ml-6 sm:ml-12">
                        <div className="text-sm font-medium text-sky-600 dark:text-sky-500 flex items-center gap-2"><Clock className="h-4 w-4 shrink-0" /> <span className="truncate">4. Retornos Agendados</span></div>
                        <div className="font-bold text-lg text-sky-600 dark:text-sky-500 shrink-0">{callbacks}</div>
                      </div>

                      <div className="mt-4 flex flex-col sm:flex-row gap-2 sm:gap-4 text-xs text-muted-foreground px-2">
                        <div className="flex items-center gap-1"><XCircle className="h-3 w-3 shrink-0" /> {notInterested} sem interesse</div>
                        <div className="flex items-center gap-1">Custo estimado da conversão: {totalCost.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}</div>
                      </div>
                    </>
                  );
                })()}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Teste A/B — qual variante de áudio converte mais */}
        <Card>
          <CardHeader><CardTitle>Performance das Variantes (Teste A/B)</CardTitle></CardHeader>
          <CardContent>
            {variants.length > 0 ? (
              <div className="space-y-4">
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  {variants.map((v) => (
                    <div key={v.variant} className="rounded-lg border p-4 bg-muted/20">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold text-sm">Variante {v.variant}</span>
                        <span className="text-xl font-bold text-green-500">{v.conversion_pct.toFixed(0)}%</span>
                      </div>
                      <div className="w-full bg-muted rounded-full h-1.5 mb-2">
                        <div className="bg-green-500 h-1.5 rounded-full" style={{ width: `${v.conversion_pct}%` }}></div>
                      </div>
                      <p className="text-xs text-muted-foreground">{v.interested} leads em {v.total} ligações</p>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-muted-foreground pt-2 border-t">A variante com maior % converte melhor — use esse áudio nas próximas campanhas.</p>
              </div>
            ) : (
               <div className="flex h-full items-center justify-center text-sm text-muted-foreground pb-4">
                Sem testes A/B no momento.
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 2. Gráfico de Evolução Diária (Substitui Tabela) */}
      <Card>
        <CardHeader>
          <CardTitle>Interações no Tempo (Últimos {days} dias)</CardTitle>
        </CardHeader>
        <CardContent>
          {daily.length > 0 ? (
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={daily} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorMsgs" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorCalls" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} opacity={0.2} />
                  <XAxis dataKey="date" tick={{fontSize: 12}} tickLine={false} axisLine={false} />
                  <YAxis tick={{fontSize: 12}} tickLine={false} axisLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: 'rgba(0,0,0,0.8)', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff' }}
                    itemStyle={{ color: '#fff' }}
                  />
                  <Area type="monotone" name="Mensagens (Total)" dataKey={(d) => d.messages_in + d.messages_out} stroke="#3b82f6" fillOpacity={1} fill="url(#colorMsgs)" />
                  <Area type="monotone" name="Ligações (Total)" dataKey={(d) => d.calls_in + d.calls_out} stroke="#10b981" fillOpacity={1} fill="url(#colorCalls)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="flex items-center justify-center h-48 text-muted-foreground text-sm">
              Sem dados suficientes para gerar o gráfico.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Indicadores Adicionais que foram pedidos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
         <Card className="flex flex-col">
          <CardHeader><CardTitle>Rejeição & Retenção</CardTitle></CardHeader>
          <CardContent className="flex-1 space-y-4">
             <div className="flex items-center justify-between">
               <div className="text-sm">Tempo médio de escuta (Ligação)</div>
               <div className="font-bold">{calls?.avg_listen_pct ?? 0}%</div>
             </div>
             <div className="w-full bg-muted rounded-full h-2">
               <div className="bg-amber-500 h-2 rounded-full" style={{ width: `${calls?.avg_listen_pct ?? 0}%` }}></div>
             </div>
             
             <div className="flex items-center justify-between pt-4">
               <div className="text-sm text-destructive flex items-center gap-2"><PhoneMissed className="h-4 w-4"/> Taxa de Rejeição (Caixa postal)</div>
               <div className="font-bold text-destructive">
                 {calls && calls.total_calls > 0 ? Math.round(((calls.failed + calls.no_answer) / calls.total_calls) * 100) : 0}%
               </div>
             </div>
          </CardContent>
        </Card>
      </div>

    </div>
  );
}

function MetricCard({ icon: Icon, tint, label, value, sub }: { icon: React.ElementType; tint: string; label: string; value: number | string; sub: string }) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center gap-2">
          <Icon className={`h-4 w-4 ${tint}`} />
          <span className="text-xs text-muted-foreground">{label}</span>
        </div>
        <p className={`mt-1 text-2xl font-bold ${tint}`}>{value}</p>
        {sub && <p className="text-xs text-muted-foreground">{sub}</p>}
      </CardContent>
    </Card>
  );
}

export default AnalyticsPage;
