import { useState, useEffect, useRef } from "react";
import { PhoneCall, PhoneOutgoing, CheckCircle2, XCircle, User, Loader2, Pause, Play } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { getCampaignResults } from "@/services/campaigns";
import { pauseBroadcast, resumeBroadcast } from "@/services/broadcast";
import { eventStream } from "@/lib/event-stream";
import { logError } from "@/lib/log";

// CampaignKanban — quadro EM TEMPO REAL da fila de discagem. Carrega o estado persistido
// da campanha (/results, já com push name) e move os cards conforme os eventos SSE que o
// backend emite por número (campaign_progress: queued→ringing→answered→completed/no-answer/
// failed). Sem dados simulados: se não houver campanha selecionada, mostra vazio honesto.

type Lead = {
  number: string;
  name?: string;
  status: string; // queued|ringing|answered|completed|no-answer|no-connect|failed|skipped|sent
};

// Agrupamento visual das colunas por família de status.
const isPending = (s: string) => s === "queued";
const isActive = (s: string) => s === "ringing" || s === "answered";
const isDone = (s: string) => s === "completed" || s === "answered" || s === "sent";
const isFailed = (s: string) => s === "no-answer" || s === "no-connect" || s === "failed" || s === "skipped";

const statusLabel: Record<string, string> = {
  queued: "Na fila",
  ringing: "Tocando…",
  answered: "Atendeu",
  completed: "Concluída",
  "no-answer": "Não atendeu",
  "no-connect": "Não completou",
  failed: "Falhou",
  skipped: "Pulado",
  sent: "Enviada",
};

