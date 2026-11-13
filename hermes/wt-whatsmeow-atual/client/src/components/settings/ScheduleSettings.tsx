import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Field, ToggleField } from "@/components/ui/field";
import { Clock } from "lucide-react";
import { Switch } from "@/components/ui/switch";
import { apiPut } from "@/lib/api";
import type { ScheduleConfig } from "@/types/settings";

const DAY_LABELS: Record<string, string> = {
  monday: "Segunda", tuesday: "Terça", wednesday: "Quarta",
  thursday: "Quinta", friday: "Sexta", saturday: "Sábado", sunday: "Domingo",
};

const DAY_KEYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"];

// Mapa nome->int que o backend (internal/schedule) usa: 0=Domingo ... 6=Sabado.
const DAY_INDEX: Record<string, number> = {
  sunday: 0, monday: 1, tuesday: 2, wednesday: 3, thursday: 4, friday: 5, saturday: 6,
};

type DayTuple = { day: number; start: string; end: string; enabled: boolean };
type DayRecord = Record<string, { enabled: boolean; start: string; end: string }>;

// O backend serializa `days` como ARRAY [{day:0,start,end,enabled}]. A UI trabalha
// com um Record por nome. Converte o array recebido no GET pro Record da tela.
// Mantem compatibilidade caso ja venha como Record (ex: estado antigo).
const daysToRecord = (days: unknown): DayRecord => {
  const rec: DayRecord = {};
  if (Array.isArray(days)) {
    for (const d of days as DayTuple[]) {
      const key = DAY_KEYS.find((k) => DAY_INDEX[k] === d.day);
      if (key) rec[key] = { enabled: !!d.enabled, start: d.start || "09:00", end: d.end || "18:00" };
    }
  } else if (days && typeof days === "object") {
    Object.assign(rec, days as DayRecord);
  }
  return rec;
};

// Serializa o Record da tela de volta pro ARRAY que o backend decodifica.
const recordToDays = (rec: DayRecord): DayTuple[] =>
  DAY_KEYS.map((k) => {
    const d = rec[k] || { enabled: false, start: "09:00", end: "18:00" };
    return { day: DAY_INDEX[k], start: d.start, end: d.end, enabled: d.enabled };
  });

interface Props {
  initial: ScheduleConfig;
  onSaved: () => void;
}

export function ScheduleSettings({ initial, onSaved }: Props) {
  const [cfg, setCfg] = useState<ScheduleConfig>(() => ({
    ...initial,
    // Quem nunca configurou recebe do servidor o horário PADRÃO, ligado
    // (seg–sex 09:00–18:00, sáb 09:00–13:00). enabled:false só se a pessoa desligou.
    enabled: initial.enabled === true,
    timezone: initial.timezone || "America/Sao_Paulo",
    days: daysToRecord((initial as { days?: unknown }).days),
  }));
  const [saving, setSaving] = useState(false);

  // Ligar: se nenhum dia estiver configurado, sugere o padrão do servidor —
  // seg–sex 09:00–18:00 e sáb 09:00–13:00 (só vale depois de Salvar).
  const turnOn = () => {
    setCfg((prev) => {
      const anyDay = DAY_KEYS.some((k) => prev.days?.[k]?.enabled);
      if (anyDay) return { ...prev, enabled: true };
      const days: DayRecord = {};
      for (const k of DAY_KEYS) days[k] = { enabled: k !== "sunday", start: "09:00", end: k === "saturday" ? "13:00" : "18:00" };
      return { ...prev, enabled: true, days };
    });
  };

  const setDay = (key: string, field: string, value: string | boolean) => {
    setCfg((prev) => ({
      ...prev,
      days: { ...prev.days, [key]: { ...prev.days[key], [field]: value } },
    }));
  };

  const save = async () => {
    setSaving(true);
    try {
      // Envia no formato que o backend decodifica: days como ARRAY [{day:int,...}].
      await apiPut<{ status: string }>("/api/settings/schedule", {
        enabled: cfg.enabled,
        timezone: cfg.timezone,
        days: recordToDays(cfg.days),
      });
      toast.success(cfg.enabled ? "Horário comercial salvo" : "Horário comercial desligado");
      onSaved();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card className="p-6 space-y-5">
      {/* Situação atual, em linguagem simples. */}
      {cfg.enabled ? (
        <div className="flex items-start gap-3 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-sm">
          <Clock className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
          <p><strong className="text-emerald-500">Ligado:</strong> a IA só atende e liga dentro dos horários abaixo. Dia desligado = dia fechado.</p>
        </div>
      ) : (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-xl border border-border/50 bg-muted/20 p-3 text-sm">
          <div className="flex items-start gap-3">
            <Clock className="h-4 w-4 text-muted-foreground shrink-0 mt-0.5" />
            <p>
              <strong>Desligado:</strong> a IA do chat responde a qualquer hora. As ligações automáticas
              (promessas e novas tentativas) continuam só no horário comercial padrão (seg–sex 9h–18h, sáb 9h–13h).
            </p>
          </div>
          <Button size="sm" variant="outline" onClick={turnOn}>Ligar horário comercial</Button>
        </div>
      )}

      <ToggleField
        label="Horário comercial ativo"
        hint="Ligado: a IA só atende e liga nos horários abaixo; fora deles, fica fechado. Desligado: o chat responde a qualquer hora, mas as ligações automáticas (promessas e novas tentativas) seguem o horário padrão (seg–sex 9h–18h, sáb 9h–13h)."
        checked={cfg.enabled}
        onChange={(v) => (v ? turnOn() : setCfg({ ...cfg, enabled: false }))}
      />

      <Field
        label="Fuso horário"
        hint="Fuso horário usado para calcular o horário comercial. Ex: America/Sao_Paulo para Brasil."
      >
        <Input value={cfg.timezone} onChange={(e) => setCfg({ ...cfg, timezone: e.target.value })} placeholder="America/Sao_Paulo" />
      </Field>

      <Field label="Dias da semana" hint={cfg.enabled ? "Configure o horário de funcionamento de cada dia. Dia desligado = dia FECHADO (sem atendimento nem ligações)." : "Estes horários só passam a valer quando o horário comercial estiver ligado."}>{null}</Field>

      <div className={`space-y-4 ${cfg.enabled ? "" : "opacity-60"}`}>
        {DAY_KEYS.map((key) => {
          const day = cfg.days?.[key] || { enabled: false, start: "09:00", end: "18:00" };
          return (
            <div key={key} className="flex flex-col sm:flex-row sm:items-center gap-3">
              <div className="flex items-center justify-between sm:justify-start gap-3 w-full sm:w-32">
                <span className="text-sm font-medium">{DAY_LABELS[key]}</span>
                <Switch
                  checked={day.enabled}
                  onCheckedChange={(v) => setDay(key, "enabled", v)}
                />
              </div>
              <div className="flex items-center gap-2">
                <Input type="time" className="w-28" value={day.start} onChange={(e) => setDay(key, "start", e.target.value)} disabled={!day.enabled} />
                <span className="text-muted-foreground text-sm">até</span>
                <Input type="time" className="w-28" value={day.end} onChange={(e) => setDay(key, "end", e.target.value)} disabled={!day.enabled} />
              </div>
            </div>
          );
        })}
      </div>

      <Button onClick={save} disabled={saving}>{saving ? "Salvando..." : "Salvar"}</Button>
    </Card>
  );
}
