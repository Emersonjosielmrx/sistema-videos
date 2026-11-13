import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Calendar as CalendarIcon, Clock, CheckCircle2, List, CalendarX, KanbanSquare, LayoutPanelLeft, CalendarClock, CalendarDays, XCircle, Phone, Trash2, RefreshCcw, Plus, Settings, Sparkles, ListChecks, ShieldCheck } from "lucide-react";
import { Field } from "@/components/ui/field";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList } from "@/components/ui/tabs";
import { HideableTab } from "@/components/ui/HideableTab";
import { cn } from "@/lib/utils";
import { apiGet, apiPost, apiPut, apiDelete } from "@/lib/api";
import { logError } from "@/lib/log";
import { AgendaAnalytics } from "@/components/analytics/AgendaAnalytics";
import { AgendaSettings } from "@/components/settings/AgendaSettings";
import { PromisesManagerTab } from "@/components/settings/PromisesManagerTab";
import { setView } from "@/stores/navigation";

// AgendaPage — agendamentos (backend /api/agenda/*). Lista compromissos, mostra
// métricas, cria novos e move status. Kanban por status (pendente/confirmado/
// concluido/cancelado) + visão lista.

type Appointment = {
  id: string;
  name: string;
  whatsapp: string;
  start_at: string;
  status: string; // confirmado|pendente|concluido|cancelado|aguardando_pagamento
  service: string;
  notes: string;
  risk?: "high" | "low" | "none"; // Risco de no-show ou conflito
  synced?: boolean; // Sincronizado com Google/Outlook
};

const STATUS_COLS: { key: string; label: string; color: string }[] = [
  { key: "pendente", label: "PENDENTE", color: "text-amber-500 bg-amber-500" },
  { key: "confirmado", label: "CONFIRMADO", color: "text-sky-500 bg-sky-500" },
  { key: "concluido", label: "CONCLUÍDO", color: "text-emerald-500 bg-emerald-500" },
  { key: "cancelado", label: "CANCELADO", color: "text-destructive bg-destructive" },
];

const fmtDateTime = (iso: string) => {
  try { return new Date(iso).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }); }
  catch { return iso; }
};

