import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Field } from "@/components/ui/field";
import { Select } from "@/components/ui/select";
import { updateWebhook, testWebhook } from "@/services/settings";
import { t } from "@/lib/i18n";
import type { WebhookSettings as WebhookCfg } from "@/types/settings";

const availableEvents = [
  "call.started", "call.ringing", "call.connected", "call.ended",
  "message.received", "message.sent", "session.connected", "session.disconnected",
  "stage_change", "ai_field_detected", "call_summary", "campaign_progress",
];

// Nome amigavel (PT) mostrado no botao + descricao no tooltip. O valor tecnico
// (call.started etc.) continua sendo o que vai salvo/enviado no webhook.
const eventLabels: Record<string, string> = {
  "call.started": "Chamada iniciada",
  "call.ringing": "Telefone tocando",
  "call.connected": "Chamada atendida",
  "call.ended": "Chamada encerrada",
  "message.received": "Mensagem recebida",
  "message.sent": "Mensagem enviada",
  "session.connected": "Numero conectado",
  "session.disconnected": "Numero desconectado",
  "stage_change": "Mudanca de etapa",
  "ai_field_detected": "Campo detectado pela IA",
  "call_summary": "Resumo da ligacao",
  "campaign_progress": "Progresso da campanha",
};

const eventHints: Record<string, string> = {
  "call.started": "Quando uma chamada e iniciada (voce disca ou recebe)",
  "call.ringing": "Quando o telefone comeca a tocar",
  "call.connected": "Quando a chamada e atendida e a conexao e estabelecida",
  "call.ended": "Quando a chamada e encerrada",
  "message.received": "Quando uma mensagem de WhatsApp e recebida",
  "message.sent": "Quando uma mensagem e enviada com sucesso",
  "session.connected": "Quando um numero do WhatsApp se conecta",
  "session.disconnected": "Quando um numero se desconecta (queda ou banimento)",
  "stage_change": "Quando o pipeline/atendimento avanca de etapa (ex: new -> qualified)",
  "ai_field_detected": "Quando a IA detecta uma intencao significativa (ex: quer contratar, falar com humano)",
  "call_summary": "Apos o fim de uma ligacao com transcricao e resumo gerado por IA",
  "campaign_progress": "Cada atualizacao de status durante uma campanha de ligacao",
};

const channelOptions: { value: WebhookCfg["notification_channel"]; label: string }[] = [
  { value: "webhook", label: "Webhook (POST para URL)" },
  { value: "telegram", label: "Telegram" },
  { value: "whatsapp", label: "WhatsApp" },
  { value: "app", label: "App (BETA - em breve)" },
];

