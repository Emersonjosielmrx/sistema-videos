import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Bot } from "lucide-react";
import { useEffect } from "react";
import { apiPut } from "@/lib/api";
import { fetchAIModels, testAIKey } from "@/services/aimodels";
import { Field, ToggleField } from "@/components/ui/field";
import { CredentialSelect } from "@/components/settings/CredentialSelect";
import { logError } from "@/lib/log";
import type { AgentConfig } from "@/types/settings";

const providers = [
  { value: "anthropic", label: "Anthropic (Claude)" },
  { value: "openai", label: "OpenAI" },
  { value: "gemini", label: "Google Gemini" },
  { value: "groq", label: "Groq" },
  { value: "custom", label: "Custom / Proxy (compatível OpenAI)" },
];

function AttendantForm({ initial, onSaved }: {
  initial: AgentConfig;
  onSaved: () => void;
}) {
  const [cfg, setCfg] = useState<AgentConfig>(initial);
  const [saving, setSaving] = useState(false);
  const [models, setModels] = useState<string[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [testing, setTesting] = useState(false);
  const isCustom = cfg.provider === "custom";

  const loadModels = async () => {
    if ((!cfg.api_key && !cfg.credential_id) || !cfg.provider) {
      toast.error("Selecione uma credencial ou preencha provider e API Key primeiro");
      return;
    }
    setLoadingModels(true);
    try {
      const list = await fetchAIModels(cfg.provider, cfg.api_key, cfg.base_url, cfg.credential_id);
      setModels(list);
      toast.success(`${list.length} modelos encontrados`);
    } catch (e) {
      toast.error("Erro ao buscar modelos", { description: (e as Error).message });
    } finally {
      setLoadingModels(false);
    }
  };

  const testKey = async () => {
    if (!cfg.api_key || !cfg.provider) {
      toast.error("Preencha provider e API Key primeiro");
      return;
    }
    setTesting(true);
    try {
      const r = await testAIKey(cfg.provider, cfg.api_key, cfg.base_url, cfg.model);
      if (r.ok) toast.success("Chave OK! A IA respondeu.");
      else toast.error("Chave não funcionou", { description: r.error });
    } catch (e) {
      toast.error("Erro ao testar", { description: (e as Error).message });
    } finally {
      setTesting(false);
    }
  };

  useEffect(() => {
    if (!cfg.system_message) {
      setCfg((c) => ({
        ...c,
        system_message: "Você é um assistente virtual de atendimento ao cliente. Responda de forma educada, clara e objetiva.\n\nSuas responsabilidades:\n- Responder perguntas sobre produtos e serviços\n- Ajudar com dúvidas e suporte\n- Encaminhar para um humano quando não souber resolver\n\nRegras:\n- Trate cada pessoa com respeito e paciência.\n- Não invente informações — se não souber, diga que vai verificar.",
      }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const save = async () => {
    setSaving(true);
    try {
      await apiPut("/api/settings/attendant", cfg);
      toast.success("Agente Especializado salvo");
      onSaved();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card className="p-4 space-y-3">
      <ToggleField
        label="Ativado"
        hint="Liga/desliga o Agente Especializado. Quando ativo, usa esta config em vez de herdar a IA Padrão."
        checked={cfg.enabled}
        onChange={(v) => setCfg({ ...cfg, enabled: v })}
      />
      <Field label="Credencial de IA" hint="Escolha uma credencial já cadastrada. A chave é resolvida no servidor — não precisa colar de novo.">
        <CredentialSelect
          type="llm"
          value={cfg.credential_id ?? ""}
          onChange={(id, cred) => {
            setCfg({ ...cfg, credential_id: id, ...(id ? { api_key: "", provider: cred?.provider || cfg.provider, base_url: cred?.base_url || "" } : {}) });
            setModels([]);
            if (id && cred) {
              fetchAIModels(cred.provider, "", cred.base_url, id).then(setModels).catch(logError("DualAgent/models"));
            }
          }}
        />
      </Field>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Provider" hint="Provedor de IA. Se vazio, herda da IA Padrão.">
          <select
            className="w-full rounded-md border bg-background px-3 py-2 text-sm"
            value={cfg.provider}
            onChange={(e) => setCfg({ ...cfg, provider: e.target.value })}
          >
            <option value="">Herdar da IA Padrão</option>
            {providers.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
          </select>
        </Field>
        <Field label="Modelo" hint={isCustom ? "Digite o nome exato do modelo." : "Clique em 'Buscar' para listar modelos disponíveis."}>
          <div className="flex gap-2">
            {models.length > 0 && !isCustom ? (
              <select className="w-full rounded-md border bg-background px-3 py-2 text-sm" value={cfg.model} onChange={(e) => setCfg({ ...cfg, model: e.target.value })}>
                <option value="">Selecione...</option>
                {models.map((m) => <option key={m} value={m}>{m}</option>)}
              </select>
            ) : (
              <Input className="flex-1" name="agent-model" autoComplete="off" value={cfg.model} onChange={(e) => setCfg({ ...cfg, model: e.target.value })} placeholder="claude-sonnet-4-20250514" />
            )}
            {!isCustom && cfg.provider && (
              <Button type="button" variant="outline" size="sm" onClick={loadModels} disabled={loadingModels}>
                {loadingModels ? "..." : "Buscar"}
              </Button>
            )}
          </div>
        </Field>
      </div>
      {!cfg.credential_id && (
        <div className="grid grid-cols-2 gap-3">
          <Field label="API Key" hint="Chave do provider. Se vazia, herda da IA Padrão.">
            <Input type="password" name="agent-apikey" autoComplete="new-password" value={cfg.api_key} onChange={(e) => setCfg({ ...cfg, api_key: e.target.value })} placeholder="sk-..." />
          </Field>
          <Field label="Base URL" hint="URL base da API. Para proxies ou providers customizados.">
            <Input value={cfg.base_url} onChange={(e) => setCfg({ ...cfg, base_url: e.target.value })} placeholder="https://api.anthropic.com" />
          </Field>
        </div>
      )}
      <Field
        label="System Prompt"
        hint="Instruções de comportamento do agente que conversa com clientes — tom de voz, abordagem, como tratar objeções, etc."
      >
        <Textarea
          value={cfg.system_message}
          onChange={(e) => setCfg({ ...cfg, system_message: e.target.value })}
          rows={5}
          placeholder="Você é um assistente virtual de atendimento ao cliente..."
        />
      </Field>
      <div className="flex gap-2">
        <Button onClick={save} disabled={saving} size="sm">Salvar Agente</Button>
        <Button type="button" variant="outline" size="sm" onClick={testKey} disabled={testing}>
          {testing ? "Testando..." : "Testar chave"}
        </Button>
      </div>
    </Card>
  );
}

const defaultAttendant: AgentConfig = { enabled: false, provider: "", model: "", api_key: "", base_url: "", system_message: "" };

// Deprecated: the manager agent config moved to ManagerAgentSettings.
// This component now only manages the specialized attendant agent.
export function DualAgentSettings({ attendant, manager: _unused, onSaved }: {
  attendant?: AgentConfig;
  manager?: AgentConfig; // kept for compatibility; manager config moved to ManagerAgentSettings
  onSaved: () => void;
}) {
  return (
    <div className="mt-4 space-y-4">
      <Card className="p-4 bg-amber-500/5 border-amber-500/20">
        <div className="flex items-center gap-2 mb-1">
          <Bot className="w-4 h-4 text-amber-400" />
          <h4 className="font-semibold text-sm">Agentes Especializados</h4>
          <Badge variant="secondary"> factory</Badge>
        </div>
        <p className="text-xs text-slate-400">
          Aqui você cria agentes de atendimento que respondem CLIENTES no WhatsApp.
          Cada agente pode ter um <strong className="text-foreground">prompt diferente</strong> —
          por produto, campanha ou etapa do funil. Quando um cliente chegar com certa tag/etiqueta,
          o sistema pode direcionar pra um agente específico.
        </p>
        <p className="text-xs text-slate-500 mt-2">
          O Agente Gerenciador (Telegram + WhatsApp da dona) fica na aba anterior — ele é o "cérebro central"
          que opera o sistema. Este aqui é o <em>atendente</em> que conversa com seus clientes.
        </p>
      </Card>

      <div className="rounded-md bg-muted/50 p-3 text-sm text-muted-foreground">
        Deixe em branco para herdar a <strong className="text-foreground">IA Padrão</strong>.
        Configure aqui se quiser um modelo/prompt <em>diferente</em> para os clientes.
      </div>

      <AttendantForm
        initial={attendant || defaultAttendant}
        onSaved={onSaved}
      />
    </div>
  );
}
