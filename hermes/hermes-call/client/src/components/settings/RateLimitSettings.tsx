import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { Field, ToggleField } from "@/components/ui/field";
import { updateRateLimit } from "@/services/security";
import type { RateLimitConfig } from "@/types/settings";

export function RateLimitSettings({ initial, onSaved }: { initial: RateLimitConfig; onSaved: () => void }) {
  const [cfg, setCfg] = useState<RateLimitConfig>(initial);
  const [saving, setSaving] = useState(false);

  const save = async () => {
    setSaving(true);
    try {
      await updateRateLimit(cfg);
      toast.success("Rate limit salvo");
      onSaved();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card className="p-6 space-y-5">
      <ToggleField
        label="Rate Limit ativo"
        hint="Liga/desliga a limitacao de mensagens. Quando ativo, clientes que enviam muitas mensagens em pouco tempo recebem uma mensagem de cooldown."
        checked={cfg.enabled}
        onChange={(v) => setCfg({ ...cfg, enabled: v })}
      />

      <Field
        label="Maximo de mensagens"
        hint="Quantidade maxima de mensagens que um cliente pode enviar dentro da janela de tempo. Acima disso, recebe a mensagem de cooldown."
      >
        <Input type="number" value={cfg.max_messages} onChange={(e) => setCfg({ ...cfg, max_messages: Number(e.target.value) })} />
      </Field>

      <Field
        label="Janela de tempo (segundos)"
        hint="Janela de tempo em segundos usada para contar as mensagens. Ex: 60 = conta as mensagens dos ultimos 60 segundos."
      >
        <Input type="number" value={cfg.window_seconds} onChange={(e) => setCfg({ ...cfg, window_seconds: Number(e.target.value) })} />
      </Field>

      <Field
        label="Mensagem de cooldown"
        hint="Mensagem enviada automaticamente para o cliente quando ele excede o limite de mensagens."
      >
        <Textarea value={cfg.cooldown_message} onChange={(e) => setCfg({ ...cfg, cooldown_message: e.target.value })} placeholder="Muitas mensagens. Aguarde um momento..." />
      </Field>

      <Button onClick={save} disabled={saving}>{saving ? "Salvando..." : "Salvar"}</Button>
    </Card>
  );
}
