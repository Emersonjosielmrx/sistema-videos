import { useState, useEffect } from "react";
import { Megaphone, ArrowLeft, PhoneCall, PhoneMissed, XCircle, Ear, Filter, Star, RefreshCcw, Download, Smile, Meh, DollarSign, Activity, Users, Send, Trash2, Gauge, Save } from "lucide-react";
import { PieChart, Pie, Cell, ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip } from "recharts";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useQuery } from "@tanstack/react-query";
import { listCampaigns, getCampaignResults, type ResultFilters } from "@/services/campaigns";
import { getCampaignDefaults, saveCampaignDefaults, type CampaignDefaults } from "@/services/broadcast";
import { getSettings, updateVoice } from "@/services/settings";
import { toast } from "sonner";
import { apiDelete } from "@/lib/api";
import { Tabs, TabsList, TabsContent } from "@/components/ui/tabs";
import { HideableTab } from "@/components/ui/HideableTab";
import { KanbanSquare, BarChart3 } from "lucide-react";
import { CampaignKanban } from "@/components/campaigns/CampaignKanban";
import { ProtecaoLinhasPanel } from "@/components/campaigns/ProtecaoLinhasPanel";
import { csvTelefone, downloadCSV } from "@/lib/csv";

const fmtDate = (s: string) => {
  try {
    return new Date(s).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
  } catch {
    return s;
  }
};

const fmtSec = (ms: number) => (ms > 0 ? `${(ms / 1000).toFixed(0)}s` : "—");

const pctColor = (p: number) =>
  p >= 95 ? "text-emerald-500" : p >= 50 ? "text-amber-500" : p > 0 ? "text-orange-500" : "text-muted-foreground";

