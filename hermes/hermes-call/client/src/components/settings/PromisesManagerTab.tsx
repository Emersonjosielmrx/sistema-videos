import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  ListTodo, CheckCircle2, Clock, CalendarDays, UserSquare2,
  PhoneCall, X, Loader2, Bot, RotateCcw, Repeat,
} from "lucide-react";
import { apiGet, apiPost, apiDelete, apiErrorMessage, apiErrorStatus } from "@/lib/api";
import { cn } from "@/lib/utils";

type ScheduledCall = {
  id: string;
  user_id: string;
  contact_jid: string;
  contact_number: string;
  contact_name: string;
  scheduled_at: string; // RFC3339
  // awaiting_confirmation = a IA detectou uma promessa e espera você confirmar antes de ligar.
  status: "awaiting_confirmation" | "pending" | "dispatched" | "completed" | "cancelled" | "failed" | "expired" | "archived";
  source: "auto_detected" | "manual";
  promise_text: string;
  agent_id?: string;
  audio_ref?: string;
  greeting?: string;
  dispatch_campaign_id?: string;
  last_error?: string;
  created_at: string;
  updated_at: string;
  dispatched_at?: string;
  result?: "answered" | "no_answer" | "no_connect" | ""; // como foi a ligação
  attempts?: number; // quantas vezes tentou ligar
};

type ListResp = {
  items: ScheduledCall[];
  pending_count: number;
  total_count: number;
};

const fmtDate = (iso: string) => {
  try {
    const d = new Date(iso);
    return d.toLocaleString("pt-BR", {
      day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit",
      timeZone: "America/Sao_Paulo",
    });
  } catch {
    return iso;
  }
};

const statusLabel: Record<ScheduledCall["status"], string> = {
  awaiting_confirmation: "Aguardando sua confirmação",
  pending: "Pendente",
  dispatched: "Disparada",
  completed: "Concluída",
  cancelled: "Cancelada",
  failed: "Falhou",
  expired: "Expirada",
  archived: "Arquivada",
};

const statusColor: Record<ScheduledCall["status"], string> = {
  awaiting_confirmation: "bg-violet-500/10 text-violet-400 border-violet-500/30",
  pending: "bg-amber-500/10 text-amber-500 border-amber-500/30",
  dispatched: "bg-blue-500/10 text-blue-500 border-blue-500/30",
  completed: "bg-emerald-500/10 text-emerald-500 border-emerald-500/30",
  cancelled: "bg-zinc-500/10 text-zinc-400 border-zinc-500/30",
  failed: "bg-red-500/10 text-red-500 border-red-500/30",
  expired: "bg-orange-500/10 text-orange-400 border-orange-500/30",
  archived: "bg-zinc-500/10 text-zinc-500 border-zinc-500/30",
};

const resultLabel: Record<string, { text: string; cls: string }> = {
  answered: { text: "Atendeu", cls: "text-emerald-500" },
  no_answer: { text: "Não atendeu", cls: "text-amber-500" },
  no_connect: { text: "Não conectou", cls: "text-red-400" },
};

// Mensagem amigável quando o servidor ainda não tem a ação nova (404).
const actionError = (e: unknown, fallback: string) =>
  apiErrorStatus(e) === 404 ? "Esta ação fica disponível depois da próxima atualização do servidor." : apiErrorMessage(e, fallback);

