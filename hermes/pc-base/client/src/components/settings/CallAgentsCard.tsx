import { useEffect, useState } from "react";
import { toast } from "sonner";
import { PhoneCall, PhoneIncoming, PhoneOutgoing, Loader2 } from "lucide-react";
import { apiGet, apiPut, apiErrorMessage, apiErrorStatus } from "@/lib/api";

// Quadro "Ligações" da tela de agentes, com os DOIS papéis lado a lado (são coisas
// diferentes, por isso ficam juntos e com nomes claros):
//   • Quem atende ligações recebidas  → agent_chat.voice_profile_id (salvo pela tela de agentes)
//   • Quem faz as ligações que você pede (Telegram/painel)
//       → GET/PUT /api/call-agent/default {"profile_id"}

type Agent = { id: string; name: string; kind?: string };

const selectCls =
  "w-full bg-background border border-border/50 rounded-md text-sm p-2 focus:ring-1 focus:ring-primary outline-none disabled:opacity-60";

export function CallAgentsCard({
  agents,
  loadingAgents,
  inboundValue,
  onInboundChange,
}: {
  agents: Agent[];
  loadingAgents?: boolean;
  inboundValue: string;
  onInboundChange: (profileId: string) => void;
}) {
  const [outbound, setOutbound] = useState("");
  const [state, setState] = useState<"loading" | "ok" | "unavailable" | "error">("loading");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    apiGet<{ profile_id?: string }>("/api/call-agent/default")
      .then((r) => { setOutbound(r.profile_id || ""); setState("ok"); })
      .catch((e) => setState(apiErrorStatus(e) === 404 ? "unavailable" : "error"));
  }, []);

  const saveOutbound = async (id: string) => {
    const prev = outbound;
    setOutbound(id);
    setSaving(true);
    try {
      await apiPut<{ ok?: boolean }>("/api/call-agent/default", { profile_id: id });
      const name = agents.find((a) => a.id === id)?.name;
      toast.success(id ? `Quem faz as ligações que você pede: ${name || "salvo"}.` : "Agente das ligações que você pede removido.");
    } catch (e) {
      setOutbound(prev);
      toast.error("Não consegui salvar", { description: apiErrorMessage(e, "Tente de novo em instantes.") });
    } finally {
      setSaving(false);
    }
  };

  // Um id salvo que não existe mais na lista (agente apagado) aparece como aviso.
  const missing = (id: string) => !!id && !loadingAgents && !agents.some((a) => a.id === id);

  return (
    <div className="bg-background/40 border border-border/50 rounded-xl p-4 space-y-4">
      <h4 className="text-sm font-bold text-foreground flex items-center gap-2">
        <PhoneCall className="h-4 w-4 text-sky-500" /> Ligações: qual agente fala em cada caso
      </h4>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Recebidas */}
        <div className="space-y-1.5">
          <label htmlFor="inbound-agent" className="text-xs font-bold text-foreground flex items-center gap-1.5">
            <PhoneIncoming className="h-3.5 w-3.5 text-emerald-500" /> Quem atende ligações recebidas
          </label>
          <select
            id="inbound-agent"
            value={inboundValue}
            disabled={loadingAgents}
            onChange={(e) => onInboundChange(e.target.value)}
            className={selectCls}
          >
            <option value="">— Padrão (IA de ligação configurada) —</option>
            {agents.map((a) => (
              <option key={a.id} value={a.id}>{a.name}</option>
            ))}
          </select>
          <p className="text-[11px] text-muted-foreground">Quando alguém liga para o seu WhatsApp, é este agente que atende.</p>
          {missing(inboundValue) && <p className="text-[11px] text-amber-500">O agente salvo não existe mais. Escolha outro.</p>}
        </div>

        {/* Feitas a pedido do dono */}
        <div className="space-y-1.5">
          <label htmlFor="outbound-agent" className="text-xs font-bold text-foreground flex items-center gap-1.5">
            <PhoneOutgoing className="h-3.5 w-3.5 text-sky-500" /> Quem faz as ligações que você pede (Telegram/painel)
          </label>
          {state === "loading" ? (
            <p className="text-xs text-muted-foreground flex items-center gap-2 h-9"><Loader2 className="h-3.5 w-3.5 animate-spin" /> Carregando…</p>
          ) : state === "unavailable" ? (
            <p className="text-xs text-muted-foreground h-9 flex items-center">Disponível depois da próxima atualização do servidor.</p>
          ) : state === "error" ? (
            <p className="text-xs text-destructive h-9 flex items-center">Não consegui carregar. Recarregue a página.</p>
          ) : (
            <div className="flex items-center gap-2">
              <select
                id="outbound-agent"
                value={outbound}
                disabled={saving || loadingAgents}
                onChange={(e) => saveOutbound(e.target.value)}
                className={selectCls}
              >
                <option value="">— Nenhum (usa a IA de ligação configurada) —</option>
                {agents.map((a) => (
                  <option key={a.id} value={a.id}>{a.name}</option>
                ))}
              </select>
              {saving && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground shrink-0" />}
            </div>
          )}
          <p className="text-[11px] text-muted-foreground">Quando você manda ligar para alguém pelo Telegram ou pelo painel, é este agente que liga.</p>
          {state === "ok" && missing(outbound) && <p className="text-[11px] text-amber-500">O agente salvo não existe mais. Escolha outro.</p>}
        </div>
      </div>
    </div>
  );
}