export const AgendaPage = () => {
  const [viewMode, setViewMode] = useState<"list" | "kanban" | "analytics" | "settings" | "calendar" | "promises">("kanban");
  const [items, setItems] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  // Calendário mensal: mês exibido + células (null = espaço antes do dia 1).
  const [calMonth, setCalMonth] = useState(() => { const d = new Date(); return new Date(d.getFullYear(), d.getMonth(), 1); });
  const calDays = useMemo(() => {
    const first = new Date(calMonth.getFullYear(), calMonth.getMonth(), 1);
    const total = new Date(calMonth.getFullYear(), calMonth.getMonth() + 1, 0).getDate();
    const cells: (Date | null)[] = Array(first.getDay()).fill(null);
    for (let d = 1; d <= total; d++) cells.push(new Date(calMonth.getFullYear(), calMonth.getMonth(), d));
    return cells;
  }, [calMonth]);
  const [saving, setSaving] = useState(false);

  // form de novo agendamento
  const [fName, setFName] = useState("");
  const [fPhone, setFPhone] = useState("");
  const [fStart, setFStart] = useState("");
  const [fService, setFService] = useState("");
  const [fNotes, setFNotes] = useState("");

  const reload = () => {
    setLoading(true);
    apiGet<{ appointments: Appointment[] }>("/api/agenda/appointments")
      .then((r) => setItems(r.appointments ?? []))
      .catch(logError("/api/agenda/appointments"))
      .finally(() => setLoading(false));
  };
  useEffect(() => { reload(); }, []);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return items;
    return items.filter((a) => a.name.toLowerCase().includes(q) || a.whatsapp.includes(q));
  }, [items, search]);

  const byStatus = (status: string) => filtered.filter((a) => a.status === status);
  const todayCount = items.filter((a) => new Date(a.start_at).toDateString() === new Date().toDateString()).length;

  const create = async () => {
    if (!fName.trim() || !fStart) { toast.error("Preencha nome e data/hora"); return; }
    setSaving(true);
    try {
      await apiPost("/api/agenda/appointments", {
        name: fName, whatsapp: fPhone, start_at: new Date(fStart).toISOString(),
        service: fService, notes: fNotes,
      });
      toast.success("Compromisso agendado");
      setFName(""); setFPhone(""); setFStart(""); setFService(""); setFNotes("");
      setDialogOpen(false);
      reload();
    } catch (e) {
      const msg = (e as Error).message;
      toast.error(msg.includes("409") ? "Horário já ocupado" : "Falha ao agendar", { description: msg });
    } finally {
      setSaving(false);
    }
  };

  const setStatus = async (id: string, status: string) => {
    try { await apiPut(`/api/agenda/appointments/${id}/status`, { status }); reload(); }
    catch (e) { toast.error((e as Error).message); }
  };

  const remove = async (id: string) => {
    if (!confirm("Excluir este compromisso?")) return;
    try { await apiDelete(`/api/agenda/appointments/${id}`); reload(); }
    catch (e) { toast.error((e as Error).message); }
  };

  const ApptCard = ({ a }: { a: Appointment }) => (
    <Card className="group relative p-4 text-sm bg-glass border-border/50 shadow-soft space-y-3 hover:border-primary/50 transition-colors overflow-hidden">
      {/* Risk Indicator line */}
      {a.risk === "high" && <div className="absolute top-0 left-0 w-full h-1 bg-destructive"></div>}
      
      <div className="flex items-start justify-between">
        <div>
           <span className="font-bold truncate text-base flex items-center gap-2">
             {a.name}
             {a.risk === "high" && <span className="flex h-2 w-2 rounded-full bg-destructive animate-pulse" title="Risco de No-show / Conflito"></span>}
           </span>
           {a.whatsapp && <div className="flex items-center gap-1.5 text-xs text-muted-foreground mt-1"><Phone className="h-3 w-3" /> {a.whatsapp}</div>}
        </div>
        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
           <button onClick={() => remove(a.id)} className="h-7 w-7 flex items-center justify-center rounded-lg bg-destructive/10 text-destructive hover:bg-destructive hover:text-white transition-colors" aria-label="Excluir"><Trash2 className="h-3.5 w-3.5" /></button>
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-2 bg-background/50 p-2 rounded-lg border border-border/50">
         <div className="flex items-center gap-1.5 text-xs font-semibold text-foreground"><Clock className="h-3.5 w-3.5 text-primary" /> {fmtDateTime(a.start_at)}</div>
         <div className="flex items-center justify-end gap-1.5 text-[10px] text-muted-foreground">
            {a.synced ? (
              <span className="flex items-center gap-1 text-sky-500 font-medium"><CalendarClock className="h-3 w-3"/> Google Calendar</span>
            ) : (
              <span className="flex items-center gap-1 opacity-50"><CalendarX className="h-3 w-3"/> Não sincronizado</span>
            )}
         </div>
      </div>
      
      {a.service && <div className="text-xs text-muted-foreground font-medium flex items-center gap-1"><Sparkles className="h-3 w-3 text-amber-500"/> {a.service}</div>}
      
      <div className="flex items-center justify-between pt-2 border-t border-border/50">
        <div className="flex flex-wrap gap-1">
          {STATUS_COLS.filter((c) => c.key !== a.status).map((c) => (
            <button key={c.key} onClick={() => setStatus(a.id, c.key)} className="text-[0.65rem] font-medium px-2 py-1 rounded bg-muted/50 hover:bg-muted text-muted-foreground transition-colors">→ {c.label}</button>
          ))}
        </div>
        <Button variant="ghost" size="sm" className="h-6 text-[10px] text-primary" onClick={() => a.notes?.trim() ? toast.info("Dossiê do compromisso", { description: a.notes }) : toast.info("Sem observações neste compromisso.")}>Dossiê IA</Button>
      </div>
    </Card>
  );

  const getTabTitle = () => {
    switch(viewMode) {
      case "list": return "Agenda em Lista";
      case "kanban": return "Agenda Kanban";
      case "calendar": return "Calendário Geral";
      case "analytics": return "Analytics da Agenda";
      case "settings": return "Configurações da Agenda";
      case "promises": return "Promessas Detectadas";
      default: return "Booking Hub IA";
    }
  };

  const getTabDesc = () => {
    switch(viewMode) {
      case "list": return "Acompanhe seus compromissos em formato de lista estruturada.";
      case "kanban": return "Acompanhe seus compromissos pelas colunas de status.";
      case "calendar": return "Visão clássica de grade mensal e semanal.";
      case "analytics": return "Métricas e resultados dos agendamentos.";
      case "settings": return "Configure dias, horários e limites de agendamento.";
      case "promises": return "Retornos detectados pela IA — acompanhe e dispare ligações.";
      default: return "";
    }
  };

  return (
    <div className="space-y-6 max-w-[1200px] mx-auto pb-10 font-sans">
      {/* Cabeçalho Compacto Agenda */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-amber-500/10 via-background to-background border border-amber-500/20 p-4 shadow-glow flex flex-col md:flex-row md:items-center justify-between gap-4 mb-2">
        <div className="absolute top-0 right-0 p-2 opacity-5 pointer-events-none">
          <CalendarDays className="w-16 h-16 text-amber-500" />
        </div>
        <div className="relative z-10 flex items-center gap-3">
          <div className="hidden sm:flex items-center justify-center p-2 bg-amber-500/10 rounded-xl border border-amber-500/20 shadow-glow shrink-0">
            <img src="/inovareLogo.png" alt="Inovare Logo" className="w-8 h-8 object-contain drop-shadow-[0_0_8px_rgba(16,185,129,0.3)] rounded-full" onError={(e) => { e.currentTarget.style.display = 'none'; }} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-2xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-br from-amber-500 to-amber-400 drop-shadow-sm">
                {getTabTitle()}
              </h2>
              <Badge className="bg-amber-500/10 text-amber-500 border-amber-500/20 hidden md:inline-flex text-[10px] px-1.5 py-0">
                Hermes Call Inovare
              </Badge>
              <Badge className="bg-amber-500/10 text-amber-500 border-amber-500/20 hidden md:inline-flex text-[10px] px-1.5 py-0">
                Reuniões Automáticas
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              {getTabDesc()}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 relative z-10 shrink-0">
          <Button disabled variant="outline" className="h-9 rounded-xl text-xs gap-2 bg-glass border-border/50 hidden md:flex"><CalendarIcon className="h-4 w-4" /> Sync Calendar <Badge className="text-[9px] px-1 py-0 bg-primary/20 text-primary border-none ml-1">Em breve</Badge></Button>
          {/* Atalho pra aba Promessas (pedido do dono: "botão que encaminhe pra aba Promessas") */}
          <Button onClick={() => setView("promises")} variant="outline" className="h-9 rounded-xl text-xs gap-2 bg-glass border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10"><ShieldCheck className="h-4 w-4" /> Promessas</Button>
          <Button onClick={() => setDialogOpen(true)} className="h-9 rounded-xl text-xs shadow-glow bg-primary text-primary-foreground gap-1"><Plus className="h-4 w-4" /> Agendar</Button>
          <Button variant="outline" size="icon" className="h-9 w-9 rounded-xl bg-glass" onClick={reload}><RefreshCcw className="h-4 w-4" /></Button>
        </div>
      </div>

      <Tabs value={viewMode} onValueChange={(v: any) => setViewMode(v)} className="flex flex-col md:flex-row gap-6 w-full">
        <div className="w-full md:w-56 shrink-0">
          <TabsList className="flex flex-col h-auto bg-transparent items-stretch p-0 space-y-1">
            <HideableTab value="calendar" className="justify-start px-4 py-2.5 rounded-xl text-sm font-medium transition-all data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-glow hover:bg-muted/50 border border-transparent data-[state=active]:border-primary/20">
              <CalendarIcon className="h-4 w-4 mr-2" /> Meu Calendário
            </HideableTab>
            <HideableTab value="kanban" className="justify-start px-4 py-2.5 rounded-xl text-sm font-medium transition-all data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-glow hover:bg-muted/50 border border-transparent data-[state=active]:border-primary/20">
              <KanbanSquare className="h-4 w-4 mr-2" /> Kanban
            </HideableTab>
            <HideableTab value="list" className="justify-start px-4 py-2.5 rounded-xl text-sm font-medium transition-all data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-glow hover:bg-muted/50 border border-transparent data-[state=active]:border-primary/20">
              <LayoutPanelLeft className="h-4 w-4 mr-2" /> Lista
            </HideableTab>
            <HideableTab value="analytics" className="justify-start px-4 py-2.5 rounded-xl text-sm font-medium transition-all data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-glow hover:bg-muted/50 border border-transparent data-[state=active]:border-primary/20">
              <CalendarClock className="h-4 w-4 mr-2" /> Analytics
            </HideableTab>
            <HideableTab value="settings" className="justify-start px-4 py-2.5 rounded-xl text-sm font-medium transition-all data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-glow hover:bg-muted/50 border border-transparent data-[state=active]:border-primary/20">
              <Settings className="h-4 w-4 mr-2" /> Configurações
            </HideableTab>
            <HideableTab value="promises" className="justify-start px-4 py-2.5 rounded-xl text-sm font-medium transition-all data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-glow hover:bg-muted/50 border border-transparent data-[state=active]:border-primary/20">
              <ListChecks className="h-4 w-4 mr-2" /> Promessas
            </HideableTab>
          </TabsList>
        </div>

        <div className="flex-1 min-w-0 space-y-6">
          {/* Link público de agendamento: a página /book ainda não existe no servidor. Antes o
              painel mostrava e copiava "/book/sua-empresa" (404 pra quem abrisse). */}
          <Card className="p-5 bg-glass border-primary/30 shadow-soft flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h3 className="text-sm font-bold text-sky-400 mb-1">Link Público da Sua Agenda <Badge className="text-[9px] px-1 py-0 bg-primary/20 text-primary border-none ml-1">Em breve</Badge></h3>
              <p className="text-xs text-muted-foreground">Por enquanto, os agendamentos são feitos pelo agente de IA (WhatsApp/ligação) ou aqui no painel.</p>
            </div>
          </Card>

          <TabsContent value="analytics" className="m-0 focus-visible:outline-none">
            <AgendaAnalytics />
          </TabsContent>

          <TabsContent value="settings" className="m-0 focus-visible:outline-none">
            <AgendaSettings />
          </TabsContent>

          <TabsContent value="promises" className="m-0 focus-visible:outline-none">
            <PromisesManagerTab />
          </TabsContent>

          <TabsContent value="list" className="m-0 focus-visible:outline-none">
            {/* Métricas Compartilhadas List/Kanban */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
              <Card className="p-4 bg-glass border-border/50 flex flex-col items-center justify-center gap-2 shadow-soft">
                <div className="flex items-center gap-2 text-sky-400"><CalendarIcon className="h-5 w-5" /><span className="text-xl font-bold text-foreground">{todayCount}</span></div>
                <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Hoje</span>
              </Card>
              <Card className="p-4 bg-glass border-border/50 flex flex-col items-center justify-center gap-2 shadow-soft">
                <div className="flex items-center gap-2 text-fuchsia-400"><List className="h-5 w-5" /><span className="text-xl font-bold text-foreground">{items.length}</span></div>
                <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Agendamentos</span>
              </Card>
              <Card className="p-4 bg-glass border-border/50 flex flex-col items-center justify-center gap-2 shadow-soft">
                <div className="flex items-center gap-2 text-emerald-500"><CheckCircle2 className="h-5 w-5" /><span className="text-xl font-bold text-foreground">{items.filter((a) => a.status === "concluido").length}</span></div>
                <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Concluídos</span>
              </Card>
              <Card className="p-4 bg-glass border-border/50 flex flex-col items-center justify-center gap-2 shadow-soft">
                <div className="flex items-center gap-2 text-destructive"><XCircle className="h-5 w-5" /><span className="text-xl font-bold text-foreground">{items.filter((a) => a.status === "cancelado").length}</span></div>
                <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Cancelados</span>
              </Card>
            </div>

            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mt-4 mb-4">
              <h3 className="text-2xl font-bold flex items-center gap-2">Lista de Agendamentos <span className="h-2 w-2 rounded-full bg-emerald-500"></span></h3>
              <Input placeholder="Buscar nome ou WhatsApp" value={search} onChange={(e) => setSearch(e.target.value)} className="h-9 w-full md:w-72 rounded-xl bg-background text-sm" />
            </div>

            {loading ? (
              <p className="text-sm text-muted-foreground">Carregando…</p>
            ) : items.length === 0 ? (
              <Card className="p-16 flex flex-col items-center justify-center text-center text-muted-foreground bg-background/20 shadow-soft border-border/50">
                <CalendarX className="h-10 w-10 mb-3 opacity-20" />
                <p className="text-sm font-medium">Nenhum agendamento ainda. Clique em "Agendar".</p>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {filtered.map((a) => <ApptCard key={a.id} a={a} />)}
              </div>
            )}
          </TabsContent>

          <TabsContent value="kanban" className="m-0 focus-visible:outline-none">
            {/* Métricas Compartilhadas List/Kanban */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
              <Card className="p-4 bg-glass border-border/50 flex flex-col items-center justify-center gap-2 shadow-soft">
                <div className="flex items-center gap-2 text-sky-400"><CalendarIcon className="h-5 w-5" /><span className="text-xl font-bold text-foreground">{todayCount}</span></div>
                <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Hoje</span>
              </Card>
              <Card className="p-4 bg-glass border-border/50 flex flex-col items-center justify-center gap-2 shadow-soft">
                <div className="flex items-center gap-2 text-fuchsia-400"><List className="h-5 w-5" /><span className="text-xl font-bold text-foreground">{items.length}</span></div>
                <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Agendamentos</span>
              </Card>
              <Card className="p-4 bg-glass border-border/50 flex flex-col items-center justify-center gap-2 shadow-soft">
                <div className="flex items-center gap-2 text-emerald-500"><CheckCircle2 className="h-5 w-5" /><span className="text-xl font-bold text-foreground">{items.filter((a) => a.status === "concluido").length}</span></div>
                <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Concluídos</span>
              </Card>
              <Card className="p-4 bg-glass border-border/50 flex flex-col items-center justify-center gap-2 shadow-soft">
                <div className="flex items-center gap-2 text-destructive"><XCircle className="h-5 w-5" /><span className="text-xl font-bold text-foreground">{items.filter((a) => a.status === "cancelado").length}</span></div>
                <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Cancelados</span>
              </Card>
            </div>

            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mt-4 mb-4">
              <h3 className="text-2xl font-bold flex items-center gap-2">Quadro Kanban <span className="h-2 w-2 rounded-full bg-emerald-500"></span></h3>
              <Input placeholder="Buscar nome ou WhatsApp" value={search} onChange={(e) => setSearch(e.target.value)} className="h-9 w-full md:w-72 rounded-xl bg-background text-sm" />
            </div>

            {loading ? (
              <p className="text-sm text-muted-foreground">Carregando…</p>
            ) : items.length === 0 ? (
              <Card className="p-16 flex flex-col items-center justify-center text-center text-muted-foreground bg-background/20 shadow-soft border-border/50">
                <CalendarX className="h-10 w-10 mb-3 opacity-20" />
                <p className="text-sm font-medium">Nenhum agendamento ainda. Clique em "Agendar".</p>
              </Card>
            ) : (
              <div className="flex gap-4 overflow-x-auto pb-4 custom-scrollbar">
                {STATUS_COLS.map((col) => {
                  const list = byStatus(col.key);
                  return (
                    <Card key={col.key} className="flex w-72 shrink-0 flex-col bg-glass border-border/50 shadow-soft overflow-hidden rounded-2xl">
                      <div className="p-3 border-b border-border/50 flex justify-between items-center bg-background/50">
                        <h5 className={cn("text-[0.65rem] font-bold flex items-center gap-1", col.color.split(" ")[0])}><span className={cn("h-1.5 w-1.5 rounded-full", col.color.split(" ")[1])}></span> {col.label}</h5>
                        <Badge variant="secondary" className="h-5 px-1.5 text-[0.6rem]">{list.length}</Badge>
                      </div>
                      <div className="p-3 space-y-2 min-h-[100px]">
                        {list.length === 0 ? <div className="p-6 text-center text-xs text-muted-foreground">Vazio</div> : list.map((a) => <ApptCard key={a.id} a={a} />)}
                      </div>
                    </Card>
                  );
                })}
              </div>
            )}
          </TabsContent>
          
          <TabsContent value="calendar" className="m-0 focus-visible:outline-none">
             {/* Calendário mensal REAL (antes: "Novembro 2026" fixo, botões mortos, sem compromissos). */}
             <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mt-4 mb-4">
               <h3 className="text-2xl font-bold flex items-center gap-2 capitalize">{calMonth.toLocaleDateString("pt-BR", { month: "long", year: "numeric" })}</h3>
               <div className="flex items-center gap-2">
                 <Button variant="outline" size="sm" className="bg-background" onClick={() => { const d = new Date(); setCalMonth(new Date(d.getFullYear(), d.getMonth(), 1)); }}>Hoje</Button>
                 <Button variant="outline" size="icon" className="bg-background h-8 w-8" onClick={() => setCalMonth(new Date(calMonth.getFullYear(), calMonth.getMonth() - 1, 1))}>&lt;</Button>
                 <Button variant="outline" size="icon" className="bg-background h-8 w-8" onClick={() => setCalMonth(new Date(calMonth.getFullYear(), calMonth.getMonth() + 1, 1))}>&gt;</Button>
               </div>
             </div>
             <Card className="p-3 bg-glass shadow-soft border-border/50 overflow-x-auto">
               <div className="grid grid-cols-7 gap-1 min-w-[560px]">
                 {["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"].map((d) => (
                   <div key={d} className="text-center text-[11px] font-semibold text-muted-foreground py-1">{d}</div>
                 ))}
                 {calDays.map((day, i) => {
                   if (!day) return <div key={`vazio-${i}`} />;
                   const doDia = items
                     .filter((a) => new Date(a.start_at).toDateString() === day.toDateString())
                     .sort((x, y) => new Date(x.start_at).getTime() - new Date(y.start_at).getTime());
                   const hoje = day.toDateString() === new Date().toDateString();
                   return (
                     <div key={day.toISOString()} className={cn("min-h-[92px] rounded-lg border p-1.5 text-left", hoje ? "border-primary/60 bg-primary/5" : "border-border/40 bg-background/40")}>
                       <div className={cn("text-xs font-semibold mb-1", hoje ? "text-primary" : "text-muted-foreground")}>{day.getDate()}</div>
                       {doDia.slice(0, 3).map((a) => (
                         <div key={a.id} title={`${a.name} — ${a.service || ""}`} className={cn("truncate text-[10px] rounded px-1 py-0.5 mb-0.5", a.status === "cancelado" ? "bg-destructive/10 text-destructive line-through" : "bg-primary/10 text-foreground")}>
                           {new Date(a.start_at).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })} {a.name}
                         </div>
                       ))}
                       {doDia.length > 3 && <div className="text-[10px] text-muted-foreground">+{doDia.length - 3} mais</div>}
                     </div>
                   );
                 })}
               </div>
             </Card>
          </TabsContent>
        </div>
      </Tabs>

      {/* Dialog novo agendamento */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-2xl bg-glass border-border/50 shadow-glow">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2"><CalendarIcon className="w-5 h-5 text-primary"/> Novo Agendamento (Booking Hub)</DialogTitle>
          </DialogHeader>
          <div className="space-y-6 mt-2">
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Field label="Nome do cliente"><Input value={fName} onChange={(e) => setFName(e.target.value)} className="rounded-xl bg-background" /></Field>
              <Field label="WhatsApp"><Input value={fPhone} onChange={(e) => setFPhone(e.target.value)} placeholder="5511999998888" className="rounded-xl bg-background" /></Field>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Field label="Data e hora fixada"><Input type="datetime-local" value={fStart} onChange={(e) => setFStart(e.target.value)} className="rounded-xl bg-background" /></Field>
              <Field label="Serviço"><Input value={fService} onChange={(e) => setFService(e.target.value)} placeholder="Ex.: Mentoria Estratégica" className="rounded-xl bg-background" /></Field>
            </div>
            <Field label="Observações de Contexto (Dossiê)"><Input value={fNotes} onChange={(e) => setFNotes(e.target.value)} className="rounded-xl bg-background" placeholder="O que a IA precisa saber sobre essa reunião?" /></Field>
            
            {/* Workflows — os lembretes são automáticos no servidor para todo compromisso
                confirmado/pendente (não há liga/desliga por agendamento). Texto honesto em
                vez de switches que não controlavam nada. */}
            <div>
               <h4 className="text-sm font-bold mb-3">Automações Pré/Pós Reunião</h4>
               <div className="space-y-2 text-xs text-muted-foreground">
                 <div className="flex items-center gap-2 p-3 border border-border/50 rounded-lg bg-background/50">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                    Lembrete automático no WhatsApp 24h antes de cada reunião confirmada.
                 </div>
                 <div className="flex items-center gap-2 p-3 border border-border/50 rounded-lg bg-background/50">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                    Lembrete automático 1h antes da reunião.
                 </div>
               </div>
            </div>

          </div>
          <DialogFooter className="border-t border-border/50 pt-4 mt-4">
            <Button variant="outline" onClick={() => setDialogOpen(false)} className="rounded-xl">Cancelar</Button>
            <Button onClick={create} disabled={saving} className="rounded-xl shadow-glow gap-2">
               <CalendarIcon className="w-4 h-4"/> {saving ? "Processando…" : "Agendar Reunião"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};
