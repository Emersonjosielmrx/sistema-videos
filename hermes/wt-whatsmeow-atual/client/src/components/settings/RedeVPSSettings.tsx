import { useCallback, useEffect, useState } from "react";
import { Network, Server, Phone } from "lucide-react";
import { apiGet, apiPut } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";

// Rede / VPS (só a dona da plataforma): divide as chamadas do Groq com a VPS 53 e, como
// reserva contra bloqueio de IP, deixa a conexão do WhatsApp de uma linha sair pela outra VPS.
interface RedeVPS {
  groq_via_vps: boolean;
  groq_proxy_configurado: boolean;
  whatsapp_proxy_configurado: boolean;
  linhas: { id: string; nome: string; via_vps: boolean }[];
}

export function RedeVPSSettings() {
  const [cfg, setCfg] = useState<RedeVPS | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      setCfg(await apiGet<RedeVPS>("/api/settings/rede-vps"));
    } catch {
      setCfg(null);
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  const salvar = async (body: Record<string, unknown>, msg: string) => {
    setSaving(true);
    try {
      setCfg(await apiPut<RedeVPS>("/api/settings/rede-vps", body));
      toast.success(msg);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Não foi possível salvar.");
    } finally {
      setSaving(false);
    }
  };

  if (!cfg) {
    return <div className="text-sm text-muted-foreground p-6">Carregando…</div>;
  }

  return (
    <div className="space-y-6">
      <Card className="bg-glass border-border/50 shadow-soft p-6 space-y-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex gap-3">
            <Network className="w-5 h-5 text-emerald-500 mt-0.5 shrink-0" />
            <div>
              <h3 className="font-bold text-sm">Dividir as chamadas do Groq com a VPS 53</h3>
              <p className="text-xs text-muted-foreground mt-1 max-w-xl">
                Uma chamada sai direto do servidor e a seguinte passa pela VPS 53 (209.145.60.53), pra não concentrar
                tudo num IP só. Vale pra IA e pra transcrição (Whisper) da sua conta. Se a VPS cair, a chamada vai direto
                na hora. Cada passagem pela VPS soma cerca de 0,1 s.
              </p>
              {!cfg.groq_proxy_configurado && (
                <p className="text-xs font-semibold text-amber-600 mt-2">
                  A VPS ainda não está configurada no servidor — o botão fica salvo, mas nada muda até configurar.
                </p>
              )}
            </div>
          </div>
          <Switch
            checked={cfg.groq_via_vps}
            disabled={saving}
            onCheckedChange={(v) => salvar({ groq_via_vps: v }, v ? "Groq dividido com a VPS 53." : "Groq todo direto.")}
          />
        </div>
      </Card>

      <Card className="bg-glass border-border/50 shadow-soft p-6 space-y-4">
        <div className="flex gap-3">
          <Server className="w-5 h-5 text-primary mt-0.5 shrink-0" />
          <div>
            <h3 className="font-bold text-sm">WhatsApp pela outra VPS (reserva)</h3>
            <p className="text-xs text-muted-foreground mt-1 max-w-xl">
              As ligações continuam saindo direto. Use isto só se o WhatsApp bloquear o IP do servidor: a conexão da linha
              passa a sair pela outra VPS. Ao ligar ou desligar, a linha reconecta (alguns segundos).
            </p>
            {!cfg.whatsapp_proxy_configurado && (
              <p className="text-xs font-semibold text-amber-600 mt-2">Não configurado no servidor — fica desligado.</p>
            )}
          </div>
        </div>
        <div className="space-y-2">
          {cfg.linhas.length === 0 && <p className="text-xs text-muted-foreground">Nenhuma linha conectada.</p>}
          {cfg.linhas.map((l) => (
            <div key={l.id} className="flex items-center justify-between border border-border/50 rounded-xl px-4 py-2 bg-background/50">
              <span className="flex items-center gap-2 text-sm"><Phone className="w-4 h-4 text-muted-foreground" /> {l.nome}</span>
              <Switch
                checked={l.via_vps}
                disabled={saving || (!cfg.whatsapp_proxy_configurado && !l.via_vps)}
                onCheckedChange={(v) =>
                  salvar({ linha: l.id, whatsapp_via_vps: v }, v ? "Linha passando pela VPS (reconectando)." : "Linha direta (reconectando).")
                }
              />
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
