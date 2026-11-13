import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Field, ToggleField } from "@/components/ui/field";
import { updateTelegram, testTelegram } from "@/services/settings";
import { t } from "@/lib/i18n";
import type { TelegramSettings as TelegramCfg } from "@/types/settings";

export function TelegramSettings({ initial, onSaved }: { initial: TelegramCfg; onSaved: () => void }) {
  const [cfg, setCfg] = useState<TelegramCfg>({ ...initial, chat_ids: initial.chat_ids ?? [] });
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);

  const save = async () => {
    setSaving(true);
    try {
      await updateTelegram(cfg);
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
      await testTelegram(cfg.chat_ids[0]);
      toast.success(t("test_success"));
    } catch (e) {
      toast.error(t("test_failed") + ": " + (e as Error).message);
    } finally {
      setTesting(false);
    }
  };

  return (
    <Card className="mt-4 space-y-5 p-4">
      <ToggleField
        label="Telegram ativo"
        hint="Liga/desliga o bot do Telegram. Quando ativo, você pode monitorar e controlar o sistema pelo Telegram."
        checked={cfg.enabled}
        onChange={(v) => setCfg({ ...cfg, enabled: v })}
      />

      <Field
        label="Token do Bot"
        hint="Token do seu bot do Telegram. Obtenha criando um bot via @BotFather no Telegram. O token e as chaves de API ficam salvos no banco de dados."
      >
        <Input type="password" value={cfg.token} onChange={(e) => setCfg({ ...cfg, token: e.target.value })} placeholder="123456:ABC-DEF..." />
      </Field>

      <Field
        label="IDs de chat autorizados"
        hint="IDs numéricos do Telegram que podem enviar comandos (ex: /ligar, /status).IDs separados por vírgula. Quem não estiver na lista será ignorado pelo bot."
      >
        <Input
          value={cfg.chat_ids.join(", ")}
          onChange={(e) => setCfg({ ...cfg, chat_ids: e.target.value.split(",").map((s) => parseInt(s.trim())).filter(Boolean) })}
          placeholder="123456789, 987654321"
        />
      </Field>

      <div className="flex gap-2">
        <Button onClick={save} disabled={saving}>{saving ? t("loading") : t("save")}</Button>
        <Button variant="outline" onClick={test} disabled={testing || !cfg.enabled}>{t("test_connection")}</Button>
      </div>
    </Card>
  );
}