export function CampaignKanban({ campaignId, sessionId }: { campaignId?: string | null; sessionId?: string | null }) {
  const [leads, setLeads] = useState<Record<string, Lead>>({});
  const [loading, setLoading] = useState(false);
  const [paused, setPaused] = useState(false);
  const [pausedReason, setPausedReason] = useState<string>("");
  const [busy, setBusy] = useState(false);
  // Ref pra o handler SSE sempre enxergar o campaignId atual sem re-assinar.
  const campRef = useRef<string | null>(campaignId ?? null);
  campRef.current = campaignId ?? null;

  const doPause = async () => {
    if (!sessionId || !campaignId) return;
    setBusy(true);
    try { await pauseBroadcast(sessionId, campaignId); setPaused(true); setPausedReason("manual"); toast.success("Campanha pausada"); }
    catch (e) { toast.error((e as Error).message); }
    finally { setBusy(false); }
  };
  const doResume = async () => {
    if (!sessionId || !campaignId) return;
    setBusy(true);
    try { await resumeBroadcast(sessionId, campaignId); setPaused(false); setPausedReason(""); toast.success("Campanha retomada"); }
    catch (e) { toast.error((e as Error).message); }
    finally { setBusy(false); }
  };

  // Carrega o estado inicial (persistido) da campanha selecionada.
  useEffect(() => {
    if (!campaignId) {
      setLeads({});
      return;
    }
    setLoading(true);
    getCampaignResults(campaignId, {})
      .then((rows) => {
        const map: Record<string, Lead> = {};
        for (const r of rows) {
          map[r.number] = { number: r.number, name: r.name, status: r.status };
        }
        setLeads(map);
      })
      .catch(logError("CampaignKanban"))
      .finally(() => setLoading(false));
  }, [campaignId]);

  // Escuta os eventos ao vivo e move os cards. O backend manda {campaignId, number, status}.
  useEffect(() => {
    const off = eventStream.on((ev: any) => {
      if (!ev || !campRef.current) return;
      if (ev.campaignId !== campRef.current) return;
      // Eventos de pausa/retomada (inclui auto-pausa por ligação prioritária).
      if (ev.type === "campaign_paused") { setPaused(true); setPausedReason(ev.reason || "manual"); return; }
      if (ev.type === "campaign_resumed") { setPaused(false); setPausedReason(""); return; }
      // Evento por número (tem number+status). Ignora os agregados (campaign_start/done).
      if (!ev.number || !ev.status) return;
      setLeads((prev) => {
        const cur = prev[ev.number];
        return {
          ...prev,
          [ev.number]: {
            number: ev.number,
            name: ev.name || cur?.name,
            status: ev.status,
          },
        };
      });
    });
    return off;
  }, []);

  if (!campaignId) {
    return (
      <Card className="p-10 flex flex-col items-center justify-center text-center gap-3 border-dashed">
        <PhoneCall className="w-8 h-8 text-muted-foreground" />
        <p className="text-sm text-muted-foreground max-w-md">
          Selecione uma campanha na aba <span className="font-semibold">Resultados</span> para
          acompanhar a fila de discagem em tempo real aqui.
        </p>
      </Card>
    );
  }

  const all = Object.values(leads);
  const pending = all.filter((l) => isPending(l.status));
  const active = all.filter((l) => isActive(l.status));
  const done = all.filter((l) => isDone(l.status) && !isActive(l.status));
  const failed = all.filter((l) => isFailed(l.status));

  const Column = ({
    title, icon, tint, items, emptyHint,
  }: { title: string; icon: React.ReactNode; tint: string; items: Lead[]; emptyHint: string }) => (
    <div className="flex flex-col gap-3 bg-muted/20 p-4 rounded-xl border border-border/50 min-h-[420px]">
      <div className="flex items-center justify-between mb-1">
        <h3 className={`font-bold text-sm flex items-center gap-2 ${tint}`}>{icon} {title}</h3>
        <Badge variant="outline">{items.length}</Badge>
      </div>
      {items.length === 0 ? (
        <p className="text-[11px] text-muted-foreground/70 mt-2">{emptyHint}</p>
      ) : (
        items.map((lead) => (
          <Card key={lead.number} className="p-3 bg-glass border-border/50 shadow-soft">
            <div className="flex items-center gap-2">
              <div className="p-1.5 bg-primary/10 text-primary rounded-md">
                <User className="w-4 h-4" />
              </div>
              <div className="min-w-0">
                <p className="text-xs font-semibold text-foreground leading-tight truncate">
                  {lead.name || `+${lead.number}`}
                </p>
                {lead.name && <p className="text-[10px] text-muted-foreground">+{lead.number}</p>}
              </div>
            </div>
            <div className="mt-2">
              <span className="text-[10px] text-muted-foreground">{statusLabel[lead.status] || lead.status}</span>
            </div>
          </Card>
        ))
      )}
    </div>
  );

  return (
    <div className="space-y-3">
      {/* Barra de controle: pausar/retomar. Mostra também quando a campanha foi
          auto-pausada por uma ligação prioritária (avulsa). */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          {loading && (<><Loader2 className="w-3 h-3 animate-spin" /> Carregando fila…</>)}
          {paused && (
            <Badge className="bg-amber-500/10 text-amber-600 border-amber-500/20">
              {pausedReason === "priority-call" ? "Pausada — ligação prioritária em andamento" : "Campanha pausada"}
            </Badge>
          )}
        </div>
        {sessionId && (
          paused ? (
            <Button size="sm" onClick={doResume} disabled={busy} className="gap-1.5 bg-emerald-600 hover:bg-emerald-500">
              <Play className="w-3.5 h-3.5" /> Retomar
            </Button>
          ) : (
            <Button size="sm" variant="outline" onClick={doPause} disabled={busy} className="gap-1.5">
              <Pause className="w-3.5 h-3.5" /> Pausar
            </Button>
          )
        )}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Column title="Na fila" icon={<PhoneCall className="w-4 h-4" />} tint="text-sky-500" items={pending}
          emptyHint="Ninguém aguardando." />
        <Column title="Discando" icon={<PhoneOutgoing className="w-4 h-4" />} tint="text-amber-500" items={active}
          emptyHint="Nenhuma ligação em andamento." />
        <Column title="Atendidas / Concluídas" icon={<CheckCircle2 className="w-4 h-4" />} tint="text-emerald-500" items={done}
          emptyHint="Ainda sem atendimentos." />
        <Column title="Não atenderam / Falha" icon={<XCircle className="w-4 h-4" />} tint="text-rose-500" items={failed}
          emptyHint="Nenhuma falha até agora." />
      </div>
    </div>
  );
}