export function WebhookSettings({ initial, onSaved }: { initial: WebhookCfg; onSaved: () => void }) {
  const [cfg, setCfg] = useState<WebhookCfg>({
    ...initial,
    events: initial.events ?? [],
    notification_channel: initial.notification_channel ?? "webhook",
    whatsapp_notify_number: initial.whatsapp_notify_number ?? "",
  });
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);

  const toggleEvent = (ev: string) => {
    const events = cfg.events.includes(ev) ? cfg.events.filter((e) => e !== ev) : [...cfg.events, ev];
    setCfg({ ...cfg, events });
  };

  const save = async () => {
    setSaving(true);
    try {
      await updateWebhook(cfg);
      toast.success(t("saved_success"));
      onSaved();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const test = async () => {
    setTesting(true);
    try {
      const res = await testWebhook();
      toast.success(t("test_success") + " (status: " + res.status_code + ")");
    } catch (e) {
      toast.error(t("test_failed") + ": " + (e as Error).message);
    } finally {
      setTesting(false);
    }
  };

  return (
    <Card className="mt-4 bg-glass border-border/50 shadow-soft overflow-hidden">
      <div className="border-b border-border/50 bg-muted/20 px-6 py-4 flex items-center justify-between">
        <div>
          <h4 className="font-bold flex items-center gap-2 text-primary">
            Event-Driven Webhooks & Retry Policies
          </h4>
          <p className="text-xs text-muted-foreground mt-1">
            Integre os eventos da plataforma ao seu próprio servidor via Pub/Sub.
          </p>
        </div>
      </div>
      
      <div className="p-6 space-y-6">

        <Field
          label="URL do Webhook Principal"
          hint="Endereco do seu servidor que recebera as notificacoes (Pub/Sub). O servidor deve aceitar POST com JSON."
        >
          <Input value={cfg.url} onChange={(e) => setCfg({ ...cfg, url: e.target.value })} placeholder="https://seu-site.com/webhook" className="rounded-xl bg-background" />
        </Field>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 border border-border/50 bg-background/50 rounded-xl space-y-2">
           <h4 className="text-sm font-bold text-amber-500">Política de Retry (Retentativa)</h4>
           <p className="text-xs text-muted-foreground">
             Se o seu servidor retornar erro ou timeout, o webhook é reenviado automaticamente algumas
             vezes. Após esgotar as tentativas, o evento é marcado como falho (dead-letter) e registrado
             com o último erro.
           </p>
        </div>
        <div className="p-4 border border-rose-500/30 bg-rose-500/5 rounded-xl space-y-2">
           <h4 className="text-sm font-bold text-rose-500">Dead-Letter Queue (DLQ)</h4>
           <p className="text-xs text-muted-foreground">
             Webhooks que falharam em todas as tentativas ficam guardados com o motivo do erro. A tela de
             consulta e reprocessamento manual da fila ainda está em desenvolvimento.
           </p>
        </div>
      </div>

      <div className="flex flex-col gap-5">
        <Field
          label="Canal de notificacao"
          hint="Escolha para onde as notificacoes de eventos serao enviadas."
        >
          <Select
            options={channelOptions}
            value={cfg.notification_channel}
            onChange={(e) => setCfg({ ...cfg, notification_channel: e.target.value as WebhookCfg["notification_channel"] })}
          />
        </Field>

        {cfg.notification_channel === "whatsapp" && (
          <Field
            label="Numero para notificacao WhatsApp"
            hint="Digite o numero com codigo do pais, ex: 5511999999999"
          >
            <Input
              value={cfg.whatsapp_notify_number}
              onChange={(e) => setCfg({ ...cfg, whatsapp_notify_number: e.target.value.replace(/\D/g, "") })}
              placeholder="5511999999999"
              type="tel"
            />
          </Field>
        )}

        {cfg.notification_channel === "app" && (
          <p className="text-xs text-muted-foreground italic">
            O canal App ainda esta em desenvolvimento. Esta funcao sera ativada em breve.
          </p>
        )}
      </div>

        <div className="space-y-3 bg-muted/20 p-4 rounded-xl border border-border/50">
          <Field
            label="Tópicos de Inscrição (Topics)"
            hint="Escolha quais eventos disparam um payload para o seu Webhook (Pub/Sub)."
          >
            <div className="flex flex-wrap gap-2 mt-2">
              {availableEvents.map((ev) => (
                <button
                  key={ev}
                  title={eventHints[ev] || ev}
                  onClick={() => toggleEvent(ev)}
                  className={"rounded-lg border px-3 py-1.5 text-xs font-semibold transition-all shadow-sm " + (
                    cfg.events.includes(ev) ? "border-primary bg-primary text-primary-foreground shadow-glow" : "border-border/50 bg-background text-muted-foreground hover:bg-muted"
                  )}
                >
                  {eventLabels[ev] || ev}
                </button>
              ))}
            </div>
          </Field>
        </div>

        <div className="flex gap-3 pt-4 border-t border-border/50">
          <Button onClick={save} disabled={saving} className="rounded-xl shadow-glow bg-primary hover:bg-primary/90 text-primary-foreground">
             {saving ? t("loading") : t("save")}
          </Button>
          <Button variant="outline" onClick={test} disabled={testing || (!cfg.url && cfg.notification_channel === "webhook")} className="rounded-xl">
             {t("test_webhook")}
          </Button>
        </div>
      </div>
    </Card>
  );
}