export const PromisesManagerTab = () => {
  const [items, setItems] = useState<ScheduledCall[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | ScheduledCall["status"]>("pending");
  const [awaitingCount, setAwaitingCount] = useState(0);
  const [busyId, setBusyId] = useState<string | null>(null);

  // form de criação manual
  const [showForm, setShowForm] = useState(false);
  const [formName, setFormName] = useState("");
  const [formNumber, setFormNumber] = useState("");
  const [formWhen, setFormWhen] = useState(""); // datetime-local string
  const [formGreeting, setFormGreeting] = useState("");
  const [formPromise, setFormPromise] = useState("");
  const [saving, setSaving] = useState(false);

  const load = async () => {
    try {
      setLoading(true);
      const status = filter === "all" ? "" : filter;
      const q = status ? `?status=${status}` : "";
      const data = await apiGet<ListResp>(`/api/scheduled_calls${q}`);
      setItems(data.items ?? []);
      // Quantas esperam confirmação (aparece em destaque mesmo em outro filtro).
      if (filter === "awaiting_confirmation") setAwaitingCount((data.items ?? []).length);
      else apiGet<ListResp>("/api/scheduled_calls?status=awaiting_confirmation")
        .then((r) => setAwaitingCount((r.items ?? []).filter((i) => i.status === "awaiting_confirmation").length))
        .catch(() => setAwaitingCount(0));
    } catch (e: any) {
      toast.error("Falha ao carregar promessas: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [filter]);

  const handleCancel = async (id: string) => {
    if (!confirm("Cancelar este agendamento? A ligação não será disparada.")) return;
    try {
      await apiDelete(`/api/scheduled_calls/${id}`);
      toast.success("Agendamento cancelado");
      load();
    } catch (e: any) {
      toast.error("Falha ao cancelar: " + e.message);
    }
  };

  // Confirma uma promessa detectada pela IA (vira agendamento pendente).
  const handleConfirm = async (id: string) => {
    setBusyId(id);
    try {
      await apiPost(`/api/scheduled_calls/${id}/confirm`, {});
      toast.success("Confirmado. A ligação será feita no horário marcado.");
      load();
    } catch (e) {
      toast.error("Não consegui confirmar", { description: actionError(e, "Tente de novo em instantes.") });
    } finally {
      setBusyId(null);
    }
  };

  // Tenta de novo uma ligação que falhou ou expirou.
  const handleRetry = async (id: string) => {
    setBusyId(id);
    try {
      await apiPost(`/api/scheduled_calls/${id}/retry`, {});
      toast.success("Nova tentativa agendada.");
      load();
    } catch (e) {
      toast.error("Não consegui tentar de novo", { description: actionError(e, "Tente de novo em instantes.") });
    } finally {
      setBusyId(null);
    }
  };

  const handleCallNow = async (id: string) => {
    try {
      await apiPost(`/api/scheduled_calls/${id}/now`, {});
      toast.success("Ligação agendada para disparar em ~1 min. Avisarei no Telegram.");
      load();
    } catch (e: any) {
      toast.error("Falha ao disparar: " + e.message);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formNumber.trim() || !formWhen.trim()) {
      toast.error("Número e horário são obrigatórios");
      return;
    }
    setSaving(true);
    try {
      // datetime-local → ISO com offset local (-03:00 fixo SP, simplificação).
      const isoLocal = formWhen; // "2026-07-21T08:00"
      const isoWithTZ = isoLocal + ":00-03:00";
      await apiPost("/api/scheduled_calls", {
        contact_name: formName,
        contact_number: formNumber.replace(/\D/g, ""),
        scheduled_at: isoWithTZ,
        greeting: formGreeting,
        promise_text: formPromise,
      });
      toast.success("Agendamento criado");
      setShowForm(false);
      setFormName(""); setFormNumber(""); setFormWhen("");
      setFormGreeting(""); setFormPromise("");
      load();
    } catch (e: any) {
      toast.error("Falha ao criar: " + e.message);
    } finally {
      setSaving(false);
    }
  };

  const pendingCount = items.filter((i) => i.status === "pending").length;
  const totalCount = items.length;

  return (
    <div className="w-full max-w-5xl mx-auto space-y-6 animate-in fade-in zoom-in-95 duration-500">

      {/* Header */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 p-6 rounded-2xl bg-gradient-to-r from-rose-500/10 to-pink-500/10 border border-rose-500/20 shadow-[0_0_30px_rgba(244,63,94,0.15)] relative overflow-hidden">
        <div className="absolute -right-10 -top-10 opacity-10 pointer-events-none">
          <ListTodo className="w-40 h-40 text-rose-500" />
        </div>
        <div className="flex items-center gap-4 relative z-10">
          <div className="bg-rose-500/20 p-3 rounded-xl border border-rose-500/30">
            <CalendarDays className="h-8 w-8 text-rose-500" />
          </div>
          <div>
            <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-rose-400 to-pink-400 drop-shadow-sm">
              Gestão de Promessas
            </h2>
            <p className="text-sm text-rose-500/80 font-medium">
              O que a IA prometeu ao cliente — e quando o Hermes vai ligar de volta.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3 relative z-10 flex-wrap justify-end">
          {awaitingCount > 0 && (
            <button type="button" onClick={() => setFilter("awaiting_confirmation")}>
              <Badge variant="outline" className="bg-violet-500/10 text-violet-400 border-violet-500/30 text-sm py-1 px-3 hover:bg-violet-500/20">
                {awaitingCount} aguardando sua confirmação
              </Badge>
            </button>
          )}
          <Badge variant="outline" className="bg-amber-500/10 text-amber-500 border-amber-500/30 text-sm py-1 px-3">
            {pendingCount} pendentes
          </Badge>
          <Button onClick={() => setShowForm((v) => !v)} className="bg-rose-500 hover:bg-rose-600 gap-2">
            {showForm ? <X className="h-4 w-4" /> : <CalendarDays className="h-4 w-4" />}
            {showForm ? "Fechar" : "Agendar manualmente"}
          </Button>
        </div>
      </div>

      {/* Form de criação */}
      {showForm && (
        <Card className="p-5 bg-black/30 border-rose-500/20">
          <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-muted-foreground">Nome do cliente</label>
              <Input value={formName} onChange={(e) => setFormName(e.target.value)} placeholder="João Silva" />
            </div>
            <div>
              <label className="text-xs text-muted-foreground">Número (com DDI)</label>
              <Input value={formNumber} onChange={(e) => setFormNumber(e.target.value)} placeholder="5511996002434" />
            </div>
            <div>
              <label className="text-xs text-muted-foreground">Quando ligar</label>
              <Input type="datetime-local" value={formWhen} onChange={(e) => setFormWhen(e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-muted-foreground">Saudação (vazio = padrão)</label>
              <Input value={formGreeting} onChange={(e) => setFormGreeting(e.target.value)} placeholder='Ex: "Oi João, sou Hermes, ligando conforme combinamos"' />
            </div>
            <div className="md:col-span-2">
              <label className="text-xs text-muted-foreground">Prometido (contexto)</label>
              <Input value={formPromise} onChange={(e) => setFormPromise(e.target.value)} placeholder='Ex: "Cliente pediu pra ligar amanhã 8h"' />
            </div>
            <div className="md:col-span-2 flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setShowForm(false)}>Cancelar</Button>
              <Button type="submit" disabled={saving} className="bg-rose-500 hover:bg-rose-600 gap-2">
                {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <CalendarDays className="h-4 w-4" />}
                Criar agendamento
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Filtros */}
      <div className="flex gap-2 flex-wrap">
        {(["awaiting_confirmation", "pending", "dispatched", "completed", "failed", "expired", "cancelled", "archived", "all"] as const).map((f) => (
          <Button
            key={f}
            variant={filter === f ? "default" : "outline"}
            size="sm"
            onClick={() => setFilter(f)}
          >
            {f === "all" ? "Todos" : statusLabel[f]}
          </Button>
        ))}
      </div>

      {/* Lista */}
      {loading ? (
        <div className="flex justify-center py-12"><Loader2 className="h-6 w-6 animate-spin text-rose-500" /></div>
      ) : items.length === 0 ? (
        <Card className="p-8 text-center text-muted-foreground bg-black/20 border-border/40">
          {filter === "awaiting_confirmation"
            ? "Nada aguardando sua confirmação."
            : <>Nenhuma promessa {filter === "pending" ? "pendente" : `com status "${filter === "all" ? "Todos" : (statusLabel[filter] || filter)}"`}.</>}
          {filter === "pending" && " A IA cria automaticamente quando o cliente fala palavras como 'agendar', 'marcar' ou 'me liga amanhã'."}
        </Card>
      ) : (
        <div className="space-y-4">
          {items.map((p) => (
            <Card key={p.id} className={cn("p-6 backdrop-blur-md shadow-soft transition-all",
              p.status === "pending" || p.status === "awaiting_confirmation" ? "bg-black/20 border-border/50" : "bg-black/10 border-border/30 opacity-80")}>
              <div className="flex flex-col md:flex-row items-start justify-between gap-4">
                <div className="flex-1 space-y-3">
                  <div className="flex flex-wrap items-center gap-3">
                    <Badge variant="outline" className={cn("text-xs py-1 px-2", statusColor[p.status] || "bg-muted text-muted-foreground")}>
                      {statusLabel[p.status] || p.status}
                    </Badge>
                    {p.result && resultLabel[p.result] && (
                      <span className={cn("text-xs font-semibold", resultLabel[p.result].cls)}>{resultLabel[p.result].text}</span>
                    )}
                    {(p.attempts ?? 0) > 0 && (
                      <span className="flex items-center gap-1 text-xs text-muted-foreground" title="Tentativas de ligação">
                        <Repeat className="h-3 w-3" /> {p.attempts} {p.attempts === 1 ? "tentativa" : "tentativas"}
                      </span>
                    )}
                    <div className="flex items-center gap-1.5 text-sm text-muted-foreground bg-muted/50 px-2.5 py-1 rounded-md">
                      <UserSquare2 className="h-4 w-4" /> {p.contact_name || p.contact_number}
                    </div>
                    <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3" /> {fmtDate(p.scheduled_at)}
                    </div>
                    {p.source === "auto_detected" && (
                      <div className="flex items-center gap-1.5 text-xs bg-violet-500/10 text-violet-400 border border-violet-500/20 px-2 py-0.5 rounded">
                        <Bot className="h-3 w-3" /> auto-detectada
                      </div>
                    )}
                  </div>
                  {p.promise_text && (
                    <div>
                      <p className="text-sm font-bold text-foreground">Prometido:</p>
                      <p className="text-base mt-1 text-rose-100">"{p.promise_text}"</p>
                    </div>
                  )}
                  {p.last_error && (
                    <p className="text-xs text-red-400">⚠️ {p.last_error}</p>
                  )}
                </div>

                <div className="shrink-0 flex items-center gap-2 mt-2 md:mt-0">
                  {p.status === "awaiting_confirmation" && (
                    <>
                      <Button size="sm" className="h-10 text-xs gap-2 bg-violet-600 hover:bg-violet-500 text-white"
                        disabled={busyId === p.id} onClick={() => handleConfirm(p.id)}>
                        {busyId === p.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />} Confirmar
                      </Button>
                      <Button variant="outline" size="sm" className="h-10 text-xs gap-2 hover:bg-white/5"
                        disabled={busyId === p.id} onClick={() => handleCancel(p.id)}>
                        <X className="h-4 w-4" /> Descartar
                      </Button>
                    </>
                  )}
                  {(p.status === "failed" || p.status === "expired") && (
                    <Button variant="outline" size="sm" className="h-10 text-xs gap-2 hover:bg-white/5"
                      disabled={busyId === p.id} onClick={() => handleRetry(p.id)}>
                      {busyId === p.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <RotateCcw className="h-4 w-4" />} Tentar de novo
                    </Button>
                  )}
                  {p.status === "pending" && (
                    <>
                      <Button variant="outline" size="sm" className="h-10 text-xs border-dashed gap-2 hover:bg-white/5"
                        onClick={() => handleCallNow(p.id)}>
                        <PhoneCall className="h-4 w-4" /> Ligar agora
                      </Button>
                      <Button variant="outline" size="sm" className="h-10 text-xs gap-2 hover:bg-white/5"
                        onClick={() => handleCancel(p.id)}>
                        <X className="h-4 w-4" /> Cancelar
                      </Button>
                    </>
                  )}
                  {p.status === "dispatched" && p.dispatch_campaign_id && (
                    <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/30 text-xs">
                      campanha {p.dispatch_campaign_id.slice(0, 8)}
                    </Badge>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      <p className="text-xs text-muted-foreground text-center pt-4">
        Total: {totalCount} agendamentos. Pendentes disparam automaticamente no horário via ticker interno.
      </p>
    </div>
  );
};