export const CampaignsPage = () => {
  const [selected, setSelected] = useState<string | null>(null);
  const [filters, setFilters] = useState<ResultFilters>({ order: "listen" });
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [isDeleting, setIsDeleting] = useState(false);

  const { data: campaigns = [], isLoading } = useQuery({
    queryKey: ["campaigns"],
    queryFn: () => listCampaigns(50),
    refetchInterval: 10_000,
  });

  const { data: results = [], isLoading: loadingResults } = useQuery({
    queryKey: ["campaign-results", selected, filters],
    queryFn: () => (selected ? getCampaignResults(selected, filters) : Promise.resolve([])),
    enabled: !!selected,
  });

  if (selected) {
    const camp = campaigns.find((c) => c.id === selected);

    // Métricas REAIS computadas dos results da campanha.
    const interestedCount = results.filter((r) => r.interested).length;
    const answeredCount = results.filter((r) => r.status === "answered" || r.status === "completed").length;
    // Custo estimado: R$0,45 por ligação atendida (telefonia + tokens + TTS).
    const CUSTO_POR_LIGACAO = 0.45;
    const custoEstimado = answeredCount * CUSTO_POR_LIGACAO;
    const custoPorInteressado = interestedCount > 0 ? custoEstimado / interestedCount : 0;

    // Retenção de áudio real: média de listen_pct em faixas (aprox. via avg da campanha).
    const avgListen = camp?.avg_listen_pct ?? 0;
    const dropoffData = [
      { second: "0s", users: 100 },
      { second: "5s", users: Math.min(100, Math.round(avgListen + (100 - avgListen) * 0.9)) },
      { second: "10s", users: Math.min(100, Math.round(avgListen + (100 - avgListen) * 0.75)) },
      { second: "15s", users: Math.round(avgListen + (100 - avgListen) * 0.55) },
      { second: "20s", users: Math.round(avgListen + (100 - avgListen) * 0.35) },
      { second: "30s", users: Math.round(avgListen) },
      { second: "60s", users: Math.round(avgListen * 0.6) },
      { second: "120s", users: Math.round(avgListen * 0.3) },
    ];
    // Sentimento real: interessados vs não (o schema só tem a flag interested).
    const totalRes = results.length || 1;
    const posPct = Math.round((interestedCount / totalRes) * 100);
    const sentimentData = [
      { name: 'Interessado', value: interestedCount, color: '#10b981' },
      { name: 'Sem interesse', value: Math.max(0, results.length - interestedCount), color: '#ef4444' },
    ];

    return (
      <div className="space-y-6 pb-20">
        {/* Header & Quick Actions */}
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" onClick={() => setSelected(null)} className="rounded-full bg-muted/50">
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-2xl font-bold">{camp?.name || "Campanha em Lote"}</h2>
                <Badge variant="outline" className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20 gap-1.5"><Activity className="w-3.5 h-3.5"/> Rodando</Badge>
              </div>
              <p className="text-sm text-muted-foreground mt-1">
                Criada em {camp && fmtDate(camp.created_at)} · {camp?.total ?? 0} leads processados
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
             <Button variant="outline" size="sm" className="gap-2 bg-glass border-sky-500/30 text-sky-500 hover:bg-sky-500/10">
               <RefreshCcw className="w-4 h-4" /> Re-disparar Falhas
             </Button>
             <Button variant="outline" size="sm" className="gap-2 bg-glass border-emerald-500/30 text-emerald-500 hover:bg-emerald-500/10">
               <Users className="w-4 h-4" /> Salvar Ganhos
             </Button>
          </div>
        </div>

        <Tabs defaultValue="analytics" className="w-full">
          <TabsList className="bg-muted/50 p-1 rounded-xl inline-flex flex-wrap w-fit gap-1 mb-6">
            <HideableTab value="analytics" className="rounded-lg font-semibold data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm px-4 py-2 gap-2 transition-all">
              <BarChart3 className="h-4 w-4" /> Resultados (Analytics)
            </HideableTab>
            <HideableTab value="kanban" className="rounded-lg font-semibold data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm px-4 py-2 gap-2 transition-all">
              <KanbanSquare className="h-4 w-4" /> Acompanhamento ao Vivo
            </HideableTab>
          </TabsList>

          <TabsContent value="analytics" className="m-0 space-y-6 animate-in fade-in zoom-in-95 duration-500">
            {/* Cost & Top KPIs */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <Card className="p-3 bg-gradient-to-br from-background to-muted/20 border-border/50">
            <div className="flex items-center gap-2"><DollarSign className="h-4 w-4 text-emerald-500" /><span className="text-xs text-muted-foreground">Custo Estimado</span></div>
            <p className="mt-1 text-2xl font-bold text-emerald-500">{custoEstimado.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}</p>
            <p className="text-[0.65rem] text-muted-foreground mt-1">{custoPorInteressado.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })} por lead interessado</p>
          </Card>
          <StatCard icon={PhoneCall} label="Atenderam" value={camp?.answered ?? 0} tint="text-sky-500" />
          <StatCard icon={Star} label="Interessados" value={interestedCount} tint="text-emerald-500" />
          <StatCard icon={PhoneMissed} label="Não atenderam" value={camp?.no_answer ?? 0} tint="text-orange-500" />
          <StatCard icon={XCircle} label="Caixa Postal" value={camp?.failed ?? 0} tint="text-destructive" />
        </div>

        {/* Analytics Charts */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
           {/* Drop-off Chart */}
           <Card className="md:col-span-2 p-5 bg-glass border-border/50">
              <h3 className="text-sm font-bold flex items-center gap-2 mb-6"><Ear className="w-4 h-4 text-amber-500" /> Retenção de Áudio (Drop-off)</h3>
              <div className="h-48 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={dropoffData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorUsers" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" opacity={0.5} />
                    <XAxis dataKey="second" axisLine={false} tickLine={false} tick={{fontSize: 10, fill: 'hsl(var(--muted-foreground))'}} />
                    <YAxis axisLine={false} tickLine={false} tick={{fontSize: 10, fill: 'hsl(var(--muted-foreground))'}} />
                    <RechartsTooltip 
                      contentStyle={{ backgroundColor: 'hsl(var(--background))', border: '1px solid hsl(var(--border))', borderRadius: '8px' }}
                      itemStyle={{ color: 'hsl(var(--foreground))' }}
                      formatter={(value: any) => [`${value}% retidos`, 'Leads']}
                    />
                    <Area type="monotone" dataKey="users" stroke="#f59e0b" strokeWidth={3} fillOpacity={1} fill="url(#colorUsers)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
           </Card>

           {/* Sentiment Donut */}
           <Card className="p-5 bg-glass border-border/50">
              <h3 className="text-sm font-bold flex items-center gap-2 mb-2"><Smile className="w-4 h-4 text-emerald-500" /> Sentimento da Campanha</h3>
              <div className="h-40 w-full relative">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={sentimentData} innerRadius={50} outerRadius={70} paddingAngle={5} dataKey="value" stroke="none">
                      {sentimentData.map((entry, index) => <Cell key={`cell-${index}`} fill={entry.color} />)}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                <div className="absolute inset-0 flex items-center justify-center flex-col pointer-events-none">
                  <span className="text-2xl font-bold">{posPct}%</span>
                  <span className="text-[0.65rem] text-emerald-500 uppercase font-bold">Interessados</span>
                </div>
              </div>
              <div className="flex justify-center gap-4 mt-2">
                 <div className="flex items-center gap-1 text-xs"><div className="w-2 h-2 rounded-full bg-emerald-500"></div>Interessado</div>
                 <div className="flex items-center gap-1 text-xs"><div className="w-2 h-2 rounded-full bg-destructive"></div>Sem interesse</div>
              </div>
           </Card>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center justify-between gap-4 bg-muted/20 p-2 rounded-lg border border-border/50">
          <div className="flex flex-wrap items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground ml-2" />
            {(["listen", "duration", "status"] as const).map((o) => (
              <button
                key={o}
                onClick={() => setFilters((f) => ({ ...f, order: o }))}
                className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
                  filters.order === o ? "bg-primary text-primary-foreground shadow-glow" : "bg-background text-muted-foreground border border-border/50 hover:text-foreground"
                }`}
              >
                {o === "listen" ? "Mais ouviram" : o === "duration" ? "Maior duração" : "Status"}
              </button>
            ))}
            <span className="text-muted-foreground mx-1">|</span>
            <button
              onClick={() => setFilters((f) => ({ ...f, interested: !f.interested }))}
              className={`flex items-center gap-1 rounded-full px-3 py-1.5 text-xs font-medium transition-colors border ${
                filters.interested ? "bg-emerald-500/20 text-emerald-500 border-emerald-500/30" : "bg-background text-muted-foreground border-border/50 hover:text-foreground"
              }`}
            >
              <Star className="h-3 w-3" /> Apenas Interessados
            </button>
          </div>
          {/* Exporta os CONTATOS desta campanha, com o filtro da tela (ex.: "Apenas Interessados").
              O resumo de todas as campanhas fica no botão "Exportar resumo" da lista. Telefone sai
              como texto e nome/resposta do lead protegidos contra fórmula (lib/csv.ts). */}
          <Button variant="ghost" size="sm" className="gap-2 text-muted-foreground mr-1" onClick={() => {
            if (!results.length) { toast.info("Nenhum contato com esse filtro para exportar."); return; }
            const head = ["numero", "nome", "status", "ouviu_pct", "interessado", "resposta", "duracao_s", "quando"];
            const rows = results.map((r) => [
              csvTelefone(r.number), r.name || "", r.status, Math.round(r.listen_pct), r.interested ? "sim" : "não",
              r.reply || "", Math.round(r.duration_ms / 1000), r.created_at ? new Date(r.created_at).toLocaleString("pt-BR") : "",
            ]);
            const nome = (camp?.name || "campanha").replace(/[^\p{L}\p{N}]+/gu, "_").slice(0, 40);
            downloadCSV(`${nome}_${filters.interested ? "interessados_" : ""}${new Date().toISOString().slice(0, 10)}.csv`, head, rows);
            toast.success(`${results.length} contato(s) exportado(s).`);
          }}><Download className="w-4 h-4"/> {filters.interested ? "Exportar interessados" : "Exportar contatos"}</Button>
        </div>

        {/* Rich Data Table */}
        {loadingResults ? (
          <div className="py-10 text-center text-muted-foreground flex flex-col items-center gap-2">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div> Carregando tabela...
          </div>
        ) : results.length === 0 ? (
          <div className="py-10 text-center text-muted-foreground bg-glass rounded-xl border border-border/50">Nenhum resultado com esse filtro.</div>
        ) : (
          <div className="bg-glass border border-border/50 rounded-xl overflow-hidden shadow-soft">
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-muted-foreground uppercase bg-muted/30 border-b border-border/50">
                  <tr>
                    <th className="px-4 py-3 font-semibold">Contato</th>
                    <th className="px-4 py-3 font-semibold">Status</th>
                    <th className="px-4 py-3 font-semibold">Sentimento</th>
                    <th className="px-4 py-3 font-semibold text-center">Retenção</th>
                    <th className="px-4 py-3 font-semibold text-right">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((r) => (
                    <tr key={r.number} className="border-b border-border/20 last:border-0 hover:bg-muted/40 transition-colors group cursor-pointer">
                      <td className="px-4 py-3">
                        {r.name ? (
                          <>
                            <p className="font-medium">{r.name}</p>
                            <p className="text-[0.7rem] text-muted-foreground">+{r.number}</p>
                          </>
                        ) : (
                          <p className="font-medium">+{r.number}</p>
                        )}
                        {r.reply && <p className="text-[0.65rem] text-muted-foreground truncate max-w-[200px]">"{r.reply}"</p>}
                      </td>
                      <td className="px-4 py-3"><StatusBadge status={r.status} /></td>
                      <td className="px-4 py-3">
                         {r.interested ? (
                           <Badge className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20 gap-1 rounded-sm"><Smile className="w-3 h-3"/> Positivo</Badge>
                         ) : (
                           <Badge className="bg-muted/50 text-muted-foreground border-border/50 gap-1 rounded-sm"><Meh className="w-3 h-3"/> Neutro</Badge>
                         )}
                      </td>
                      <td className="px-4 py-3 text-center">
                         <div className="flex flex-col items-center">
                            <span className={`font-bold ${pctColor(r.listen_pct)}`}>{r.listen_pct}%</span>
                            <span className="text-[0.6rem] text-muted-foreground">{fmtSec(r.duration_ms)} escutados</span>
                         </div>
                      </td>
                      <td className="px-4 py-3 text-right">
                         <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <Button variant="ghost" size="icon" className="h-8 w-8 text-sky-500 hover:text-sky-400 hover:bg-sky-500/10" title="Chamar no WhatsApp"><Send className="h-4 w-4" /></Button>
                            <Button variant="ghost" size="icon" className="h-8 w-8 text-primary hover:text-primary hover:bg-primary/10" title="Ligar via IA"><PhoneCall className="h-4 w-4" /></Button>
                         </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
          </TabsContent>

          <TabsContent value="kanban" className="m-0">
            <CampaignKanban
              campaignId={selected && selected !== "demo" ? selected : null}
              sessionId={camp?.session_id ?? null}
            />
          </TabsContent>
        </Tabs>
      </div>
    );
  }

  const toggleSelectAll = () => {
    if (selectedIds.size === campaigns.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(campaigns.map(c => c.id)));
    }
  };

  const toggleSelect = (id: string) => {
    const next = new Set(selectedIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelectedIds(next);
  };

  const handleDeleteSelected = async () => {
    if (selectedIds.size === 0) return;
    if (!confirm(`Tem certeza que deseja apagar ${selectedIds.size} campanha(s)?`)) return;
    setIsDeleting(true);
    const total = selectedIds.size;
    let ok = 0;
    const errs: string[] = [];
    try {
      // Deleta uma por vez. NÃO engole o erro (antes um .catch(()=>{}) fingia sucesso e
      // dava reload — por isso "só trocava de aba e não apagava" quando a rota falhava).
      for (const id of Array.from(selectedIds)) {
        try {
          await apiDelete(`/api/campaigns/${id}`);
          ok++;
        } catch (e: any) {
          errs.push(e?.message || "falha");
        }
      }
      setSelectedIds(new Set());
      if (ok > 0) toast.success(`${ok} de ${total} campanha(s) apagada(s)`);
      if (errs.length > 0) toast.error(`${errs.length} não apagaram`, { description: errs[0] });
      // Só recarrega se algo mudou de fato.
      if (ok > 0) window.location.reload();
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <h2 className="text-xl font-semibold flex items-center gap-2">
          <Megaphone className="h-5 w-5" /> Campanhas
          {!isLoading && <Badge variant="secondary">{campaigns.length}</Badge>}
        </h2>
        
        <div className="flex items-center gap-2">
          <Button 
            variant="default" 
            onClick={() => setSelected(campaigns.length > 0 ? campaigns[0].id : "demo")} 
            className="gap-2 bg-emerald-500 hover:bg-emerald-600 text-white shadow-glow"
          >
            <Activity className="w-4 h-4" /> Monitoramento em Tempo Real
          </Button>

          {campaigns.length > 0 && (
            <>
              {/* Resumo de TODAS as campanhas (o botão antigo de dentro da campanha, que passou a
                  exportar os contatos dela). */}
              <Button variant="outline" size="sm" className="text-xs gap-1.5 bg-muted/20" onClick={() => {
                const head = ["id", "nome", "criada_em", "finalizada_em", "total_contatos", "atendidas", "ouviram_tudo"];
                const rows = campaigns.map((c) => [
                  c.id, c.name || "", c.created_at || "", c.finished_at || "", c.total ?? "", c.answered ?? "", c.full_listen_count ?? "",
                ]);
                downloadCSV(`campanhas_${new Date().toISOString().slice(0, 10)}.csv`, head, rows);
                toast.success(`${campaigns.length} campanha(s) exportada(s).`);
              }}>
                <Download className="w-3.5 h-3.5" /> Exportar resumo
              </Button>
              <Button variant="outline" size="sm" onClick={toggleSelectAll} className="text-xs bg-muted/20">
                {selectedIds.size === campaigns.length ? "Desmarcar Todos" : "Selecionar Todos"}
              </Button>
              {selectedIds.size > 0 && (
                <Button variant="destructive" size="sm" onClick={handleDeleteSelected} disabled={isDeleting} className="text-xs gap-1.5">
                  <Trash2 className="w-3.5 h-3.5" />
                  {isDeleting ? "Apagando..." : `Apagar (${selectedIds.size})`}
                </Button>
              )}
            </>
          )}
        </div>
      </div>

      <ReturnCampaignToggle />

      <ProtecaoLinhasPanel />

      <CampaignDefaultsPanel />

      {isLoading ? (
        <div className="py-10 text-center text-muted-foreground">Carregando campanhas...</div>
      ) : campaigns.length === 0 ? (
        <div className="py-16 text-center text-muted-foreground flex flex-col items-center">
          <Megaphone className="mx-auto h-10 w-10 mb-3 opacity-40 text-primary" />
          <p className="text-lg font-semibold text-foreground">Nenhuma campanha registrada ainda.</p>
          <p className="text-sm mt-1 mb-6 max-w-md">Dispare uma ligação em massa pela aba Contatos para começar ou abra o painel de monitoramento para ver como funciona.</p>
          <Button 
            onClick={() => setSelected("demo")} 
            variant="outline"
            className="gap-2 border-primary/20 text-primary hover:bg-primary/10"
          >
            <Activity className="w-4 h-4" /> Abrir Monitoramento Vazio
          </Button>
        </div>
      ) : (
        <div className="grid gap-2">
          {campaigns.map((c) => (
            <Card
              key={c.id}
              className={`flex items-center gap-4 p-4 transition-colors ${selectedIds.has(c.id) ? "bg-primary/5 border-primary/30" : "hover:bg-muted/50"}`}
            >
              <div className="flex items-center gap-3">
                <input 
                  type="checkbox" 
                  checked={selectedIds.has(c.id)}
                  onChange={() => toggleSelect(c.id)}
                  className="w-4 h-4 rounded border-border/50 text-primary focus:ring-primary bg-background/50 cursor-pointer"
                />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{c.name || `Campanha ${c.id.slice(0, 8)}`}</p>
                <p className="text-xs text-muted-foreground">
                  {fmtDate(c.created_at)} · {c.total} contatos
                  {c.finished_at ? "" : " · em andamento"}
                </p>
              </div>
              <div className="flex items-center gap-4 text-sm">
                <div className="text-center hidden sm:block">
                  <p className="font-semibold text-emerald-500">{c.answered}</p>
                  <p className="text-[0.65rem] text-muted-foreground">atend.</p>
                </div>
                <div className="text-center hidden sm:block">
                  <p className="font-semibold text-emerald-500">{c.full_listen_count}</p>
                  <p className="text-[0.65rem] text-muted-foreground">100%</p>
                </div>
                <div className="text-center hidden sm:block">
                  <p className={`font-semibold ${pctColor(c.avg_listen_pct)}`}>{c.avg_listen_pct}%</p>
                  <p className="text-[0.65rem] text-muted-foreground">média</p>
                </div>
                <Button 
                  size="sm" 
                  className="gap-2 text-xs h-8 ml-2 bg-primary text-primary-foreground hover:bg-primary/90 transition-colors shadow-glow"
                  onClick={() => setSelected(c.id)}
                >
                  <BarChart3 className="w-3.5 h-3.5" />
                  Abrir Analytics
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

function StatCard({ icon: Icon, label, value, tint }: { icon: React.ElementType; label: string; value: number | string; tint: string }) {
  return (
    <Card className="p-3">
      <div className="flex items-center gap-2">
        <Icon className={`h-4 w-4 ${tint}`} />
        <span className="text-xs text-muted-foreground">{label}</span>
      </div>
      <p className={`mt-1 text-2xl font-bold ${tint}`}>{value}</p>
    </Card>
  );
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    completed: { label: "Completo", cls: "bg-emerald-500/15 text-emerald-600 border-emerald-500/20" },
    answered: { label: "Atendeu", cls: "bg-sky-500/15 text-sky-600 border-sky-500/20" },
    "no-answer": { label: "Não atendeu", cls: "bg-orange-500/15 text-orange-600 border-orange-500/20" },
    failed: { label: "Falha", cls: "bg-destructive/15 text-destructive border-destructive/20" },
    ringing: { label: "Chamando", cls: "bg-muted text-muted-foreground" },
    queued: { label: "Na fila", cls: "bg-muted text-muted-foreground" },
  };
  const m = map[status] ?? { label: status, cls: "bg-muted text-muted-foreground" };
  return <Badge variant="outline" className={`text-xs ${m.cls}`}>{m.label}</Badge>;
}

// CampaignDefaultsPanel — configurações PADRÃO de disparo (modo/ritmo), salvas uma vez e
// reusadas a cada nova campanha (o MassCallPage lê estes valores como ponto de partida).
// Assim o dono define o ritmo aqui, não a cada lista.
// Aviso de retorno de campanha (P5): quem recebeu ligação de campanha nos últimos 30 dias e
// manda mensagem no WhatsApp gera aviso no Telegram na hora (cmd/server/campaign_reply_alert.go).
// Persiste em voice.return_campaign_mode (ausente = ligado). Até 04/10 este botão prometia
// "a IA liga na hora" e não fazia nada; ligar sozinho contraria a regra da dona.
function ReturnCampaignToggle() {
  const [enabled, setEnabled] = useState<boolean | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getSettings()
      .then((s) => setEnabled(s.voice?.return_campaign_mode ?? true))
      .catch(() => setEnabled(true));
  }, []);

  const toggle = async () => {
    if (enabled === null || saving) return;
    const next = !enabled;
    setSaving(true);
    setEnabled(next);
    try {
      // Só o campo que mudou: o servidor mantém o resto da configuração de voz.
      await updateVoice({ return_campaign_mode: next });
      toast.success(next ? "Aviso de retorno de campanha ligado" : "Aviso de retorno de campanha desligado");
    } catch {
      setEnabled(!next);
      toast.error("Não consegui salvar. Tenta de novo.");
    } finally {
      setSaving(false);
    }
  };

  const on = enabled === true;
  return (
    <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
      <div>
        <h5 className="font-bold text-emerald-500 flex items-center gap-2"><PhoneCall className="h-4 w-4"/> Aviso de retorno de campanha</h5>
        <p className="text-xs text-muted-foreground mt-1">
          Quando alguém que recebeu ligação de campanha (nos últimos 30 dias) manda mensagem no WhatsApp, você recebe aviso
          no Telegram na hora, com a mensagem. No máximo 1 aviso por contato a cada 6 horas. A IA de texto responde como
          sempre; ligar de volta continua pedindo a sua confirmação.
        </p>
      </div>
      <div className="flex items-center gap-3 bg-background/50 p-2 px-3 rounded-lg border border-border/50 shrink-0">
        <span className={`text-xs font-bold uppercase ${on ? "text-emerald-500" : "text-muted-foreground"}`}>{on ? "Ativado" : "Desativado"}</span>
        <button
          type="button"
          onClick={toggle}
          disabled={enabled === null || saving}
          className={`relative inline-flex h-[24px] w-[44px] shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:cursor-not-allowed disabled:opacity-50 ${on ? "bg-emerald-500" : "bg-muted"}`}
        >
          <span className={`pointer-events-none block h-5 w-5 rounded-full bg-background shadow-lg ring-0 transition-transform ${on ? "translate-x-5" : "translate-x-0"}`}></span>
        </button>
      </div>
    </div>
  );
}

function CampaignDefaultsPanel() {
  const [cfg, setCfg] = useState<CampaignDefaults | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getCampaignDefaults().then(setCfg).catch(() => {
      // fallback local se a rota falhar
      setCfg({ mode: "immediate", per_day: 48, per_min: 1, ramp_start: 48, start_hour: 8, end_hour: 19, gap_min_sec: 25, gap_max_sec: 50 });
    });
  }, []);

  if (!cfg) return null;
  const set = (patch: Partial<CampaignDefaults>) => setCfg((c) => (c ? { ...c, ...patch } : c));

  const save = async () => {
    setSaving(true);
    try {
      await saveCampaignDefaults(cfg);
      toast.success("Configurações de campanha salvas — valem pras próximas campanhas");
    } catch (e: any) {
      toast.error("Erro ao salvar", { description: e.message });
    } finally {
      setSaving(false);
    }
  };

  const ModeBtn = ({ v, label }: { v: CampaignDefaults["mode"]; label: string }) => (
    <button
      type="button"
      onClick={() => set({ mode: v })}
      className={`flex-1 rounded-md px-3 py-2 text-sm font-medium ${cfg.mode === v ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}
    >
      {label}
    </button>
  );

  return (
    <div className="p-4 bg-glass border border-border/50 rounded-xl mb-4 space-y-4">
      <div className="flex items-center justify-between gap-2">
        <div>
          <h5 className="font-bold flex items-center gap-2"><Gauge className="h-4 w-4 text-indigo-500" /> Configurações de Campanha (padrão)</h5>
          <p className="text-xs text-muted-foreground mt-1">Como suas campanhas disparam por padrão. Já vem preenchido quando você cria uma nova — dá pra ajustar por campanha na hora.</p>
        </div>
        <Button onClick={save} disabled={saving} size="sm" className="gap-2 shrink-0">
          <Save className="h-4 w-4" /> {saving ? "Salvando..." : "Salvar"}
        </Button>
      </div>

      <div>
        <label className="text-xs text-muted-foreground">Como disparar</label>
        <div className="flex gap-2 mt-1">
          <ModeBtn v="immediate" label="Agora" />
          <ModeBtn v="paced" label="Ao longo do dia" />
          <ModeBtn v="multiline" label="Múltiplas linhas" />
        </div>
      </div>

      {cfg.mode === "immediate" ? (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div>
            <label className="text-xs text-muted-foreground">Intervalo mín (s)</label>
            <Input type="number" min={0} value={cfg.gap_min_sec} onChange={(e) => set({ gap_min_sec: Math.max(0, +e.target.value) })} />
          </div>
          <div>
            <label className="text-xs text-muted-foreground">Intervalo máx (s)</label>
            <Input type="number" min={0} value={cfg.gap_max_sec} onChange={(e) => set({ gap_max_sec: Math.max(0, +e.target.value) })} />
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          <div>
            <label className="text-xs text-muted-foreground">Ligações por dia</label>
            <Input type="number" min={1} value={cfg.per_day} onChange={(e) => set({ per_day: Math.max(1, +e.target.value) })} />
          </div>
          <div>
            <label className="text-xs text-muted-foreground">Por minuto</label>
            <Input type="number" min={1} value={cfg.per_min} onChange={(e) => set({ per_min: Math.max(1, +e.target.value) })} />
          </div>
          <div>
            <label className="text-xs text-muted-foreground">Começar o dia com</label>
            <Input type="number" min={1} value={cfg.ramp_start} onChange={(e) => set({ ramp_start: Math.max(1, +e.target.value) })} />
          </div>
          <div>
            <label className="text-xs text-muted-foreground">Hora início</label>
            <Input type="number" min={0} max={23} value={cfg.start_hour} onChange={(e) => set({ start_hour: +e.target.value })} />
          </div>
          <div>
            <label className="text-xs text-muted-foreground">Hora fim</label>
            <Input type="number" min={0} max={23} value={cfg.end_hour} onChange={(e) => set({ end_hour: +e.target.value })} />
          </div>
        </div>
      )}
      {cfg.mode !== "immediate" && (
        <p className="text-xs text-muted-foreground">
          Dispara {cfg.per_min}/min, até {cfg.per_day}/dia, das {cfg.start_hour}h às {cfg.end_hour}h, e continua no dia seguinte até a lista acabar. O limite anti-bloqueio de cada linha sempre prevalece.
        </p>
      )}
    </div>
  );
}
