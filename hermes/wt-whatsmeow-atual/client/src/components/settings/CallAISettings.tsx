import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { ToggleField } from "@/components/ui/field";
import { CredentialSelect } from "@/components/settings/CredentialSelect";
import { apiPut } from "@/lib/api";
import { fetchAIModels, testAIKey } from "@/services/aimodels";
import { t } from "@/lib/i18n";
import type { CallAISettings as CallAICfg } from "@/types/settings";
import { Zap, CheckCircle2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const providers = [
  { value: "gemini", label: "Google Gemini (recomendado para ligação)" },
  { value: "anthropic", label: "Anthropic (Claude)" },
  { value: "openai", label: "OpenAI" },
  { value: "groq", label: "Groq" },
  { value: "custom", label: "Custom / Proxy (compatível OpenAI)" },
];

export function CallAISettings({ initial, onSaved }: { initial: CallAICfg; onSaved: () => void }) {
  // Se o provider vier vazio do servidor, o <select> mostra a 1ª opção mas o
  // estado fica "" (bug: busca/teste vão com provider vazio → 400). Defaulta.
  const [cfg, setCfg] = useState<CallAICfg>({ ...initial, provider: initial.provider || "gemini" });
  const [saving, setSaving] = useState(false);
  const [models, setModels] = useState<string[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [testing, setTesting] = useState(false);
  const isCustom = cfg.provider === "custom";

  const loadModels = async () => {
    // Aceita credencial vinculada OU chave manual — o backend resolve a chave
    // real quando vem credential_id. Só trava se não houver nenhum dos dois.
    if (!cfg.api_key && !cfg.credential_id) {
      toast.error("Preencha a API Key ou selecione uma credencial primeiro");
      return;
    }
    setLoadingModels(true);
    try {
      const list = await fetchAIModels(cfg.provider, cfg.api_key, cfg.api_base_url, cfg.credential_id);
      setModels(list);
      toast.success(`${list.length} modelos encontrados`);
    } catch (e) {
      toast.error("Erro ao buscar modelos", { description: (e as Error).message });
    } finally {
      setLoadingModels(false);
    }
  };

  const testKey = async () => {
    if (!cfg.api_key) {
      toast.error("Preencha a API Key primeiro");
      return;
    }
    setTesting(true);
    try {
      const r = await testAIKey(cfg.provider, cfg.api_key, cfg.api_base_url, cfg.model);
      if (r.ok) toast.success("Chave OK! A IA respondeu.");
      else toast.error("Chave não funcionou", { description: r.error });
    } catch (e) {
      toast.error("Erro ao testar", { description: (e as Error).message });
    } finally {
      setTesting(false);
    }
  };

  const save = async () => {
    setSaving(true);
    try {
      await apiPut("/api/settings/call-ai", cfg);
      toast.success(t("saved_success"));
      onSaved();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card className="bg-glass border-border/50 shadow-soft overflow-hidden mt-4">
      <div className="p-4 border-b border-border/50 bg-muted/20 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Zap className="w-5 h-5 text-emerald-500" />
          <h3 className="font-bold text-sm">IA da Ligação (Via Rápida)</h3>
        </div>
        <Badge variant="outline" className={cn("gap-1.5 px-2", cfg.enabled ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" : "bg-muted text-muted-foreground")}>
           <div className={cn("w-2 h-2 rounded-full", cfg.enabled ? "bg-emerald-500 animate-pulse" : "bg-muted-foreground")}></div>
           {cfg.enabled ? "Ativo" : "Desligado"}
        </Badge>
      </div>

      <div className={cn("p-6 space-y-6 transition-opacity", !cfg.enabled && "opacity-50")}>
        <div className="rounded-md bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 p-4 text-sm text-muted-foreground">
          <strong className="text-blue-700 dark:text-blue-400">IA da Ligação (via rápida).</strong> Esta credencial é usada exclusivamente durante as <strong className="text-foreground">chamadas de voz em tempo real</strong>. Configure aqui um modelo mais rápido e barato (ex: Gemini Flash) separado da IA padrão, para que a ligação seja fluida mesmo se a IA principal estiver ocupada ou lenta. Se deixar desligada, usa a IA padrão.
        </div>

        <div className="flex items-center justify-between p-4 bg-background/50 rounded-xl border border-border/50">
          <div>
             <p className="font-semibold">Ativação da Inteligência Separada</p>
             <p className="text-xs text-muted-foreground mt-0.5">Liga/desliga o uso de uma credencial dedicada durante chamadas de voz.</p>
          </div>
          <ToggleField label="" checked={cfg.enabled} onChange={(v) => setCfg({ ...cfg, enabled: v })} />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1">
            <label className="text-sm font-semibold">Provedor de IA (Provider)</label>
            <Select options={providers} value={cfg.provider} onChange={(e) => setCfg({ ...cfg, provider: e.target.value })} />
          </div>

          <div className="space-y-1">
            <label className="text-sm font-semibold">Credencial Vinculada</label>
            <CredentialSelect
              type="llm"
              value={cfg.credential_id ?? ""}
              onChange={(id, cred) =>
                setCfg({
                  ...cfg,
                  credential_id: id,
                  ...(id
                    ? { api_key: "", provider: cred?.provider || cfg.provider, api_base_url: cred?.base_url || "" }
                    : {}),
                })
              }
            />
          </div>
        </div>

        {!cfg.credential_id && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-sm font-semibold">API Key Manual</label>
              <Input type="password" autoComplete="new-password" value={cfg.api_key} onChange={(e) => setCfg({ ...cfg, api_key: e.target.value })} placeholder="Cole aqui a chave da IA rápida..." className="bg-background" />
            </div>

            <div className="space-y-1">
              <label className="text-sm font-semibold">Base URL (opcional)</label>
              <Input value={cfg.api_base_url} onChange={(e) => setCfg({ ...cfg, api_base_url: e.target.value })} placeholder="https://generativelanguage.googleapis.com" className="bg-background" />
            </div>
          </div>
        )}

        <div className="space-y-1">
          <label className="text-sm font-semibold">Modelo de Linguagem (LLM)</label>
          <p className="text-xs text-muted-foreground mb-2">
            {isCustom ? "Proxy/custom não lista modelos automaticamente — digite o nome exato." : "Nome do modelo. Clique em 'Buscar' para listar."}
          </p>
          <div className="flex gap-2">
            {models.length > 0 && !isCustom ? (
              <select
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:ring-2 focus:ring-primary/50"
                value={cfg.model}
                onChange={(e) => setCfg({ ...cfg, model: e.target.value })}
              >
                <option value="">Selecione um modelo...</option>
                {models.map((m) => <option key={m} value={m}>{m}</option>)}
              </select>
            ) : (
              <Input className="flex-1 bg-background" value={cfg.model} onChange={(e) => setCfg({ ...cfg, model: e.target.value })} placeholder={isCustom ? "digite o nome do modelo" : "gemini-2.0-flash-exp, etc..."} />
            )}
            {!isCustom && (
              <Button type="button" variant="secondary" onClick={loadModels} disabled={loadingModels} className="shrink-0">
                {loadingModels ? "Buscando..." : "Buscar modelos"}
              </Button>
            )}
          </div>
        </div>

        <div className="space-y-1 mt-4">
          <label className="text-sm font-semibold">System Prompt (opcional)</label>
          <p className="text-xs text-muted-foreground mb-2">Instruções especiais para o agente durante a ligação. Se vazio, usa o padrão do sistema.</p>
          <Textarea rows={4} value={cfg.system_message} onChange={(e) => setCfg({ ...cfg, system_message: e.target.value })} placeholder="Deixe vazio para usar o padrão do sistema..." className="bg-[#0D1117] text-[#C9D1D9] border-border/50 font-mono text-sm resize-none focus:ring-primary/50" />
        </div>

        <div className="pt-4 border-t border-border/50 flex items-center justify-between">
           <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Zap className="w-4 h-4 text-amber-500" /> Teste a conexão antes de salvar.
           </div>
           <div className="flex items-center gap-2">
              <Button type="button" variant="outline" onClick={testKey} disabled={testing} className="gap-2">
                {testing ? <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-foreground"></span> : <CheckCircle2 className="w-4 h-4" />}
                {testing ? "Diagnosticando..." : "Testar chave"}
              </Button>
              <Button onClick={save} disabled={saving} className="gap-2 shadow-glow">
                <Zap className="w-4 h-4"/> Salvar Motor Ligação
              </Button>
           </div>
        </div>
      </div>
    </Card>
  );
}
